#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/10 13:21
@Desc: 角色 ORM 模型
"""

from enum import IntEnum

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class RoleStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


class Role(DBBaseModel):
    __tablename__ = "PEACH_ROLE"

    role_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="角色编码",
    )
    role_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="角色名称",
    )
    role_desc: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="角色描述",
    )
    role_scope: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="角色范围",
    )
    role_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="角色类型",
    )
    fiscal: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="年度",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=RoleStatus.ENABLED.value,
        comment="状态",
    )
    skip_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="默认跳转地址",
    )
