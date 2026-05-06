#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: database.py
@Create: 2026/4/20 21:27
@Desc: 数据库依赖
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)


# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False, # 是否自动刷新
    autocommit=False, # 是否自动提交
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（不自动提交事务）。
    Returns:
        AsyncGenerator[AsyncSession, None]: FastAPI 依赖注入可消费的异步会话生成器。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            logger.exception("Database session error in get_db.")
            raise
        finally:
            await session.close()


async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（自动事务提交/回滚）。
    Returns:
        AsyncGenerator[AsyncSession, None]: 带自动事务控制的异步会话生成器。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            logger.exception("Database transaction error in get_db_transaction.")
            await session.rollback()  # 回滚事务
            raise
        finally:
            await session.close()


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncIterator[AsyncSession]:
    """
    为已有会话提供事务上下文。
    Args:
        db: 已创建的异步数据库会话。
    Returns:
        AsyncIterator[AsyncSession]: 可在 `async with` 中使用的事务上下文。
    """
    try:
        yield db
        await db.commit()
    except Exception:
        logger.exception("Database transaction context error.")
        await db.rollback()
        raise


DbSession = Annotated[AsyncSession, Depends(get_db)]