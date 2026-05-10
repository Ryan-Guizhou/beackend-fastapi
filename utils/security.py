#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: security.py
@Create: 2026/4/17 21:28
@Desc: JWT 解析工具
"""

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _base64_url_encode(data: bytes) -> str:
    """
    base64url 编码。
    """
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64_url_decode(data: str) -> bytes:
    """
    base64url 解码。
    """
    padding_len = (-len(data)) % 4
    return base64.urlsafe_b64decode((data + "=" * padding_len).encode("utf-8"))


def hash_password(password: str, algorithm: str = "bcrypt") -> str:
    """
    对登录密码生成不可逆摘要。

    Args:
        password: 明文密码。
        algorithm: 摘要算法，支持 `bcrypt` 和 `sha256_base64`。

    Returns:
        str: 密码摘要。
    """
    if algorithm == "bcrypt":
        return password_context.hash(password)
    if algorithm == "sha256_base64":
        salt = os.urandom(16)
        digest = hashlib.sha256(salt + password.encode("utf-8")).digest()
        return f"sha256_base64${_base64_url_encode(salt)}${_base64_url_encode(digest)}"
    raise ValueError(f"不支持的密码摘要算法: {algorithm}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码和不可逆摘要是否匹配。

    Args:
        plain_password: 解密后的明文密码。
        hashed_password: 数据库存储的密码摘要。

    Returns:
        bool: 匹配返回 `True`，否则返回 `False`。
    """
    if not plain_password or not hashed_password:
        return False
    if hashed_password.startswith("sha256_base64$"):
        try:
            _, salt_text, digest_text = hashed_password.split("$", 2)
            salt = _base64_url_decode(salt_text)
            expected = _base64_url_decode(digest_text)
        except ValueError:
            return False
        actual = hashlib.sha256(salt + plain_password.encode("utf-8")).digest()
        return hmac.compare_digest(actual, expected)
    return password_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建 Access Token。

    Args:
        data: 需要编码进 Token 的业务数据。
        expires_delta: 自定义过期时长，未传入时使用系统默认值。

    Returns:
        str: 编码后的 Access Token 字符串。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    # 补充过期时间和 Token 类型后统一编码
    to_encode.update({
        "exp": expire,
        "type": "access",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建 Refresh Token。

    Args:
        data: 需要编码进 Token 的业务数据。
        expires_delta: 自定义过期时长，未传入时使用刷新令牌默认值。

    Returns:
        str: 编码后的 Refresh Token 字符串。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt.refresh_token_expire_days
        )

    to_encode.update({
        "exp": expire,
        "type": "refresh",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """
    解码 JWT Token。

    Args:
        token: 待解码的 JWT 字符串。

    Returns:
        dict | None: 解码后的载荷数据；解码失败时返回 `None`。
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> dict | None:
    """
    校验 Access Token。

    Args:
        token: 待校验的 JWT 字符串。

    Returns:
        dict | None: 校验通过时返回解码后的数据，否则返回 `None`。
    """
    payload = decode_token(token)
    if payload and "access" == payload.get("type"):
        return payload
    return None


def verify_refresh_token(token: str) -> dict | None:
    """
    校验 Refresh Token。

    Args:
        token: 待校验的 JWT 字符串。

    Returns:
        dict | None: 校验通过时返回解码后的数据，否则返回 `None`。
    """
    payload = decode_token(token)
    if payload and "refresh" == payload.get("type"):
        return payload
    return None
