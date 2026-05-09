#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/4/17 22:07
@Desc: 演示路由
"""

import logging
from typing import List

from fastapi import APIRouter, Depends

from base.base_schema import PaginatedResponse, Response
from demo.custom.schema import User, UserDTO

router = APIRouter(
    prefix="/custom",
    tags=["测试路由管理"],
)

# 使用内存数据模拟用户列表，便于演示基本增删改查流程
users: List[User] = [
    User(
        id=1,
        username="Mr Shu",
        password="123456",
        email="huanhuanshu48@gmail.com",
        full_name="shuhuanhuan",
        disabled=True,
    ),
    User(
        id=2,
        username="Mr Li",
        password="123456",
        email="huanhuanshu48@gmail.com",
        full_name="shuhuanhuan",
        disabled=True,
    ),
    User(
        id=3,
        username="Mr Wang",
        password="123456",
        email="huanhuanshu48@gmail.com",
        full_name="shuhuanhuan",
        disabled=True,
    ),
    User(
        id=4,
        username="Mr Zhang",
        password="123456",
        email="huanhuanshu48@gmail.com",
        full_name="shuhuanhuan",
        disabled=True,
    ),
]

logger = logging.Logger(__name__)


@router.get("/", response_model=Response, summary="测试获取用户列表")
def user_list() -> Response[list[User]]:
    """
    获取全部用户列表。

    Returns:
        Response[list[User]]: 包含全部用户数据的统一响应对象。
    """
    return Response.success(data=users)


@router.get("/page", response_model=Response, summary="分页获取用户信息")
def user_page(userDTO: UserDTO = Depends()) -> Response:
    """
    分页查询用户列表。

    Args:
        userDTO: 分页查询参数对象。

    Returns:
        Response[PaginatedResponse]: 包含分页数据的统一响应对象。
    """
    total = len(users)
    return Response.success(data=PaginatedResponse(total=total, items=users))


@router.post("", response_model=Response, summary="新增用户信息")
def add_user(user: User) -> Response:
    """
    新增用户。

    Args:
        user: 需要新增的用户对象。

    Returns:
        Response: 新增成功后的统一响应对象。
    """
    users.append(user)
    return Response.success()


@router.get("/{user_id}", response_model=Response, summary="根据ID获取用户信息")
def user_info(user_id: int) -> Response:
    """
    根据用户编号查询用户详情。

    Args:
        user_id: 用户编号。

    Returns:
        Response[User]: 查询成功时返回用户信息，未命中时返回失败响应。
    """
    for user in users:
        if user.id == user_id:
            return Response.success(data=user)
    return Response.failure(msg="User not found")


@router.delete("/{user_id}", response_model=Response, summary="根据ID删除用户")
def del_user_by_id(user_id: int) -> Response:
    """
    根据用户编号删除用户。

    Args:
        user_id: 用户编号。

    Returns:
        Response: 删除成功或失败的统一响应对象。
    """
    for user in users:
        if user.id == user_id:
            users.remove(user)
            return Response.success()
    return Response.failure(msg="User not found")
