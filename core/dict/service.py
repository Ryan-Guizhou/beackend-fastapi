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

from base.base_service import BaseService, T
from config.database import DbSession
from core.dict.model import Dict, DictStatus
from core.dict.schema import DictCreate, DictUpdate

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
    async def get_all_active_dict(cls, db: DbSession) -> List[Dict]:
        """
        获取全部启用状态的字典。
        Args:
            db: 数据库会话。
        Returns:
            List[Dict]: 启用状态的字典列表。
        """
        result = await db.execute(
            select(cls.model).where(
                cls.model.status == DictStatus.ENABLED.value,
                cls.model.is_deleted.is_(False),
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def batch_update_status(
        cls,
        db: DbSession,
        ids: List[str],
        status: int,
    ) -> int:
        """
        批量更新字典状态。
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
            code: str,
            db: DbSession
    ) -> Optional[T]:

        result = await db.execute(
            select(cls.model).where(
                cls.model.code == code,
            cls.model.is_deleted.is_(False),
            )
        )

        return result.scalar_one_or_none() or None
