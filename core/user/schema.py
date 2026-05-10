#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/4/17 22:00
@Desc: 用户请求与响应模型
"""

from datetime import datetime

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class UserCreate(ApiInSchema):
    user_code: str = Field(
        ...,
        alias="userCode",
        min_length=2,
        max_length=64,
        description="登录账号",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="登录密码",
    )
    user_name: str = Field(
        ...,
        alias="userName",
        min_length=1,
        max_length=64,
        description="用户名称",
    )
    identity_code: str | None = Field(
        default=None,
        alias="identityCode",
        max_length=30,
        description="证件号码",
    )
    invalidate: datetime | None = Field(
        default=None,
        description="账号失效时间",
    )
    auth_mode: str | None = Field(
        default=None,
        alias="authMode",
        max_length=20,
        description="认证方式",
    )
    status: int = Field(
        default=1,
        ge=0,
        le=1,
        description="用户状态",
    )
    mobile_phone: str | None = Field(
        default=None,
        alias="mobilePhone",
        max_length=20,
        description="手机号",
    )
    email: str | None = Field(
        default=None,
        max_length=64,
        description="邮箱",
    )


class UserUpdate(ApiInSchema):
    user_code: str | None = Field(
        default=None,
        alias="userCode",
        min_length=2,
        max_length=64,
        description="登录账号",
    )
    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="登录密码",
    )
    user_name: str | None = Field(
        default=None,
        alias="userName",
        min_length=1,
        max_length=64,
        description="用户名称",
    )
    identity_code: str | None = Field(
        default=None,
        alias="identityCode",
        max_length=30,
        description="证件号码",
    )
    invalidate: datetime | None = Field(
        default=None,
        description="账号失效时间",
    )
    auth_mode: str | None = Field(
        default=None,
        alias="authMode",
        max_length=20,
        description="认证方式",
    )
    status: int | None = Field(
        default=None,
        ge=0,
        le=1,
        description="用户状态",
    )
    mobile_phone: str | None = Field(
        default=None,
        alias="mobilePhone",
        max_length=20,
        description="手机号",
    )
    email: str | None = Field(
        default=None,
        max_length=64,
        description="邮箱",
    )
    is_modify: int | None = Field(
        default=None,
        alias="isModify",
        ge=0,
        le=1,
        description="密码是否已修改",
    )
    password_modify_time: datetime | None = Field(
        default=None,
        alias="passwordModifyTime",
        description="密码修改时间",
    )


class UserPageRequest(PaginatedRequest):
    user_code: str | None = Field(
        default=None,
        alias="userCode",
        description="登录账号",
    )
    user_name: str | None = Field(
        default=None,
        alias="userName",
        description="用户名称",
    )
    mobile_phone: str | None = Field(
        default=None,
        alias="mobilePhone",
        description="手机号",
    )
    email: str | None = Field(
        default=None,
        description="邮箱",
    )
    status: int | None = Field(
        default=None,
        ge=0,
        le=1,
        description="用户状态",
    )


class UserStatusUpdate(ApiInSchema):
    status: int = Field(
        ...,
        ge=0,
        le=1,
        description="用户状态",
    )


class UserBatchDelete(ApiInSchema):
    ids: list[str] = Field(
        ...,
        min_length=1,
        description="用户ID列表",
    )


class UserInfo(ApiOutSchema):
    id: str = Field(
        description="用户ID",
    )
    user_code: str = Field(
        alias="userCode",
        description="登录账号",
    )
    user_name: str = Field(
        alias="userName",
        description="用户名称",
    )
    identity_code: str | None = Field(
        default=None,
        alias="identityCode",
        description="证件号码",
    )
    invalidate: datetime | None = Field(
        default=None,
        description="账号失效时间",
    )
    auth_mode: str | None = Field(
        default=None,
        alias="authMode",
        description="认证方式",
    )
    status: int = Field(
        description="用户状态",
    )
    lastest_login: datetime | None = Field(
        default=None,
        alias="lastestLogin",
        description="最后登录时间",
    )
    mobile_phone: str | None = Field(
        default=None,
        alias="mobilePhone",
        description="手机号",
    )
    email: str | None = Field(
        default=None,
        description="邮箱",
    )
    is_modify: int = Field(
        alias="isModify",
        description="密码是否已修改",
    )
    password_modify_time: datetime | None = Field(
        default=None,
        alias="passwordModifyTime",
        description="密码修改时间",
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

    @field_serializer("create_time", "modify_time", "invalidate", "lastest_login", "password_modify_time")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
