#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 16:00
@Desc: 应用接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response
from config.database import DbSession
from core.application.schema import ApplicationBatchDelete, ApplicationCreate, ApplicationPageRequest, ApplicationUpdate
from core.application.service import ApplicationService

router = APIRouter(prefix="/application", tags=["应用管理"])


@router.post("", response_model=Response, summary="创建应用")
async def create_application(db: DbSession, data: ApplicationCreate) -> Response:
    try:
        return Response.success(data=await ApplicationService.create_application(db, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.get("/list", response_model=Response, summary="获取启用应用列表")
async def list_applications(db: DbSession) -> Response:
    return Response.success(data=await ApplicationService.list_active_applications(db))


@router.get("/page_list", response_model=Response, summary="分页获取应用列表")
async def page_applications(
        db: DbSession,
        data: Annotated[ApplicationPageRequest, Depends()],
) -> Response:
    return Response.success(data=await ApplicationService.page_application_infos(db, data))


@router.post("/batch_delete", response_model=Response, summary="批量删除应用")
async def batch_delete_applications(db: DbSession, data: ApplicationBatchDelete) -> Response:
    success_count, fail_count = await ApplicationService.batch_delete(db, data.ids)
    return Response.success(data={"successCount": success_count, "failCount": fail_count})


@router.get("/{app_id}", response_model=Response, summary="获取应用详情")
async def get_application(
        db: DbSession,
        app_id: Annotated[str, Path(..., description="应用ID")],
) -> Response:
    app = await ApplicationService.get_application_info(db, app_id)
    if not app:
        return Response.failure(msg="应用不存在")
    return Response.success(data=app)


@router.put("/{app_id}", response_model=Response, summary="更新应用")
async def update_application(
        db: DbSession,
        data: ApplicationUpdate,
        app_id: Annotated[str, Path(..., description="应用ID")],
) -> Response:
    try:
        return Response.success(data=await ApplicationService.update_application(db, app_id, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.delete("/{app_id}", response_model=Response, summary="删除应用")
async def delete_application(
        db: DbSession,
        app_id: Annotated[str, Path(..., description="应用ID")],
) -> Response:
    if not await ApplicationService.del_by_id(db, app_id):
        return Response.failure(msg="应用不存在或删除失败")
    return Response.success()
