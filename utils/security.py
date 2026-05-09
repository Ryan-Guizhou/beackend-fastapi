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

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config.config import settings


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
