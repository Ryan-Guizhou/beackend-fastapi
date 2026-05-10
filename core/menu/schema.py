#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 16:10
@Desc: 菜单请求和响应模型
"""

from datetime import datetime

from pydantic import Field, field_serializer

from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest


class MenuCreate(ApiInSchema):
    menu_name: str | None = Field(
        default=None,
        alias="menuName",
        max_length=64,
        description="菜单名称",
    )
    menu_code: str | None = Field(
        default=None,
        alias="menuCode",
        max_length=128,
        description="菜单编码",
    )
    is_leaf: int | None = Field(
        default=None,
        alias="isLeaf",
        ge=0,
        le=1,
        description="是否叶子节点",
    )
    menu_url: str | None = Field(
        default=None,
        alias="menuUrl",
        max_length=1500,
        description="菜单地址",
    )
    menu_param: str | None = Field(
        default=None,
        alias="menuParam",
        max_length=255,
        description="菜单参数",
    )
    parent_menu_id: str | None = Field(
        default=None,
        alias="parentMenuId",
        max_length=32,
        description="父级菜单ID",
    )
    menu_level: str | None = Field(
        default=None,
        alias="menuLevel",
        max_length=16,
        description="菜单层级",
    )
    sort_no: int | None = Field(
        default=None,
        alias="sortNo",
        description="排序号",
    )
    collapse_icon: str | None = Field(
        default=None,
        alias="collapseIcon",
        max_length=64,
        description="收起图标",
    )
    expand_icon: str | None = Field(
        default=None,
        alias="expandIcon",
        max_length=64,
        description="展开图标",
    )
    menu_seq: str | None = Field(
        default=None,
        alias="menuSeq",
        max_length=128,
        description="菜单序号",
    )
    open_mode: str | None = Field(
        default=None,
        alias="openMode",
        max_length=20,
        description="打开方式",
    )
    subcount: str | None = Field(
        default=None,
        max_length=32,
        description="子节点数量",
    )
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        max_length=128,
        description="功能编码",
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
        description="禁用标记",
    )
    is_show: int = Field(
        default=1,
        alias="isShow",
        ge=0,
        le=1,
        description="显示标记",
    )
    sf_blank: int = Field(
        default=0,
        alias="sfBlank",
        ge=0,
        le=1,
        description="是否新窗口打开",
    )
    menu_icon: str | None = Field(
        default=None,
        alias="menuIcon",
        max_length=200,
        description="菜单图标",
    )


class MenuUpdate(MenuCreate):
    pass


class MenuPageRequest(PaginatedRequest):
    menu_code: str | None = Field(
        default=None,
        alias="menuCode",
        description="菜单编码",
    )
    menu_name: str | None = Field(
        default=None,
        alias="menuName",
        description="菜单名称",
    )
    parent_menu_id: str | None = Field(
        default=None,
        alias="parentMenuId",
        description="父级菜单ID",
    )
    func_code: str | None = Field(
        default=None,
        alias="funcCode",
        description="功能编码",
    )
    app_code: str | None = Field(
        default=None,
        alias="appCode",
        description="应用编码",
    )
    is_disable: int | None = Field(
        default=None,
        alias="isDisable",
        ge=0,
        le=1,
        description="禁用标记",
    )
    is_show: int | None = Field(
        default=None,
        alias="isShow",
        ge=0,
        le=1,
        description="显示标记",
    )


class MenuBatchDelete(ApiInSchema):
    ids: list[str] = Field(
        ...,
        min_length=1,
        description="菜单ID列表",
    )


class MenuInfo(MenuCreate, ApiOutSchema):
    id: str = Field(
        description="菜单ID",
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
