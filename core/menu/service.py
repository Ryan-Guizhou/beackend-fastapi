#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 16:10
@Desc: 菜单业务服务
"""

from base.audit import build_audit_info, build_audit_infos
from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.menu.model import Menu
from core.menu.schema import MenuCreate, MenuInfo, MenuPageRequest, MenuUpdate


class MenuService(BaseService[Menu, MenuCreate, MenuUpdate]):
    model = Menu

    @classmethod
    async def create_menu(cls, db: DbSession, data: MenuCreate) -> MenuInfo:
        if data.menu_code and not await cls.check_unique(db, "menu_code", data.menu_code):
            raise ValueError(f"菜单编码 {data.menu_code} 已存在")
        obj = await cls.create(db, data)
        return await build_audit_info(db, obj, MenuInfo)

    @classmethod
    async def update_menu(cls, db: DbSession, menu_id: str, data: MenuUpdate) -> MenuInfo:
        if not await cls.get_by_id(db, menu_id):
            raise ValueError("菜单不存在")
        if data.menu_code and not await cls.check_unique(db, "menu_code", data.menu_code, exclude_id=menu_id):
            raise ValueError(f"菜单编码 {data.menu_code} 已存在")
        obj = await cls.update(db, menu_id, data)
        if not obj:
            raise ValueError("菜单不存在")
        return await build_audit_info(db, obj, MenuInfo)

    @classmethod
    async def get_menu_info(cls, db: DbSession, menu_id: str) -> MenuInfo | None:
        obj = await cls.get_by_id(db, menu_id)
        return await build_audit_info(db, obj, MenuInfo)

    @classmethod
    async def page_menu_infos(cls, db: DbSession, data: MenuPageRequest) -> PaginatedResponse[MenuInfo]:
        filters = []
        if data.menu_code:
            filters.append(cls.model.menu_code == data.menu_code)
        if data.menu_name:
            filters.append(cls.model.menu_name.ilike(f"%{data.menu_name}%"))
        if data.parent_menu_id:
            filters.append(cls.model.parent_menu_id == data.parent_menu_id)
        if data.func_code:
            filters.append(cls.model.func_code == data.func_code)
        if data.app_code:
            filters.append(cls.model.app_code == data.app_code)
        if data.is_disable is not None:
            filters.append(cls.model.is_disable == data.is_disable)
        if data.is_show is not None:
            filters.append(cls.model.is_show == data.is_show)

        items, total = await cls.page_list(db, data.page_index, data.page_size, filters)
        return PaginatedResponse(
            items=await build_audit_infos(db, items, MenuInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )
