#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 16:20
@Desc: 前端路由接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response
from config.database import DbSession
from core.router.schema import RouterBatchDelete, RouterCreate, RouterPageRequest, RouterUpdate
from core.router.service import RouterService

router = APIRouter(prefix="/router", tags=["路由管理"])


@router.post("", response_model=Response, summary="创建路由")
async def create_router(db: DbSession, data: RouterCreate) -> Response:
    try:
        return Response.success(data=await RouterService.create_router(db, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.get("/page_list", response_model=Response, summary="分页获取路由列表")
async def page_routers(db: DbSession, data: Annotated[RouterPageRequest, Depends()]) -> Response:
    return Response.success(data=await RouterService.page_router_infos(db, data))


@router.post("/batch_delete", response_model=Response, summary="批量删除路由")
async def batch_delete_routers(db: DbSession, data: RouterBatchDelete) -> Response:
    success_count, fail_count = await RouterService.batch_delete(db, data.ids)
    return Response.success(data={"successCount": success_count, "failCount": fail_count})


@router.get("/{router_id}", response_model=Response, summary="获取路由详情")
async def get_router(db: DbSession, router_id: Annotated[str, Path(..., description="路由ID")]) -> Response:
    obj = await RouterService.get_router_info(db, router_id)
    if not obj:
        return Response.failure(msg="路由不存在")
    return Response.success(data=obj)


@router.put("/{router_id}", response_model=Response, summary="更新路由")
async def update_router(
        db: DbSession,
        data: RouterUpdate,
        router_id: Annotated[str, Path(..., description="路由ID")],
) -> Response:
    try:
        return Response.success(data=await RouterService.update_router(db, router_id, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.delete("/{router_id}", response_model=Response, summary="删除路由")
async def delete_router(db: DbSession, router_id: Annotated[str, Path(..., description="路由ID")]) -> Response:
    if not await RouterService.del_by_id(db, router_id):
        return Response.failure(msg="路由不存在或删除失败")
    return Response.success()
