#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/10 16:15
@Desc: 前端路由数据模型
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class Router(DBBaseModel):
    __tablename__ = "PEACH_ROUTER"

    router_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="路由编码",
    )
    router_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="路由名称",
    )
    router_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="路由地址",
    )
    file_path: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="组件文件路径",
    )
    is_auth: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="是否鉴权",
    )
    is_cache: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="是否缓存",
    )
    module_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="模块编码",
    )
    router_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="路由层级",
    )
