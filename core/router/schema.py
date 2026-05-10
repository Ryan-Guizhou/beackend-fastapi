#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 16:20
@Desc: 前端路由请求和响应模型
"""

from datetime import datetime

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class RouterCreate(ApiInSchema):
    router_code: str = Field(
        ...,
        alias="routerCode",
        min_length=1,
        max_length=100,
        description="路由编码",
    )
    router_name: str = Field(
        ...,
        alias="routerName",
        min_length=1,
        max_length=100,
        description="路由名称",
    )
    router_url: str = Field(
        ...,
        alias="routerUrl",
        min_length=1,
        max_length=255,
        description="路由地址",
    )
    file_path: str = Field(
        ...,
        alias="filePath",
        min_length=1,
        max_length=255,
        description="组件文件路径",
    )
    is_auth: int = Field(
        default=1,
        alias="isAuth",
        ge=0,
        le=1,
        description="是否鉴权",
    )
    is_cache: int = Field(
        default=0,
        alias="isCache",
        ge=0,
        le=1,
        description="是否缓存",
    )
    module_code: str = Field(
        ...,
        alias="moduleCode",
        min_length=1,
        max_length=32,
        description="模块编码",
    )
    router_level: int = Field(
        ...,
        alias="routerLevel",
        description="路由层级",
    )


class RouterUpdate(ApiInSchema):
    router_code: str | None = Field(
        default=None,
        alias="routerCode",
        min_length=1,
        max_length=100,
        description="路由编码",
    )
    router_name: str | None = Field(
        default=None,
        alias="routerName",
        min_length=1,
        max_length=100,
        description="路由名称",
    )
    router_url: str | None = Field(
        default=None,
        alias="routerUrl",
        min_length=1,
        max_length=255,
        description="路由地址",
    )
    file_path: str | None = Field(
        default=None,
        alias="filePath",
        min_length=1,
        max_length=255,
        description="组件文件路径",
    )
    is_auth: int | None = Field(
        default=None,
        alias="isAuth",
        ge=0,
        le=1,
        description="是否鉴权",
    )
    is_cache: int | None = Field(
        default=None,
        alias="isCache",
        ge=0,
        le=1,
        description="是否缓存",
    )
    module_code: str | None = Field(
        default=None,
        alias="moduleCode",
        min_length=1,
        max_length=32,
        description="模块编码",
    )
    router_level: int | None = Field(
        default=None,
        alias="routerLevel",
        description="路由层级",
    )


class RouterPageRequest(PaginatedRequest):
    router_code: str | None = Field(
        default=None,
        alias="routerCode",
        description="路由编码",
    )
    router_name: str | None = Field(
        default=None,
        alias="routerName",
        description="路由名称",
    )
    router_url: str | None = Field(
        default=None,
        alias="routerUrl",
        description="路由地址",
    )
    module_code: str | None = Field(
        default=None,
        alias="moduleCode",
        description="模块编码",
    )
    is_auth: int | None = Field(
        default=None,
        alias="isAuth",
        ge=0,
        le=1,
        description="是否鉴权",
    )


class RouterBatchDelete(ApiInSchema):
    ids: list[str] = Field(
        ...,
        min_length=1,
        description="路由ID列表",
    )


class RouterInfo(ApiOutSchema):
    id: str = Field(
        description="路由ID",
    )
    router_code: str = Field(
        alias="routerCode",
        description="路由编码",
    )
    router_name: str = Field(
        alias="routerName",
        description="路由名称",
    )
    router_url: str = Field(
        alias="routerUrl",
        description="路由地址",
    )
    file_path: str = Field(
        alias="filePath",
        description="组件文件路径",
    )
    is_auth: int = Field(
        alias="isAuth",
        description="是否鉴权",
    )
    is_cache: int = Field(
        alias="isCache",
        description="是否缓存",
    )
    module_code: str = Field(
        alias="moduleCode",
        description="模块编码",
    )
    router_level: int = Field(
        alias="routerLevel",
        description="路由层级",
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
