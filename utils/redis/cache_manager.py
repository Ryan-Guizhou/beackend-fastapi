#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: cache_manager.py
@Create: 2026/5/9
@Desc: Redis 缓存管理器
"""

from __future__ import annotations

import asyncio
import json
from contextlib import suppress
from typing import Any

from utils.redis.local_cache import LocalCache
from utils.redis.redis_service import RedisService


class CacheManager:
    """
    二级缓存管理器。
    Args:
        redis_service: Redis 服务实例。
        local_cache: 本地缓存实例，为空时使用默认本地缓存。
        invalidation_channel: 缓存失效通知频道。
        default_local_ttl: 本地缓存默认过期时间，单位秒。
    """

    NULL_SENTINEL = "__fastapi_cache_null__"

    def __init__(
        self,
        redis_service: RedisService,
        *,
        local_cache: LocalCache | None = None,
        invalidation_channel: str = "fastapi:cache:invalidation",
        default_local_ttl: int = 60,
    ) -> None:
        self.redis_service = redis_service
        self.local_cache = local_cache or LocalCache()
        self.invalidation_channel = invalidation_channel
        self.default_local_ttl = default_local_ttl
        self._pubsub = None
        self._listener_task: asyncio.Task | None = None
        self._started = False

    def build_key(self, cache_name: str, raw_key: str) -> str:
        """
        构造完整缓存键。
        Args:
            cache_name: 缓存命名空间，作为一类缓存的统一前缀。
            raw_key: 业务原始键。
        Returns:
            str: 完整缓存键。
        """
        return self.redis_service.build_key(cache_name, raw_key)

    def _serialize_cache_value(self, value: Any) -> str:
        """
        序列化缓存值。
        Args:
            value: 待缓存的数据。
        Returns:
            str: 可写入 Redis 和本地缓存的字符串。
        """
        if value is None:
            return self.NULL_SENTINEL
        return self.redis_service.serialize(value)

    def _deserialize_cache_value(self, raw: str, target_type: Any = None) -> Any:
        """
        反序列化缓存值。
        Args:
            raw: 缓存中的原始字符串。
            target_type: 目标类型。
        Returns:
            Any: 反序列化后的缓存值。
        """
        if raw == self.NULL_SENTINEL:
            return None
        return self.redis_service.deserialize(raw, target_type)

    async def start(self) -> None:
        """
        启动缓存失效消息监听。
        """
        if self._started:
            return

        self._pubsub = self.redis_service.client.pubsub()
        await self._pubsub.subscribe(self.invalidation_channel)
        self._listener_task = asyncio.create_task(self._listen_invalidation())
        self._started = True

    async def stop(self) -> None:
        """
        停止缓存失效监听并释放订阅资源。
        """
        if not self._started:
            return

        if self._listener_task is not None:
            self._listener_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._listener_task

        if self._pubsub is not None:
            await self._pubsub.unsubscribe(self.invalidation_channel)
            await self._pubsub.aclose()

        self._listener_task = None
        self._pubsub = None
        self._started = False

    async def _listen_invalidation(self) -> None:
        """
        监听缓存失效消息，并同步清理当前进程的本地缓存。
        """
        if self._pubsub is None:
            return

        while True:
            message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                await asyncio.sleep(0.05)
                continue

            data = message.get("data")
            if not data:
                continue

            payload = json.loads(data)
            action = payload["action"]
            cache_name = payload["cache_name"]

            if action == "evict":
                full_key = self.build_key(cache_name, payload["raw_key"])
                await self.local_cache.delete(full_key)
            elif action == "clear":
                prefix = self.redis_service.build_key(cache_name)
                await self.local_cache.clear_prefix(f"{prefix}:")

    async def _publish_invalidation(self, action: str, cache_name: str, raw_key: str | None = None) -> None:
        """
        发布缓存失效消息。
        Args:
            action: 失效动作，支持 `evict` 和 `clear`。
            cache_name: 缓存命名空间。
            raw_key: 业务原始键。
        """
        payload = {
            "action": action,
            "cache_name": cache_name,
            "raw_key": raw_key,
        }
        await self.redis_service.publish(self.invalidation_channel, json.dumps(payload, ensure_ascii=False))

    async def get(
        self,
        cache_name: str,
        raw_key: str,
        *,
        target_type: Any = None,
        local_ttl: int | None = None,
        use_local: bool = True,
        use_remote: bool = True,
    ) -> tuple[bool, Any]:
        """
        读取缓存。
        Args:
            cache_name: 缓存命名空间。
            raw_key: 业务原始键。
            target_type: 反序列化目标类型。
            local_ttl: Redis 命中后回填本地缓存的过期时间。
            use_local: 是否读取本地缓存。
            use_remote: 是否读取 Redis 缓存。
        Returns:
            tuple[bool, Any]: 第一个值表示是否命中，第二个值为缓存结果。
        """
        full_key = self.build_key(cache_name, raw_key)
        final_local_ttl = local_ttl or self.default_local_ttl

        if use_local:
            local_raw = await self.local_cache.get(full_key)
            if local_raw is not None:
                return True, self._deserialize_cache_value(local_raw, target_type)

        if use_remote:
            remote_raw = await self.redis_service.get_raw(full_key)
            if remote_raw is not None:
                if use_local and final_local_ttl > 0:
                    await self.local_cache.set(full_key, remote_raw, final_local_ttl)
                return True, self._deserialize_cache_value(remote_raw, target_type)

        return False, None

    async def put(
        self,
        cache_name: str,
        raw_key: str,
        value: Any,
        *,
        ttl: int,
        local_ttl: int | None = None,
        cache_none: bool = False,
        use_local: bool = True,
        use_remote: bool = True,
    ) -> None:
        """
        写入缓存。
        Args:
            cache_name: 缓存命名空间。
            raw_key: 业务原始键。
            value: 待缓存的数据。
            ttl: Redis 过期时间，单位秒。
            local_ttl: 本地缓存过期时间，单位秒。
            cache_none: 是否缓存 `None`。
            use_local: 是否写入本地缓存。
            use_remote: 是否写入 Redis 缓存。
        """
        if value is None and not cache_none:
            return

        full_key = self.build_key(cache_name, raw_key)
        final_local_ttl = local_ttl or min(ttl, self.default_local_ttl)
        raw_value = self._serialize_cache_value(value)

        if use_remote:
            await self.redis_service.set_raw(full_key, raw_value, ex=ttl)

        if use_local and final_local_ttl > 0:
            await self.local_cache.set(full_key, raw_value, final_local_ttl)

    async def evict(self, cache_name: str, raw_key: str) -> None:
        """
        删除单个缓存并广播失效消息。
        Args:
            cache_name: 缓存命名空间。
            raw_key: 业务原始键。
        """
        full_key = self.build_key(cache_name, raw_key)
        await self.local_cache.delete(full_key)
        await self.redis_service.delete(full_key)
        await self._publish_invalidation("evict", cache_name, raw_key)

    async def clear(self, cache_name: str) -> None:
        """
        清空指定命名空间下的全部缓存。
        Args:
            cache_name: 缓存命名空间。
        """
        prefix = self.redis_service.build_key(cache_name)
        pattern = f"{prefix}:*"

        await self.local_cache.clear_prefix(f"{prefix}:")

        keys: list[str] = []
        async for key in self.redis_service.scan_iter(pattern):
            keys.append(key)

        if keys:
            await self.redis_service.delete(*keys)

        await self._publish_invalidation("clear", cache_name)
