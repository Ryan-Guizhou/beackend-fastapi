#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 22:40
@Desc: 登录日志接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from base.base_schema import Response
from core.login_log.schema import LoginLogPageRequest
from core.login_log.service import LoginLogService
from utils.mongo import MongoManager

router = APIRouter(prefix="/login_log", tags=["登录日志"])


def get_mongo_manager(request: Request) -> MongoManager:
    """
    获取应用生命周期中初始化的 Mongo 管理器。
    """
    mongo_manager = getattr(request.app.state, "mongo_manager", None)
    if not isinstance(mongo_manager, MongoManager):
        raise RuntimeError("MongoManager 尚未初始化")
    return mongo_manager


@router.get("/page_list", response_model=Response, summary="分页查询登录日志")
async def page_login_logs(
        data: Annotated[LoginLogPageRequest, Depends()],
        mongo_manager: Annotated[MongoManager, Depends(get_mongo_manager)],
) -> Response:
    """
    分页查询登录日志。
    """
    return Response.success(data=await LoginLogService.page_logs(mongo_manager, data))


@router.get("/{log_id}", response_model=Response, summary="获取登录日志详情")
async def get_login_log(
        log_id: Annotated[str, Path(..., description="登录日志ID")],
        mongo_manager: Annotated[MongoManager, Depends(get_mongo_manager)],
) -> Response:
    """
    根据日志 ID 查询登录日志详情。
    """
    login_log = await LoginLogService.get_log_by_id(mongo_manager, log_id)
    if not login_log:
        return Response.failure(msg="登录日志不存在")
    return Response.success(data=login_log)


@router.delete("/{log_id}", response_model=Response, summary="删除登录日志")
async def delete_login_log(
        log_id: Annotated[str, Path(..., description="登录日志ID")],
        mongo_manager: Annotated[MongoManager, Depends(get_mongo_manager)],
) -> Response:
    """
    删除登录日志。
    """
    deleted = await LoginLogService.delete_log(mongo_manager, log_id)
    if not deleted:
        return Response.failure(msg="登录日志不存在或删除失败")
    return Response.success()
