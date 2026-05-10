#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 16:05
@Desc: 功能业务服务
"""

from base.audit import build_audit_info, build_audit_infos
from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.function.model import Function
from core.function.schema import FunctionCreate, FunctionInfo, FunctionPageRequest, FunctionUpdate


class FunctionService(BaseService[Function, FunctionCreate, FunctionUpdate]):
    model = Function

    @classmethod
    async def create_function(cls, db: DbSession, data: FunctionCreate) -> FunctionInfo:
        if not await cls.check_unique(db, "func_code", data.func_code):
            raise ValueError(f"功能编码 {data.func_code} 已存在")
        obj = await cls.create(db, data)
        return await build_audit_info(db, obj, FunctionInfo)

    @classmethod
    async def update_function(cls, db: DbSession, function_id: str, data: FunctionUpdate) -> FunctionInfo:
        if not await cls.get_by_id(db, function_id):
            raise ValueError("功能不存在")
        if data.func_code and not await cls.check_unique(db, "func_code", data.func_code, exclude_id=function_id):
            raise ValueError(f"功能编码 {data.func_code} 已存在")
        obj = await cls.update(db, function_id, data)
        if not obj:
            raise ValueError("功能不存在")
        return await build_audit_info(db, obj, FunctionInfo)

    @classmethod
    async def get_function_info(cls, db: DbSession, function_id: str) -> FunctionInfo | None:
        obj = await cls.get_by_id(db, function_id)
        return await build_audit_info(db, obj, FunctionInfo)

    @classmethod
    async def page_function_infos(cls, db: DbSession, data: FunctionPageRequest) -> PaginatedResponse[FunctionInfo]:
        filters = []
        if data.func_code:
            filters.append(cls.model.func_code == data.func_code)
        if data.func_name:
            filters.append(cls.model.func_name.ilike(f"%{data.func_name}%"))
        if data.parent_func_code:
            filters.append(cls.model.parent_func_code == data.parent_func_code)
        if data.app_code:
            filters.append(cls.model.app_code == data.app_code)
        if data.func_type:
            filters.append(cls.model.func_type == data.func_type)
        if data.is_disable is not None:
            filters.append(cls.model.is_disable == data.is_disable)

        items, total = await cls.page_list(db, data.page_index, data.page_size, filters)
        return PaginatedResponse(
            items=await build_audit_infos(db, items, FunctionInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )
