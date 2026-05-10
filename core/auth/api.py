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

from typing import Annotated

from fastapi import APIRouter, Header, Request

from base.base_schema import Response
from config.database import DbSession
from core.auth.schema import LoginInfo
from core.auth.service import AuthCryptoService, AuthService, AuthTokenService

router = APIRouter(prefix="/auth", tags=["认证管理"])


def get_redis_service(request: Request):
    """
    获取应用生命周期中初始化的 RedisService。

    Args:
        request: FastAPI 请求对象。

    Returns:
        RedisService: Redis 服务实例。

    Raises:
        RuntimeError: RedisService 未初始化时抛出异常。
    """
    redis_service = getattr(request.app.state, "redis_service", None)
    if redis_service is None:
        raise RuntimeError("RedisService 尚未初始化")
    return redis_service


def get_mongo_manager(request: Request):
    """
    获取应用生命周期中初始化的 MongoManager。

    Args:
        request: FastAPI 请求对象。

    Returns:
        MongoManager | None: Mongo 管理器。
    """
    return getattr(request.app.state, "mongo_manager", None)


def get_client_ip(request: Request) -> str | None:
    """
    获取客户端 IP。

    Args:
        request: FastAPI 请求对象。

    Returns:
        str | None: 客户端 IP。
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return None


@router.get("/init", response_model=Response, summary="初始化传输加密密钥")
async def init_crypto(request: Request) -> Response:
    """
    初始化前后端传输加密密钥。

    Args:
        request: FastAPI 请求对象。

    Returns:
        Response: 初始化密钥信息。
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

    Args:
        request: FastAPI 请求对象。
        db: 数据库会话。
        login_info: 登录请求参数。

    Returns:
        Response: 登录结果和令牌信息。
    """
    result = await AuthService.login(
        db,
        get_redis_service(request),
        get_mongo_manager(request),
        login_info,
        AuthService.build_request_context(
            trace_id=request.headers.get("x-request-id") or request.headers.get("x-trace-id"),
            client_ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_path=request.url.path,
            request_method=request.method,
        ),
    )
    if result.success:
        return Response.success(data=result.data, msg=result.msg, code=result.code)
    return Response.failure(code=result.code, msg=result.msg)


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
        Response: 退出处理结果。
    """
    logout_info = await AuthTokenService.logout(get_redis_service(request), authorization)
    return Response.success(data=logout_info)


@router.api_route(
    "/refresh_token",
    methods=["GET", "POST"],
    response_model=Response,
    summary="刷新访问令牌",
)
async def refresh_token(
    request: Request,
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    """
    使用 refresh token 刷新 access token。

    Args:
        request: FastAPI 请求对象。
        db: 数据库会话。
        authorization: Authorization 请求头。

    Returns:
        Response: 刷新结果。
    """
    result = await AuthService.refresh_access_token(
        db,
        get_redis_service(request),
        authorization,
    )
    if result.success:
        return Response.success(data=result.data, msg=result.msg, code=result.code)
    return Response.failure(code=result.code, msg=result.msg)
