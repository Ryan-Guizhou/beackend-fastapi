#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/7 22:04
@Desc: 字典项数据模型
"""
from enum import IntEnum

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class DictItemStatus(IntEnum):
    """
    字典项状态枚举。
    """

    DISABLED = 0
    ENABLED = 1


class DictItem(DBBaseModel):
    """
    字典项 ORM 模型。
    Args:
        无。
    Returns:
        无。
    """

    __tablename__ = "PEACH_DICT_ITEM"

    dict_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="字典ID",
    )
    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="显示名称",
    )
    value: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="实际值",
    )
    icon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="图标",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DictItemStatus.ENABLED,
        comment="字典项状态 1:启用 0:禁用",
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
