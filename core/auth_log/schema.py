#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 16:30
@Desc: 授权日志请求和响应模型
"""

from datetime import datetime
from typing import Any

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class AuthLogCreate(ApiInSchema):
    trace_id: str | None = Field(
        default=None,
        alias="traceId",
        description="请求追踪ID",
    )
    action_type: str = Field(
        ...,
        alias="actionType",
        description="操作类型",
    )
    object_type: str = Field(
        ...,
        alias="objectType",
        description="授权对象类型",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
    )
    fiscal: int | None = Field(
        default=None,
        description="年度",
    )
    operator_id: str | None = Field(
        default=None,
        alias="operatorId",
        description="操作人ID",
    )
    operator_code: str = Field(
        ...,
        alias="operatorCode",
        description="操作人编码",
    )
    operator_name: str = Field(
        ...,
        alias="operatorName",
        description="操作人名称",
    )
    target_party_code: str | None = Field(
        default=None,
        alias="targetPartyCode",
        description="目标主体编码",
    )
    target_party_type: str | None = Field(
        default=None,
        alias="targetPartyType",
        description="目标主体类型",
    )
    target_party_name: str | None = Field(
        default=None,
        alias="targetPartyName",
        description="目标主体名称",
    )
    role_code: str | None = Field(
        default=None,
        alias="roleCode",
        description="角色编码",
    )
    role_type: str | None = Field(
        default=None,
        alias="roleType",
        description="角色类型",
    )
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        description="功能编码",
    )
    resource_code: str | None = Field(
        default=None,
        alias="resourceCode",
        description="资源编码",
    )
    resource_type: str | None = Field(
        default=None,
        alias="resourceType",
        description="资源类型",
    )
    before_data: dict[str, Any] | None = Field(
        default=None,
        alias="beforeData",
        description="操作前数据",
    )
    after_data: dict[str, Any] | None = Field(
        default=None,
        alias="afterData",
        description="操作后数据",
    )
    auth_desc: str | None = Field(
        default=None,
        alias="authDesc",
        description="授权操作描述",
    )
    result: str = Field(
        default="SUCCESS",
        description="操作结果",
    )
    fail_reason: str | None = Field(
        default=None,
        alias="failReason",
        description="失败原因",
    )
    client_ip: str | None = Field(
        default=None,
        alias="clientIp",
        description="客户端IP",
    )
    user_agent: str | None = Field(
        default=None,
        alias="userAgent",
        description="User-Agent",
    )
    operate_time: datetime = Field(
        default_factory=datetime.now,
        alias="operateTime",
        description="操作时间",
    )


class AuthLogPageRequest(PaginatedRequest):
    operator_code: str | None = Field(
        default=None,
        alias="operatorCode",
        description="操作人编码",
    )
    target_party_code: str | None = Field(
        default=None,
        alias="targetPartyCode",
        description="目标主体编码",
    )
    target_party_type: str | None = Field(
        default=None,
        alias="targetPartyType",
        description="目标主体类型",
    )
    action_type: str | None = Field(
        default=None,
        alias="actionType",
        description="操作类型",
    )
    object_type: str | None = Field(
        default=None,
        alias="objectType",
        description="授权对象类型",
    )
    role_code: str | None = Field(
        default=None,
        alias="roleCode",
        description="角色编码",
    )
    trace_id: str | None = Field(
        default=None,
        alias="traceId",
        description="请求追踪ID",
    )
    start_time: datetime | None = Field(
        default=None,
        alias="startTime",
        description="开始时间",
    )
    end_time: datetime | None = Field(
        default=None,
        alias="endTime",
        description="结束时间",
    )


class AuthLogInfo(ApiOutSchema):
    id: str = Field(
        description="日志ID",
    )
    trace_id: str | None = Field(
        default=None,
        alias="traceId",
        description="请求追踪ID",
    )
    action_type: str = Field(
        alias="actionType",
        description="操作类型",
    )
    object_type: str = Field(
        alias="objectType",
        description="授权对象类型",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
    )
    fiscal: int | None = Field(
        default=None,
        description="年度",
    )
    operator_code: str = Field(
        alias="operatorCode",
        description="操作人编码",
    )
    operator_name: str = Field(
        alias="operatorName",
        description="操作人名称",
    )
    target_party_code: str | None = Field(
        default=None,
        alias="targetPartyCode",
        description="目标主体编码",
    )
    target_party_type: str | None = Field(
        default=None,
        alias="targetPartyType",
        description="目标主体类型",
    )
    target_party_name: str | None = Field(
        default=None,
        alias="targetPartyName",
        description="目标主体名称",
    )
    role_code: str | None = Field(
        default=None,
        alias="roleCode",
        description="角色编码",
    )
    role_type: str | None = Field(
        default=None,
        alias="roleType",
        description="角色类型",
    )
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        description="功能编码",
    )
    resource_code: str | None = Field(
        default=None,
        alias="resourceCode",
        description="资源编码",
    )
    resource_type: str | None = Field(
        default=None,
        alias="resourceType",
        description="资源类型",
    )
    auth_desc: str | None = Field(
        default=None,
        alias="authDesc",
        description="授权操作描述",
    )
    result: str = Field(
        default="SUCCESS",
        description="操作结果",
    )
    fail_reason: str | None = Field(
        default=None,
        alias="failReason",
        description="失败原因",
    )
    client_ip: str | None = Field(
        default=None,
        alias="clientIp",
        description="客户端IP",
    )
    operate_time: datetime = Field(
        alias="operateTime",
        description="操作时间",
    )

    @field_serializer("operate_time")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")
