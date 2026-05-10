#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/10 16:00
@Desc: 应用数据模型
"""

from enum import IntEnum

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class ApplicationStatus(IntEnum):
    """
    应用状态枚举。
    """

    DISABLED = 0
    ENABLED = 1


class Application(DBBaseModel):
    """
    应用表 ORM 模型。
    """

    __tablename__ = "PEACH_APPLICATION"

    app_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="应用编码",
    )
    app_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="应用名称",
    )
    app_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="应用类型",
    )
    app_desc: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="应用描述",
    )
    logout_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="退出登录回调地址",
    )
    sort_num: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序号",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=ApplicationStatus.ENABLED.value,
        comment="状态",
    )
