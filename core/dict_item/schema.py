#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/7 23:10
@Desc: 字典项请求模型
"""
from datetime import datetime
from typing import List

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class DictItemUpdate(ApiInSchema):
    """
    字典项更新请求模型。
    Args:
        无。
    Returns:
        无。
    """

    dict_code: str = Field(..., min_length=1,alias='dictCode', max_length=32, description="字典ID")
    label: str = Field(..., min_length=1, max_length=100, description="显示名称")
    value: str = Field(..., min_length=1, max_length=100, description="实际值")
    icon: str | None = Field(default=None, max_length=100, description="图标")
    status: int = Field(default=1, ge=0, le=1, description="字典项状态")
    sort: int = Field(default=0, description="排序")
    remark: str | None = Field(default=None, description="备注")


class DictItemCreate(DictItemUpdate):
    """
    字典项创建请求模型。
    Args:
        无。
    Returns:
        无。
    """


class DictItemPageRequest(PaginatedRequest):
    """
    字典项分页查询请求模型。
    Args:
        无。
    Returns:
        无。
    """

    dict_code: str | None = Field(default=None, alias="dictCode", description="字典编码")
    label: str | None = Field(default=None, description="显示名称")
    value: str | None = Field(default=None, description="实际值")
    status: int | None = Field(default=None, ge=0, le=1, description="字典项状态")


class DictItemBatchDelete(ApiInSchema):
    """
    字典项批量删除请求模型。
    Args:
        无。
    Returns:
        无。
    """

    ids: List[str] = Field(..., min_length=1, description="需要删除的字典项ID")


class DictItemBatchUpdateStatus(ApiInSchema):
    """
    字典项批量状态更新请求模型。
    Args:
        无。
    Returns:
        无。
    """

    ids: List[str] = Field(..., min_length=1, description="需要变更的字典项ID")
    status: int = Field(..., ge=0, le=1, description="需要变更的字典项状态")


class DictItemInfo(ApiOutSchema):
    """
    字典项响应模型。
    Args:
        无。
    Returns:
        无。
    """

    id: str = Field(description="字典项ID")
    dict_code: str = Field(description="字典ID")
    label: str = Field(description="显示名称")
    value: str = Field(description="实际值")
    icon: str | None = Field(default=None, description="图标")
    status: int = Field(description="字典项状态")
    sort: int = Field(description="排序")
    remark: str | None = Field(default=None, description="备注")
    create_time: datetime = Field(description="创建时间")
    modify_time: datetime = Field(description="修改时间")

    @field_serializer("create_time", "modify_time")
    def serialize_datetime(self, value: datetime) -> str:
        """
        格式化时间字段。
        Args:
            value: 原始时间值。
        Returns:
            str: 格式化后的时间字符串。
        """
        return value.strftime("%Y-%m-%d %H:%M:%S")
