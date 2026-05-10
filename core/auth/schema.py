#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/4/21 21:18
@Desc: 认证请求和响应模型
"""

from pydantic import Field

from base.base_schema import ApiInSchema, ApiOutSchema


class LoginInfo(ApiInSchema):
    user_code: str = Field(
        ...,
        alias="userCode",
        description="账号",
    )
    password: str = Field(
        ...,
        description="RSA 加密后的登录密码",
    )
    captcha: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="验证码",
    )


class CryptoInitInfo(ApiOutSchema):
    rsa_public_key: str = Field(
        ...,
        alias="rsaPublicKey",
        description="RSA 公钥 DER Base64",
    )
    rsa_algorithm: str = Field(
        default="RSA-OAEP-SHA256",
        alias="rsaAlgorithm",
        description="RSA 加密算法",
    )
    aes_key: str = Field(
        ...,
        alias="aesKey",
        description="AES 密钥，base64url 编码",
    )
    aes_algorithm: str = Field(
        default="AES-256-GCM",
        alias="aesAlgorithm",
        description="AES 加密算法",
    )
    encoding: str = Field(
        default="base64url",
        description="密文编码方式",
    )


class TokenInfo(ApiOutSchema):
    access_token: str = Field(
        ...,
        alias="accessToken",
        description="访问令牌",
    )
    refresh_token: str | None = Field(
        default=None,
        alias="refreshToken",
        description="刷新令牌",
    )
    token_type: str = Field(
        default="bearer",
        alias="tokenType",
        description="令牌类型",
    )
    expires_in: int = Field(
        ...,
        alias="expiresIn",
        description="access token 过期时间，单位秒",
    )
    refresh_expires_in: int | None = Field(
        default=None,
        alias="refreshExpiresIn",
        description="refresh token 过期时间，单位秒",
    )


class LogoutInfo(ApiOutSchema):
    revoked: bool = Field(
        default=True,
        description="是否已处理退出登录",
    )
