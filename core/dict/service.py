#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/7 22:23
@Desc: 字典业务服务
"""

import logging
from typing import List, Optional

from sqlalchemy import select

from base.audit import build_audit_info, build_audit_infos
from base.base_schema import PaginatedResponse
from base.base_service import BaseService, T
from config.database import DbSession
from core.dict.model import Dict, DictStatus
from core.dict.schema import DictBatchDeleteResult, DictCreate, DictInfo, DictPageRequest, DictUpdate
from utils.redis.cache_decorator import CacheEvictOp, cacheable, caching

logger = logging.getLogger(__name__)


class DictService(BaseService[Dict, DictCreate, DictUpdate]):
    """
    字典业务服务类。
    Args:
        无。
    Returns:
        无。
    """

    model = Dict

    @classmethod
    @caching(
        evict=[
            CacheEvictOp(cache_name="dict", all_entries=True),
            CacheEvictOp(cache_name="dict_item", all_entries=True),
        ]
    )
    async def create_dict(cls, db: DbSession, data: DictCreate) -> DictInfo:
        """
        创建字典并清理缓存。
        Args:
            db: 数据库会话。
            data: 字典创建数据。
        Returns:
            DictInfo: 创建后的字典响应数据。
        """
        if not await cls.check_unique(db, field="code", value=data.code):
            raise ValueError(f"字典编码 {data.code} 已存在")
        dict_obj = await cls.create(db, data)
        return await build_audit_info(db, dict_obj, DictInfo)

    @classmethod
    @cacheable(cache_name="dict", key="active", ttl=60, local_ttl=30, sync=True)
    async def get_all_active_dict(cls, db: DbSession) -> list[DictInfo]:
        """
        获取全部启用状态的字典。
        Args:
            db: 数据库会话。
        Returns:
            list[DictInfo]: 启用状态的字典列表。
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.status == DictStatus.ENABLED.value,
                cls.model.is_deleted.is_(False),
            )
        )
        dicts = list(result.scalars().all())
        return await build_audit_infos(db, dicts, DictInfo)

    @classmethod
    async def page_dict_infos(
        cls,
        db: DbSession,
        data: DictPageRequest,
    ) -> PaginatedResponse[DictInfo]:
        """
        分页查询字典。
        Args:
            db: 数据库会话。
            data: 字典分页查询参数。
        Returns:
            PaginatedResponse[DictInfo]: 字典分页结果。
        """
        filters = []
        if data.name:
            filters.append(Dict.name.like(f"%{data.name}%"))
        if data.code:
            filters.append(Dict.code == data.code)
        if data.status is not None:
            filters.append(Dict.status == data.status)

        items, total = await cls.page_list(
            db,
            page=data.page_index,
            page_size=data.page_size,
            filters=filters,
        )
        return PaginatedResponse(
            items=await build_audit_infos(db, items, DictInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )

    @classmethod
    @cacheable(cache_name="dict", key="detail:{dict_id}", ttl=60, local_ttl=30)
    async def get_dict_info_by_id(cls, db: DbSession, dict_id: str) -> DictInfo | None:
        """
        根据字典 ID 获取字典详情。
        Args:
            db: 数据库会话。
            dict_id: 字典 ID。
        Returns:
            DictInfo | None: 字典详情，未找到时返回 `None`。
        """
        dict_obj = await cls.get_by_id(db, dict_id)
        return await build_audit_info(db, dict_obj, DictInfo)

    @classmethod
    @caching(
        evict=[
            CacheEvictOp(cache_name="dict", all_entries=True),
            CacheEvictOp(cache_name="dict_item", all_entries=True),
        ]
    )
    async def update_dict(cls, db: DbSession, dict_id: str, data: DictUpdate) -> DictInfo:
        """
        更新字典并清理缓存。
        Args:
            db: 数据库会话。
            dict_id: 字典 ID。
            data: 字典更新数据。
        Returns:
            DictInfo: 更新后的字典响应数据。
        """
        dict_obj = await cls.get_by_id(db, dict_id)
        if not dict_obj:
            raise ValueError("字典不存在")

        if data.code:
            is_unique = await cls.check_unique(
                db,
                field="code",
                value=data.code,
                exclude_id=dict_id,
            )
            if not is_unique:
                raise ValueError(f"编码 {data.code} 已存在")

        updated_dict = await cls.update(db, dict_id, data)
        if not updated_dict:
            raise ValueError("字典不存在")
        return await build_audit_info(db, updated_dict, DictInfo)

    @classmethod
    @caching(
        evict=[
            CacheEvictOp(cache_name="dict", all_entries=True),
            CacheEvictOp(cache_name="dict_item", all_entries=True),
        ]
    )
    async def batch_update_status(
        cls,
        db: DbSession,
        ids: List[str],
        status: int,
    ) -> int:
        """
        批量更新字典状态并清理缓存。
        Args:
            db: 数据库会话。
            ids: 待更新的字典 ID 列表。
            status: 目标状态值。
        Returns:
            int: 实际更新成功的数量。
        """
        updated_count = 0
        if not ids:
            return updated_count

        for record_id in ids:
            dict_obj = await cls.get_by_id(db, record_id)
            if not dict_obj:
                continue
            dict_obj.status = status
            updated_count += 1

        if updated_count > 0:
            await db.commit()
        return updated_count

    @classmethod
    async def get_by_code(
        cls,
        db: DbSession,
        code: str,
    ) -> Optional[T]:
        """
        根据字典编码获取字典对象。
        Args:
            db: 数据库会话。
            code: 字典编码。
        Returns:
            Optional[T]: 命中时返回字典 ORM 对象，否则返回 `None`。
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.code == code,
                cls.model.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none() or None

    @classmethod
    @caching(
        evict=[
            CacheEvictOp(cache_name="dict", all_entries=True),
            CacheEvictOp(cache_name="dict_item", all_entries=True),
        ]
    )
    async def batch_delete_dict(cls, db: DbSession, ids: list[str]) -> DictBatchDeleteResult:
        """
        批量删除字典并清理缓存。
        Args:
            db: 数据库会话。
            ids: 字典 ID 列表。
        Returns:
            DictBatchDeleteResult: 批量删除结果。
        """
        success_count, fail_count = await cls.batch_delete(db, ids)
        return DictBatchDeleteResult(
            success_count=success_count,
            fail_count=fail_count,
        )

    @classmethod
    @caching(
        evict=[
            CacheEvictOp(cache_name="dict", all_entries=True),
            CacheEvictOp(cache_name="dict_item", all_entries=True),
        ]
    )
    async def del_by_id(
        cls,
        db: DbSession,
        record_id: str,
        auto_commit: bool = True,
        hard: bool = False,
    ) -> bool:
        """
        删除字典并清理缓存。
        Args:
            db: 数据库会话。
            record_id: 字典 ID。
            auto_commit: 是否自动提交事务。
            hard: 是否物理删除。
        Returns:
            bool: 删除成功返回 `True`，否则返回 `False`。
        """
        return await super().del_by_id(db, record_id, auto_commit, hard)

    @classmethod
    async def delete_dict_with_items(cls, db: DbSession, dict_id: str) -> bool:
        """
        删除字典及其字典项。
        Args:
            db: 数据库会话。
            dict_id: 字典 ID。
        Returns:
            bool: 删除成功返回 `True`，否则返回 `False`。
        """
        dict_obj = await cls.get_by_id(db, dict_id)
        if not dict_obj:
            raise ValueError("字典不存在")

        from core.dict_item.service import DictItemService

        item_ids = await DictItemService.get_ids_by_dict_code(db, dict_obj.code)
        if item_ids:
            delete_result = await DictItemService.batch_delete_dict_item(db, item_ids)
            if delete_result.success_count != len(item_ids) or delete_result.fail_count > 0:
                raise ValueError("字典项删除失败")

        return await cls.del_by_id(db, dict_id)
