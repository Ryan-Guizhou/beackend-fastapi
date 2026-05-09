#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: mongo_manager.py
@Create: 2026/5/9
@Desc: Mongo 生命周期管理
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.results import DeleteResult, InsertManyResult, InsertOneResult, UpdateResult


Document = Mapping[str, Any]
Filter = Mapping[str, Any]
Projection = Mapping[str, Any] | Sequence[str] | None
Sort = Sequence[tuple[str, int]] | None


class MongoManager:
    """
    MongoDB 异步工具类。
    Args:
        url: MongoDB 连接地址。
        database: 默认数据库名称。
        max_pool_size: 连接池最大连接数。
        min_pool_size: 连接池最小连接数。
        server_selection_timeout_ms: 服务发现超时时间，单位毫秒。
    """

    def __init__(
        self,
        url: str,
        database: str,
        *,
        max_pool_size: int = 100,
        min_pool_size: int = 0,
        server_selection_timeout_ms: int = 5000,
    ) -> None:
        self.url = url
        self.database_name = database
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.server_selection_timeout_ms = server_selection_timeout_ms
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    async def init(self) -> None:
        """
        初始化 MongoDB 客户端并校验连接。
        """
        self._client = AsyncIOMotorClient(
            self.url,
            maxPoolSize=self.max_pool_size,
            minPoolSize=self.min_pool_size,
            serverSelectionTimeoutMS=self.server_selection_timeout_ms,
            uuidRepresentation="standard",
        )
        self._db = self._client[self.database_name]
        await self._client.admin.command("ping")

    async def close(self) -> None:
        """
        关闭 MongoDB 客户端连接。
        """
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None

    @property
    def client(self) -> AsyncIOMotorClient:
        """
        获取已初始化的 MongoDB 客户端。
        Returns:
            AsyncIOMotorClient: MongoDB 异步客户端。
        Raises:
            RuntimeError: 客户端尚未初始化时抛出。
        """
        if self._client is None:
            raise RuntimeError("MongoManager 尚未初始化")
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """
        获取默认数据库。
        Returns:
            AsyncIOMotorDatabase: MongoDB 数据库对象。
        Raises:
            RuntimeError: 数据库尚未初始化时抛出。
        """
        if self._db is None:
            raise RuntimeError("MongoManager 尚未初始化")
        return self._db

    def collection(self, name: str) -> AsyncIOMotorCollection:
        """
        获取集合对象。
        Args:
            name: 集合名称。
        Returns:
            AsyncIOMotorCollection: MongoDB 集合对象。
        """
        return self.db[name]

    @staticmethod
    def object_id(value: str | ObjectId) -> ObjectId:
        """
        转换 ObjectId。
        Args:
            value: ObjectId 字符串或 ObjectId 实例。
        Returns:
            ObjectId: MongoDB ObjectId。
        """
        if isinstance(value, ObjectId):
            return value
        return ObjectId(value)

    async def ping(self) -> bool:
        """
        检查 MongoDB 连接。
        Returns:
            bool: 连接可用时返回 `True`。
        """
        await self.client.admin.command("ping")
        return True

    async def insert_one(
        self,
        collection: str,
        document: Document,
        *,
        session: AsyncIOMotorClientSession | None = None,
    ) -> InsertOneResult:
        """
        插入单条文档。
        Args:
            collection: 集合名称。
            document: 待插入文档。
            session: MongoDB 会话。
        Returns:
            InsertOneResult: 插入结果。
        """
        return await self.collection(collection).insert_one(dict(document), session=session)

    async def insert_many(
        self,
        collection: str,
        documents: Sequence[Document],
        *,
        ordered: bool = True,
        session: AsyncIOMotorClientSession | None = None,
    ) -> InsertManyResult:
        """
        批量插入文档。
        Args:
            collection: 集合名称。
            documents: 待插入文档列表。
            ordered: 是否按顺序插入。
            session: MongoDB 会话。
        Returns:
            InsertManyResult: 插入结果。
        """
        return await self.collection(collection).insert_many(
            [dict(document) for document in documents],
            ordered=ordered,
            session=session,
        )

    async def find_one(
        self,
        collection: str,
        filter_: Filter | None = None,
        *,
        projection: Projection = None,
        sort: Sort = None,
        session: AsyncIOMotorClientSession | None = None,
    ) -> dict[str, Any] | None:
        """
        查询单条文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            projection: 返回字段。
            sort: 排序规则。
            session: MongoDB 会话。
        Returns:
            dict[str, Any] | None: 查询结果。
        """
        return await self.collection(collection).find_one(
            filter_ or {},
            projection=projection,
            sort=sort,
            session=session,
        )

    async def find_by_id(
        self,
        collection: str,
        id_: str | ObjectId,
        *,
        projection: Projection = None,
        session: AsyncIOMotorClientSession | None = None,
    ) -> dict[str, Any] | None:
        """
        根据 `_id` 查询单条文档。
        Args:
            collection: 集合名称。
            id_: 文档 `_id`。
            projection: 返回字段。
            session: MongoDB 会话。
        Returns:
            dict[str, Any] | None: 查询结果。
        """
        return await self.find_one(
            collection,
            {"_id": self.object_id(id_)},
            projection=projection,
            session=session,
        )

    async def find_many(
        self,
        collection: str,
        filter_: Filter | None = None,
        *,
        projection: Projection = None,
        sort: Sort = None,
        skip: int = 0,
        limit: int = 100,
        session: AsyncIOMotorClientSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        查询多条文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            projection: 返回字段。
            sort: 排序规则。
            skip: 跳过数量。
            limit: 返回数量。
            session: MongoDB 会话。
        Returns:
            list[dict[str, Any]]: 查询结果列表。
        """
        cursor = self.collection(collection).find(
            filter_ or {},
            projection=projection,
            skip=skip,
            limit=limit,
            session=session,
        )
        if sort:
            cursor = cursor.sort(list(sort))
        return await cursor.to_list(length=limit)

    async def count(
        self,
        collection: str,
        filter_: Filter | None = None,
        *,
        session: AsyncIOMotorClientSession | None = None,
    ) -> int:
        """
        统计文档数量。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            session: MongoDB 会话。
        Returns:
            int: 文档数量。
        """
        return await self.collection(collection).count_documents(filter_ or {}, session=session)

    async def exists(
        self,
        collection: str,
        filter_: Filter,
        *,
        session: AsyncIOMotorClientSession | None = None,
    ) -> bool:
        """
        判断文档是否存在。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            session: MongoDB 会话。
        Returns:
            bool: 是否存在。
        """
        total = await self.count(collection, filter_, session=session)
        return total > 0

    async def update_one(
        self,
        collection: str,
        filter_: Filter,
        update: Document,
        *,
        upsert: bool = False,
        session: AsyncIOMotorClientSession | None = None,
    ) -> UpdateResult:
        """
        更新单条文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            update: 更新表达式。
            upsert: 不存在时是否插入。
            session: MongoDB 会话。
        Returns:
            UpdateResult: 更新结果。
        """
        return await self.collection(collection).update_one(
            dict(filter_),
            dict(update),
            upsert=upsert,
            session=session,
        )

    async def update_many(
        self,
        collection: str,
        filter_: Filter,
        update: Document,
        *,
        upsert: bool = False,
        session: AsyncIOMotorClientSession | None = None,
    ) -> UpdateResult:
        """
        批量更新文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            update: 更新表达式。
            upsert: 不存在时是否插入。
            session: MongoDB 会话。
        Returns:
            UpdateResult: 更新结果。
        """
        return await self.collection(collection).update_many(
            dict(filter_),
            dict(update),
            upsert=upsert,
            session=session,
        )

    async def set_one(
        self,
        collection: str,
        filter_: Filter,
        values: Document,
        *,
        upsert: bool = False,
        session: AsyncIOMotorClientSession | None = None,
    ) -> UpdateResult:
        """
        使用 `$set` 更新单条文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            values: 待设置字段。
            upsert: 不存在时是否插入。
            session: MongoDB 会话。
        Returns:
            UpdateResult: 更新结果。
        """
        return await self.update_one(
            collection,
            filter_,
            {"$set": dict(values)},
            upsert=upsert,
            session=session,
        )

    async def find_one_and_update(
        self,
        collection: str,
        filter_: Filter,
        update: Document,
        *,
        projection: Projection = None,
        upsert: bool = False,
        return_after: bool = True,
        session: AsyncIOMotorClientSession | None = None,
    ) -> dict[str, Any] | None:
        """
        更新单条文档并返回更新前或更新后的文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            update: 更新表达式。
            projection: 返回字段。
            upsert: 不存在时是否插入。
            return_after: 是否返回更新后的文档。
            session: MongoDB 会话。
        Returns:
            dict[str, Any] | None: 文档结果。
        """
        return_document = ReturnDocument.AFTER if return_after else ReturnDocument.BEFORE
        return await self.collection(collection).find_one_and_update(
            dict(filter_),
            dict(update),
            projection=projection,
            upsert=upsert,
            return_document=return_document,
            session=session,
        )

    async def delete_one(
        self,
        collection: str,
        filter_: Filter,
        *,
        session: AsyncIOMotorClientSession | None = None,
    ) -> DeleteResult:
        """
        删除单条文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            session: MongoDB 会话。
        Returns:
            DeleteResult: 删除结果。
        """
        return await self.collection(collection).delete_one(dict(filter_), session=session)

    async def delete_many(
        self,
        collection: str,
        filter_: Filter,
        *,
        session: AsyncIOMotorClientSession | None = None,
    ) -> DeleteResult:
        """
        批量删除文档。
        Args:
            collection: 集合名称。
            filter_: 查询条件。
            session: MongoDB 会话。
        Returns:
            DeleteResult: 删除结果。
        """
        return await self.collection(collection).delete_many(dict(filter_), session=session)

    async def aggregate(
        self,
        collection: str,
        pipeline: Sequence[Document],
        *,
        session: AsyncIOMotorClientSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        执行聚合查询。
        Args:
            collection: 集合名称。
            pipeline: 聚合管道。
            session: MongoDB 会话。
        Returns:
            list[dict[str, Any]]: 聚合结果。
        """
        cursor = self.collection(collection).aggregate(list(pipeline), session=session)
        return await cursor.to_list(length=None)

    async def create_index(
        self,
        collection: str,
        keys: str | Sequence[tuple[str, int]],
        *,
        unique: bool = False,
        name: str | None = None,
        background: bool = True,
        **kwargs: Any,
    ) -> str:
        """
        创建索引。
        Args:
            collection: 集合名称。
            keys: 单字段名称或多字段索引定义。
            unique: 是否唯一索引。
            name: 索引名称。
            background: 是否后台创建。
            **kwargs: 其他索引参数。
        Returns:
            str: 索引名称。
        """
        index_keys = [(keys, ASCENDING)] if isinstance(keys, str) else list(keys)
        return await self.collection(collection).create_index(
            index_keys,
            unique=unique,
            name=name,
            background=background,
            **kwargs,
        )

    async def drop_index(self, collection: str, name: str) -> None:
        """
        删除索引。
        Args:
            collection: 集合名称。
            name: 索引名称。
        """
        await self.collection(collection).drop_index(name)

    async def list_indexes(self, collection: str) -> list[dict[str, Any]]:
        """
        查询集合索引列表。
        Args:
            collection: 集合名称。
        Returns:
            list[dict[str, Any]]: 索引信息列表。
        """
        return await self.collection(collection).list_indexes().to_list(length=None)

    async def drop_collection(self, collection: str) -> None:
        """
        删除集合。
        Args:
            collection: 集合名称。
        """
        await self.db.drop_collection(collection)

    async def list_collection_names(self) -> list[str]:
        """
        查询数据库集合名称列表。
        Returns:
            list[str]: 集合名称列表。
        """
        return await self.db.list_collection_names()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncIOMotorClientSession]:
        """
        创建 MongoDB 会话上下文。
        Yields:
            AsyncIOMotorClientSession: MongoDB 会话。
        """
        async with await self.client.start_session() as session:
            yield session

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncIOMotorClientSession]:
        """
        创建 MongoDB 事务上下文。
        Yields:
            AsyncIOMotorClientSession: MongoDB 会话。
        """
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session


__all__ = [
    "ASCENDING",
    "DESCENDING",
    "MongoManager",
]
