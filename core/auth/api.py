#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/4/21 21:16
@Desc: 认证接口定义
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Header, Request

from base.base_schema import ErrorCode, Response
from config.database import DbSession
from core.auth.schema import LoginInfo, LogoutInfo
from core.auth.service import AuthCryptoService, AuthTokenService
from core.user.service import UserService
from utils.security import create_access_token, create_refresh_token, verify_password

router = APIRouter(prefix="/auth", tags=["认证管理"])

logger = logging.getLogger(__name__)


def get_redis_service(request: Request):
    """
    获取应用生命周期中初始化的 RedisService。

    Args:
        request: FastAPI 请求对象。

    Returns:
        RedisService: Redis 服务。

    Raises:
        RuntimeError: RedisService 未初始化时抛出。
    """
    redis_service = getattr(request.app.state, "redis_service", None)
    if redis_service is None:
        raise RuntimeError("RedisService 尚未初始化")
    return redis_service


@router.get("/init", response_model=Response, summary="初始化传输加密密钥")
async def init_crypto(request: Request) -> Response:
    """
    初始化前后端传输加密密钥。

    说明：
        优先从 Redis 获取 RSA 密钥对；Redis 没有时读取指定目录下的 PEM 文件；
        PEM 文件不存在时生成标准 RSA 密钥对文件，并写入 Redis 后返回公钥。

    Args:
        request: FastAPI 请求对象。

    Returns:
        Response: RSA 公钥和会话 ID。
    """
    crypto_info = await AuthCryptoService.init_crypto(get_redis_service(request))
    return Response.success(data=crypto_info)


@router.post("/login", response_model=Response, summary="用户登录")
async def login(
        request: Request,
        db: DbSession,
        login_info: LoginInfo,
) -> Response:
    """
    用户登录。

    说明：
        前端使用 `/auth/init` 返回的 RSA 公钥加密密码，登录时传入密文和 sessionId。
        验证码字段暂时保留，后续接入验证码服务后再校验。

    Args:
        request: FastAPI 请求对象。
        db: 数据库会话。
        login_info: 登录请求数据。

    Returns:
        Response: 登录结果。
    """
    try:
        plain_password = await AuthCryptoService.decrypt_rsa_text(
            get_redis_service(request),
            login_info.session_id,
            login_info.password,
        )
    except Exception:
        logger.exception("login password decrypt failed")
        return Response.failure(code=ErrorCode.COMMON_FAILURE, msg="密码解密失败")

    user = await UserService.get_by_field(db, "user_code", login_info.user_code)
    if not user or not user.can_login():
        return Response.failure(code=ErrorCode.AUTH_FAILURE, msg="账号不存在或不可登录")

    if not verify_password(plain_password, user.password):
        return Response.failure(code=ErrorCode.AUTH_FAILURE, msg="账号或密码错误")

    token_payload = {
        "sub": user.id,
        "userCode": user.user_code,
        "userName": user.user_name,
    }
    return Response.success(
        data={
            "accessToken": create_access_token(token_payload),
            "refreshToken": create_refresh_token(token_payload),
            "tokenType": "bearer",
        }
    )


@router.post("/logout", response_model=Response, summary="退出登录")
async def logout(
        request: Request,
        authorization: Annotated[str | None, Header()] = None,
) -> Response:
    """
    退出登录。

    Args:
        request: FastAPI 请求对象。
        authorization: Authorization 请求头。

    Returns:
        Response: 退出登录结果。
    """
    revoked = await AuthTokenService.logout(get_redis_service(request), authorization)
    return Response.success(data=LogoutInfo(revoked=revoked))
