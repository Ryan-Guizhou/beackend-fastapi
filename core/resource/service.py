#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 16:15
@Desc: 资源业务服务
"""

from base.audit import build_audit_info, build_audit_infos
from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.resource.model import Resource
from core.resource.schema import ResourceCreate, ResourceInfo, ResourcePageRequest, ResourceUpdate


class ResourceService(BaseService[Resource, ResourceCreate, ResourceUpdate]):
    model = Resource

    @classmethod
    async def _check_resource_unique(
            cls,
            db: DbSession,
            func_code: str | None,
            resource_type: str,
            resource_code: str,
            exclude_id: str | None = None,
    ) -> bool:
        """
        校验资源业务键是否唯一。
        """
        filters = [
            cls.model.func_code == func_code,
            cls.model.resource_type == resource_type,
            cls.model.resource_code == resource_code,
        ]
        if exclude_id:
            filters.append(cls.model.id != exclude_id)
        return not await cls.exists(db, filters)

    @classmethod
    async def create_resource(cls, db: DbSession, data: ResourceCreate) -> ResourceInfo:
        if not await cls._check_resource_unique(db, data.func_code, data.resource_type, data.resource_code):
            raise ValueError("功能、资源类型和资源编码组合已存在")
        obj = await cls.create(db, data)
        return await build_audit_info(db, obj, ResourceInfo)

    @classmethod
    async def update_resource(cls, db: DbSession, resource_id: str, data: ResourceUpdate) -> ResourceInfo:
        if not await cls.get_by_id(db, resource_id):
            raise ValueError("资源不存在")
        current = await cls.get_by_id(db, resource_id)
        func_code = data.func_code if data.func_code is not None else current.func_code
        resource_type = data.resource_type or current.resource_type
        resource_code = data.resource_code or current.resource_code
        if not await cls._check_resource_unique(db, func_code, resource_type, resource_code, exclude_id=resource_id):
            raise ValueError("功能、资源类型和资源编码组合已存在")
        obj = await cls.update(db, resource_id, data)
        if not obj:
            raise ValueError("资源不存在")
        return await build_audit_info(db, obj, ResourceInfo)

    @classmethod
    async def get_resource_info(cls, db: DbSession, resource_id: str) -> ResourceInfo | None:
        obj = await cls.get_by_id(db, resource_id)
        return await build_audit_info(db, obj, ResourceInfo)

    @classmethod
    async def page_resource_infos(cls, db: DbSession, data: ResourcePageRequest) -> PaginatedResponse[ResourceInfo]:
        filters = []
        if data.func_code:
            filters.append(cls.model.func_code == data.func_code)
        if data.resource_type:
            filters.append(cls.model.resource_type == data.resource_type)
        if data.resource_code:
            filters.append(cls.model.resource_code == data.resource_code)
        if data.resource_name:
            filters.append(cls.model.resource_name.ilike(f"%{data.resource_name}%"))
        if data.app_code:
            filters.append(cls.model.app_code == data.app_code)

        items, total = await cls.page_list(db, data.page_index, data.page_size, filters)
        return PaginatedResponse(
            items=await build_audit_infos(db, items, ResourceInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )
