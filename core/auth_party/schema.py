#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/10 13:22
@Desc: 文件描述
"""
from base.base_schema import ApiInSchema, ApiOutSchema, PaginatedRequest
from pydantic import Field


class AuthPartyCreate(ApiInSchema):
    role_code: str = Field(
        default=None,
        alias="roleCode",
        description="角色编码",
    )
    role_name: str = Field(
        default=None,
        alias="roleName",
        description="角色名称",
    )
    party_code: str = Field(
        default=None,
        alias="partyCode",
        description="参与者编码",
    )
    party_name: str = Field(
        default=None,
        alias="partyName",
        description="参与者名称",
    )
    fiscal: int = Field(
        default=None,
        alias="fiscal",
        description="年度",
    )


class AuthPartyUpdate(ApiInSchema):
    id: str = Field(
        default=None,
        description="主键ID",
    )


class AuthPartyInfo(ApiOutSchema):
    id: str = Field(
        default=None,
        description="主键ID",
    )
    role_code: str = Field(
        default=None,
        alias="roleCode",
        description="角色编码",
    )
    role_name: str = Field(
        default=None,
        alias="roleName",
        description="角色名称",
    )
    party_code: str = Field(
        default=None,
        alias="partyCode",
        description="参与者编码",
    )
    party_name: str = Field(
        default=None,
        alias="partyName",
        description="参与者名称",
    )
    fiscal: int = Field(
        default=None,
        alias="fiscal",
        description="年度",
    )
    create_id: str = Field(
        default=None,
        alias="createId",
        description="创建者ID",
    )
    modify_id: str = Field(
        default=None,
        alias="modifyId",
        description="更新者ID",
    )
    create_time: str = Field(
        default=None,
        alias="createTime",
        description="更新者时间",
    )
    modify_time: str = Field(
        default=None,
        alias="modifyTime",
        description="更新者时间",
    )
    creator: str = Field(
        default=None,
        alias="creator",
        description="创建者",
    )
    modifier: str = Field(
        default=None,
        alias="modifier",
        description="更新者",
    )


class AuthPartyPageRequest(PaginatedRequest):
    role_code: str = Field(
        default=None,
        alias="roleCode",
        description="角色编码",
    )
    role_name: str = Field(
        default=None,
        alias="roleName",
        description="角色名称",
    )
    party_code: str = Field(
        default=None,
        alias="partyCode",
        description="参与者编码",
    )
    party_name: str = Field(
        default=None,
        alias="partyName",
        description="参与者名称",
    )
    fiscal: str = Field(
        default=None,
        alias="fiscal",
        description="角色名称",
    )
    create_time: str = Field(
        default=None,
        alias="createTime",
        description="更新者时间",
    )
    modify_time: str = Field(
        default=None,
        alias="modifyTime",
        description="更新者时间",
    )
