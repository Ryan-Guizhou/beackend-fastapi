#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: config.py
@Create: 2026/4/17 23:59
@Desc: 日志配置初始化
"""
import logging.config
from pathlib import Path

from config.config import settings


def setup_logging() -> None:
    """
    初始化项目日志配置。

    说明：
        该函数负责创建日志目录，并通过 `dictConfig` 注册控制台、
        应用日志、错误日志和访问日志等处理器。
    """
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_context": {
                "()": "config.log.formatters.RequestContextFilter",
            },
            "error_only": {
                "()": "config.log.filters.ErrorOnlyFilter",
            },
            "access_only": {
                "()": "config.log.filters.AccessLogFilter",
            },
            "exclude_access": {
                "()": "config.log.filters.ExcludeAccessLogFilter",
            },
        },
        "formatters": {
            "console": {
                "()": "config.log.formatters.ColorConsoleFormatter",
            },
            "json": {
                "()": "config.log.formatters.JsonFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "console",
                "filters": ["request_context"],
            },
            "app_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "json",
                "filename": str(log_dir / "app.log"),
                "when": "midnight",
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
                "filters": ["request_context", "exclude_access"],
            },
            "error_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": str(log_dir / "error.log"),
                "when": "midnight",
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
                "filters": ["request_context", "error_only", "exclude_access"],
            },
            "access_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_dir / "access.log"),
                "when": "midnight",
                "backupCount": settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
                "filters": ["request_context", "access_only"],
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "app_file", "error_file"],
        },
        "loggers": {
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "app.request": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "app.access": {
                "level": "INFO",
                "handlers": ["console", "access_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "apscheduler": {
                "level": "INFO",
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(config)
