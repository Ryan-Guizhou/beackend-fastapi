#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: redis_client.py
@Create: 2026/4/18 14:39
@Desc: 文件描述
"""

import json
from typing import Any

import aioredis
from redis import asyncio as aioredis
from redis.asyncio import Redis

from config.config import settings

"""
Redis 缓存模块
提供Redis连接管理和缓存操作工具类
"""

class RedisClient:

    _client: Redis | None


    @classmethod
    async def get_client(cls) -> Redis:

        if cls._client is None:
            cls._client = await aioredis.from_url(
                settings.redis.url,
                encoding="utf-8",
                encode_response=True,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if  cls._client:
            await cls._client.close()
            cls._client = None

class CacheManager:

    def __init__(self,prefix:str = "") -> None:
        self.prefix = f"{settings.cache.prefix}{prefix}"

    def _build_key(self,key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self,key: str) -> Any | None:

        client = await RedisClient.get_client()
        value = await client.get(self._build_key(key))
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self,key: str,value: Any,expire: int | None = None) -> None:
        client = await RedisClient.get_client()
        expire = expire or settings.cache.default_expire
        if isinstance(value,(dict,list)):
            value = json.dumps(value,ensure_ascii=False,default=str)
        elif not isinstance(value,str):
            value = json.dumps(value,default=str)
        return await client.set(self._build_key(key), json.dumps(value), expire)


    async def delete(self,key: str) -> int:
        client = await RedisClient.get_client()
        return await client.delete(self._build_key(key))



async def get_redis() -> Redis:
    return await RedisClient.get_client()

