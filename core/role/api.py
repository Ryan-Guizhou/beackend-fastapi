#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 13:21
@Desc: 角色接口定义
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response
from config.database import DbSession
from core.role.schema import RoleBatchDelete, RoleCreate, RolePageRequest, RoleUpdate
from core.role.service import RoleService

router = APIRouter(prefix="/role", tags=["角色管理"])


@router.post("", response_model=Response, summary="创建角色")
async def create_role(db: DbSession, data: RoleCreate) -> Response:
    try:
        return Response.success(data=await RoleService.create_role(db, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.get("/list", response_model=Response, summary="获取启用角色列表")
async def list_roles(db: DbSession) -> Response:
    return Response.success(data=await RoleService.list_active_roles(db))


@router.get("/page_list", response_model=Response, summary="分页获取角色列表")
async def page_roles(db: DbSession, data: Annotated[RolePageRequest, Depends()]) -> Response:
    return Response.success(data=await RoleService.page_role_infos(db, data))


@router.post("/batch_delete", response_model=Response, summary="批量删除角色")
async def batch_delete_roles(db: DbSession, data: RoleBatchDelete) -> Response:
    success_count, fail_count = await RoleService.batch_delete(db, data.ids)
    return Response.success(data={"successCount": success_count, "failCount": fail_count})


@router.get("/{role_id}", response_model=Response, summary="获取角色详情")
async def get_role(db: DbSession, role_id: Annotated[str, Path(..., description="角色ID")]) -> Response:
    role = await RoleService.get_role_info(db, role_id)
    if not role:
        return Response.failure(msg="角色不存在")
    return Response.success(data=role)


@router.put("/{role_id}", response_model=Response, summary="更新角色")
async def update_role(
        db: DbSession,
        data: RoleUpdate,
        role_id: Annotated[str, Path(..., description="角色ID")],
) -> Response:
    try:
        return Response.success(data=await RoleService.update_role(db, role_id, data))
    except ValueError as exc:
        return Response.failure(msg=str(exc))


@router.delete("/{role_id}", response_model=Response, summary="删除角色")
async def delete_role(db: DbSession, role_id: Annotated[str, Path(..., description="角色ID")]) -> Response:
    if not await RoleService.del_by_id(db, role_id):
        return Response.failure(msg="角色不存在或删除失败")
    return Response.success()
