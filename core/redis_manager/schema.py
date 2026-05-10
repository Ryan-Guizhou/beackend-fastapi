#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/4/18 15:06
@Desc: Redis 管理模型
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from base.base_schema import PaginatedRequest


class RedisKeyTypeEnum(str, Enum):
    """
    Redis 键类型枚举。

    说明：
        用于约束 Redis 键的数据类型，避免在接口层传入非法类型值。
    """

    STRING = "string"
    HASH = "hash"
    LIST = "list"
    SET = "set"
    ZSET = "zset"


class RedisKeySearchSchema(PaginatedRequest):
    """
    Redis 键搜索请求模型。

    说明：
        用于接收 key 模式匹配、类型过滤和分页参数。
    """

    pattern: str = Field(
        default="*",
        description="搜索模式，支持通配符",
    )
    key_type: RedisKeyTypeEnum | None = Field(
        default=None,
        alias="keyType",
        description="按 Redis 键类型过滤",
    )



class RedisKeyCreateSchema(BaseModel):
    """
    Redis 键创建请求模型。
    """

    key: str = Field(
        ...,
        description="键名",
    )
    key_type: RedisKeyTypeEnum = Field(
        ...,
        alias="keyType",
        description="Redis 键类型",
    )
    value: Any = Field(
        ...,
        description="键值",
    )
    ttl: int | None = Field(
        None,
        description="过期时间，单位秒，-1 表示永久",
    )


class RedisBatchDeleteSchema(BaseModel):
    """
    Redis 批量删除请求模型。
    """

    keys: list[str] = Field(
        ...,
        description="待删除的 Redis 键列表",
    )


class RedisKeyUpdateSchema(BaseModel):
    """
    Redis 键更新请求模型。
    """

    value: Any = Field(
        ...,
        description="新的键值",
    )
    ttl: int | None = Field(
        None,
        description="新的过期时间，单位秒，-1 表示永久",
    )


class RedisKeyRenameSchema(BaseModel):
    """
    Redis 键重命名请求模型。
    """

    new_key: str = Field(
        ...,
        alias="newKey",
        description="新的键名",
    )


class RedisKeyExpireSchema(BaseModel):
    """
    Redis 键过期时间设置请求模型。
    """

    ttl: int = Field(
        ...,
        description="过期时间，单位秒，-1 表示永久",
    )


class RedisFlushDBSchema(BaseModel):
    """
    Redis 清库请求模型。
    """

    confirm: bool = Field(
        ...,
        description="是否确认清空当前数据库，必须显式传入 true",
        examples=[True],
    )
