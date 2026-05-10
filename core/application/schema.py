#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 16:00
@Desc: 应用请求和响应模型
"""

from datetime import datetime

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class ApplicationBase(ApiInSchema):
    app_code: str = Field(
        ...,
        alias="appCode",
        min_length=1,
        max_length=64,
        description="应用编码",
    )
    app_name: str = Field(
        ...,
        alias="appName",
        min_length=1,
        max_length=64,
        description="应用名称",
    )
    app_type: str = Field(
        ...,
        alias="appType",
        min_length=1,
        max_length=32,
        description="应用类型",
    )
    app_desc: str | None = Field(
        default=None,
        alias="appDesc",
        max_length=255,
        description="应用描述",
    )
    logout_url: str | None = Field(
        default=None,
        alias="logoutUrl",
        max_length=255,
        description="退出登录回调地址",
    )
    sort_num: int = Field(
        default=0,
        alias="sortNum",
        description="排序号",
    )
    status: int = Field(
        default=1,
        ge=0,
        le=1,
        description="状态",
    )


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(ApiInSchema):
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        min_length=1,
        max_length=64,
        description="应用编码",
    )
    app_name: str | None = Field(
        default=None,
        alias="appName",
        min_length=1,
        max_length=64,
        description="应用名称",
    )
    app_type: str | None = Field(
        default=None,
        alias="appType",
        min_length=1,
        max_length=32,
        description="应用类型",
    )
    app_desc: str | None = Field(
        default=None,
        alias="appDesc",
        max_length=255,
        description="应用描述",
    )
    logout_url: str | None = Field(
        default=None,
        alias="logoutUrl",
        max_length=255,
        description="退出登录回调地址",
    )
    sort_num: int | None = Field(
        default=None,
        alias="sortNum",
        description="排序号",
    )
    status: int | None = Field(
        default=None,
        ge=0,
        le=1,
        description="状态",
    )


class ApplicationPageRequest(PaginatedRequest):
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
    )
    app_name: str | None = Field(
        default=None,
        alias="appName",
        description="应用名称",
    )
    app_type: str | None = Field(
        default=None,
        alias="appType",
        description="应用类型",
    )
    status: int | None = Field(
        default=None,
        ge=0,
        le=1,
        description="状态",
    )


class ApplicationBatchDelete(ApiInSchema):
    ids: list[str] = Field(
        ...,
        min_length=1,
        description="应用ID列表",
    )


class ApplicationInfo(ApiOutSchema):
    id: str = Field(
        description="应用ID",
    )
    app_code: str = Field(
        alias="appCode",
        description="应用编码",
    )
    app_name: str = Field(
        alias="appName",
        description="应用名称",
    )
    app_type: str = Field(
        alias="appType",
        description="应用类型",
    )
    app_desc: str | None = Field(
        default=None,
        alias="appDesc",
        description="应用描述",
    )
    logout_url: str | None = Field(
        default=None,
        alias="logoutUrl",
        description="退出登录回调地址",
    )
    sort_num: int = Field(
        alias="sortNum",
        description="排序号",
    )
    status: int = Field(
        description="状态",
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
