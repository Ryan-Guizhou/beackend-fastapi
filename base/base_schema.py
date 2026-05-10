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

def to_camel(field_name: str) -> str:
    """
    将下划线命名的字段名转换为小驼峰命名。
    Args:
        field_name: 原始字段名。
    Returns:
        str: 转换后的小驼峰字段名。
    """
    parts = field_name.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])



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
    AUTH_EXPIRED = 402
    COMMON_FAILURE = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNAUTHORIZED = 405
    VALIDATE_ERROR = 406
    TOO_MANY_REQUESTS = 429
    GATEWAY_TIMEOUT = 502

class CamelBaseModel(BaseModel):
    """
    统一支持驼峰与下划线字段名的基础模型。
    Args:
        无。
    Returns:
        无。
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

class ApiInSchema(CamelBaseModel):
    """API 输入基类: 同时兼容 snake_case 和 camelCase。"""



class ApiOutSchema(CamelBaseModel):
    """API 输出基类: 统一输出 camelCase，并支持从 ORM 对象构建。"""

    model_config = ConfigDict(
        from_attributes=True,
    )

class Response(ApiOutSchema, Generic[T]):
    """
    通用响应模型。

    说明：
        该模型用于统一接口返回结构，默认包含状态码、响应数据和提示信息。
        其中 `data` 支持泛型，方便不同接口复用同一套返回包装格式。
    """

    code: int = Field(default=ErrorCode.SUCCESS, description="响应编码")
    data: T | None = Field(default=None, description="响应数据")
    msg: str = Field(default="操作成功", description="响应消息")

    @classmethod
    def success(
            cls,
            code: int = ErrorCode.SUCCESS,
            data: T | None = None,
            msg: str = "操作成功",
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
            msg: str = "操作失败",
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
        """
        将响应模型转换为 HTTP 响应对象。
        Args:
            status_code: HTTP 状态码，默认返回 200。
        Returns:
            JSONResponse: 使用字段别名序列化后的 JSON 响应对象。
        """
        return JSONResponse(
            status_code=status_code,
            content=self.model_dump(by_alias=True),
        )



class PaginatedResponse(ApiOutSchema, Generic[T]):
    """
    分页响应模型。

    说明：
        该模型用于统一分页查询接口的返回结构，
        包含当前页数据列表、总记录数以及是否存在下一页等信息。
    """

    items: list[T] = Field(default_factory=list, description="数据项")
    total: int = Field(default=0, description="返回数据总数")
    has_next: bool = Field(default=False, description="是否还有下一页")


class PaginatedRequest(ApiInSchema):
    """
    分页请求模型。

    说明：
        该模型用于接收分页查询参数，
        通过 `page_size` 和 `page_index` 约束分页请求的大小和页码范围。
    """

    page_size: int = Field(
        default=20,
        ge=1,
        le=200,
        alias="pageSize",
        description="分页大小",
    )
    page_index: int = Field(
        default=1,
        ge=1,
        alias="pageIndex",
        description="第几页",
    )

