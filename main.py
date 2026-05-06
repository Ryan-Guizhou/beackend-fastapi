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
from scheduler.router import router as scheduler_router
from utils.redis_client import RedisClient
from apscheduler import AsyncScheduler
from scheduler.service import scheduler_service as service

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理。
    说明:
        在应用启动阶段初始化日志系统，并按配置启动 APScheduler；
        在应用关闭阶段统一释放调度器与 Redis 等资源。
    """
    setup_logging()
    app.state.logger = logger
    app.state.scheduler = None

    logger.info(
        "application starting",
        extra={
            "service": settings.APP_NAME,
            "env": settings.ENV,
            "host": settings.APP_HOST,
            "port": settings.APP_PORT,
        },
    )

    scheduler = None
    scheduler_service = service
    try:
        if getattr(settings, "ENABLE_SCHEDULER", True):
            scheduler = AsyncScheduler()
            await scheduler.__aenter__()
            await scheduler.start_in_background()
            scheduler_service.set_scheduler(scheduler)
            await scheduler_service.load_jobs_from_db()
            app.state.scheduler = scheduler
            logger.info("scheduler started")

        logger.info("application started")
        yield
    finally:
        if scheduler_service is not None:
            scheduler_service.set_running(False)

        if scheduler is not None:
            await scheduler.__aexit__(None, None, None)
            logger.info("scheduler stopped")

        await RedisClient.close()
        logger.info("application stopped")
        logging.shutdown()


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

app.add_middleware(RequestLogMiddleware)
app.include_router(core_router, prefix="/api/core")
app.include_router(demo_router, prefix="/demo")
app.include_router(scheduler_router, prefix="/api")


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
