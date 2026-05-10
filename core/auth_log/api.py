#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 17:05
@Desc: 授权日志接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from base.base_schema import Response
from core.auth_log.schema import AuthLogCreate, AuthLogPageRequest
from core.auth_log.service import AuthLogService
from utils.mongo import MongoManager

router = APIRouter(prefix="/auth_log", tags=["授权日志"])


def get_mongo_manager(request: Request) -> MongoManager:
    """
    获取应用生命周期中初始化的 Mongo 管理器。

    Args:
        request: FastAPI 请求对象。

    Returns:
        MongoManager: Mongo 管理器。

    Raises:
        RuntimeError: Mongo 管理器未初始化时抛出。
    """
    mongo_manager = getattr(request.app.state, "mongo_manager", None)
    if not isinstance(mongo_manager, MongoManager):
        raise RuntimeError("MongoManager 尚未初始化")
    return mongo_manager


@router.post("", response_model=Response, summary="写入授权日志")
async def create_auth_log(
        data: AuthLogCreate,
        mongo_manager: Annotated[MongoManager, Depends(get_mongo_manager)],
) -> Response:
    """
    写入授权日志。

    Args:
        data: 授权日志数据。
        mongo_manager: Mongo 管理器。

    Returns:
        Response: 写入后的日志信息。
    """
    return Response.success(data=await AuthLogService.create_log(mongo_manager, data))


@router.get("/page_list", response_model=Response, summary="分页查询授权日志")
async def page_auth_logs(
        data: Annotated[AuthLogPageRequest, Depends()],
        mongo_manager: Annotated[MongoManager, Depends(get_mongo_manager)],
) -> Response:
    """
    分页查询授权日志。

    Args:
        data: 授权日志分页查询参数。
        mongo_manager: Mongo 管理器。

    Returns:
        Response: 授权日志分页结果。
    """
    return Response.success(data=await AuthLogService.page_logs(mongo_manager, data))


@router.get("/{log_id}", response_model=Response, summary="获取授权日志详情")
async def get_auth_log(
        log_id: Annotated[str, Path(..., description="授权日志ID")],
        mongo_manager: Annotated[MongoManager, Depends(get_mongo_manager)],
) -> Response:
    """
    根据日志 ID 查询授权日志详情。

    Args:
        log_id: 授权日志 ID。
        mongo_manager: Mongo 管理器。

    Returns:
        Response: 授权日志详情。
    """
    auth_log = await AuthLogService.get_log_by_id(mongo_manager, log_id)
    if not auth_log:
        return Response.failure(msg="授权日志不存在")
    return Response.success(data=auth_log)


@router.delete("/{log_id}", response_model=Response, summary="删除授权日志")
async def delete_auth_log(
        log_id: Annotated[str, Path(..., description="授权日志ID")],
        mongo_manager: Annotated[MongoManager, Depends(get_mongo_manager)],
) -> Response:
    """
    删除授权日志。

    Args:
        log_id: 授权日志 ID。
        mongo_manager: Mongo 管理器。

    Returns:
        Response: 删除结果。
    """
    deleted = await AuthLogService.delete_log(mongo_manager, log_id)
    if not deleted:
        return Response.failure(msg="授权日志不存在或删除失败")
    return Response.success()
