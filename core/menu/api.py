#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 16:10
@Desc: 菜单接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response
from config.database import DbSession
from core.menu.schema import MenuBatchDelete, MenuCreate, MenuPageRequest, MenuUpdate
from core.menu.service import MenuService

router = APIRouter(prefix="/menu", tags=["菜单管理"])


@router.post("", response_model=Response, summary="创建菜单")
async def create_menu(db: DbSession, data: MenuCreate) -> Response:
    try:
        return Response.success(data=await MenuService.create_menu(db, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.get("/page_list", response_model=Response, summary="分页获取菜单列表")
async def page_menus(db: DbSession, data: Annotated[MenuPageRequest, Depends()]) -> Response:
    return Response.success(data=await MenuService.page_menu_infos(db, data))


@router.post("/batch_delete", response_model=Response, summary="批量删除菜单")
async def batch_delete_menus(db: DbSession, data: MenuBatchDelete) -> Response:
    success_count, fail_count = await MenuService.batch_delete(db, data.ids)
    return Response.success(data={"successCount": success_count, "failCount": fail_count})


@router.get("/{menu_id}", response_model=Response, summary="获取菜单详情")
async def get_menu(db: DbSession, menu_id: Annotated[str, Path(..., description="菜单ID")]) -> Response:
    obj = await MenuService.get_menu_info(db, menu_id)
    if not obj:
        return Response.failure(msg="菜单不存在")
    return Response.success(data=obj)


@router.put("/{menu_id}", response_model=Response, summary="更新菜单")
async def update_menu(
        db: DbSession,
        data: MenuUpdate,
        menu_id: Annotated[str, Path(..., description="菜单ID")],
) -> Response:
    try:
        return Response.success(data=await MenuService.update_menu(db, menu_id, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.delete("/{menu_id}", response_model=Response, summary="删除菜单")
async def delete_menu(db: DbSession, menu_id: Annotated[str, Path(..., description="菜单ID")]) -> Response:
    if not await MenuService.del_by_id(db, menu_id):
        return Response.failure(msg="菜单不存在或删除失败")
    return Response.success()
