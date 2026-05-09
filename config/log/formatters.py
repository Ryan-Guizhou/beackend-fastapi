#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: formatters.py
@Create: 2026/4/17 23:59
@Desc: 日志格式化器
"""

import json
import logging
from datetime import datetime

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

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class RequestContextFilter(logging.Filter):
    """
    请求上下文注入过滤器。

    说明：
        该过滤器会在日志输出前，将请求上下文中的公共字段挂载到日志记录对象上。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        将上下文字段注入到日志记录中。
        """
        record.request_id = getattr(record, "request_id", request_id_var.get())
        record.method = getattr(record, "method", method_var.get())
        record.path = getattr(record, "path", path_var.get())
        record.route = getattr(record, "route", route_var.get())
        record.status_code = getattr(record, "status_code", status_code_var.get())
        record.duration_ms = getattr(record, "duration_ms", duration_ms_var.get())
        record.client_ip = getattr(record, "client_ip", client_ip_var.get())
        record.user_agent = getattr(record, "user_agent", user_agent_var.get())
        return True


class ColorConsoleFormatter(logging.Formatter):
    """
    控制台彩色日志格式化器。
    """

    RESET = "\033[0m"
    DIM = "\033[2m"
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[37;41m",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        将日志记录渲染为更紧凑的彩色控制台文本。
        """
        timestamp = datetime.fromtimestamp(record.created).strftime(TIME_FORMAT)
        level = record.levelname
        color = self.COLORS.get(level, "")
        message = record.getMessage()
        request_id = getattr(record, "request_id", None)
        method = getattr(record, "method", None)
        path = getattr(record, "path", None)
        status_code = getattr(record, "status_code", None)
        duration_ms = getattr(record, "duration_ms", None)

        segments = [
            f"{self.DIM}{timestamp}{self.RESET}",
            f"{color}{level:>8}{self.RESET}",
            record.name,
        ]

        if request_id:
            segments.append(f"request_id={request_id}")

        if method and path:
            route_text = f"{method:<6} {path}"
            if status_code is not None:
                route_text = f"{route_text} -> {status_code}"
            segments.append(route_text)

        if duration_ms is not None:
            segments.append(f"{duration_ms:.2f}ms")

        segments.append(message)

        rendered = " | ".join(segments)
        if record.exc_info:
            rendered = f"{rendered}\n{self.formatException(record.exc_info)}"
        return rendered


class JsonFormatter(logging.Formatter):
    """
    JSON 日志格式化器。
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        将日志记录渲染为 JSON 字符串。
        """
        payload = {
            "timestamp": datetime.fromtimestamp(record.created).strftime(TIME_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "route": getattr(record, "route", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "client_ip": getattr(record, "client_ip", None),
            "user_agent": getattr(record, "user_agent", None),
            "module": record.module,
            "filename": record.filename,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
