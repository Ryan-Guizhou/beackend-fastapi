#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/7 23:10
@Desc: 字典项业务服务
"""

from typing import List

from sqlalchemy import select

from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.dict_item.model import DictItem, DictItemStatus
from core.dict_item.schema import (
    DictItemBatchDeleteResult,
    DictItemCreate,
    DictItemInfo,
    DictItemPageRequest,
    DictItemUpdate,
)
from utils.redis.cache_decorator import cache_evict, cacheable


class DictItemService(BaseService[DictItem, DictItemCreate, DictItemUpdate]):
    """
    字典项业务服务类。
    Args:
        无。
    Returns:
        无。
    """

    model = DictItem

    @classmethod
    @cache_evict(cache_name="dict_item", all_entries=True)
    async def create_dict_item(cls, db: DbSession, data: DictItemCreate) -> DictItemInfo:
        """
        创建字典项并清理字典项缓存。
        Args:
            db: 数据库会话。
            data: 字典项创建数据。
        Returns:
            DictItemInfo: 创建后的字典项响应数据。
        """
        from core.dict.service import DictService

        dict_obj = await DictService.get_by_code(db, data.dict_code)
        if not dict_obj:
            raise ValueError("所属字典不存在")

        is_unique = await cls.check_unique_value(db, data.dict_code, data.value)
        if not is_unique:
            raise ValueError(f"字典项值 {data.value} 已存在")

        dict_item = await cls.create(db, data)
        return DictItemInfo.model_validate(dict_item)

    @classmethod
    async def get_by_dict_code(
        cls,
        db: DbSession,
        dict_code: str,
    ) -> List[DictItem]:
        """
        根据字典编码获取全部字典项。
        Args:
            db: 数据库会话。
            dict_code: 字典编码。
        Returns:
            List[DictItem]: 字典项列表。
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.dict_code == dict_code,
                cls.model.is_deleted.is_(False),
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def get_ids_by_dict_code(
        cls,
        db: DbSession,
        dict_code: str,
    ) -> list[str]:
        """
        根据字典编码获取字典项 ID 列表。
        Args:
            db: 数据库会话。
            dict_code: 字典编码。
        Returns:
            list[str]: 字典项 ID 列表。
        """
        items = await cls.get_by_dict_code(db, dict_code)
        return [item.id for item in items]

    @classmethod
    @cacheable(cache_name="dict_item", key="active:{dict_code}", ttl=3600, local_ttl=300, sync=True)
    async def get_active_infos_by_dict_code(
        cls,
        db: DbSession,
        dict_code: str,
    ) -> list[DictItemInfo]:
        """
        根据字典编码获取启用状态的字典项。
        Args:
            db: 数据库会话。
            dict_code: 字典编码。
        Returns:
            list[DictItemInfo]: 启用状态的字典项列表。
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.dict_code == dict_code,
                cls.model.status == DictItemStatus.ENABLED.value,
                cls.model.is_deleted.is_(False),
            )
        )
        items = list(result.scalars().all())
        return [DictItemInfo.model_validate(item) for item in items]

    @classmethod
    async def page_dict_item_infos(
        cls,
        db: DbSession,
        data: DictItemPageRequest,
    ) -> PaginatedResponse[DictItemInfo]:
        """
        分页查询字典项。
        Args:
            db: 数据库会话。
            data: 字典项分页查询参数。
        Returns:
            PaginatedResponse[DictItemInfo]: 字典项分页结果。
        """
        filters = []
        if data.dict_code:
            filters.append(DictItem.dict_code == data.dict_code)
        if data.label:
            filters.append(DictItem.label.like(f"%{data.label}%"))
        if data.value:
            filters.append(DictItem.value.like(f"%{data.value}%"))
        if data.status is not None:
            filters.append(DictItem.status == data.status)

        items, total = await cls.page_list(
            db,
            page=data.page_index,
            page_size=data.page_size,
            filters=filters,
        )
        return PaginatedResponse(
            items=[DictItemInfo.model_validate(item) for item in items],
            total=total,
            has_next=data.page_index * data.page_size < total,
        )

    @classmethod
    async def check_unique_value(
        cls,
        db: DbSession,
        dict_code: str,
        value: str,
        exclude_id: str | None = None,
    ) -> bool:
        """
        检查同一字典下字典项值是否唯一。
        Args:
            db: 数据库会话。
            dict_code: 字典编码。
            value: 字典项值。
            exclude_id: 更新场景下需要排除的字典项 ID。
        Returns:
            bool: 唯一返回 `True`，否则返回 `False`。
        """
        stmt = select(cls.model).where(
            cls.model.dict_code == dict_code,
            cls.model.value == value,
            cls.model.is_deleted.is_(False),
        )
        if exclude_id:
            stmt = stmt.where(cls.model.id != exclude_id)

        result = await db.execute(stmt)
        return result.scalar_one_or_none() is None

    @classmethod
    @cache_evict(cache_name="dict_item", all_entries=True)
    async def batch_update_status(
        cls,
        db: DbSession,
        ids: List[str],
        status: int,
    ) -> int:
        """
        批量更新字典项状态并清理字典项缓存。
        Args:
            db: 数据库会话。
            ids: 待更新的字典项 ID 列表。
            status: 目标状态值。
        Returns:
            int: 实际更新成功的数量。
        """
        updated_count = 0
        if not ids:
            return updated_count

        for record_id in ids:
            dict_item = await cls.get_by_id(db, record_id)
            if not dict_item:
                continue
            dict_item.status = status
            updated_count += 1

        if updated_count > 0:
            await db.commit()
        return updated_count

    @classmethod
    @cache_evict(cache_name="dict_item", all_entries=True)
    async def batch_delete_dict_item(cls, db: DbSession, ids: list[str]) -> DictItemBatchDeleteResult:
        """
        批量删除字典项并清理字典项缓存。
        Args:
            db: 数据库会话。
            ids: 字典项 ID 列表。
        Returns:
            DictItemBatchDeleteResult: 批量删除结果。
        """
        success_count, fail_count = await cls.batch_delete(db, ids)
        return DictItemBatchDeleteResult(
            success_count=success_count,
            fail_count=fail_count,
        )

    @classmethod
    @cacheable(cache_name="dict_item", key="detail:{item_id}", ttl=1800, local_ttl=300)
    async def get_info_by_id(cls, db: DbSession, item_id: str) -> DictItemInfo | None:
        """
        根据字典项 ID 获取字典项详情。
        Args:
            db: 数据库会话。
            item_id: 字典项 ID。
        Returns:
            DictItemInfo | None: 字典项详情，未找到时返回 `None`。
        """
        dict_item = await cls.get_by_id(db, item_id)
        if not dict_item:
            return None
        return DictItemInfo.model_validate(dict_item)

    @classmethod
    @cache_evict(cache_name="dict_item", all_entries=True)
    async def update_dict_item(cls, db: DbSession, item_id: str, data: DictItemUpdate) -> DictItemInfo:
        """
        更新字典项并清理字典项缓存。
        Args:
            db: 数据库会话。
            item_id: 字典项 ID。
            data: 字典项更新数据。
        Returns:
            DictItemInfo: 更新后的字典项响应数据。
        """
        from core.dict.service import DictService

        dict_item = await cls.get_by_id(db, item_id)
        if not dict_item:
            raise ValueError("字典项不存在")

        dict_obj = await DictService.get_by_code(db, data.dict_code)
        if not dict_obj:
            raise ValueError("所属字典不存在")

        is_unique = await cls.check_unique_value(
            db,
            dict_code=data.dict_code,
            value=data.value,
            exclude_id=item_id,
        )
        if not is_unique:
            raise ValueError(f"字典项值 {data.value} 已存在")

        updated_dict_item = await cls.update(db, item_id, data)
        if not updated_dict_item:
            raise ValueError("字典项不存在")
        return DictItemInfo.model_validate(updated_dict_item)

    @classmethod
    @cache_evict(cache_name="dict_item", all_entries=True)
    async def del_by_id(
        cls,
        db: DbSession,
        record_id: str,
        auto_commit: bool = True,
        hard: bool = False,
    ) -> bool:
        """
        删除字典项并清理字典项缓存。
        Args:
            db: 数据库会话。
            record_id: 字典项 ID。
            auto_commit: 是否自动提交事务。
            hard: 是否物理删除。
        Returns:
            bool: 删除成功返回 `True`，否则返回 `False`。
        """
        return await super().del_by_id(db, record_id, auto_commit, hard)

    @classmethod
    async def delete_dict_item(cls, db: DbSession, item_id: str) -> bool:
        """
        删除字典项。
        Args:
            db: 数据库会话。
            item_id: 字典项 ID。
        Returns:
            bool: 删除成功返回 `True`，否则返回 `False`。
        """
        return await cls.del_by_id(db, item_id)
