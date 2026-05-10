#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/10 16:15
@Desc: 资源数据模型
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class Resource(DBBaseModel):
    __tablename__ = "PEACH_RESOURCE"

    func_code: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        comment="功能编码",
    )
    resource_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="资源类型",
    )
    resource_code: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="资源编码",
    )
    resource_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="资源名称",
    )
    resource_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="资源地址",
    )
    http_method: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="HTTP方法",
    )
    app_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="应用编码",
    )
