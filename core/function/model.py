#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/10 16:05
@Desc: 功能数据模型
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class Function(DBBaseModel):
    __tablename__ = "PEACH_FUNCTION"

    func_code: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
        comment="功能编码",
    )
    parent_func_code: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="父级功能编码",
    )
    func_name: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="功能名称",
    )
    func_desc: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="功能描述",
    )
    func_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="功能地址",
    )
    func_seq: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="功能序号",
    )
    func_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="功能类型",
    )
    is_menu: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="是否菜单",
    )
    is_authorize: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="是否需要授权",
    )
    app_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="应用编码",
    )
    is_disable: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="禁用标记",
    )
