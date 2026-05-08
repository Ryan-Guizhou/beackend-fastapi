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

from base.base_service import BaseService
from config.database import DbSession
from core.dict_item.model import DictItem, DictItemStatus
from core.dict_item.schema import DictItemCreate, DictItemUpdate


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
    async def get_by_dict_id(
        cls,
        db: DbSession,
        dict_id: str,
    ) -> List[DictItem]:
        """
        根据字典 ID 获取全部字典项。
        Args:
            db: 数据库会话。
            dict_id: 字典 ID。
        Returns:
            List[DictItem]: 字典项列表。
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.dict_id == dict_id,
                cls.model.is_deleted.is_(False),
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def get_all_active_by_dict_code(
        cls,
        db: DbSession,
        dict_code: str,
    ) -> List[DictItem]:
        """
        根据字典 ID 获取全部启用字典项。
        Args:
            db: 数据库会话。
            dict_code: 字典 ID。
        Returns:
            List[DictItem]: 启用状态的字典项列表。
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.dict_code == dict_code,
                cls.model.status == DictItemStatus.ENABLED.value,
                cls.model.is_deleted.is_(False),
            )
        )
        return list(result.scalars().all())

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
            dict_code: 字典 ID。
            value: 字典项实际值。
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
    async def batch_update_status(
        cls,
        db: DbSession,
        ids: List[str],
        status: int,
    ) -> int:
        """
        批量更新字典项状态。
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
