#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 22:40
@Desc: 登录日志请求和响应模型
"""

from datetime import datetime
from typing import Any

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class LoginLogCreate(ApiInSchema):
    trace_id: str | None = Field(
        default=None,
        alias="traceId",
        description="请求追踪ID",
    )
    user_code: str = Field(
        ...,
        alias="userCode",
        description="登录账号",
    )
    success: bool = Field(
        ...,
        description="是否登录成功",
    )
    result: str = Field(
        default="SUCCESS",
        description="登录结果",
    )
    fail_reason: str | None = Field(
        default=None,
        alias="failReason",
        description="失败原因",
    )
    failed_count: int | None = Field(
        default=None,
        alias="failedCount",
        description="当前失败次数",
    )
    locked: bool = Field(
        default=False,
        description="是否触发锁定",
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
    request_path: str | None = Field(
        default=None,
        alias="requestPath",
        description="请求路径",
    )
    request_method: str | None = Field(
        default=None,
        alias="requestMethod",
        description="请求方法",
    )
    access_jti: str | None = Field(
        default=None,
        alias="accessJti",
        description="Access Token 标识",
    )
    refresh_jti: str | None = Field(
        default=None,
        alias="refreshJti",
        description="Refresh Token 标识",
    )
    user: dict[str, Any] = Field(
        default_factory=dict,
        description="登录用户快照",
    )
    operate_time: datetime = Field(
        default_factory=datetime.now,
        alias="operateTime",
        description="登录时间",
    )


class LoginLogPageRequest(PaginatedRequest):
    user_code: str | None = Field(
        default=None,
        alias="userCode",
        description="登录账号",
    )
    success: bool | None = Field(
        default=None,
        description="是否登录成功",
    )
    client_ip: str | None = Field(
        default=None,
        alias="clientIp",
        description="客户端IP",
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


class LoginLogInfo(ApiOutSchema):
    id: str = Field(
        description="日志ID",
    )
    trace_id: str | None = Field(
        default=None,
        alias="traceId",
        description="请求追踪ID",
    )
    user_code: str = Field(
        alias="userCode",
        description="登录账号",
    )
    success: bool = Field(
        description="是否登录成功",
    )
    result: str = Field(
        description="登录结果",
    )
    fail_reason: str | None = Field(
        default=None,
        alias="failReason",
        description="失败原因",
    )
    failed_count: int | None = Field(
        default=None,
        alias="failedCount",
        description="当前失败次数",
    )
    locked: bool = Field(
        default=False,
        description="是否触发锁定",
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
    access_jti: str | None = Field(
        default=None,
        alias="accessJti",
        description="Access Token 标识",
    )
    refresh_jti: str | None = Field(
        default=None,
        alias="refreshJti",
        description="Refresh Token 标识",
    )
    user: dict[str, Any] = Field(
        default_factory=dict,
        description="登录用户快照",
    )
    operate_time: datetime = Field(
        alias="operateTime",
        description="登录时间",
    )

    @field_serializer("operate_time")
    def serialize_datetime(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")
