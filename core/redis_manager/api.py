#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/4/18 15:06
@Desc: Redis 管理路由
"""
import logging

from fastapi import APIRouter

from base.base_schema import ErrorCode, Response
from core.redis_manager.schema import (
    RedisBatchDeleteSchema,
    RedisFlushDBSchema,
    RedisKeyCreateSchema,
    RedisKeyExpireSchema,
    RedisKeyRenameSchema,
    RedisKeySearchSchema,
    RedisKeyUpdateSchema,
)
from core.redis_manager.service import AsyncRedisManagerService

logger = logging.getLogger("app")

router = APIRouter(prefix="/redis_manager", tags=["Redis管理"])


@router.get("/database", response_model=Response, summary="获取所有 Redis 库信息")
async def get_redis_database() -> Response:
    """
    获取 Redis 全部逻辑库统计信息。

    Returns:
        Response: 包含逻辑库基础统计信息的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=0)
    try:
        databases, total_keys = await service.get_all_database()
        return Response.success(
            data={
                "databases": databases,
                "total_keys": total_keys,
            }
        )
    except Exception as exc:
        logger.error("Failed to get redis database: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.post("/{db_index}/keys/search", response_model=Response, summary="搜索 Redis 键")
async def search_redis_keys(db_index: int, search: RedisKeySearchSchema) -> Response:
    """
    搜索指定逻辑库中的 Redis 键。

    Args:
        db_index: Redis 逻辑库编号。
        search: Redis 键搜索条件。

    Returns:
        Response: 包含分页搜索结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        keys, total = await service.search_keys(
            pattern=search.pattern,
            key_type=search.key_type,
            page_size=search.page_size,
            page=search.page_index,
        )
        return Response.success(
            data={
                "total": total,
                "keys": keys,
                "page": search.page_index,
                "page_size": search.page_size,
            }
        )
    except Exception as exc:
        logger.error("Failed to search redis keys: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.get("/{db_index}/keys/{key:path}", response_model=Response, summary="获取 Redis 键详情")
async def get_redis_key_detail(db_index: int, key: str) -> Response:
    """
    获取指定 Redis 键的详细信息。

    Args:
        db_index: Redis 逻辑库编号。
        key: Redis 键名。

    Returns:
        Response: 包含键详情的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        detail: dict = await service.get_key_detail(key)
        return Response.success(data=detail)
    except ValueError as exc:
        return Response.failure(code=ErrorCode.NOT_FOUND, msg=str(exc))
    except Exception as exc:
        logger.error("Failed to get redis key detail: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.post("/{db_index}/keys", response_model=Response, summary="创建 Redis 键")
async def create_redis_key(db_index: int, data: RedisKeyCreateSchema) -> Response:
    """
    创建指定类型的 Redis 键。

    Args:
        db_index: Redis 逻辑库编号。
        data: Redis 键创建参数。

    Returns:
        Response: 创建结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        await service.create_key(
            key=data.key,
            key_type=data.key_type,
            value=data.value,
            ttl=data.ttl,
        )
        return Response.success(msg=f"Key '{data.key}' created successfully")
    except Exception as exc:
        logger.error("Failed to create redis key: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.delete("/{db_index}/keys/{key:path}", response_model=Response, summary="删除 Redis 键")
async def delete_redis_key(db_index: int, key: str) -> Response:
    """
    删除单个 Redis 键。

    Args:
        db_index: Redis 逻辑库编号。
        key: Redis 键名。

    Returns:
        Response: 删除结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        is_success = await service.delete_key(key)
        if is_success:
            return Response.success(msg=f"Key '{key}' deleted successfully")
        return Response.failure(msg=f"Key '{key}' not found")
    except Exception as exc:
        logger.error("Failed to delete redis key: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.delete("/{db_index}/keys/batch-delete", response_model=Response, summary="批量删除 Redis 键")
async def batch_delete_redis_keys(db_index: int, data: RedisBatchDeleteSchema) -> Response:
    """
    批量删除 Redis 键。

    Args:
        db_index: Redis 逻辑库编号。
        data: Redis 批量删除参数。

    Returns:
        Response: 批量删除结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        count = await service.batch_delete_keys(keys=data.keys)
        return Response.success(data={"deleted_count": count})
    except Exception as exc:
        logger.error("Failed to delete redis keys: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.post("/{db_index}/keys/{key:path}/rename", response_model=Response, summary="重命名 Redis 键")
async def rename_redis_key(db_index: int, key: str, data: RedisKeyRenameSchema) -> Response:
    """
    重命名 Redis 键。

    Args:
        db_index: Redis 逻辑库编号。
        key: 原 Redis 键名。
        data: Redis 键重命名参数。

    Returns:
        Response: 重命名结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        await service.rename_key(key, data.new_key)
        return Response.success(msg="Key renamed successfully")
    except Exception as exc:
        logger.error("Failed to rename redis key: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.post("/{db_index}/keys/{key:path}/expire", response_model=Response, summary="设置 Redis 键过期时间")
async def set_redis_key_expire(db_index: int, key: str, data: RedisKeyExpireSchema) -> Response:
    """
    设置 Redis 键过期时间。

    Args:
        db_index: Redis 逻辑库编号。
        key: Redis 键名。
        data: Redis 键过期时间参数。

    Returns:
        Response: 过期时间设置结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        await service.set_expire(key, data.ttl)
        return Response.success(msg="TTL updated successfully")
    except Exception as exc:
        logger.error("Failed to set redis key ttl: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.post("/{db_index}/keys/flush", response_model=Response, summary="清空 Redis 数据库")
async def flush_redis_database(db_index: int, data: RedisFlushDBSchema) -> Response:
    """
    清空指定逻辑库。

    Args:
        db_index: Redis 逻辑库编号。
        data: Redis 清库确认参数。

    Returns:
        Response: 清库结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        await service.flush_db(data.confirm)
        return Response.success(msg="Database flushed successfully")
    except Exception as exc:
        logger.error("Failed to flush redis database: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()


@router.put("/{db_index}/keys/{key:path}", response_model=Response, summary="更新 Redis 键")
async def update_redis_key(db_index: int, key: str, data: RedisKeyUpdateSchema) -> Response:
    """
    更新指定 Redis 键的值和过期时间。

    Args:
        db_index: Redis 逻辑库编号。
        key: Redis 键名。
        data: Redis 键更新参数。

    Returns:
        Response: 更新结果的统一响应对象。
    """
    service = AsyncRedisManagerService(db_index=db_index)
    try:
        await service.update_key(
            key=key,
            value=data.value,
            ttl=data.ttl,
        )
        return Response.success(msg="Key updated successfully")
    except Exception as exc:
        logger.error("Failed to update redis key: %s", exc)
        return Response.failure(msg=str(exc))
    finally:
        await service.close()
