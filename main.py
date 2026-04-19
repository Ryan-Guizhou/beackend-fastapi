#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: main.py
@Create: 2026/4/17 23:59
@Desc: FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from base.base_schema import Response
from config.config import settings
from config.log.config import setup_logging
from core.router import router as core_router
from demo.router import router as demo_router
from middleware.log_middleware import RequestLogMiddleware


setup_logging()
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    应用生命周期管理。

    说明：
        使用 FastAPI 推荐的 lifespan 方案替代过时的 `@app.on_event`。
    """
    logger.info(
        "application started",
        extra={
            "service": settings.APP_NAME,
            "env": settings.ENV,
            "host": settings.APP_HOST,
            "port": settings.APP_PORT,
        },
    )
    yield
    logger.info("application stopped")


# 创建 FastAPI 应用实例，并注入基础项目信息
app = FastAPI(
    title=settings.APP_NAME,
    description="一个简单的 FastAPI CRUD 示例",
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

# 注册请求日志中间件和业务路由
app.add_middleware(RequestLogMiddleware)
app.include_router(core_router, prefix="/api/core")
app.include_router(demo_router, prefix="/demo")


@app.get("/", tags=["根路由"])
async def root() -> Response:
    """
    获取应用基础信息。

    Returns:
        Response: 包含应用名称、版本和描述信息的统一响应对象。
    """
    logger.info("root endpoint accessed")
    return Response.success(data=[{
        "appName": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
    }])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app="main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        access_log=False,
    )
