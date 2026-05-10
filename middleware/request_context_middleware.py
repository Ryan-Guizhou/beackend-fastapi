#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: request_context_middleware.py
@Create: 2026/5/11 00:40
@Desc: 请求上下文中间件
"""

import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_context_var: ContextVar["RequestContextData | None"] = ContextVar(
    "request_context",
    default=None,
)


@dataclass(slots=True)
class RequestContextData:
    """
    当前请求上下文。

    Args:
        request_id: 请求 ID。
        method: 请求方法。
        path: 请求路径。
        client_ip: 客户端 IP。
        user_agent: 请求头中的 User-Agent。
        current_user: 当前登录用户信息。
        roles: 当前用户角色列表。
        permissions: 当前用户权限列表。
        extensions: 预留扩展字段。
    """

    request_id: str
    method: str
    path: str
    client_ip: str | None
    user_agent: str | None
    current_user: dict[str, Any] | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(cls, request: Request) -> "RequestContextData":
        """
        基于当前请求构造上下文对象。

        Args:
            request: FastAPI 请求对象。

        Returns:
            RequestContextData: 初始化后的请求上下文。
        """
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = None
        if forwarded_for:
            client_ip = forwarded_for.split(",", 1)[0].strip()
        elif request.client:
            client_ip = request.client.host

        return cls(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
        )

    def set_user(self, user_info: dict[str, Any]) -> None:
        """
        设置当前用户信息。

        Args:
            user_info: 当前用户信息。
        """
        self.current_user = dict(user_info)

    def set_extension(self, key: str, value: Any) -> None:
        """
        写入扩展字段。

        Args:
            key: 扩展字段名。
            value: 扩展字段值。
        """
        self.extensions[key] = value


def set_current_request_context(context: RequestContextData) -> Token:
    """
    写入当前请求上下文。

    Args:
        context: 请求上下文对象。

    Returns:
        Token: ContextVar reset 所需的 token。
    """
    return request_context_var.set(context)


def reset_current_request_context(token: Token) -> None:
    """
    清理当前请求上下文。

    Args:
        token: 由 `set_current_request_context` 返回的 token。
    """
    request_context_var.reset(token)


def get_current_request_context() -> RequestContextData | None:
    """
    获取当前请求上下文。

    Returns:
        RequestContextData | None: 当前请求上下文，不存在时返回 None。
    """
    return request_context_var.get()


def require_current_request_context() -> RequestContextData:
    """
    获取当前请求上下文，不存在时抛出异常。

    Returns:
        RequestContextData: 当前请求上下文。

    Raises:
        RuntimeError: 当前协程不存在请求上下文时抛出异常。
    """
    context = get_current_request_context()
    if context is None:
        raise RuntimeError("request context is not initialized")
    return context


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    请求上下文中间件。

    负责为每个请求初始化统一上下文，并通过 ContextVar 在当前请求协程范围内透传。
    """

    async def dispatch(self, request: Request, call_next):
        """
        初始化请求上下文并继续下游处理。

        Args:
            request: FastAPI 请求对象。
            call_next: 下一个中间件或路由处理器。

        Returns:
            Response: 下游响应对象。
        """
        request_context = RequestContextData.build(request)
        context_token = set_current_request_context(request_context)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_context.request_id
            return response
        finally:
            reset_current_request_context(context_token)
