#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 16:05
@Desc: 功能接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response
from config.database import DbSession
from core.function.schema import FunctionBatchDelete, FunctionCreate, FunctionPageRequest, FunctionUpdate
from core.function.service import FunctionService

router = APIRouter(prefix="/function", tags=["功能管理"])


@router.post("", response_model=Response, summary="创建功能")
async def create_function(db: DbSession, data: FunctionCreate) -> Response:
    try:
        return Response.success(data=await FunctionService.create_function(db, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.get("/page_list", response_model=Response, summary="分页获取功能列表")
async def page_functions(db: DbSession, data: Annotated[FunctionPageRequest, Depends()]) -> Response:
    return Response.success(data=await FunctionService.page_function_infos(db, data))


@router.post("/batch_delete", response_model=Response, summary="批量删除功能")
async def batch_delete_functions(db: DbSession, data: FunctionBatchDelete) -> Response:
    success_count, fail_count = await FunctionService.batch_delete(db, data.ids)
    return Response.success(data={"successCount": success_count, "failCount": fail_count})


@router.get("/{function_id}", response_model=Response, summary="获取功能详情")
async def get_function(db: DbSession, function_id: Annotated[str, Path(..., description="功能ID")]) -> Response:
    obj = await FunctionService.get_function_info(db, function_id)
    if not obj:
        return Response.failure(msg="功能不存在")
    return Response.success(data=obj)


@router.put("/{function_id}", response_model=Response, summary="更新功能")
async def update_function(
        db: DbSession,
        data: FunctionUpdate,
        function_id: Annotated[str, Path(..., description="功能ID")],
) -> Response:
    try:
        return Response.success(data=await FunctionService.update_function(db, function_id, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.delete("/{function_id}", response_model=Response, summary="删除功能")
async def delete_function(db: DbSession, function_id: Annotated[str, Path(..., description="功能ID")]) -> Response:
    if not await FunctionService.del_by_id(db, function_id):
        return Response.failure(msg="功能不存在或删除失败")
    return Response.success()
