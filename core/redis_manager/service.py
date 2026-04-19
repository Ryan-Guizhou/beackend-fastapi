#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/4/18 15:06
@Desc: Redis 管理服务
"""
import logging
from typing import Any

from redis import asyncio as aioredis

from config.config import settings
from core.redis_manager.schema import RedisKeyTypeEnum

logger = logging.getLogger("app")


class AsyncRedisManagerService:
    """
    Redis 管理服务。

    说明：
        该服务用于查询 Redis 数据库信息、搜索键、管理键值和维护 TTL。
    """

    def __init__(self, db_index: int = 0):
        redis_password = settings.REDIS_PASSWORD or None
        self.client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=db_index,
            password=redis_password,
            decode_responses=False,
        )
        self.db_index = db_index
        self.host = settings.REDIS_HOST
        self.port = settings.REDIS_PORT
        self.password = redis_password

    async def get_all_database(self) -> tuple[list[dict[str, Any]], int]:
        """
        获取 Redis 全部逻辑库的统计信息。

        Returns:
            tuple[list[dict[str, Any]], int]: 库信息列表和全部键总数。
        """
        databases: list[dict[str, Any]] = []
        total_keys = 0

        for db_index in range(16):
            temp_client = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=db_index,
                password=self.password,
                decode_responses=True,
            )
            try:
                info = await temp_client.info("keyspace")
                db_key = f"db{db_index}"
                db_info = info.get(db_key, {})
                keys_count = db_info.get("keys", 0)
                expires_count = db_info.get("expires", 0)
                avg_ttl = db_info.get("avg_ttl", 0)

                databases.append(
                    {
                        "db_index": db_index,
                        "keys_count": keys_count,
                        "expires_count": expires_count,
                        "avg_ttl": avg_ttl,
                    }
                )
                total_keys += keys_count
            except Exception as exc:
                logger.error("Failed to get info for db%s: %s", db_index, exc)
                databases.append(
                    {
                        "db_index": db_index,
                        "keys_count": 0,
                        "expires_count": 0,
                        "avg_ttl": 0,
                    }
                )
            finally:
                await temp_client.close()

        return databases, total_keys

    async def search_keys(
            self,
            pattern: str = "*",
            key_type: RedisKeyTypeEnum | None = None,
            page: int = 1,
            page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        搜索 Redis 键。

        Args:
            pattern: Redis Scan 匹配模式。
            key_type: 键类型过滤条件。
            page: 当前页码。
            page_size: 每页数量。

        Returns:
            tuple[list[dict[str, Any]], int]: 当前页键信息和匹配总数。
        """
        try:
            all_keys: list[str] = []
            cursor = 0
            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
                all_keys.extend([self._safe_decode(key) for key in keys])
                if cursor == 0:
                    break

            if key_type is not None:
                filtered_keys: list[str] = []
                for key in all_keys:
                    current_type = self._safe_decode(await self.client.type(key))
                    if current_type == key_type.value:
                        filtered_keys.append(key)
                all_keys = filtered_keys

            total = len(all_keys)
            start = (page - 1) * page_size
            end = start + page_size
            page_keys = all_keys[start:end]

            keys_info: list[dict[str, Any]] = []
            for key in page_keys:
                try:
                    keys_info.append(await self._get_key_info(key))
                except Exception as exc:
                    logger.error("Failed to get info for key %s: %s", key, exc)
                    keys_info.append(
                        {
                            "key": key,
                            "key_type": "unknown",
                            "ttl": -1,
                            "size": None,
                            "length": None,
                            "encoding": None,
                        }
                    )
            return keys_info, total
        except Exception as exc:
            logger.error("Failed to scan keys: %s", exc)
            raise

    async def create_key(
            self,
            key: str,
            key_type: RedisKeyTypeEnum,
            value: Any,
            ttl: int | None = None,
    ) -> bool:
        """
        创建 Redis 键。
        """
        try:
            if await self.client.exists(key):
                raise ValueError(f"Key '{key}' already exists")

            if key_type is RedisKeyTypeEnum.STRING:
                await self.client.set(key, value)
            elif key_type is RedisKeyTypeEnum.LIST:
                if not isinstance(value, list):
                    raise ValueError("List type requires a list value")
                await self.client.rpush(key, *value)
            elif key_type is RedisKeyTypeEnum.SET:
                if not isinstance(value, list):
                    raise ValueError("Set type requires a list value")
                await self.client.sadd(key, *value)
            elif key_type is RedisKeyTypeEnum.ZSET:
                if not isinstance(value, list):
                    raise ValueError("Zset type requires a list value")
                mapping = {item["member"]: item["score"] for item in value}
                await self.client.zadd(key, mapping)
            elif key_type is RedisKeyTypeEnum.HASH:
                if not isinstance(value, dict):
                    raise ValueError("Hash type requires a dict value")
                await self.client.hset(key, mapping=value)

            if ttl is not None:
                if ttl > 0:
                    await self.client.expire(key, ttl)
                elif ttl == -1:
                    await self.client.persist(key)

            logger.info("Redis key created: %s", key)
            return True
        except Exception as exc:
            logger.error("Failed to create redis key %s: %s", key, exc)
            raise

    async def batch_delete_keys(self, keys: list[str]) -> int:
        """
        批量删除 Redis 键。
        """
        try:
            if not keys:
                return 0
            return await self.client.delete(*keys)
        except Exception as exc:
            logger.error("Failed to delete redis keys: %s", exc)
            raise

    async def delete_key(self, key: str) -> bool:
        """
        删除单个 Redis 键。
        """
        try:
            return (await self.client.delete(key)) > 0
        except Exception as exc:
            logger.error("Failed to delete key %s: %s", key, exc)
            raise

    def _safe_decode(self, value: Any) -> str:
        """
        安全解码 Redis 返回值。
        """
        if value is None:
            return ""
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                import base64

                return f"<binary data:{base64.b64encode(value).decode('ascii')}>"
        return str(value)

    async def _get_key_info(self, key: str) -> dict[str, Any]:
        """
        获取 Redis 键的基础信息。
        """
        key_bytes = key.encode() if isinstance(key, str) else key
        key_type = self._safe_decode(await self.client.type(key_bytes))
        ttl = await self.client.ttl(key_bytes)

        info: dict[str, Any] = {
            "key": key,
            "key_type": key_type,
            "ttl": ttl,
            "encoding": None,
        }

        try:
            if await self.client.exists(key_bytes):
                encoding = await self.client.object("encoding", key_bytes)
                info["encoding"] = self._safe_decode(encoding) if encoding else None
        except Exception as exc:
            logger.error("Failed to get encoding for key %s: %s", key, exc)

        if key_type == RedisKeyTypeEnum.STRING.value:
            value = await self.client.get(key_bytes)
            info["size"] = len(value) if value else 0
        elif key_type == RedisKeyTypeEnum.LIST.value:
            info["length"] = await self.client.llen(key_bytes)
        elif key_type == RedisKeyTypeEnum.SET.value:
            info["length"] = await self.client.scard(key_bytes)
        elif key_type == RedisKeyTypeEnum.ZSET.value:
            info["length"] = await self.client.zcard(key_bytes)
        elif key_type == RedisKeyTypeEnum.HASH.value:
            info["length"] = await self.client.hlen(key_bytes)
        return info

    async def rename_key(self, old_key: str, new_key: str) -> bool:
        """
        重命名 Redis 键。
        """
        try:
            if not await self.client.exists(old_key):
                raise ValueError(f"Key '{old_key}' does not exist")
            if await self.client.exists(new_key):
                raise ValueError(f"Key '{new_key}' already exists")
            await self.client.rename(old_key, new_key)
            return True
        except Exception as exc:
            logger.error("Failed to rename key %s to %s: %s", old_key, new_key, exc)
            raise

    async def set_expire(self, key: str, ttl: int) -> bool:
        """
        设置 Redis 键过期时间。
        """
        try:
            if not await self.client.exists(key):
                raise ValueError(f"Key '{key}' does not exist")
            if ttl == -1:
                await self.client.persist(key)
            else:
                await self.client.expire(key, ttl)
            return True
        except Exception as exc:
            logger.error("Failed to set ttl for key %s: %s", key, exc)
            raise

    async def update_key(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        更新 Redis 键值。
        """
        try:
            if not await self.client.exists(key):
                raise ValueError(f"Key '{key}' does not exist")

            key_type = self._safe_decode(await self.client.type(key))
            await self.client.delete(key)

            if key_type == RedisKeyTypeEnum.STRING.value:
                await self.client.set(key, value)
            elif key_type == RedisKeyTypeEnum.LIST.value:
                if not isinstance(value, list):
                    raise ValueError("List type requires a list value")
                await self.client.rpush(key, *value)
            elif key_type == RedisKeyTypeEnum.SET.value:
                if not isinstance(value, list):
                    raise ValueError("Set type requires a list value")
                await self.client.sadd(key, *value)
            elif key_type == RedisKeyTypeEnum.ZSET.value:
                if not isinstance(value, list):
                    raise ValueError("Zset type requires a list value")
                mapping = {item["member"]: item["score"] for item in value}
                await self.client.zadd(key, mapping)
            elif key_type == RedisKeyTypeEnum.HASH.value:
                if not isinstance(value, dict):
                    raise ValueError("Hash type requires a dict value")
                await self.client.hset(key, mapping=value)

            if ttl is not None:
                if ttl > 0:
                    await self.client.expire(key, ttl)
                elif ttl == -1:
                    await self.client.persist(key)
            return True
        except Exception as exc:
            logger.error("Failed to update key %s: %s", key, exc)
            raise

    async def flush_db(self, confirm: bool = False) -> bool:
        """
        清空当前 Redis 数据库。
        """
        if not confirm:
            raise ValueError("Must confirm to flush database")

        try:
            await self.client.flushdb()
            return True
        except Exception as exc:
            logger.error("Failed to flush database: %s", exc)
            raise

    async def get_key_detail(self, key: str) -> dict[str, Any]:
        """
        获取 Redis 键详细信息。
        """
        key_bytes = key.encode() if isinstance(key, str) else key

        if not await self.client.exists(key_bytes):
            raise ValueError(f"Key '{key}' does not exist")

        key_type = self._safe_decode(await self.client.type(key_bytes))
        ttl = await self.client.ttl(key_bytes)

        detail: dict[str, Any] = {
            "key": key,
            "key_type": key_type,
            "ttl": ttl,
            "encoding": None,
        }

        try:
            encoding = await self.client.object("encoding", key_bytes)
            detail["encoding"] = self._safe_decode(encoding) if encoding else None
        except Exception:
            pass

        if key_type == RedisKeyTypeEnum.STRING.value:
            value = await self.client.get(key_bytes)
            detail["value"] = self._safe_decode(value)
            detail["size"] = len(value) if value else 0
        elif key_type == RedisKeyTypeEnum.LIST.value:
            values = await self.client.lrange(key_bytes, 0, -1)
            detail["value"] = [self._safe_decode(item) for item in values]
            detail["length"] = len(values)
        elif key_type == RedisKeyTypeEnum.SET.value:
            members = await self.client.smembers(key_bytes)
            detail["value"] = [self._safe_decode(member) for member in members]
            detail["length"] = len(members)
        elif key_type == RedisKeyTypeEnum.ZSET.value:
            members = await self.client.zrange(key_bytes, 0, -1, withscores=True)
            detail["value"] = [
                {"member": self._safe_decode(member), "score": score}
                for member, score in members
            ]
            detail["length"] = len(members)
        elif key_type == RedisKeyTypeEnum.HASH.value:
            hash_data = await self.client.hgetall(key_bytes)
            detail["value"] = {
                self._safe_decode(hash_key): self._safe_decode(hash_value)
                for hash_key, hash_value in hash_data.items()
            }
            detail["length"] = len(hash_data)

        return detail

    async def close(self) -> None:
        """
        关闭 Redis 客户端连接。
        """
        if self.client:
            await self.client.close()
