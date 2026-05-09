#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: __init__.py
@Create: 2026/5/9
@Desc: 日志配置包初始化
"""

from config.log.config import setup_logging
from middleware.log_middleware import RequestLogMiddleware

__all__ = ["setup_logging"]
