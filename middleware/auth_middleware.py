#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: auth_middleware.py
@Create: 2026/5/11 00:40
@Desc: 认证中间件
"""

import logging

from jose import ExpiredSignatureError, JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from base.base_schema import ErrorCode, Response
from config.config import settings
from config.database import AsyncSessionLocal
from core.auth.service import AuthTokenService
from core.user.service import UserService
from middleware.request_context_middleware import require_current_request_context

logger = logging.getLogger("app.auth")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件。

    负责统一校验请求头中的 access token，并将当前用户信息写入请求上下文，
    便于后续在业务层、日志和权限校验中复用。
    """

    public_exact_paths = {
        "/",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/api/core/auth/init",
        "/api/core/auth/login",
        "/api/core/auth/refresh_token",
    }
    public_prefixes = (
        "/docs/",
        "/redoc/",
    )
    protected_prefixes = (
        "/api/",
    )

    @classmethod
    def _is_public_path(cls, path: str) -> bool:
        """
        判断当前路径是否为免认证路径。

        Args:
            path: 当前请求路径。

        Returns:
            bool: 是否免认证。
        """
        if path in cls.public_exact_paths:
            return True
        return any(path.startswith(prefix) for prefix in cls.public_prefixes)

    @classmethod
    def _should_authenticate(cls, path: str, method: str) -> bool:
        """
        判断当前请求是否需要执行认证。

        Args:
            path: 当前请求路径。
            method: 当前请求方法。

        Returns:
            bool: 是否需要认证。
        """
        if method.upper() == "OPTIONS":
            return False
        if cls._is_public_path(path):
            return False
        return any(path.startswith(prefix) for prefix in cls.protected_prefixes)

    @staticmethod
    def _build_failure_response(code: ErrorCode, msg: str) -> StarletteResponse:
        """
        构造统一认证失败响应。

        Args:
            code: 业务状态码。
            msg: 响应消息。

        Returns:
            StarletteResponse: JSON 响应对象。
        """
        return Response.failure(
            code=code,
            msg=msg,
        ).to_http_response()

    @staticmethod
    def _decode_access_token(token: str) -> dict:
        """
        解码并校验 access token。

        Args:
            token: access token 字符串。

        Returns:
            dict: 解码后的载荷。

        Raises:
            ExpiredSignatureError: token 已过期。
            JWTError: token 非法。
            ValueError: token 类型错误。
        """
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        if payload.get("type") != "access":
            raise ValueError("token type invalid")
        return payload

    async def dispatch(self, request: Request, call_next):
        """
        执行认证校验并写入当前用户上下文。

        Args:
            request: FastAPI 请求对象。
            call_next: 下一个中间件或路由处理器。

        Returns:
            StarletteResponse: 下游响应或认证失败响应。
        """
        request_context = require_current_request_context()
        path = request.url.path

        if not self._should_authenticate(path, request.method):
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization:
            logger.warning(
                "authorization header missing or invalid",
                extra={
                    "request_id": request_context.request_id,
                    "method": request.method,
                    "path": path,
                },
            )
            return self._build_failure_response(
                ErrorCode.AUTH_FAILURE,
                "未登录或token无效",
            )

        try:
            payload = self._decode_access_token(authorization)
        except ExpiredSignatureError:
            return self._build_failure_response(
                ErrorCode.AUTH_EXPIRED,
                "token已过期",
            )
        except (JWTError, ValueError):
            return self._build_failure_response(
                ErrorCode.AUTH_FAILURE,
                "token无效",
            )

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not isinstance(jti, str) or not isinstance(user_id, str):
            return self._build_failure_response(
                ErrorCode.AUTH_FAILURE,
                "token无效",
            )

        redis_service = getattr(request.app.state, "redis_service", None)
        if redis_service is None:
            logger.error("redis service not initialized for auth middleware")
            return self._build_failure_response(
                ErrorCode.COMMON_FAILURE,
                "认证服务未初始化",
            )

        cached_token = await AuthTokenService.get_cached_token(
            redis_service,
            token_type="access",
            jti=jti,
        )
        if not cached_token or cached_token != authorization:
            return self._build_failure_response(
                ErrorCode.AUTH_FAILURE,
                "token无效或已退出登录",
            )

        async with AsyncSessionLocal() as db:
            user = await UserService.get_by_id(db, user_id)

        if user is None:
            return self._build_failure_response(
                ErrorCode.AUTH_FAILURE,
                "用户不存在",
            )

        block_reason = UserService.login_block_reason(user)
        if block_reason:
            return self._build_failure_response(
                ErrorCode.AUTH_FAILURE,
                block_reason,
            )

        current_user = {
            "id": user.id,
            "userCode": user.user_code,
            "userName": user.user_name,
            "status": user.status,
            "authMode": user.auth_mode,
        }
        request_context.set_user(current_user)
        request_context.set_extension("token_payload", payload)

        return await call_next(request)
