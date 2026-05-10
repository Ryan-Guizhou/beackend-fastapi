#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/10 16:10
@Desc: 菜单数据模型
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class Menu(DBBaseModel):
    __tablename__ = "PEACH_MENU"

    menu_name: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="菜单名称",
    )
    menu_code: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
        index=True,
        comment="菜单编码",
    )
    is_leaf: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="是否叶子节点",
    )
    menu_url: Mapped[str | None] = mapped_column(
        String(1500),
        nullable=True,
        comment="菜单地址",
    )
    menu_param: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="菜单参数",
    )
    parent_menu_id: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="父级菜单ID",
    )
    menu_level: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="菜单层级",
    )
    sort_no: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="排序号",
    )
    collapse_icon: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="收起图标",
    )
    expand_icon: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="展开图标",
    )
    menu_seq: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="菜单序号",
    )
    open_mode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="打开方式",
    )
    subcount: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="子节点数量",
    )
    func_code: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="功能编码",
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
    is_show: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="显示标记",
    )
    sf_blank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="是否新窗口打开",
    )
    menu_icon: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="菜单图标",
    )
