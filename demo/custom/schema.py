#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/4/17 22:09
@Desc: 演示用户模型
"""
from pydantic import BaseModel

from base.base_schema import PaginatedRequest


class User(BaseModel):
    """
    演示用户模型。

    说明：
        该模型用于描述演示模块中的用户基础信息，
        同时作为新增和查询接口的响应数据结构。
    """

    id: int
    username: str
    password: str
    email: str
    full_name: str | None = None
    disabled: bool = False


class UserDTO(PaginatedRequest):
    """
    演示用户分页查询参数模型。

    说明：
        该模型在基础分页参数上扩展了用户编号字段，
        用于演示分页场景下的查询条件接收方式。
    """

    id: int
