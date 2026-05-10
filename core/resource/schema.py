#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 16:15
@Desc: 资源请求和响应模型
"""

from datetime import datetime

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class ResourceCreate(ApiInSchema):
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        max_length=128,
        description="功能编码",
    )
    resource_type: str = Field(
        ...,
        alias="resourceType",
        min_length=1,
        max_length=20,
        description="资源类型",
    )
    resource_code: str = Field(
        ...,
        alias="resourceCode",
        min_length=1,
        max_length=128,
        description="资源编码",
    )
    resource_name: str | None = Field(
        default=None,
        alias="resourceName",
        max_length=128,
        description="资源名称",
    )
    resource_url: str | None = Field(
        default=None,
        alias="resourceUrl",
        max_length=255,
        description="资源地址",
    )
    http_method: str | None = Field(
        default=None,
        alias="httpMethod",
        max_length=16,
        description="HTTP方法",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        max_length=64,
        description="应用编码",
    )


class ResourceUpdate(ApiInSchema):
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        max_length=128,
        description="功能编码",
    )
    resource_type: str | None = Field(
        default=None,
        alias="resourceType",
        min_length=1,
        max_length=20,
        description="资源类型",
    )
    resource_code: str | None = Field(
        default=None,
        alias="resourceCode",
        min_length=1,
        max_length=128,
        description="资源编码",
    )
    resource_name: str | None = Field(
        default=None,
        alias="resourceName",
        max_length=128,
        description="资源名称",
    )
    resource_url: str | None = Field(
        default=None,
        alias="resourceUrl",
        max_length=255,
        description="资源地址",
    )
    http_method: str | None = Field(
        default=None,
        alias="httpMethod",
        max_length=16,
        description="HTTP方法",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        max_length=64,
        description="应用编码",
    )


class ResourcePageRequest(PaginatedRequest):
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        description="功能编码",
    )
    resource_type: str | None = Field(
        default=None,
        alias="resourceType",
        description="资源类型",
    )
    resource_code: str | None = Field(
        default=None,
        alias="resourceCode",
        description="资源编码",
    )
    resource_name: str | None = Field(
        default=None,
        alias="resourceName",
        description="资源名称",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
    )


class ResourceBatchDelete(ApiInSchema):
    ids: list[str] = Field(
        ...,
        min_length=1,
        description="资源ID列表",
    )


class ResourceInfo(ApiOutSchema):
    id: str = Field(
        description="资源ID",
    )
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        description="功能编码",
    )
    resource_type: str = Field(
        alias="resourceType",
        description="资源类型",
    )
    resource_code: str = Field(
        alias="resourceCode",
        description="资源编码",
    )
    resource_name: str | None = Field(
        default=None,
        alias="resourceName",
        description="资源名称",
    )
    resource_url: str | None = Field(
        default=None,
        alias="resourceUrl",
        description="资源地址",
    )
    http_method: str | None = Field(
        default=None,
        alias="httpMethod",
        description="HTTP方法",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
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
