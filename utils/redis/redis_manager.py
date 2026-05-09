#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: redis_manager.py
@Create: 2026/5/9
@Desc: Redis 生命周期管理
"""

from __future__ import annotations

import redis.asyncio as redis


class RedisManager:
    """
    Redis 连接管理器。
    Args:
        url: Redis 连接地址。
        max_connections: 连接池最大连接数。
        decode_responses: 是否自动解码 Redis 响应。
    """

    def __init__(
        self,
        url: str,
        *,
        max_connections: int = 50,
        decode_responses: bool = True,
    ) -> None:
        self.url = url
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        self._client: redis.Redis | None = None

    async def init(self) -> None:
        """
        初始化 Redis 客户端并校验连接。
        """
        self._client = redis.from_url(
            self.url,
            max_connections=self.max_connections,
            decode_responses=self.decode_responses,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        await self._client.ping()

    async def close(self) -> None:
        """
        关闭 Redis 客户端连接。
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """
        获取已初始化的 Redis 客户端。
        Returns:
            redis.Redis: Redis 异步客户端实例。
        Raises:
            RuntimeError: Redis 客户端尚未初始化时抛出。
        """
        if self._client is None:
            raise RuntimeError("RedisManager 尚未初始化")
        return self._client
