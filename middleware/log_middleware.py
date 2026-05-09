#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: log_middleware.py
@Create: 2026/4/18 00:08
@Desc: 请求日志中间件
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config.log.context import (
    client_ip_var,
    duration_ms_var,
    method_var,
    path_var,
    request_id_var,
    route_var,
    status_code_var,
    user_agent_var,
)

access_logger = logging.getLogger("app.access")
app_logger = logging.getLogger("app.request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件。

    说明：
        该中间件用于为每个请求生成请求标识，统计耗时，
        并将请求上下文写入日志系统。
    """

    async def dispatch(self, request: Request, call_next):
        """
        处理请求并记录访问日志。
        """
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        start = time.perf_counter()
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        request_id_token = request_id_var.set(request_id)
        method_token = method_var.set(request.method)
        path_token = path_var.set(request.url.path)
        route_token = route_var.set(route_path)
        status_code_token = status_code_var.set(None)
        duration_token = duration_ms_var.set(None)
        client_ip_token = client_ip_var.set(client_ip)
        user_agent_token = user_agent_var.set(user_agent)

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path)
            route_var.set(route_path)
            status_code_var.set(status_code)
            duration_ms_var.set(duration_ms)
            response.headers["X-Request-ID"] = request_id

            access_logger.info(
                "request completed",
                extra={
                    "is_access_log": True,
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "route": route_path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                },
            )
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code_var.set(500)
            duration_ms_var.set(duration_ms)
            app_logger.exception(
                "request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "route": route_path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                },
            )
            raise
        finally:
            request_id_var.reset(request_id_token)
            method_var.reset(method_token)
            path_var.reset(path_token)
            route_var.reset(route_token)
            status_code_var.reset(status_code_token)
            duration_ms_var.reset(duration_token)
            client_ip_var.reset(client_ip_token)
            user_agent_var.reset(user_agent_token)
