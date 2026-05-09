#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: context.py
@Create: 2026/4/17 23:59
@Desc: 请求日志上下文
"""

from contextvars import ContextVar


# 以下上下文变量用于在一次请求生命周期内透传日志字段
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
method_var: ContextVar[str | None] = ContextVar("method", default=None)
path_var: ContextVar[str | None] = ContextVar("path", default=None)
route_var: ContextVar[str | None] = ContextVar("route", default=None)
status_code_var: ContextVar[int | None] = ContextVar("status_code", default=None)
duration_ms_var: ContextVar[float | None] = ContextVar("duration_ms", default=None)
client_ip_var: ContextVar[str | None] = ContextVar("client_ip", default=None)
user_agent_var: ContextVar[str | None] = ContextVar("user_agent", default=None)
