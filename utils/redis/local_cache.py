#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: local_cache.py
@Create: 2026/5/9
@Desc: 本地缓存管理
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import OrderedDict as OrderedDictType, Optional


@dataclass
class LocalCacheItem:
    """
    本地缓存条目。
    Args:
        value: 缓存值。
        expires_at: 过期时间戳。
    """
    value: str
    expires_at: float


class LocalCache:
    """
    异步本地 LRU 缓存。
    支持 TTL 过期时间和最大容量限制。
    """

    def __init__(self, *, max_size: int = 10000) -> None:
        """
        初始化本地缓存。
        Args:
            max_size: 缓存最大容量，超过后淘汰最久未访问的数据。
        """
        self.max_size = max_size
        # OrderedDict 左侧为最久未访问项，右侧为最新访问项。
        self._store: OrderedDictType[str, LocalCacheItem] = OrderedDict()
        # 使用异步锁保护本地缓存容器，避免并发读写冲突。
        self._lock = asyncio.Lock()

    def _now(self) -> float:
        """
        获取当前时间戳。
        Returns:
            float: 当前 Unix 时间戳。
        """
        return time.time()

    def _is_expired(self, item: LocalCacheItem) -> bool:
        """
        判断缓存条目是否已过期。
        Args:
            item: 待检查的缓存条目。
        Returns:
            bool: 已过期返回 `True`，否则返回 `False`。
        """
        return item.expires_at <= self._now()

    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存值。
        Args:
            key: 缓存键。
        Returns:
            Optional[str]: 命中时返回缓存值，未命中或已过期时返回 `None`。
        """
        async with self._lock:
            item = self._store.get(key)
            if item is None:
                return None

            # 过期数据采用懒删除，读取时发现过期再清理。
            if self._is_expired(item):
                self._store.pop(key, None)
                return None

            # 命中后移动到末尾，表示最近访问。
            self._store.move_to_end(key)
            return item.value

    async def set(self, key: str, value: str, ttl: int) -> None:
        """
        设置缓存值。
        Args:
            key: 缓存键。
            value: 缓存值。
            ttl: 生存时间，单位秒。
        """
        if ttl <= 0:
            return

        async with self._lock:
            self._store[key] = LocalCacheItem(
                value=value,
                expires_at=self._now() + ttl
            )
            self._store.move_to_end(key)
            self._evict_if_needed()

    async def delete(self, key: str) -> None:
        """
        删除指定缓存。
        Args:
            key: 缓存键。
        """
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        """
        清空全部本地缓存。
        """
        async with self._lock:
            self._store.clear()

    async def clear_prefix(self, prefix: str) -> None:
        """
        按前缀批量删除缓存。
        Args:
            prefix: 缓存键前缀。
        """
        async with self._lock:
            keys = [key for key in self._store.keys() if key.startswith(prefix)]
            for key in keys:
                self._store.pop(key, None)

    async def cleanup(self) -> None:
        """
        主动清理已过期的缓存项。
        """
        async with self._lock:
            keys = [key for key, item in self._store.items() if self._is_expired(item)]
            for key in keys:
                self._store.pop(key, None)

    def _evict_if_needed(self) -> None:
        """
        执行过期清理和容量淘汰。
        """
        expired_keys = [
            key
            for key, item in self._store.items()
            if self._is_expired(item)
        ]
        for key in expired_keys:
            self._store.pop(key, None)

        while len(self._store) > self.max_size:
            self._store.popitem(last=False)
