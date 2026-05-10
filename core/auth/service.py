#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 11:20
@Desc: 认证模块服务
"""

import base64
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from base.base_schema import ErrorCode
from config.config import settings
from config.database import DbSession
from core.auth.schema import CryptoInitInfo, LoginInfo, LogoutInfo, TokenInfo
from core.login_log.service import LoginLogService
from core.user.model import User
from core.user.service import UserService
from utils.mongo import MongoManager
from utils.redis.redis_service import RedisService
from utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)


@dataclass(slots=True)
class AuthRequestContext:
    """
    认证请求上下文。

    Args:
        trace_id: 请求追踪 ID。
        client_ip: 客户端 IP。
        user_agent: 请求头中的 User-Agent。
        request_path: 请求路径。
        request_method: 请求方法。
    """

    trace_id: str | None
    client_ip: str | None
    user_agent: str | None
    request_path: str
    request_method: str


@dataclass(slots=True)
class AuthServiceResult:
    """
    认证服务统一返回结构。

    Args:
        success: 是否成功。
        code: 业务状态码。
        msg: 返回消息。
        data: 返回数据。
    """

    success: bool
    code: int
    msg: str
    data: Any = None


class AuthCryptoService:
    """认证加密服务。"""

    rsa_cache_name = "auth:crypto:rsa"
    aes_cache_name = "auth:crypto:aes"
    cache_ttl = 300
    key_dir = Path(__file__).resolve().parents[2] / "algorithm" / "rsa"
    private_key_file = key_dir / "private.pem"
    public_key_file = key_dir / "public.pem"
    aes_key_dir = Path(__file__).resolve().parents[2] / "algorithm" / "aes"
    aes_key_file = aes_key_dir / "aes.key"

    @staticmethod
    def _b64encode(data: bytes) -> str:
        """
        将字节数据编码为 URL 安全的 Base64 字符串。

        Args:
            data: 原始字节数据。

        Returns:
            str: 去掉补位符后的 Base64 字符串。
        """
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64decode(data: str) -> bytes:
        """
        将 URL 安全的 Base64 字符串解码为字节数据。

        Args:
            data: Base64 字符串。

        Returns:
            bytes: 解码后的字节数据。
        """
        padding_size = (-len(data)) % 4
        return base64.urlsafe_b64decode(f"{data}{'=' * padding_size}")

    @classmethod
    def _rsa_cache_key(cls) -> str:
        """
        获取 RSA 密钥缓存键。

        Returns:
            str: Redis 中 RSA 密钥使用的缓存键。
        """
        return cls.rsa_cache_name

    @classmethod
    def _aes_cache_key(cls) -> str:
        """
        获取 AES 密钥缓存键。

        Returns:
            str: Redis 中 AES 密钥使用的缓存键。
        """
        return cls.aes_cache_name

    @staticmethod
    def _pem_to_base64(pem_text: str) -> str:
        """
        将 PEM 文本转换为纯 Base64 内容。

        Args:
            pem_text: PEM 格式密钥文本。

        Returns:
            str: 去除头尾标识后的 Base64 字符串。
        """
        lines = [
            line.strip()
            for line in pem_text.splitlines()
            if line and not line.startswith("-----")
        ]
        return "".join(lines)

    @staticmethod
    def _base64_to_der(key_text: str) -> bytes:
        """
        将 Base64 编码的 DER 数据还原为字节串。

        Args:
            key_text: Base64 格式密钥内容。

        Returns:
            bytes: DER 字节数据。
        """
        normalized = key_text.strip()
        padding_size = (-len(normalized)) % 4
        return base64.b64decode(f"{normalized}{'=' * padding_size}")

    @staticmethod
    def _serialize_private_key(private_key: rsa.RSAPrivateKey) -> str:
        """
        序列化 RSA 私钥为 PEM 文本。

        Args:
            private_key: RSA 私钥对象。

        Returns:
            str: PEM 格式私钥文本。
        """
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

    @staticmethod
    def _serialize_public_key(public_key: rsa.RSAPublicKey) -> str:
        """
        序列化 RSA 公钥为 PEM 文本。

        Args:
            public_key: RSA 公钥对象。

        Returns:
            str: PEM 格式公钥文本。
        """
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    @classmethod
    def _payload(
        cls,
        private_pem: str,
        public_pem: str,
        aes_key: str,
    ) -> dict[str, Any]:
        """
        组装统一的密钥缓存结构。

        Args:
            private_pem: PEM 格式 RSA 私钥文本。
            public_pem: PEM 格式 RSA 公钥文本。
            aes_key: Base64 编码的 AES 密钥。

        Returns:
            dict[str, Any]: 统一缓存结构，供 Redis 和接口返回复用。
        """
        return {
            "rsa_private_key": cls._pem_to_base64(private_pem),
            "rsa_public_key": cls._pem_to_base64(public_pem),
            "rsa_algorithm": "RSA-OAEP-SHA256",
            "aes_key": aes_key,
            "aes_algorithm": "AES-256-GCM",
        }

    @classmethod
    def _read_aes_key_file(cls) -> str | None:
        """
        读取本地 AES 密钥文件。

        Returns:
            str | None: Base64 编码的 AES 密钥；文件不存在时返回 None。
        """
        if not cls.aes_key_file.exists():
            return None
        return cls.aes_key_file.read_text(encoding="utf-8").strip()

    @classmethod
    def _generate_aes_key_file(cls) -> str:
        """
        生成并写入本地 AES 密钥文件。

        Returns:
            str: Base64 编码的 AES 密钥。
        """
        cls.aes_key_dir.mkdir(parents=True, exist_ok=True)
        aes_key = cls._b64encode(os.urandom(32))
        cls.aes_key_file.write_text(aes_key, encoding="utf-8")
        try:
            os.chmod(cls.aes_key_file, 0o600)
        except OSError:
            pass
        return aes_key

    @classmethod
    def _ensure_aes_key_file(cls) -> str:
        """
        确保本地存在可用的 AES 密钥文件。

        Returns:
            str: Base64 编码的 AES 密钥。
        """
        aes_key = cls._read_aes_key_file()
        if aes_key:
            return aes_key
        return cls._generate_aes_key_file()

    @classmethod
    def _read_pem_files(cls) -> dict[str, Any] | None:
        """
        读取本地 RSA 密钥文件，并补齐缺失的公钥文件。

        Returns:
            dict[str, Any] | None: 密钥缓存结构；私钥文件不存在时返回 None。
        """
        if not cls.private_key_file.exists():
            return None

        private_pem = cls.private_key_file.read_text(encoding="utf-8")
        aes_key = cls._ensure_aes_key_file()

        if cls.public_key_file.exists():
            public_pem = cls.public_key_file.read_text(encoding="utf-8")
        else:
            private_key = serialization.load_pem_private_key(
                private_pem.encode("utf-8"),
                password=None,
            )
            public_pem = cls._serialize_public_key(private_key.public_key())
            cls.key_dir.mkdir(parents=True, exist_ok=True)
            cls.public_key_file.write_text(public_pem, encoding="utf-8")

        return cls._payload(private_pem, public_pem, aes_key)

    @classmethod
    def _generate_pem_files(cls) -> dict[str, Any]:
        """
        生成 RSA 密钥对并写入本地 PEM 文件。

        Returns:
            dict[str, Any]: 密钥缓存结构。
        """
        cls.key_dir.mkdir(parents=True, exist_ok=True)
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = cls._serialize_private_key(private_key)
        public_pem = cls._serialize_public_key(private_key.public_key())
        aes_key = cls._ensure_aes_key_file()

        cls.private_key_file.write_text(private_pem, encoding="utf-8")
        cls.public_key_file.write_text(public_pem, encoding="utf-8")

        try:
            os.chmod(cls.private_key_file, 0o600)
            os.chmod(cls.public_key_file, 0o644)
        except OSError:
            pass

        return cls._payload(private_pem, public_pem, aes_key)

    @classmethod
    def generate_rsa_key_pair(cls, overwrite: bool = False) -> CryptoInitInfo:
        """
        生成或读取本地 RSA 密钥对。

        Args:
            overwrite: 是否强制覆盖已有密钥文件。

        Returns:
            CryptoInitInfo: 初始化接口所需的公钥信息。
        """
        if (
            not overwrite
            and cls.private_key_file.exists()
            and cls.public_key_file.exists()
        ):
            payload = cls._read_pem_files()
            if payload is not None:
                return CryptoInitInfo(
                    rsaPublicKey=payload["rsa_public_key"],
                    aesKey=cls._ensure_aes_key_file(),
                )

        payload = cls._generate_pem_files()
        return CryptoInitInfo(
            rsaPublicKey=payload["rsa_public_key"],
            aesKey=payload["aes_key"],
        )

    @classmethod
    def generate_aes_key(cls, overwrite: bool = False) -> str:
        """
        生成或读取本地 AES 密钥文件。

        Args:
            overwrite: 是否强制覆盖已有密钥文件。

        Returns:
            str: Base64 编码的 AES 密钥。
        """
        if overwrite:
            return cls._generate_aes_key_file()
        return cls._ensure_aes_key_file()

    @classmethod
    def generate_crypto_keys(cls, overwrite: bool = False) -> CryptoInitInfo:
        """
        统一生成或读取 RSA 与 AES 密钥。

        Args:
            overwrite: 是否强制覆盖已有密钥文件。

        Returns:
            CryptoInitInfo: 初始化接口所需的密钥信息。
        """
        if overwrite:
            cls._generate_aes_key_file()
        else:
            cls._ensure_aes_key_file()
        return cls.generate_rsa_key_pair(overwrite=overwrite)

    @staticmethod
    def create_password_hash(password: str, algorithm: str = "bcrypt") -> str:
        """
        生成不可逆密码摘要。

        Args:
            password: 明文密码。
            algorithm: 摘要算法名称。

        Returns:
            str: 加密后的密码摘要。
        """
        return hash_password(password=password, algorithm=algorithm)

    @staticmethod
    def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
        """
        校验明文密码与摘要是否匹配。

        Args:
            plain_password: 明文密码。
            hashed_password: 数据库存储的密码摘要。

        Returns:
            bool: 是否匹配。
        """
        return verify_password(
            plain_password=plain_password,
            hashed_password=hashed_password,
        )

    @classmethod
    async def _cache_payload(
        cls,
        redis_service: RedisService,
        payload: dict[str, Any],
    ) -> None:
        """
        写入共享密钥缓存。

        Args:
            redis_service: Redis 服务实例。
            payload: 需要缓存的密钥数据。
        """
        rsa_payload = {
            "rsa_private_key": payload["rsa_private_key"],
            "rsa_public_key": payload["rsa_public_key"],
            "rsa_algorithm": payload.get("rsa_algorithm", "RSA-OAEP-SHA256"),
        }
        aes_payload = {
            "aes_key": payload["aes_key"],
            "aes_algorithm": payload.get("aes_algorithm", "AES-256-GCM"),
        }
        await redis_service.set(
            cls._rsa_cache_key(),
            rsa_payload,
            ex=cls.cache_ttl,
        )
        await redis_service.set(
            cls._aes_cache_key(),
            aes_payload,
            ex=cls.cache_ttl,
        )

    @classmethod
    def _merge_payloads(
        cls,
        rsa_payload: dict[str, Any],
        aes_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        合并 RSA 与 AES 缓存结构。

        Args:
            rsa_payload: RSA 密钥缓存数据。
            aes_payload: AES 密钥缓存数据。

        Returns:
            dict[str, Any]: 合并后的完整密钥结构。
        """
        return {
            "rsa_private_key": rsa_payload["rsa_private_key"],
            "rsa_public_key": rsa_payload["rsa_public_key"],
            "rsa_algorithm": rsa_payload.get("rsa_algorithm", "RSA-OAEP-SHA256"),
            "aes_key": aes_payload["aes_key"],
            "aes_algorithm": aes_payload.get("aes_algorithm", "AES-256-GCM"),
        }

    @classmethod
    def _normalize_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """
        兼容旧版缓存结构，统一转换为当前字段格式。

        Args:
            payload: 原始缓存数据。

        Returns:
            dict[str, Any]: 标准化后的缓存结构。
        """
        normalized = dict(payload)
        private_key = normalized.get("rsa_private_key")
        public_key = normalized.get("rsa_public_key")

        if isinstance(private_key, str) and "BEGIN" in private_key:
            normalized["rsa_private_key"] = cls._pem_to_base64(private_key)
        if isinstance(public_key, str) and "BEGIN" in public_key:
            normalized["rsa_public_key"] = cls._pem_to_base64(public_key)

        if not normalized.get("rsa_private_key") and normalized.get("rsa_private_key_base64"):
            normalized["rsa_private_key"] = normalized["rsa_private_key_base64"]
        if not normalized.get("rsa_public_key") and normalized.get("rsa_public_key_base64"):
            normalized["rsa_public_key"] = normalized["rsa_public_key_base64"]

        normalized.pop("rsa_private_key_base64", None)
        normalized.pop("rsa_public_key_base64", None)
        return normalized

    @classmethod
    async def _ensure_payload(cls, redis_service: RedisService) -> dict[str, Any]:
        """
        确保 Redis 中存在可用密钥；Redis 缺失时从文件恢复或重新生成。

        Args:
            redis_service: Redis 服务实例。

        Returns:
            dict[str, Any]: 可直接用于加解密的密钥缓存结构。
        """
        rsa_cache_key = cls._rsa_cache_key()
        aes_cache_key = cls._aes_cache_key()

        rsa_payload = await redis_service.get(rsa_cache_key)
        aes_payload = await redis_service.get(aes_cache_key)
        if isinstance(rsa_payload, dict) and isinstance(aes_payload, dict):
            normalized_rsa = cls._normalize_payload(rsa_payload)
            normalized_aes = dict(aes_payload)
            if not normalized_aes.get("aes_key"):
                normalized_aes["aes_key"] = cls._ensure_aes_key_file()
                normalized_aes["aes_algorithm"] = "AES-256-GCM"
            merged_payload = cls._merge_payloads(normalized_rsa, normalized_aes)
            await cls._cache_payload(redis_service, merged_payload)
            await redis_service.expire(rsa_cache_key, cls.cache_ttl)
            await redis_service.expire(aes_cache_key, cls.cache_ttl)
            return merged_payload

        file_payload = cls._read_pem_files()
        if file_payload is None:
            file_payload = cls._generate_pem_files()

        await cls._cache_payload(redis_service, file_payload)
        return file_payload

    @classmethod
    async def init_crypto(cls, redis_service: RedisService) -> CryptoInitInfo:
        """
        获取前端初始化所需的共享密钥信息。

        Args:
            redis_service: Redis 服务实例。

        Returns:
            CryptoInitInfo: 返回共享会话、RSA 公钥和 AES 密钥。
        """
        payload = await cls._ensure_payload(redis_service)
        return CryptoInitInfo(
            rsaPublicKey=payload["rsa_public_key"],
            aesKey=payload["aes_key"],
        )

    @classmethod
    async def encrypt_rsa_text(
        cls,
        redis_service: RedisService,
        text: str,
    ) -> str:
        """
        使用共享 RSA 公钥加密文本。

        Args:
            redis_service: Redis 服务实例。
            text: 待加密明文。

        Returns:
            str: Base64 编码的密文。
        """
        payload = await cls._ensure_payload(redis_service)
        public_key = serialization.load_der_public_key(
            cls._base64_to_der(payload["rsa_public_key"]),
        )
        cipher_text = public_key.encrypt(
            text.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return cls._b64encode(cipher_text)

    @classmethod
    async def decrypt_rsa_text(
        cls,
        redis_service: RedisService,
        cipher_text: str,
    ) -> str:
        """
        使用共享 RSA 私钥解密文本。

        Args:
            redis_service: Redis 服务实例。
            cipher_text: Base64 编码的密文。

        Returns:
            str: 解密后的明文。
        """
        payload = await cls._ensure_payload(redis_service)
        private_key_der = cls._base64_to_der(payload["rsa_private_key"])
        private_key = serialization.load_der_private_key(
            private_key_der,
            password=None,
        )
        plain_text = private_key.decrypt(
            cls._b64decode(cipher_text),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return plain_text.decode("utf-8")

    @classmethod
    async def encrypt_aes_text(
        cls,
        redis_service: RedisService,
        text: str,
        associated_data: str | None = None,
    ) -> dict[str, str]:
        """
        使用共享 AES 密钥加密文本。

        Args:
            redis_service: Redis 服务实例。
            text: 待加密明文。
            associated_data: 附加认证数据，用于 GCM 校验。

        Returns:
            dict[str, str]: 包含随机 nonce、密文和算法名称。
        """
        payload = await cls._ensure_payload(redis_service)
        aes_key = cls._b64decode(payload["aes_key"])
        nonce = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        cipher_text = aesgcm.encrypt(
            nonce,
            text.encode("utf-8"),
            associated_data.encode("utf-8") if associated_data else None,
        )
        return {
            "nonce": cls._b64encode(nonce),
            "cipherText": cls._b64encode(cipher_text),
            "algorithm": payload.get("aes_algorithm", "AES-256-GCM"),
        }

    @classmethod
    async def decrypt_aes_text(
        cls,
        redis_service: RedisService,
        nonce: str,
        cipher_text: str,
        associated_data: str | None = None,
    ) -> str:
        """
        使用共享 AES 密钥解密文本。

        Args:
            redis_service: Redis 服务实例。
            nonce: Base64 编码的随机向量。
            cipher_text: Base64 编码的密文。
            associated_data: 附加认证数据，需与加密时保持一致。

        Returns:
            str: 解密后的明文。
        """
        payload = await cls._ensure_payload(redis_service)
        aes_key = cls._b64decode(payload["aes_key"])
        aesgcm = AESGCM(aes_key)
        plain_text = aesgcm.decrypt(
            cls._b64decode(nonce),
            cls._b64decode(cipher_text),
            associated_data.encode("utf-8") if associated_data else None,
        )
        return plain_text.decode("utf-8")


class AuthTokenService:
    """认证令牌服务。"""

    token_cache_name = "auth:token"

    @staticmethod
    def new_jti() -> str:
        """
        生成令牌唯一标识。

        Returns:
            str: UUID 字符串。
        """
        return uuid.uuid4().hex

    @classmethod
    def _token_key(cls, token_type: str, jti: str) -> str:
        """
        构造令牌缓存键。

        Args:
            token_type: 令牌类型，如 access 或 refresh。
            jti: 令牌唯一标识。

        Returns:
            str: Redis 中使用的缓存键。
        """
        return f"{cls.token_cache_name}:{token_type}:{jti}"

    @classmethod
    async def store_login_tokens(
        cls,
        redis_service: RedisService,
        *,
        access_token: str,
        refresh_token: str,
        access_jti: str,
        refresh_jti: str,
    ) -> None:
        """
        将登录产生的 access 和 refresh token 写入 Redis。

        Args:
            redis_service: Redis 服务实例。
            user: 当前登录用户。
            access_token: access token 字符串。
            refresh_token: refresh token 字符串。
            access_jti: access token 唯一标识。
            refresh_jti: refresh token 唯一标识。
        """

        await redis_service.set(
            cls._token_key("access", access_jti),
            access_token,
            ex=settings.jwt.access_token_expire_minutes * 60,
        )
        await redis_service.set(
            cls._token_key("refresh", refresh_jti),
            refresh_token,
            ex=settings.jwt.refresh_token_expire_minutes * 60,
        )

    @classmethod
    async def store_access_token(
        cls,
        redis_service: RedisService,
        *,
        user: User,
        access_token: str,
        access_jti: str,
    ) -> None:
        """
        单独写入新的 access token。

        Args:
            redis_service: Redis 服务实例。
            user: 当前登录用户。
            access_token: access token 字符串。
            access_jti: access token 唯一标识。
        """
        await redis_service.set(
            cls._token_key("access", access_jti),
            {
                "userId": user.id,
                "userCode": user.user_code,
                "type": "access",
                "token": access_token,
                "jti": access_jti,
            },
            ex=settings.jwt.access_token_expire_minutes * 60,
        )

    @classmethod
    async def get_cached_token(
        cls,
        redis_service: RedisService,
        *,
        token_type: str,
        jti: str,
    ) -> dict[str, Any] | None:
        """
        根据 token 类型和 jti 获取 Redis 中的缓存记录。

        Args:
            redis_service: Redis 服务实例。
            token_type: 令牌类型。
            jti: 令牌唯一标识。

        Returns:
            dict[str, Any] | None: 缓存中的令牌信息。
        """
        payload = await redis_service.get(cls._token_key(token_type, jti))
        if payload:
            return payload
        return None

    @classmethod
    async def logout(
        cls,
        redis_service: RedisService,
        authorization: str | None,
    ) -> LogoutInfo:
        """
        注销当前 access token 对应的 Redis 缓存。

        Args:
            redis_service: Redis 服务实例。
            authorization: 请求头中的 Authorization 值。

        Returns:
            LogoutInfo: 退出结果。
        """
        if not authorization:
            return LogoutInfo(revoked=False)

        token = authorization.strip()
        payload = decode_token(token)
        if not isinstance(payload, dict):
            return LogoutInfo(revoked=False)

        token_type = payload.get("type")
        jti = payload.get("jti")
        if token_type != "access" or not isinstance(jti, str):
            return LogoutInfo(revoked=False)

        deleted = await redis_service.delete(cls._token_key("access", jti))
        return LogoutInfo(revoked=bool(deleted))


class AuthLoginFailureService:
    """登录失败控制服务。"""

    failure_cache_name = "auth:login_failure"
    lock_cache_name = "auth:login_lock"

    @classmethod
    def _failure_key(cls, user_code: str) -> str:
        """
        构造登录失败计数缓存键。

        Args:
            user_code: 用户编码。

        Returns:
            str: Redis 中使用的失败计数键。
        """
        return f"{cls.failure_cache_name}:{user_code}"

    @classmethod
    def _lock_key(cls, user_code: str) -> str:
        """
        构造登录锁定缓存键。

        Args:
            user_code: 用户编码。

        Returns:
            str: Redis 中使用的锁定键。
        """
        return f"{cls.lock_cache_name}:{user_code}"

    @classmethod
    async def is_locked(cls, redis_service: RedisService, user_code: str) -> bool:
        """
        判断用户是否处于登录锁定状态。

        Args:
            redis_service: Redis 服务实例。
            user_code: 用户编码。

        Returns:
            bool: 是否已锁定。
        """
        return bool(await redis_service.exists(cls._lock_key(user_code)))

    @classmethod
    async def get_failed_count(
        cls,
        redis_service: RedisService,
        user_code: str,
    ) -> int:
        """
        获取用户当前登录失败次数。

        Args:
            redis_service: Redis 服务实例。
            user_code: 用户编码。

        Returns:
            int: 当前失败次数。
        """
        value = await redis_service.get(cls._failure_key(user_code))
        if value is None:
            return 0
        return int(value)

    @classmethod
    async def record_failure(
        cls,
        redis_service: RedisService,
        user_code: str,
    ) -> tuple[int, bool]:
        """
        记录一次登录失败，并在达到阈值后写入锁定状态。

        Args:
            redis_service: Redis 服务实例。
            user_code: 用户编码。

        Returns:
            tuple[int, bool]: 返回失败次数以及当前是否已锁定。
        """
        failure_key = cls._failure_key(user_code)
        lock_key = cls._lock_key(user_code)
        ttl_seconds = settings.jwt.login_failure_lock_minutes * 60
        count = await redis_service.incr(failure_key)
        await redis_service.expire(failure_key, ttl_seconds)

        locked = count >= settings.jwt.login_failure_lock_threshold
        if locked:
            await redis_service.set(
                lock_key,
                {
                    "userCode": user_code,
                    "failedCount": count,
                    "lockedAt": datetime.now(timezone.utc).isoformat(),
                },
                ex=ttl_seconds,
            )

        return count, locked

    @classmethod
    async def clear(cls, redis_service: RedisService, user_code: str) -> None:
        """
        清理用户登录失败次数和锁定状态。

        Args:
            redis_service: Redis 服务实例。
            user_code: 用户编码。
        """
        await redis_service.delete(cls._failure_key(user_code))
        await redis_service.delete(cls._lock_key(user_code))


class AuthService:
    """认证业务服务。"""

    @staticmethod
    def build_request_context(
        *,
        trace_id: str | None,
        client_ip: str | None,
        user_agent: str | None,
        request_path: str,
        request_method: str,
    ) -> AuthRequestContext:
        """
        构造认证请求上下文。

        Args:
            trace_id: 请求追踪 ID。
            client_ip: 客户端 IP。
            user_agent: 请求头中的 User-Agent。
            request_path: 请求路径。
            request_method: 请求方法。

        Returns:
            AuthRequestContext: 标准化后的请求上下文。
        """
        return AuthRequestContext(
            trace_id=trace_id,
            client_ip=client_ip,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
        )

    @staticmethod
    async def _record_login_log(
        mongo_manager: MongoManager | None,
        context: AuthRequestContext,
        login_info: LoginInfo,
        *,
        user: User | None,
        success: bool,
        fail_reason: str | None,
        failed_count: int | None = None,
        locked: bool = False,
        access_jti: str | None = None,
        refresh_jti: str | None = None,
    ) -> None:
        """
        记录登录日志；日志失败不影响主流程。

        Args:
            mongo_manager: Mongo 管理器。
            context: 请求上下文。
            login_info: 登录请求数据。
            user: 命中的用户对象。
            success: 是否成功。
            fail_reason: 失败原因。
            failed_count: 当前失败次数。
            locked: 是否触发锁定。
            access_jti: access token 标识。
            refresh_jti: refresh token 标识。
        """
        try:
            await LoginLogService.record_login(
                mongo_manager,
                trace_id=context.trace_id,
                user_code=login_info.user_code,
                user=user,
                success=success,
                fail_reason=fail_reason,
                client_ip=context.client_ip,
                user_agent=context.user_agent,
                request_path=context.request_path,
                request_method=context.request_method,
                failed_count=failed_count,
                locked=locked,
                access_jti=access_jti,
                refresh_jti=refresh_jti,
            )
        except Exception:
            pass

    @staticmethod
    def _build_token_payload(user: User) -> dict[str, Any]:
        """
        构造 JWT 业务载荷。

        Args:
            user: 当前登录用户。

        Returns:
            dict[str, Any]: JWT 公共业务字段。
        """
        return {
            "sub": user.id,
            "userCode": user.user_code,
            "userName": user.user_name,
        }

    @classmethod
    async def login(
        cls,
        db: DbSession,
        redis_service: RedisService,
        mongo_manager: MongoManager | None,
        login_info: LoginInfo,
        context: AuthRequestContext,
    ) -> AuthServiceResult:
        """
        执行用户登录。

        Args:
            db: 数据库会话。
            redis_service: Redis 服务实例。
            mongo_manager: Mongo 管理器。
            login_info: 登录请求数据。
            context: 请求上下文。

        Returns:
            AuthServiceResult: 登录处理结果。
        """
        try:
            plain_password = await AuthCryptoService.decrypt_rsa_text(
                redis_service,
                login_info.password,
            )
        except Exception:
            await cls._record_login_log(
                mongo_manager,
                context,
                login_info,
                user=None,
                success=False,
                fail_reason="密码解密失败",
            )
            return AuthServiceResult(
                success=False,
                code=ErrorCode.COMMON_FAILURE,
                msg="密码解密失败",
            )

        user = await UserService.get_by_field(db, "user_code", login_info.user_code)
        if not user:
            await cls._record_login_log(
                mongo_manager,
                context,
                login_info,
                user=None,
                success=False,
                fail_reason="账号不存在",
            )
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg="账号不存在或不可登录",
            )

        if await AuthLoginFailureService.is_locked(redis_service, login_info.user_code):
            if user.is_active():
                await UserService.record_login_locked(db, user)
            failed_count = await AuthLoginFailureService.get_failed_count(
                redis_service,
                login_info.user_code,
            )
            await cls._record_login_log(
                mongo_manager,
                context,
                login_info,
                user=user,
                success=False,
                fail_reason="账号已锁定",
                failed_count=failed_count,
                locked=True,
            )
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg="账号已锁定",
            )

        block_reason = UserService.login_block_reason(user)
        if block_reason:
            await cls._record_login_log(
                mongo_manager,
                context,
                login_info,
                user=user,
                success=False,
                fail_reason=block_reason,
                failed_count=await AuthLoginFailureService.get_failed_count(
                    redis_service,
                    login_info.user_code,
                ),
                locked=block_reason == "账号已锁定",
            )
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg=block_reason,
            )

        if not verify_password(plain_password, user.password):
            failed_count, locked = await AuthLoginFailureService.record_failure(
                redis_service,
                login_info.user_code,
            )
            if locked:
                await UserService.record_login_locked(db, user)
            fail_reason = "密码错误次数过多，账号已锁定" if locked else "账号或密码错误"
            await cls._record_login_log(
                mongo_manager,
                context,
                login_info,
                user=user,
                success=False,
                fail_reason=fail_reason,
                failed_count=failed_count,
                locked=locked,
            )
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg=fail_reason,
            )

        await AuthLoginFailureService.clear(redis_service, login_info.user_code)
        await UserService.record_login_success(db, user)

        access_jti = AuthTokenService.new_jti()
        refresh_jti = AuthTokenService.new_jti()
        token_payload = cls._build_token_payload(user)

        access_token = create_access_token(
            {
                **token_payload,
                "jti": access_jti,
            },
            expires_delta=timedelta(minutes=settings.jwt.access_token_expire_minutes),
        )
        refresh_token = create_refresh_token(
            {
                **token_payload,
                "jti": refresh_jti,
            },
            expires_delta=timedelta(minutes=settings.jwt.refresh_token_expire_minutes),
        )

        await AuthTokenService.store_login_tokens(
            redis_service,
            access_token=access_token,
            refresh_token=refresh_token,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
        )

        await cls._record_login_log(
            mongo_manager,
            context,
            login_info,
            user=user,
            success=True,
            fail_reason=None,
            failed_count=0,
            access_jti=access_jti,
            refresh_jti=refresh_jti,
        )

        return AuthServiceResult(
            success=True,
            code=ErrorCode.SUCCESS,
            msg="操作成功",
            data=TokenInfo(
                accessToken=access_token,
                refreshToken=refresh_token,
                expiresIn=settings.jwt.access_token_expire_minutes * 60,
                refreshExpiresIn=settings.jwt.refresh_token_expire_minutes * 60,
            ),
        )

    @classmethod
    async def refresh_access_token(
        cls,
        db: DbSession,
        redis_service: RedisService,
        authorization: str | None,
    ) -> AuthServiceResult:
        """
        使用 refresh token 刷新 access token。

        Args:
            db: 数据库会话。
            redis_service: Redis 服务实例。
            authorization: 请求头中的 Authorization 值。

        Returns:
            AuthServiceResult: 刷新结果。
        """
        if not authorization:
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg="refresh token 无效",
            )

        refresh_token = authorization.strip()
        payload = verify_refresh_token(refresh_token)
        if not isinstance(payload, dict):
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_EXPIRED,
                msg="refresh token 已失效",
            )

        refresh_jti = payload.get("jti")
        user_id = payload.get("sub")
        if not isinstance(refresh_jti, str) or not isinstance(user_id, str):
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg="refresh token 无效",
            )

        cached_refresh = await AuthTokenService.get_cached_token(
            redis_service,
            token_type="refresh",
            jti=refresh_jti,
        )
        if not cached_refresh or cached_refresh.get("token") != refresh_token:
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_EXPIRED,
                msg="refresh token 已失效",
            )

        user = await UserService.get_by_id(db, user_id)
        if not user:
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg="用户不存在",
            )

        block_reason = UserService.login_block_reason(user)
        if block_reason:
            return AuthServiceResult(
                success=False,
                code=ErrorCode.AUTH_FAILURE,
                msg=block_reason,
            )

        access_jti = AuthTokenService.new_jti()
        access_token = create_access_token(
            {
                **cls._build_token_payload(user),
                "jti": access_jti,
            },
            expires_delta=timedelta(minutes=settings.jwt.access_token_expire_minutes),
        )

        await AuthTokenService.store_access_token(
            redis_service,
            user=user,
            access_token=access_token,
            access_jti=access_jti,
        )

        return AuthServiceResult(
            success=True,
            code=ErrorCode.SUCCESS,
            msg="操作成功",
            data=TokenInfo(
                accessToken=access_token,
                refreshToken=refresh_token,
                tokenType="bearer",
                expiresIn=settings.jwt.access_token_expire_minutes * 60,
                refreshExpiresIn=settings.jwt.refresh_token_expire_minutes * 60,
            ),
        )
