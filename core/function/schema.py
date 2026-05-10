#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 16:05
@Desc: 功能请求和响应模型
"""

from datetime import datetime

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class FunctionCreate(ApiInSchema):
    func_code: str = Field(
        ...,
        alias="funcCode",
        min_length=1,
        max_length=128,
        description="功能编码",
    )
    parent_func_code: str | None = Field(
        default=None,
        alias="parentFuncCode",
        max_length=128,
        description="父级功能编码",
    )
    func_name: str | None = Field(
        default=None,
        alias="funcName",
        max_length=64,
        description="功能名称",
    )
    func_desc: str | None = Field(
        default=None,
        alias="funcDesc",
        max_length=255,
        description="功能描述",
    )
    func_url: str | None = Field(
        default=None,
        alias="funcUrl",
        max_length=255,
        description="功能地址",
    )
    func_seq: str | None = Field(
        default=None,
        alias="funcSeq",
        max_length=128,
        description="功能序号",
    )
    func_type: str | None = Field(
        default=None,
        alias="funcType",
        max_length=20,
        description="功能类型",
    )
    is_menu: int = Field(
        default=0,
        alias="isMenu",
        ge=0,
        le=1,
        description="是否菜单",
    )
    is_authorize: int = Field(
        default=0,
        alias="isAuthorize",
        ge=0,
        le=1,
        description="是否需要授权",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        max_length=64,
        description="应用编码",
    )
    is_disable: int = Field(
        default=0,
        alias="isDisable",
        ge=0,
        le=1,
        description="是否禁用",
    )


class FunctionUpdate(ApiInSchema):
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        min_length=1,
        max_length=128,
        description="功能编码",
    )
    parent_func_code: str | None = Field(
        default=None,
        alias="parentFuncCode",
        max_length=128,
        description="父级功能编码",
    )
    func_name: str | None = Field(
        default=None,
        alias="funcName",
        max_length=64,
        description="功能名称",
    )
    func_desc: str | None = Field(
        default=None,
        alias="funcDesc",
        max_length=255,
        description="功能描述",
    )
    func_url: str | None = Field(
        default=None,
        alias="funcUrl",
        max_length=255,
        description="功能地址",
    )
    func_seq: str | None = Field(
        default=None,
        alias="funcSeq",
        max_length=128,
        description="功能序号",
    )
    func_type: str | None = Field(
        default=None,
        alias="funcType",
        max_length=20,
        description="功能类型",
    )
    is_menu: int | None = Field(
        default=None,
        alias="isMenu",
        ge=0,
        le=1,
        description="是否菜单",
    )
    is_authorize: int | None = Field(
        default=None,
        alias="isAuthorize",
        ge=0,
        le=1,
        description="是否需要授权",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        max_length=64,
        description="应用编码",
    )
    is_disable: int | None = Field(
        default=None,
        alias="isDisable",
        ge=0,
        le=1,
        description="是否禁用",
    )


class FunctionPageRequest(PaginatedRequest):
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        description="功能编码",
    )
    func_name: str | None = Field(
        default=None,
        alias="funcName",
        description="功能名称",
    )
    parent_func_code: str | None = Field(
        default=None,
        alias="parentFuncCode",
        description="父级功能编码",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
    )
    func_type: str | None = Field(
        default=None,
        alias="funcType",
        description="功能类型",
    )
    is_disable: int | None = Field(
        default=None,
        alias="isDisable",
        ge=0,
        le=1,
        description="是否禁用",
    )


class FunctionBatchDelete(ApiInSchema):
    ids: list[str] = Field(
        ...,
        min_length=1,
        description="功能ID列表",
    )


class FunctionInfo(ApiOutSchema):
    id: str = Field(
        description="功能ID",
    )
    func_code: str = Field(
        alias="funcCode",
        description="功能编码",
    )
    parent_func_code: str | None = Field(
        default=None,
        alias="parentFuncCode",
        description="父级功能编码",
    )
    func_name: str | None = Field(
        default=None,
        alias="funcName",
        description="功能名称",
    )
    func_desc: str | None = Field(
        default=None,
        alias="funcDesc",
        description="功能描述",
    )
    func_url: str | None = Field(
        default=None,
        alias="funcUrl",
        description="功能地址",
    )
    func_seq: str | None = Field(
        default=None,
        alias="funcSeq",
        description="功能序号",
    )
    func_type: str | None = Field(
        default=None,
        alias="funcType",
        description="功能类型",
    )
    is_menu: int = Field(
        alias="isMenu",
        description="是否菜单",
    )
    is_authorize: int = Field(
        alias="isAuthorize",
        description="是否需要授权",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
    )
    is_disable: int = Field(
        alias="isDisable",
        description="是否禁用",
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
