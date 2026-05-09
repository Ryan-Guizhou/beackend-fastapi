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
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event

from config.config import settings

logger = logging.getLogger(__name__)


# ==================== SQL debug config ====================
class SQLDebugConfig:
    """
    SQL 调试配置。
    """

    _enabled = os.getenv('SQL_DEBUG', 'false').lower() in ('true', '1', 'yes')
    _print_full_sql = os.getenv('PRINT_FULL_SQL', 'false').lower() in ('true', '1', 'yes')
    _log_slow_query = int(os.getenv('SLOW_QUERY_THRESHOLD', '1000'))  # Milliseconds

    @classmethod
    def is_enabled(cls):
        return cls._enabled or settings.debug

    @classmethod
    def should_print_full_sql(cls):
        return cls._print_full_sql and cls.is_enabled()

    @classmethod
    def slow_query_threshold(cls):
        return cls._log_slow_query

    @classmethod
    def set_enabled(cls, enabled: bool):
        cls._enabled = enabled
        logger.info("sql debug mode %s", "enabled" if enabled else "disabled")


engine = create_async_engine(
    settings.database.url,
    echo=SQLDebugConfig.is_enabled(),
    echo_pool=SQLDebugConfig.is_enabled() if os.getenv('ECHO_POOL') else False,
)


def setup_sql_debug_listener(engine):
    """
    注册 SQL 调试事件监听器。
    Args:
        engine: SQLAlchemy 异步引擎。
    """

    @event.listens_for(engine.sync_engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement, params, context, executemany):
        """
        记录 SQL 执行开始时间。
        """
        if SQLDebugConfig.is_enabled():
            context._query_start_time = time.time()

            if SQLDebugConfig.should_print_full_sql():
                formatted_sql = statement
                if params:
                    try:
                        for param in (params if isinstance(params, (list, tuple)) else [params]):
                            if isinstance(param, str):
                                formatted_sql = formatted_sql.replace('%s', f"'{param}'", 1)
                            else:
                                formatted_sql = formatted_sql.replace('%s', str(param), 1)
                    except Exception:
                        pass

                logger.info("\n%s\n[SQL EXECUTE] %s\n%s", "=" * 80, formatted_sql, "=" * 80)
            else:
                logger.debug("[SQL STATEMENT] %s", statement)
                if params:
                    logger.debug("[SQL PARAMS] %s", params)

    @event.listens_for(engine.sync_engine, 'after_cursor_execute')
    def after_cursor_execute(conn, cursor, statement, params, context, executemany):
        """
        记录 SQL 执行耗时。
        """
        if SQLDebugConfig.is_enabled() and hasattr(context, '_query_start_time'):
            elapsed_time = (time.time() - context._query_start_time) * 1000

            if elapsed_time > SQLDebugConfig.slow_query_threshold():
                logger.warning(
                    "[SLOW QUERY] elapsed=%.2fms threshold=%sms sql=%s",
                    elapsed_time,
                    SQLDebugConfig.slow_query_threshold(),
                    statement[:500],
                )
            else:
                logger.debug("[SQL FINISHED] elapsed=%.2fms", elapsed_time)


setup_sql_debug_listener(engine)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

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
