#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/7 22:23
@Desc: 字典请求模型
"""

from datetime import datetime
from typing import List

from pydantic import Field, field_serializer, field_validator

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class DictUpdate(ApiInSchema):
    """
    字典更新请求模型。
    Args:
        无。
    Returns:
        无。
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="字典名称",
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="字典编码",
    )
    status: int = Field(
        default=1,
        ge=0,
        le=1,
        description="字典状态",
    )
    sort: int = Field(
        default=0,
        description="排序",
    )
    remark: str | None = Field(
        default=None,
        description="备注",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        """
        校验字典编码格式。
        Args:
            value: 待校验的字典编码。
        Returns:
            str: 校验通过后的字典编码。
        """
        if not value:
            raise ValueError("字典编码不能为空")
        if not value.replace("_", "").isalnum():
            raise ValueError("字典编码只能包含字母、数字和下划线")
        return value


class DictCreate(DictUpdate):
    """
    字典创建请求模型。
    Args:
        无。
    Returns:
        无。
    """


class DictPageRequest(PaginatedRequest):
    """
    字典分页查询请求模型。
    Args:
        无。
    Returns:
        无。
    """

    code: str | None = Field(
        default=None,
        description="字典编码",
    )
    name: str | None = Field(
        default=None,
        description="字典名称",
    )
    status: int | None = Field(
        default=None,
        ge=0,
        le=1,
        description="字典状态",
    )


class DictBatchDelete(ApiInSchema):
    """
    字典批量删除请求模型。
    Args:
        无。
    Returns:
        无。
    """

    ids: List[str] = Field(
        ...,
        min_length=1,
        description="需要删除的字典ID",
    )


class DictBatchUpdateStatus(ApiInSchema):
    """
    字典批量状态更新请求模型。
    Args:
        无。
    Returns:
        无。
    """

    ids: List[str] = Field(
        ...,
        min_length=1,
        description="需要变更的字典ID",
    )
    status: int = Field(
        ...,
        ge=0,
        le=1,
        description="需要变更的字典状态",
    )


class DictBatchDeleteResult(ApiOutSchema):
    """
    字典批量删除响应模型。
    Args:
        无。
    Returns:
        无。
    """

    success_count: int = Field(
        description="删除成功数量",
    )
    fail_count: int = Field(
        description="删除失败数量",
    )


class DictInfo(ApiOutSchema):
    """
    字典响应模型。
    Args:
        无。
    Returns:
        无。
    """

    id: str = Field(
        description="字典ID",
    )
    name: str = Field(
        description="字典名称",
    )
    code: str = Field(
        description="字典编码",
    )
    status: int = Field(
        description="字典状态",
    )
    sort: int = Field(
        description="排序",
    )
    remark: str | None = Field(
        default=None,
        description="备注",
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
        description="创建时间",
    )
    modify_time: datetime | None = Field(
        default=None,
        description="修改时间",
    )

    @field_serializer("create_time", "modify_time")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """
        格式化时间字段。
        Args:
            value: 原始时间值。
        Returns:
            str: 格式化后的时间字符串。
        """
        return value.strftime("%Y-%m-%d %H:%M:%S") if value else None
