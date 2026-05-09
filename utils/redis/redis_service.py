#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: redis_service.py
@Create: 2026/5/9
@Desc: Redis 通用服务
"""

from __future__ import annotations

import json
import inspect
import types
import uuid
from contextlib import asynccontextmanager
from typing import Any, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel
from redis.asyncio import Redis

# 泛型参数，用于类型提示。
T = TypeVar("T")


def _is_pydantic_model_type(target_type: Any) -> bool:
    """
    判断目标类型是否为 Pydantic 模型类。

    Args:
        target_type: 待判断的目标类型。

    Returns:
        bool: 是 Pydantic 模型类时返回 `True`。
    """
    if not inspect.isclass(target_type):
        return False
    try:
        return issubclass(target_type, BaseModel)
    except TypeError:
        return False


class RedisService:
    """
    通用 Redis 异步服务。
    集成 Pydantic 序列化、类型恢复、分布式锁等通用能力。
    """

    def __init__(self, client: Redis) -> None:
        """
        初始化 Redis 服务。
        Args:
            client: Redis 异步客户端实例。
        """
        self.client = client

    def build_key(self, *parts: Any) -> str:
        """
        构造 Redis Key。
        Args:
            *parts: Key 的各段内容。
        Returns:
            str: 拼接后的 Redis Key。
        """
        clean_parts = [str(part).strip(":") for part in parts if part is not None and str(part) != ""]
        return ":".join(clean_parts)

    def to_jsonable(self, value: Any) -> Any:
        """
        将复杂对象转换为可 JSON 序列化的基础类型。
        Args:
            value: 待转换对象。
        Returns:
            Any: 可直接交给 `json.dumps()` 的对象。
        """
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return {str(k): self.to_jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self.to_jsonable(item) for item in value]
        return value

    def serialize(self, value: Any) -> str:
        """
        将对象序列化为 JSON 字符串。
        Args:
            value: 待序列化对象。
        Returns:
            str: JSON 字符串。
        """
        return json.dumps(self.to_jsonable(value), ensure_ascii=False, separators=(",", ":"))

    def _restore_type(self, data: Any, target_type: Any) -> Any:
        """
        按目标类型递归恢复反序列化结果。
        Args:
            data: JSON 解析后的基础数据。
            target_type: 目标类型。
        Returns:
            Any: 类型恢复后的结果。
        """
        if target_type is None or target_type is Any:
            return data

        if data is None:
            return None

        origin = get_origin(target_type)
        args = get_args(target_type)

        if origin in (Union, types.UnionType):
            non_none_args = [arg for arg in args if arg is not type(None)]
            if not non_none_args:
                return data
            return self._restore_type(data, non_none_args[0])

        if _is_pydantic_model_type(target_type):
            return target_type.model_validate(data)

        if target_type is str:
            return str(data)
        if target_type is int:
            return int(data)
        if target_type is float:
            return float(data)
        if target_type is bool:
            return bool(data)

        if origin is list:
            item_type = args[0] if args else Any
            return [self._restore_type(item, item_type) for item in data]

        if origin is set:
            item_type = args[0] if args else Any
            return {self._restore_type(item, item_type) for item in data}

        if origin is tuple:
            if len(args) == 2 and args[1] is Ellipsis:
                return tuple(self._restore_type(item, args[0]) for item in data)
            return tuple(
                self._restore_type(item, args[idx] if idx < len(args) else Any)
                for idx, item in enumerate(data)
            )

        if origin is dict:
            key_type = args[0] if len(args) > 0 else Any
            value_type = args[1] if len(args) > 1 else Any
            return {
                self._restore_type(k, key_type): self._restore_type(v, value_type)
                for k, v in data.items()
            }

        return data

    def deserialize(self, value: str | None, target_type: Any = None) -> Any:
        """
        将 JSON 字符串反序列化为 Python 对象。
        Args:
            value: JSON 字符串。
            target_type: 目标类型。
        Returns:
            Any: 反序列化后的结果。
        """
        if value is None:
            return None
        data = json.loads(value)
        return self._restore_type(data, target_type)

    # --- String 操作 ---

    async def set(self, key: str, value: Any, *, ex: int | None = None, nx: bool = False) -> bool:
        """
        存储对象。
        Args:
            key: Redis Key。
            value: 待存储对象。
            ex: 过期时间，单位秒。
            nx: 是否仅在 Key 不存在时写入。
        Returns:
            bool: 是否写入成功。
        """
        return bool(await self.client.set(key, self.serialize(value), ex=ex, nx=nx))

    async def get(self, key: str, target_type: Any = None) -> Any:
        """
        读取对象。
        Args:
            key: Redis Key。
            target_type: 目标类型。
        Returns:
            Any: 反序列化后的对象。
        """
        value = await self.client.get(key)
        return self.deserialize(value, target_type)

    async def set_raw(self, key: str, value: str, *, ex: int | None = None, nx: bool = False) -> bool:
        """
        存储原始字符串。
        Args:
            key: Redis Key。
            value: 原始字符串。
            ex: 过期时间，单位秒。
            nx: 是否仅在 Key 不存在时写入。
        Returns:
            bool: 是否写入成功。
        """
        return bool(await self.client.set(key, value, ex=ex, nx=nx))

    async def get_raw(self, key: str) -> str | None:
        """
        读取原始字符串。
        Args:
            key: Redis Key。
        Returns:
            str | None: 原始字符串或 `None`。
        """
        return await self.client.get(key)

    # --- 通用 Key 管理 ---

    async def delete(self, *keys: str) -> int:
        """
        删除一个或多个 Key。
        Args:
            *keys: Redis Key 列表。
        Returns:
            int: 实际删除数量。
        """
        if not keys:
            return 0
        return int(await self.client.delete(*keys))

    async def exists(self, key: str) -> bool:
        """
        检查 Key 是否存在。
        Args:
            key: Redis Key。
        Returns:
            bool: 是否存在。
        """
        return bool(await self.client.exists(key))

    async def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间。
        Args:
            key: Redis Key。
            seconds: 过期时间，单位秒。
        Returns:
            bool: 是否设置成功。
        """
        return bool(await self.client.expire(key, seconds))

    async def ttl(self, key: str) -> int:
        """
        查询剩余过期时间。
        Args:
            key: Redis Key。
        Returns:
            int: 剩余过期时间，单位秒。
        """
        return int(await self.client.ttl(key))

    # --- 原子计数操作 ---

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        原子自增。
        Args:
            key: Redis Key。
            amount: 自增步长。
        Returns:
            int: 自增后的值。
        """
        return int(await self.client.incr(key, amount))

    async def decr(self, key: str, amount: int = 1) -> int:
        """
        原子自减。
        Args:
            key: Redis Key。
            amount: 自减步长。
        Returns:
            int: 自减后的值。
        """
        return int(await self.client.decr(key, amount))

    # --- 批量操作 ---

    async def mset(self, mapping: dict[str, Any], *, ex: int | None = None) -> None:
        """
        批量设置多个 Key。
        Args:
            mapping: Key 与对象的映射。
            ex: 过期时间，单位秒。
        """
        async with self.client.pipeline(transaction=False) as pipe:
            for key, value in mapping.items():
                pipe.set(key, self.serialize(value), ex=ex)
            await pipe.execute()

    async def mget(self, keys: list[str], target_type: Any = None) -> list[Any]:
        """
        批量获取多个 Key。
        Args:
            keys: Redis Key 列表。
            target_type: 目标类型。
        Returns:
            list[Any]: 反序列化后的结果列表。
        """
        if not keys:
            return []
        values = await self.client.mget(keys)
        return [self.deserialize(value, target_type) for value in values]

    # --- Hash 操作 ---

    async def hset(self, key: str, field: str, value: Any) -> int:
        """
        设置哈希字段。
        Args:
            key: Redis Key。
            field: 哈希字段名。
            value: 字段值。
        Returns:
            int: Redis 返回的写入结果。
        """
        return int(await self.client.hset(key, field, self.serialize(value)))

    async def hmset(self, key: str, mapping: dict[str, Any]) -> int:
        """
        批量设置哈希字段。
        Args:
            key: Redis Key。
            mapping: 字段与对象的映射。
        Returns:
            int: Redis 返回的写入结果。
        """
        data = {field: self.serialize(value) for field, value in mapping.items()}
        return int(await self.client.hset(key, mapping=data))

    async def hget(self, key: str, field: str, target_type: Any = None) -> Any:
        """
        获取哈希字段。
        Args:
            key: Redis Key。
            field: 哈希字段名。
            target_type: 目标类型。
        Returns:
            Any: 字段值。
        """
        value = await self.client.hget(key, field)
        return self.deserialize(value, target_type)

    async def hgetall(self, key: str, value_type: Any = None) -> dict[str, Any]:
        """
        获取哈希表全部字段。
        Args:
            key: Redis Key。
            value_type: 字段值目标类型。
        Returns:
            dict[str, Any]: 哈希字段映射。
        """
        result = await self.client.hgetall(key)
        return {field: self.deserialize(value, value_type) for field, value in result.items()}

    async def hdel(self, key: str, *fields: str) -> int:
        """
        删除哈希字段。
        Args:
            key: Redis Key。
            *fields: 待删除字段名。
        Returns:
            int: 实际删除数量。
        """
        if not fields:
            return 0
        return int(await self.client.hdel(key, *fields))

    # --- List 操作 ---

    async def lpush(self, key: str, *values: Any) -> int:
        """
        从左侧写入列表。
        Args:
            key: Redis Key。
            *values: 待写入对象。
        Returns:
            int: 写入后的列表长度。
        """
        if not values:
            return 0
        payload = [self.serialize(value) for value in values]
        return int(await self.client.lpush(key, *payload))

    async def rpush(self, key: str, *values: Any) -> int:
        """
        从右侧写入列表。
        Args:
            key: Redis Key。
            *values: 待写入对象。
        Returns:
            int: 写入后的列表长度。
        """
        if not values:
            return 0
        payload = [self.serialize(value) for value in values]
        return int(await self.client.rpush(key, *payload))

    async def lrange(self, key: str, start: int, end: int, item_type: Any = None) -> list[Any]:
        """
        获取列表范围内的元素。
        Args:
            key: Redis Key。
            start: 起始下标。
            end: 结束下标。
            item_type: 元素目标类型。
        Returns:
            list[Any]: 反序列化后的元素列表。
        """
        values = await self.client.lrange(key, start, end)
        return [self.deserialize(value, item_type) for value in values]

    # --- Set 操作 ---

    async def sadd(self, key: str, *values: Any) -> int:
        """
        向集合添加元素。
        Args:
            key: Redis Key。
            *values: 待添加对象。
        Returns:
            int: 实际新增数量。
        """
        if not values:
            return 0
        payload = [self.serialize(value) for value in values]
        return int(await self.client.sadd(key, *payload))

    async def smembers(self, key: str, item_type: Any = None) -> set[Any]:
        """
        获取集合全部成员。
        Args:
            key: Redis Key。
            item_type: 元素目标类型。
        Returns:
            set[Any]: 集合成员。
        """
        values = await self.client.smembers(key)
        return {self.deserialize(value, item_type) for value in values}

    async def srem(self, key: str, *values: Any) -> int:
        """
        从集合移除元素。
        Args:
            key: Redis Key。
            *values: 待移除对象。
        Returns:
            int: 实际移除数量。
        """
        if not values:
            return 0
        payload = [self.serialize(value) for value in values]
        return int(await self.client.srem(key, *payload))

    # --- ZSet 操作 ---

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        """
        添加有序集合成员及其分数。
        Args:
            key: Redis Key。
            mapping: 成员与分数的映射。
        Returns:
            int: 实际新增数量。
        """
        return int(await self.client.zadd(key, mapping))

    async def zrange(self, key: str, start: int, end: int, *, withscores: bool = False) -> Any:
        """
        获取有序集合范围内的成员。
        Args:
            key: Redis Key。
            start: 起始下标。
            end: 结束下标。
            withscores: 是否返回分数。
        Returns:
            Any: Redis 返回的成员列表。
        """
        return await self.client.zrange(key, start, end, withscores=withscores)

    async def zrem(self, key: str, *members: str) -> int:
        """
        移除有序集合成员。
        Args:
            key: Redis Key。
            *members: 待移除成员。
        Returns:
            int: 实际移除数量。
        """
        if not members:
            return 0
        return int(await self.client.zrem(key, *members))

    # --- 扫描与发布订阅 ---

    async def keys(self, pattern: str) -> list[str]:
        """
        按模式匹配 Key，大数据量下谨慎使用。
        Args:
            pattern: Key 匹配模式。
        Returns:
            list[str]: 匹配到的 Key 列表。
        """
        return await self.client.keys(pattern)

    async def scan_iter(self, pattern: str):
        """
        使用迭代器扫描 Key。
        Args:
            pattern: Key 匹配模式。
        Yields:
            str: 匹配到的 Key。
        """
        async for key in self.client.scan_iter(match=pattern):
            yield key

    async def publish(self, channel: str, message: str) -> int:
        """
        发布消息到频道。
        Args:
            channel: Redis 频道。
            message: 消息内容。
        Returns:
            int: 接收到消息的订阅者数量。
        """
        return int(await self.client.publish(channel, message))

    # --- 分布式锁 ---

    async def acquire_lock(self, key: str, *, expire: int = 10, value: str | None = None) -> str | None:
        """
        获取分布式锁。
        Args:
            key: 锁 Key。
            expire: 锁有效期，单位秒。
            value: 锁唯一标识，不传时自动生成。
        Returns:
            str | None: 成功返回 token，失败返回 `None`。
        """
        token = value or uuid.uuid4().hex
        success = await self.client.set(key, token, ex=expire, nx=True)
        return token if success else None

    async def release_lock(self, key: str, token: str) -> bool:
        """
        释放分布式锁。
        Args:
            key: 锁 Key。
            token: 获取锁时返回的 token。
        Returns:
            bool: 是否释放成功。
        """
        lua = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        end
        return 0
        """
        result = await self.client.eval(lua, 1, key, token)
        return bool(result)

    @asynccontextmanager
    async def lock(
        self,
        key: str,
        *,
        expire: int = 10,
        retry_interval: float = 0.1,
        retry_times: int = 10,
    ):
        """
        分布式锁上下文管理器。
        Args:
            key: 锁 Key。
            expire: 锁有效期，单位秒。
            retry_interval: 获取锁失败后的重试间隔。
            retry_times: 获取锁重试次数。
        """
        import asyncio

        token = None
        for _ in range(retry_times):
            token = await self.acquire_lock(key, expire=expire)
            if token is not None:
                break
            await asyncio.sleep(retry_interval)

        if token is None:
            raise TimeoutError(f"获取分布式锁失败: {key}")

        try:
            yield
        finally:
            await self.release_lock(key, token)
