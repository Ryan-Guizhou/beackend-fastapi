#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/7 22:23
@Desc: 字典接口定义
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from base.base_schema import Response
from config.database import DbSession
from core.dict.schema import DictBatchDelete, DictBatchUpdateStatus, DictCreate, DictPageRequest, DictUpdate
from core.dict.service import DictService

router = APIRouter(prefix="/dict", tags=["字典管理"])

logger = logging.getLogger(__name__)


@router.post("", response_model=Response, summary="创建字典")
async def create_dict(
    db: DbSession,
    data: DictCreate,
) -> Response:
    """
    创建字典。
    Args:
        db: 数据库会话。
        data: 字典创建请求数据。
    Returns:
        Response: 创建结果。
    """
    try:
        dict_info = await DictService.create_dict(db, data)
    except ValueError as exc:
        return Response.failure(msg=str(exc))
    return Response.success(data=dict_info)


@router.get("/list", response_model=Response, summary="获取全部启用字典")
async def get_all_active_dicts(db: DbSession) -> Response:
    """
    获取全部启用状态的字典。
    Args:
        db: 数据库会话。
    Returns:
        Response: 字典列表。
    """
    return Response.success(data=await DictService.get_all_active_dict(db))


@router.get("/page_list", response_model=Response, summary="分页获取字典列表")
async def get_dict_list(
    db: DbSession,
    data: Annotated[DictPageRequest, Depends()],
) -> Response:
    """
    分页查询字典列表。
    Args:
        db: 数据库会话。
        data: 分页查询参数。
    Returns:
        Response: 分页结果。
    """
    return Response.success(data=await DictService.page_dict_infos(db, data))


@router.post("/batch/delete", response_model=Response, summary="批量删除字典")
async def batch_delete_dict(
    db: DbSession,
    data: DictBatchDelete,
) -> Response:
    """
    批量删除字典。
    Args:
        db: 数据库会话。
        data: 批量删除请求数据。
    Returns:
        Response: 删除结果。
    """
    return Response.success(data=await DictService.batch_delete_dict(db, data.ids))


@router.post("/batch/update_status", response_model=Response, summary="批量更新字典状态")
async def batch_update_status(
    db: DbSession,
    data: DictBatchUpdateStatus,
) -> Response:
    """
    批量更新字典状态。
    Args:
        db: 数据库会话。
        data: 批量状态更新请求数据。
    Returns:
        Response: 更新结果。
    """
    count = await DictService.batch_update_status(db, data.ids, data.status)
    return Response.success(data=count)


@router.get("/check/unique", response_model=Response, summary="检查字典字段唯一性")
async def check_dict_unique(
    db: DbSession,
    field: str = Query(..., description="字段名"),
    value: str = Query(..., description="字段值"),
    exclude_id: str | None = Query(default=None, alias="excludeId", description="排除ID"),
) -> Response:
    """
    检查字典字段值是否唯一。
    Args:
        db: 数据库会话。
        field: 待校验字段名。
        value: 待校验字段值。
        exclude_id: 更新场景下需要排除的字典 ID。
    Returns:
        Response: 校验结果。
    """
    allowed_fields = ["code"]
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"不支持检查字段 {field}")

    is_unique = await DictService.check_unique(
        db,
        field=field,
        value=value,
        exclude_id=exclude_id,
    )
    if not is_unique:
        return Response.failure(msg=f"字段 {field} 的值 {value} 已存在")
    return Response.success()


@router.get("/{dict_id}", response_model=Response, summary="获取字典详情")
async def get_by_id(
    db: DbSession,
    dict_id: Annotated[str, Path(..., description="字典ID")],
) -> Response:
    """
    根据字典 ID 获取字典详情。
    Args:
        db: 数据库会话。
        dict_id: 字典 ID。
    Returns:
        Response: 查询结果。
    """
    dict_info = await DictService.get_dict_info_by_id(db, dict_id)
    if not dict_info:
        return Response.failure(msg="字典不存在")
    return Response.success(data=dict_info)


@router.put("/{dict_id}", response_model=Response, summary="修改字典")
async def update_dict(
    db: DbSession,
    data: DictUpdate,
    dict_id: Annotated[str, Path(..., description="字典ID")],
) -> Response:
    """
    修改字典信息。
    Args:
        db: 数据库会话。
        data: 字典更新请求数据。
        dict_id: 字典 ID。
    Returns:
        Response: 更新结果。
    """
    try:
        updated_dict_info = await DictService.update_dict(db, dict_id, data)
    except ValueError as exc:
        return Response.failure(msg=str(exc))
    return Response.success(data=updated_dict_info)


@router.delete("/{dict_id}", response_model=Response, summary="删除字典")
async def delete_dict(
    db: DbSession,
    dict_id: Annotated[str, Path(..., description="字典ID")],
) -> Response:
    """
    删除字典，同时删除该字典下的字典项。
    Args:
        db: 数据库会话。
        dict_id: 字典 ID。
    Returns:
        Response: 删除结果。
    """
    try:
        deleted = await DictService.delete_dict_with_items(db, dict_id)
    except ValueError as exc:
        return Response.failure(msg=str(exc))
    if not deleted:
        return Response.failure(msg="字典删除失败")
    return Response.success(msg="删除成功")
