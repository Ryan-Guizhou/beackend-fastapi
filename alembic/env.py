#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: env.py
@Create: 2026/4/21 00:00
@Desc: Alembic 迁移环境配置
"""
import asyncio
import importlib
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_engine_from_config

from config.config import settings
from config.database import Base

# Alembic 配置对象，可读取 alembic.ini 中的配置项
config = context.config

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def load_model_modules() -> None:
    """
    自动加载项目中的模型模块。
    说明：
        Alembic 的自动迁移依赖 ORM 模型已经注册到 `Base.metadata`。
        这里会扫描 `core`、`demo` 目录下的所有 `model.py` 文件并动态导入，
        避免每新增一个模块都要手动修改 `env.py`。
    """
    project_root = Path(__file__).resolve().parent.parent
    scan_dirs = ("core", "demo")

    for scan_dir in scan_dirs:
        base_dir = project_root / scan_dir
        if not base_dir.exists():
            continue

        for model_file in base_dir.rglob("model.py"):
            module_name = ".".join(
                model_file.relative_to(project_root).with_suffix("").parts
            )
            importlib.import_module(module_name)


# 先加载所有模型模块，再读取元数据，确保自动迁移能感知全部表结构
load_model_modules()

# 使用项目真实 ORM 基类的元数据，供 autogenerate 比对数据库结构
target_metadata = Base.metadata

# 将运行时数据库连接串注入 Alembic 配置，避免依赖 alembic.ini 中的占位值
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    离线模式执行迁移。
    Args:
        无。
    Returns:
        无。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    基于同步连接执行迁移。
    Args:
        connection: Alembic 迁移阶段使用的数据库连接。
    Returns:
        无。
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    在线模式执行迁移。
    Args:
        无。
    Returns:
        无。
    """
    connectable: AsyncEngine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
