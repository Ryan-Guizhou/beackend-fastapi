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
from middleware.auth_middleware import AuthMiddleware
from middleware.log_middleware import RequestLogMiddleware
from middleware.request_context_middleware import RequestContextMiddleware
from scheduler.router import router as scheduler_router
from apscheduler import AsyncScheduler
from scheduler.service import scheduler_service as service
from utils.mongo import MongoManager
from utils.redis.cache_decorator import set_default_cache_manager
from utils.redis.cache_manager import CacheManager
from utils.redis.redis_manager import RedisManager
from utils.redis.redis_service import RedisService

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理。

    在应用启动阶段初始化日志系统，并按配置启动 APScheduler，
    在应用关闭阶段统一释放调度器、Redis 与 Mongo 等资源。
    """
    setup_logging()
    app.state.logger = logger
    app.state.scheduler = None
    app.state.redis_manager = None
    app.state.redis_service = None
    app.state.cache_manager = None
    app.state.mongo_manager = None

    logger.info(
        "application starting",
        extra={
            "service": settings.app.name,
            "env": settings.env,
            "host": settings.app.host,
            "port": settings.app.port,
        },
    )

    scheduler = None
    scheduler_service = service
    redis_manager = None
    cache_manager = None
    mongo_manager = None
    try:
        redis_manager = RedisManager(settings.redis.url)
        await redis_manager.init()
        redis_service = RedisService(redis_manager.client)
        cache_manager = CacheManager(redis_service=redis_service)
        await cache_manager.start()
        app.state.redis_manager = redis_manager
        app.state.redis_service = redis_service
        app.state.cache_manager = cache_manager
        set_default_cache_manager(cache_manager)
        logger.info("redis started")

        mongo_manager = MongoManager(settings.mongo.url, settings.mongo.db)
        await mongo_manager.init()
        app.state.mongo_manager = mongo_manager
        logger.info("mongo started")

        if settings.scheduler.enabled:
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

        if cache_manager is not None:
            set_default_cache_manager(None)
            await cache_manager.stop()
            logger.info("cache manager stopped")

        if redis_manager is not None:
            await redis_manager.close()
            logger.info("redis stopped")

        if mongo_manager is not None:
            await mongo_manager.close()
            logger.info("mongo stopped")

        logger.info("application stopped")
        logging.shutdown()


app = FastAPI(
    title=settings.app.name,
    description="一个简单的 FastAPI CRUD 示例",
    version=settings.app.version,
    debug=settings.debug,
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

app.add_middleware(AuthMiddleware)
app.add_middleware(RequestContextMiddleware)
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
        "appName": settings.app.name,
        "version": settings.app.version,
        "description": settings.app.description,
    }])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app="main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.debug,
        access_log=False,
    )
