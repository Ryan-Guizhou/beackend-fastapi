#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 16:20
@Desc: 前端路由业务服务
"""

from base.audit import build_audit_info, build_audit_infos
from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.router.model import Router
from core.router.schema import RouterCreate, RouterInfo, RouterPageRequest, RouterUpdate


class RouterService(BaseService[Router, RouterCreate, RouterUpdate]):
    model = Router

    @classmethod
    async def create_router(cls, db: DbSession, data: RouterCreate) -> RouterInfo:
        if not await cls.check_unique(db, "router_code", data.router_code):
            raise ValueError(f"路由编码 {data.router_code} 已存在")
        if not await cls.check_unique(db, "router_url", data.router_url):
            raise ValueError(f"路由地址 {data.router_url} 已存在")
        obj = await cls.create(db, data)
        return await build_audit_info(db, obj, RouterInfo)

    @classmethod
    async def update_router(cls, db: DbSession, router_id: str, data: RouterUpdate) -> RouterInfo:
        if not await cls.get_by_id(db, router_id):
            raise ValueError("路由不存在")
        if data.router_code and not await cls.check_unique(db, "router_code", data.router_code, exclude_id=router_id):
            raise ValueError(f"路由编码 {data.router_code} 已存在")
        if data.router_url and not await cls.check_unique(db, "router_url", data.router_url, exclude_id=router_id):
            raise ValueError(f"路由地址 {data.router_url} 已存在")
        obj = await cls.update(db, router_id, data)
        if not obj:
            raise ValueError("路由不存在")
        return await build_audit_info(db, obj, RouterInfo)

    @classmethod
    async def get_router_info(cls, db: DbSession, router_id: str) -> RouterInfo | None:
        obj = await cls.get_by_id(db, router_id)
        return await build_audit_info(db, obj, RouterInfo)

    @classmethod
    async def page_router_infos(cls, db: DbSession, data: RouterPageRequest) -> PaginatedResponse[RouterInfo]:
        filters = []
        if data.router_code:
            filters.append(cls.model.router_code == data.router_code)
        if data.router_name:
            filters.append(cls.model.router_name.ilike(f"%{data.router_name}%"))
        if data.router_url:
            filters.append(cls.model.router_url == data.router_url)
        if data.module_code:
            filters.append(cls.model.module_code == data.module_code)
        if data.is_auth is not None:
            filters.append(cls.model.is_auth == data.is_auth)

        items, total = await cls.page_list(db, data.page_index, data.page_size, filters)
        return PaginatedResponse(
            items=await build_audit_infos(db, items, RouterInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )
