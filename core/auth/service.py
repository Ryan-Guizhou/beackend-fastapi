#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 17:30
@Desc: 认证加密服务
"""

import base64
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.auth.schema import CryptoInitInfo
from utils.redis.redis_service import RedisService
from utils.security import decode_token, hash_password, verify_password


class AuthCryptoService:
    """
    认证传输加密服务。
    """

    cache_name = "auth:crypto"
    shared_session_id = "shared"
    cache_ttl = 300
    key_dir = Path(__file__).resolve().parents[2] / "algorithm" / "rsa"
    private_key_file = key_dir / "private.pem"
    public_key_file = key_dir / "public.pem"
    aes_key_dir = Path(__file__).resolve().parents[2] / "algorithm"/ "aes"
    aes_key_file = aes_key_dir / "aes.key"

    @staticmethod
    def _b64encode(data: bytes) -> str:
        """
        base64url 编码。

        Args:
            data: 待编码字节。

        Returns:
            str: 去除补位字符后的 base64url 文本。
        """
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64decode(data: str) -> bytes:
        """
        base64url 解码。

        Args:
            data: base64url 文本。

        Returns:
            bytes: 解码后的字节。
        """
        padding_len = (-len(data)) % 4
        return base64.urlsafe_b64decode((data + "=" * padding_len).encode("utf-8"))

    @classmethod
    def _cache_key(cls) -> str:
        """
        构造共享传输密钥 Redis 缓存 Key。

        Returns:
            str: Redis 缓存 Key。
        """
        return f"{cls.cache_name}:{cls.shared_session_id}"

    @staticmethod
    def _pem_to_base64(pem_text: str) -> str:
        """
        提取 PEM 中间的 Base64 内容。

        Args:
            pem_text: PEM 格式密钥文本。

        Returns:
            str: 去除头尾和空白后的 Base64 内容。
        """
        return "".join(
            line.strip()
            for line in pem_text.splitlines()
            if line.strip() and not line.startswith("-----")
        )

    @staticmethod
    def _base64_to_der(key_text: str) -> bytes:
        """
        将 DER Base64 密钥文本还原为字节。

        Args:
            key_text: DER Base64 密钥文本。

        Returns:
            bytes: DER 密钥字节。
        """
        padding_len = (-len(key_text)) % 4
        return base64.b64decode((key_text + "=" * padding_len).encode("utf-8"))

    @classmethod
    def _serialize_private_key(cls, private_key: rsa.RSAPrivateKey) -> str:
        """
        序列化 RSA 私钥。

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

    @classmethod
    def _serialize_public_key(cls, public_key: rsa.RSAPublicKey) -> str:
        """
        序列化 RSA 公钥。

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
    def _payload(cls, private_pem: str, public_pem: str, aes_key: str) -> dict[str, Any]:
        """
        构造 Redis 缓存数据。

        Args:
            private_pem: PEM 格式私钥。
            public_pem: PEM 格式公钥。
            aes_key: base64url 编码后的 AES 密钥。

        Returns:
            dict[str, Any]: 密钥缓存数据。
        """
        return {
            "session_id": cls.shared_session_id,
            "rsa_private_key": cls._pem_to_base64(private_pem),
            "rsa_public_key": cls._pem_to_base64(public_pem),
            "rsa_algorithm": "RSA-OAEP-SHA256",
            "aes_key": aes_key,
            "aes_algorithm": "AES-256-GCM",
        }

    @classmethod
    def _read_aes_key_file(cls) -> str | None:
        """
        读取 AES 密钥文件。

        Returns:
            str | None: AES 密钥存在时返回密钥文本，否则返回 None。
        """
        if not cls.aes_key_file.exists():
            return None
        key_text = cls.aes_key_file.read_text(encoding="utf-8").strip()
        return key_text or None

    @classmethod
    def _generate_aes_key_file(cls) -> str:
        """
        生成 AES-256-GCM 密钥文件。

        Returns:
            str: base64url 编码后的 AES 密钥。
        """
        aes_key = cls._b64encode(os.urandom(32))
        cls.aes_key_dir.mkdir(parents=True, exist_ok=True)
        cls.aes_key_file.write_text(aes_key, encoding="utf-8")
        try:
            os.chmod(cls.aes_key_file, 0o600)
        except OSError:
            pass
        return aes_key

    @classmethod
    def _ensure_aes_key_file(cls) -> str:
        """
        获取 AES 密钥文件，不存在时自动生成。

        Returns:
            str: base64url 编码后的 AES 密钥。
        """
        aes_key = cls._read_aes_key_file()
        if aes_key is not None:
            return aes_key
        return cls._generate_aes_key_file()

    @classmethod
    def _read_pem_files(cls) -> dict[str, Any] | None:
        """
        从指定目录读取标准 PEM 密钥对。

        Returns:
            dict[str, Any] | None: 读取成功返回密钥数据，否则返回 None。
        """
        if not cls.private_key_file.exists():
            return None

        private_pem = cls.private_key_file.read_text(encoding="utf-8")
        aes_key = cls._ensure_aes_key_file()
        if cls.public_key_file.exists():
            public_pem = cls.public_key_file.read_text(encoding="utf-8")
            return cls._payload(private_pem, public_pem, aes_key)

        private_key = serialization.load_pem_private_key(private_pem.encode("utf-8"), password=None)
        public_pem = cls._serialize_public_key(private_key.public_key())
        cls.public_key_file.write_text(public_pem, encoding="utf-8")
        return cls._payload(private_pem, public_pem, aes_key)

    @classmethod
    def _generate_pem_files(cls) -> dict[str, Any]:
        """
        生成 RSA 密钥对并写入指定目录。

        Returns:
            dict[str, Any]: 新生成的密钥数据。
        """
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        private_pem = cls._serialize_private_key(private_key)
        public_pem = cls._serialize_public_key(private_key.public_key())
        aes_key = cls._ensure_aes_key_file()

        cls.key_dir.mkdir(parents=True, exist_ok=True)
        cls.private_key_file.write_text(private_pem, encoding="utf-8")
        cls.public_key_file.write_text(public_pem, encoding="utf-8")
        try:
            os.chmod(cls.private_key_file, 0o600)
            os.chmod(cls.public_key_file, 0o644)
        except OSError:
            pass
        return cls._payload(private_pem, public_pem, aes_key)

    @classmethod
    def generate_rsa_key_pair(cls, *, overwrite: bool = False) -> CryptoInitInfo:
        """
        生成标准 RSA PEM 密钥对文件。

        Args:
            overwrite: 是否覆盖已存在的密钥文件。默认不覆盖，避免已有密文无法解密。

        Returns:
            CryptoInitInfo: 生成或读取到的 RSA 公钥参数。

        Raises:
            FileExistsError: 密钥文件已存在且不允许覆盖时抛出。
        """
        if not overwrite and (cls.private_key_file.exists() or cls.public_key_file.exists()):
            payload = cls._read_pem_files()
            if payload is None:
                raise FileExistsError("RSA 密钥文件不完整，请确认 private.pem 和 public.pem")
        else:
            payload = cls._generate_pem_files()

        return CryptoInitInfo(
            sessionId=cls.shared_session_id,
            rsaPublicKey=payload["rsa_public_key"],
            aesKey=cls._ensure_aes_key_file(),
        )

    @classmethod
    def generate_aes_key(cls, *, overwrite: bool = False) -> str:
        """
        生成 AES-256-GCM 密钥文件。

        Args:
            overwrite: 是否覆盖已存在的 AES 密钥。默认不覆盖，避免已有密文无法解密。

        Returns:
            str: base64url 编码后的 AES 密钥。

        Raises:
            FileExistsError: AES 密钥文件已存在且不允许覆盖时抛出。
        """
        if cls.aes_key_file.exists() and not overwrite:
            aes_key = cls._read_aes_key_file()
            if aes_key is None:
                raise FileExistsError("AES 密钥文件为空，请确认 aes.key")
            return aes_key
        return cls._generate_aes_key_file()

    @classmethod
    def generate_crypto_keys(cls, *, overwrite: bool = False) -> CryptoInitInfo:
        """
        生成 RSA 密钥对和 AES 密钥文件。

        Args:
            overwrite: 是否覆盖已存在的密钥文件。

        Returns:
            CryptoInitInfo: 当前传输加密参数。
        """
        if overwrite and cls.aes_key_file.exists():
            cls.generate_aes_key(overwrite=True)
        else:
            cls._ensure_aes_key_file()
        return cls.generate_rsa_key_pair(overwrite=overwrite)

    @staticmethod
    def create_password_hash(password: str, algorithm: str = "bcrypt") -> str:
        """
        生成不可逆密码摘要。

        Args:
            password: 明文密码。
            algorithm: 摘要算法，支持 `bcrypt` 和 `sha256_base64`。

        Returns:
            str: 密码摘要。
        """
        return hash_password(password, algorithm)

    @staticmethod
    def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
        """
        校验明文密码和不可逆摘要是否匹配。

        Args:
            plain_password: 明文密码。
            hashed_password: 密码摘要。

        Returns:
            bool: 匹配返回 True，否则返回 False。
        """
        return verify_password(plain_password, hashed_password)

    @classmethod
    async def _cache_payload(cls, redis_service: RedisService, payload: dict[str, Any]) -> None:
        """
        将 PEM 密钥对回填到 Redis。

        Args:
            redis_service: Redis 服务。
            payload: 密钥数据。
        """
        await redis_service.set(cls._cache_key(), payload, ex=cls.cache_ttl)

    @classmethod
    def _normalize_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """
        将旧缓存中的 PEM 字段归一化为 DER Base64 字段。

        Args:
            payload: Redis 中读取到的密钥数据。

        Returns:
            dict[str, Any]: 仅包含 Base64 密钥内容的缓存数据。
        """
        normalized = dict(payload)
        private_key = normalized.get("rsa_private_key")
        public_key = normalized.get("rsa_public_key")

        if isinstance(private_key, str) and "BEGIN" in private_key:
            normalized["rsa_private_key"] = cls._pem_to_base64(private_key)
        elif not private_key and normalized.get("rsa_private_key_base64"):
            normalized["rsa_private_key"] = normalized["rsa_private_key_base64"]

        if isinstance(public_key, str) and "BEGIN" in public_key:
            normalized["rsa_public_key"] = cls._pem_to_base64(public_key)
        elif not public_key and normalized.get("rsa_public_key_base64"):
            normalized["rsa_public_key"] = normalized["rsa_public_key_base64"]

        normalized.pop("rsa_private_key_base64", None)
        normalized.pop("rsa_public_key_base64", None)
        return normalized

    @classmethod
    async def _ensure_payload(cls, redis_service: RedisService) -> dict[str, Any]:
        """
        按 Redis、PEM 文件、重新生成的顺序获取密钥对。

        Args:
            redis_service: Redis 服务。

        Returns:
            dict[str, Any]: 当前共享 RSA 密钥对。
        """
        cached = await redis_service.get(cls._cache_key(), dict)
        if cached:
            cached = cls._normalize_payload(cached)
            if "aes_key" not in cached:
                cached["aes_key"] = cls._ensure_aes_key_file()
                cached["aes_algorithm"] = "AES-256-GCM"
            await cls._cache_payload(redis_service, cached)
            await redis_service.expire(cls._cache_key(), cls.cache_ttl)
            return cached

        payload = cls._read_pem_files()
        if payload is None:
            payload = cls._generate_pem_files()

        await cls._cache_payload(redis_service, payload)
        return payload

    @classmethod
    async def init_crypto(cls, redis_service: RedisService) -> CryptoInitInfo:
        """
        初始化前后端传输加密密钥。

        Args:
            redis_service: Redis 服务。

        Returns:
            CryptoInitInfo: 前端需要的 RSA 公钥参数。
        """
        payload = await cls._ensure_payload(redis_service)
        return CryptoInitInfo(
            sessionId=cls.shared_session_id,
            rsaPublicKey=payload["rsa_public_key"],
            aesKey=payload["aes_key"],
        )

    @classmethod
    async def encrypt_rsa_text(cls, redis_service: RedisService, text: str) -> str:
        """
        使用共享 RSA 公钥加密文本。

        Args:
            redis_service: Redis 服务。
            session_id: 传输密钥会话 ID，保留用于兼容前端参数。
            text: 待加密明文。

        Returns:
            str: base64url 编码后的 RSA 密文。
        """
        payload = await cls._ensure_payload(redis_service)
        public_key = serialization.load_der_public_key(cls._base64_to_der(payload["rsa_public_key"]))
        cipher_bytes = public_key.encrypt(
            text.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return cls._b64encode(cipher_bytes)

    @classmethod
    async def decrypt_rsa_text(cls, redis_service: RedisService,cipher_text: str) -> str:
        """
        使用共享 RSA 私钥解密文本。

        Args:
            redis_service: Redis 服务。
            cipher_text: base64url 编码的 RSA 密文。

        Returns:
            str: 解密后的明文。
        """
        payload = await cls._ensure_payload(redis_service)
        private_key = serialization.load_der_private_key(
            cls._base64_to_der(payload["rsa_private_key"]),
            password=None,
        )
        plain_bytes = private_key.decrypt(
            cls._b64decode(cipher_text),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return plain_bytes.decode("utf-8")

    @classmethod
    async def encrypt_aes_text(
            cls,
            redis_service: RedisService,
            text: str,
            associated_data: str | None = None,
    ) -> dict[str, str]:
        """
        使用共享 AES-GCM 密钥加密文本。

        Args:
            redis_service: Redis 服务。
            text: 待加密明文。
            associated_data: 附加认证数据。

        Returns:
            dict[str, str]: nonce、密文和算法信息。
        """
        payload = await cls._ensure_payload(redis_service)
        nonce = os.urandom(12)
        aesgcm = AESGCM(cls._b64decode(payload["aes_key"]))
        cipher_bytes = aesgcm.encrypt(
            nonce,
            text.encode("utf-8"),
            associated_data.encode("utf-8") if associated_data else None,
        )
        return {
            "nonce": cls._b64encode(nonce),
            "cipherText": cls._b64encode(cipher_bytes),
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
        使用共享 AES-GCM 密钥解密文本。

        Args:
            redis_service: Redis 服务。
            nonce: base64url 编码的 AES-GCM nonce。
            cipher_text: base64url 编码的 AES-GCM 密文。
            associated_data: 附加认证数据。

        Returns:
            str: 解密后的明文。
        """
        payload = await cls._ensure_payload(redis_service)
        aesgcm = AESGCM(cls._b64decode(payload["aes_key"]))
        plain_bytes = aesgcm.decrypt(
            cls._b64decode(nonce),
            cls._b64decode(cipher_text),
            associated_data.encode("utf-8") if associated_data else None,
        )
        return plain_bytes.decode("utf-8")


class AuthTokenService:
    """
    认证 Token 服务。
    """

    logout_cache_name = "auth:logout"

    @classmethod
    def _logout_key(cls, token: str) -> str:
        """
        构造退出登录 Token 缓存 Key。

        Args:
            token: JWT Token。

        Returns:
            str: Redis 缓存 Key。
        """
        return f"{cls.logout_cache_name}:{token}"

    @classmethod
    async def logout(cls, redis_service: RedisService, authorization: str | None) -> bool:
        """
        记录退出登录 Token。

        Args:
            redis_service: Redis 服务。
            authorization: Authorization 请求头。

        Returns:
            bool: 是否记录了有效 Token。
        """
        if not authorization:
            return False

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return False

        payload = decode_token(token)
        if not payload:
            return False

        expire_at = payload.get("exp")
        ttl = 300
        if isinstance(expire_at, int):
            ttl = max(expire_at - int(datetime.now(timezone.utc).timestamp()), 1)
        await redis_service.set(cls._logout_key(token), True, ex=ttl)
        return True
