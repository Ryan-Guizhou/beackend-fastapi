#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: filters.py
@Create: 2026/4/17 23:59
@Desc: 日志过滤器
"""

import logging


class ErrorOnlyFilter(logging.Filter):
    """
    仅保留错误级别日志的过滤器。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        判断当前日志是否属于错误日志。
        """
        return record.levelno >= logging.ERROR


class AccessLogFilter(logging.Filter):
    """
    仅保留访问日志的过滤器。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        判断当前日志是否为访问日志。
        """
        return getattr(record, "is_access_log", False) is True


class ExcludeAccessLogFilter(logging.Filter):
    """
    排除访问日志的过滤器。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        判断当前日志是否应排除访问日志。
        """
        return getattr(record, "is_access_log", False) is not True
