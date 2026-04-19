#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: base_schema.py
@Create: 2026/4/17 21:44
@Desc: 基础响应模型
"""
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse

T = TypeVar("T")


class ErrorCode(int, Enum):
    """
    统一错误码枚举。

    说明：
        该枚举用于定义接口返回中通用的业务状态码，
        便于在响应体中统一表达成功、失败、鉴权异常和参数校验异常等状态。
    """

    SUCCESS = 200
    FAILURE = 500
    AUTH_FAILURE = 401
    COMMON_FAILURE = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNAUTHORIZED = 405
    VALIDATE_ERROR = 406
    TOO_MANY_REQUESTS = 429
    GATEWAY_TIMEOUT = 502


class Response(BaseModel, Generic[T]):
    """
    通用响应模型。

    说明：
        该模型用于统一接口返回结构，默认包含状态码、响应数据和提示信息。
        其中 `data` 支持泛型，方便不同接口复用同一套返回包装格式。
    """

    code: int = Field(default=ErrorCode.SUCCESS, description="Response code")
    data: T | None = Field(default=None, description="Response data")
    msg: str = Field(default="Operation successful", description="Response message")

    @classmethod
    def success(
            cls,
            code: int = ErrorCode.SUCCESS,
            data: T | None = None,
            msg: str = "Operation successful",
    ) -> "Response[T]":
        """
        创建成功响应。

        Args:
            code: 响应状态码，默认使用成功状态码。
            data: 响应数据内容。
            msg: 响应提示信息。

        Returns:
            Response[T]: 标准成功响应对象。
        """
        return cls(
            code=code,
            data=data,
            msg=msg,
        )

    @classmethod
    def failure(
            cls,
            code: int = ErrorCode.SUCCESS,
            data: T | None = None,
            msg: str = "Operation failure",
    ) -> "Response[T]":
        """
        创建失败响应。

        Args:
            code: 响应状态码，通常传入失败或异常类状态码。
            data: 响应数据内容。
            msg: 响应提示信息。

        Returns:
            Response[T]: 标准失败响应对象。
        """
        return cls(
            code=code,
            data=data,
            msg=msg,
        )

    def to_http_response(self, status_code: int = 200) -> JSONResponse:
        return JSONResponse(status_code=status_code, content=self.model_dump())




class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应模型。

    说明：
        该模型用于统一分页查询接口的返回结构，
        包含当前页数据列表、总记录数以及是否存在下一页等信息。
    """

    items: list[T] = Field(default_factory=list, description="Data items")
    total: int = Field(default=0, description="Total count")
    has_next: bool = Field(default=False, description="Has next page")


class PaginatedRequest(BaseModel):
    """
    分页请求模型。

    说明：
        该模型用于接收分页查询参数，
        通过 `page_size` 和 `page_index` 约束分页请求的大小和页码范围。
    """

    # 允许同时接收字段原名和 alias，例如 page_size 与 pageSize
    model_config = ConfigDict(populate_by_name=True)

    page_size: int = Field(
        default=20,
        ge=1,
        le=200,
        alias="pageSize",
        description="Page size",
    )
    page_index: int = Field(
        default=1,
        ge=1,
        alias="pageIndex",
        description="Page index",
    )
