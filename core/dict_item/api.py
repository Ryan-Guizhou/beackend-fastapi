#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/7 23:10
@Desc: 字典项接口定义
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from base.base_schema import Response
from config.database import DbSession
from core.dict_item.schema import (
    DictItemBatchDelete,
    DictItemBatchUpdateStatus,
    DictItemCreate,
    DictItemPageRequest,
    DictItemUpdate,
)
from core.dict_item.service import DictItemService

router = APIRouter(prefix="/dict_item", tags=["字典项管理"])

logger = logging.getLogger(__name__)


@router.post("", response_model=Response, summary="创建字典项")
async def create_dict_item(
    db: DbSession,
    data: DictItemCreate,
) -> Response:
    """
    创建字典项。
    Args:
        db: 数据库会话。
        data: 字典项创建请求数据。
    Returns:
        Response: 创建结果。
    """
    try:
        dict_item = await DictItemService.create_dict_item(db, data)
    except ValueError as exc:
        return Response.failure(msg=str(exc))
    return Response.success(data=dict_item)


@router.get("/list/by_dict/{dict_code}", response_model=Response, summary="获取字典下全部启用字典项")
async def get_active_dict_items_by_dict_code(
    db: DbSession,
    dict_code: Annotated[str, Path(..., description="字典编码")],
) -> Response:
    """
    获取指定字典下全部启用字典项。
    Args:
        db: 数据库会话。
        dict_code: 字典编码。
    Returns:
        Response: 字典项列表。
    """
    items = await DictItemService.get_active_infos_by_dict_code(db, dict_code)
    return Response.success(data=items)


@router.get("/page_list", response_model=Response, summary="分页获取字典项列表")
async def get_dict_item_list(
    db: DbSession,
    data: Annotated[DictItemPageRequest, Depends()],
) -> Response:
    """
    分页查询字典项列表。
    Args:
        db: 数据库会话。
        data: 分页查询参数。
    Returns:
        Response: 分页结果。
    """
    return Response.success(data=await DictItemService.page_dict_item_infos(db, data))


@router.post("/batch/delete", response_model=Response, summary="批量删除字典项")
async def batch_delete_dict_item(
    db: DbSession,
    data: DictItemBatchDelete,
) -> Response:
    """
    批量删除字典项。
    Args:
        db: 数据库会话。
        data: 批量删除请求数据。
    Returns:
        Response: 删除结果。
    """
    return Response.success(data=await DictItemService.batch_delete_dict_item(db, data.ids))


@router.post("/batch/update_status", response_model=Response, summary="批量更新字典项状态")
async def batch_update_dict_item_status(
    db: DbSession,
    data: DictItemBatchUpdateStatus,
) -> Response:
    """
    批量更新字典项状态。
    Args:
        db: 数据库会话。
        data: 批量状态更新请求数据。
    Returns:
        Response: 更新结果。
    """
    count = await DictItemService.batch_update_status(db, data.ids, data.status)
    return Response.success(data=count)


@router.get("/check/unique", response_model=Response, summary="检查字典项字段唯一性")
async def check_dict_item_unique(
    db: DbSession,
    dict_code: str = Query(..., alias="dictCode", description="字典编码"),
    value: str = Query(..., description="字段值"),
    exclude_id: str | None = Query(default=None, alias="excludeId", description="排除ID"),
) -> Response:
    """
    检查字典项值是否唯一。
    Args:
        db: 数据库会话。
        dict_code: 字典编码。
        value: 字典项值。
        exclude_id: 更新场景下需要排除的字典项 ID。
    Returns:
        Response: 校验结果。
    """
    is_unique = await DictItemService.check_unique_value(
        db,
        dict_code=dict_code,
        value=value,
        exclude_id=exclude_id,
    )
    if not is_unique:
        return Response.failure(msg=f"字典项值 {value} 已存在")
    return Response.success()


@router.get("/{item_id}", response_model=Response, summary="获取字典项详情")
async def get_dict_item_by_id(
    db: DbSession,
    item_id: Annotated[str, Path(..., description="字典项ID")],
) -> Response:
    """
    根据字典项 ID 获取详情。
    Args:
        db: 数据库会话。
        item_id: 字典项 ID。
    Returns:
        Response: 查询结果。
    """
    dict_item = await DictItemService.get_info_by_id(db, item_id)
    if not dict_item:
        return Response.failure(msg="字典项不存在")
    return Response.success(data=dict_item)


@router.put("/{item_id}", response_model=Response, summary="修改字典项")
async def update_dict_item(
    db: DbSession,
    data: DictItemUpdate,
    item_id: Annotated[str, Path(..., description="字典项ID")],
) -> Response:
    """
    修改字典项信息。
    Args:
        db: 数据库会话。
        data: 字典项更新请求数据。
        item_id: 字典项 ID。
    Returns:
        Response: 更新结果。
    """
    try:
        updated_dict_item = await DictItemService.update_dict_item(db, item_id, data)
    except ValueError as exc:
        return Response.failure(msg=str(exc))
    return Response.success(data=updated_dict_item)


@router.delete("/{item_id}", response_model=Response, summary="删除字典项")
async def delete_dict_item(
    db: DbSession,
    item_id: Annotated[str, Path(..., description="字典项ID")],
) -> Response:
    """
    删除字典项。
    Args:
        db: 数据库会话。
        item_id: 字典项 ID。
    Returns:
        Response: 删除结果。
    """
    deleted = await DictItemService.delete_dict_item(db, item_id)
    if not deleted:
        return Response.failure(msg="字典项不存在")
    return Response.success(msg="删除成功")
