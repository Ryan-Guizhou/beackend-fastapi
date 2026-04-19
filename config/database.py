#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: database.py
@Create: 2026/4/18 00:08
@Desc: 数据库连接配置
"""
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config.config import settings


class Base(DeclarativeBase):
    """
    SQLAlchemy 声明式模型基类。

    说明：
        所有 ORM 模型都应继承该基类，
        以便统一纳入 SQLAlchemy 的元数据管理。
    """

    pass


# 创建异步数据库引擎，供全局会话工厂复用
engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    future=True,
)

# 创建异步会话工厂，用于按需生成数据库会话
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """
    获取数据库会话。

    说明：
        该函数通常作为 FastAPI 的依赖项使用，
        每次请求按需创建一个异步会话，并在请求结束后自动释放。

    Yields:
        AsyncSession: 当前请求可用的数据库会话对象。
    """
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def transaction(db: AsyncSession):
    """
    数据库事务上下文管理器。

    说明：
        该上下文管理器用于将多个数据库操作包裹在同一事务中。
        当代码块执行成功时自动提交事务，发生异常时自动回滚。

    Args:
        db: 当前使用的异步数据库会话。

    Yields:
        AsyncSession: 当前事务内可复用的数据库会话对象。
    """
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
