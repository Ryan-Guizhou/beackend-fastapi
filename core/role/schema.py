#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 13:21
@Desc: 角色请求和响应模型
"""

from datetime import datetime

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class RoleCreate(ApiInSchema):
    role_code: str = Field(
        ...,
        alias="roleCode",
        min_length=1,
        max_length=32,
        description="角色编码",
    )
    role_name: str = Field(
        ...,
        alias="roleName",
        min_length=1,
        max_length=64,
        description="角色名称",
    )
    role_desc: str | None = Field(
        default=None,
        alias="roleDesc",
        max_length=255,
        description="角色描述",
    )
    role_scope: str | None = Field(
        default=None,
        alias="roleScope",
        max_length=20,
        description="角色范围",
    )
    role_type: str = Field(
        ...,
        alias="roleType",
        min_length=1,
        max_length=32,
        description="角色类型",
    )
    fiscal: int = Field(
        ...,
        description="年度",
    )
    status: int = Field(
        default=1,
        ge=0,
        le=1,
        description="状态",
    )
    skip_url: str | None = Field(
        default=None,
        alias="skipUrl",
        max_length=255,
        description="默认跳转地址",
    )


class RoleUpdate(ApiInSchema):
    role_code: str | None = Field(
        default=None,
        alias="roleCode",
        min_length=1,
        max_length=32,
        description="角色编码",
    )
    role_name: str | None = Field(
        default=None,
        alias="roleName",
        min_length=1,
        max_length=64,
        description="角色名称",
    )
    role_desc: str | None = Field(
        default=None,
        alias="roleDesc",
        max_length=255,
        description="角色描述",
    )
    role_scope: str | None = Field(
        default=None,
        alias="roleScope",
        max_length=20,
        description="角色范围",
    )
    role_type: str | None = Field(
        default=None,
        alias="roleType",
        min_length=1,
        max_length=32,
        description="角色类型",
    )
    fiscal: int | None = Field(
        default=None,
        description="年度",
    )
    status: int | None = Field(
        default=None,
        ge=0,
        le=1,
        description="状态",
    )
    skip_url: str | None = Field(
        default=None,
        alias="skipUrl",
        max_length=255,
        description="默认跳转地址",
    )


class RolePageRequest(PaginatedRequest):
    role_code: str | None = Field(
        default=None,
        alias="roleCode",
        description="角色编码",
    )
    role_name: str | None = Field(
        default=None,
        alias="roleName",
        description="角色名称",
    )
    role_type: str | None = Field(
        default=None,
        alias="roleType",
        description="角色类型",
    )
    fiscal: int | None = Field(
        default=None,
        description="年度",
    )
    status: int | None = Field(
        default=None,
        ge=0,
        le=1,
        description="状态",
    )


class RoleBatchDelete(ApiInSchema):
    ids: list[str] = Field(
        ...,
        min_length=1,
        description="角色ID列表",
    )


class RoleInfo(ApiOutSchema):
    id: str = Field(
        description="角色ID",
    )
    role_code: str = Field(
        alias="roleCode",
        description="角色编码",
    )
    role_name: str = Field(
        alias="roleName",
        description="角色名称",
    )
    role_desc: str | None = Field(
        default=None,
        alias="roleDesc",
        description="角色描述",
    )
    role_scope: str | None = Field(
        default=None,
        alias="roleScope",
        description="角色范围",
    )
    role_type: str = Field(
        alias="roleType",
        description="角色类型",
    )
    fiscal: int = Field(
        description="年度",
    )
    status: int = Field(
        description="状态",
    )
    skip_url: str | None = Field(
        default=None,
        alias="skipUrl",
        description="默认跳转地址",
    )
    create_id: str | None = Field(
        default=None,
        alias="createId",
        description="创建人ID",
    )
    modify_id: str | None = Field(
        default=None,
        alias="modifyId",
        description="更新人ID",
    )
    creator: str | None = Field(
        default=None,
        description="创建人名称",
    )
    modifier: str | None = Field(
        default=None,
        description="更新人名称",
    )
    create_time: datetime | None = Field(
        default=None,
        alias="createTime",
        description="创建时间",
    )
    modify_time: datetime | None = Field(
        default=None,
        alias="modifyTime",
        description="更新时间",
    )

    @field_serializer("create_time", "modify_time")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
