#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 16:15
@Desc: 资源接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response
from config.database import DbSession
from core.resource.schema import ResourceBatchDelete, ResourceCreate, ResourcePageRequest, ResourceUpdate
from core.resource.service import ResourceService

router = APIRouter(prefix="/resource", tags=["资源管理"])


@router.post("", response_model=Response, summary="创建资源")
async def create_resource(db: DbSession, data: ResourceCreate) -> Response:
    try:
        return Response.success(data=await ResourceService.create_resource(db, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.get("/page_list", response_model=Response, summary="分页获取资源列表")
async def page_resources(db: DbSession, data: Annotated[ResourcePageRequest, Depends()]) -> Response:
    return Response.success(data=await ResourceService.page_resource_infos(db, data))


@router.post("/batch_delete", response_model=Response, summary="批量删除资源")
async def batch_delete_resources(db: DbSession, data: ResourceBatchDelete) -> Response:
    success_count, fail_count = await ResourceService.batch_delete(db, data.ids)
    return Response.success(data={"successCount": success_count, "failCount": fail_count})


@router.get("/{resource_id}", response_model=Response, summary="获取资源详情")
async def get_resource(db: DbSession, resource_id: Annotated[str, Path(..., description="资源ID")]) -> Response:
    obj = await ResourceService.get_resource_info(db, resource_id)
    if not obj:
        return Response.failure(msg="资源不存在")
    return Response.success(data=obj)


@router.put("/{resource_id}", response_model=Response, summary="更新资源")
async def update_resource(
        db: DbSession,
        data: ResourceUpdate,
        resource_id: Annotated[str, Path(..., description="资源ID")],
) -> Response:
    try:
        return Response.success(data=await ResourceService.update_resource(db, resource_id, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.delete("/{resource_id}", response_model=Response, summary="删除资源")
async def delete_resource(db: DbSession, resource_id: Annotated[str, Path(..., description="资源ID")]) -> Response:
    if not await ResourceService.del_by_id(db, resource_id):
        return Response.failure(msg="资源不存在或删除失败")
    return Response.success()
