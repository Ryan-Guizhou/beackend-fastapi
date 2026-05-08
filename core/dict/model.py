#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/7 22:04
@Desc: 字典数据模型
"""
from enum import IntEnum

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class DictStatus(IntEnum):
    """
    字典状态枚举。
    """

    DISABLED = 0
    ENABLED = 1


class Dict(DBBaseModel):
    """
    字典主表 ORM 模型。
    Args:
        无。
    Returns:
        无。
    """

    __tablename__ = "PEACH_DICT"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="字典名称",
    )
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="字典编码",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DictStatus.ENABLED,
        comment="字典状态 1:启用 0:禁用",
    )
    sort: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序",
    )
    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注",
    )
