#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/4/17 22:00
@Desc: 用户接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response
from config.database import DbSession
from core.user.schema import UserBatchDelete, UserCreate, UserPageRequest, UserStatusUpdate, UserUpdate
from core.user.service import UserService

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post("", response_model=Response, summary="创建用户")
async def create_user(db: DbSession, data: UserCreate) -> Response:
    try:
        return Response.success(data=await UserService.create_user(db, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.get("/page_list", response_model=Response, summary="分页获取用户列表")
async def page_users(db: DbSession, data: Annotated[UserPageRequest, Depends()]) -> Response:
    return Response.success(data=await UserService.page_user_infos(db, data))


@router.post("/batch_delete", response_model=Response, summary="批量删除用户")
async def batch_delete_users(db: DbSession, data: UserBatchDelete) -> Response:
    success_count, fail_count = await UserService.batch_delete(db, data.ids)
    return Response.success(data={"successCount": success_count, "failCount": fail_count})


@router.get("/{user_id}", response_model=Response, summary="获取用户详情")
async def get_user(db: DbSession, user_id: Annotated[str, Path(..., description="用户ID")]) -> Response:
    user = await UserService.get_user_info(db, user_id)
    if not user:
        return Response.failure(msg="用户不存在")
    return Response.success(data=user)


@router.put("/{user_id}", response_model=Response, summary="更新用户")
async def update_user(
        db: DbSession,
        data: UserUpdate,
        user_id: Annotated[str, Path(..., description="用户ID")],
) -> Response:
    try:
        return Response.success(data=await UserService.update_user(db, user_id, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.put("/{user_id}/status", response_model=Response, summary="更新用户状态")
async def update_user_status(
        db: DbSession,
        data: UserStatusUpdate,
        user_id: Annotated[str, Path(..., description="用户ID")],
) -> Response:
    try:
        return Response.success(data=await UserService.update_user(db, user_id, UserUpdate(status=data.status)))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.delete("/{user_id}", response_model=Response, summary="删除用户")
async def delete_user(db: DbSession, user_id: Annotated[str, Path(..., description="用户ID")]) -> Response:
    if not await UserService.del_by_id(db, user_id):
        return Response.failure(msg="用户不存在或删除失败")
    return Response.success()
