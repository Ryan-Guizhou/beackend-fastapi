#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: base_model.py
@Create: 2026/4/18 0:06
@Desc: ORM 基础模型 所有业务model都需要实现此类
"""
import datetime
import uuid

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


def generate_uuid() -> str:
    """
    生成主键 UUID。

    Returns:
        str: 去掉连字符后的 32 位 UUID 字符串。
    """
    return uuid.uuid4().hex


class IdMixin:
    """
    主键字段混入类。

    说明：
        为继承该类的 ORM 模型提供统一的字符串主键字段。
    """

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        comment="Primary key UUID",
    )


class SoftMixin:
    """
    软删除字段混入类。

    说明：
        通过 `is_deleted` 标记数据是否逻辑删除，
        避免直接物理删除记录。
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Soft delete",
        nullable=False,
        index=True,
    )


class TimestampMixin:
    """
    时间戳字段混入类。

    说明：
        为模型统一提供创建时间和更新时间字段。
    """

    create_time: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="Create time",
    )

    modify_time: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Modify time",
    )


class AuditMixin:
    """
    审计字段混入类。

    说明：
        用于记录数据的创建人和修改人标识。
    """

    create_id: Mapped[str] = mapped_column(
        String(32),
        nullable=True,
        comment="Create user ID",
    )

    modify_id: Mapped[str] = mapped_column(
        String(32),
        nullable=True,
        comment="Modify user ID",
    )


class DBBaseModel(
    Base,
    IdMixin,
    SoftMixin,
    TimestampMixin,
    AuditMixin,
):
    """
    ORM 抽象基础模型。

    说明：
        该抽象类整合了主键、软删除、时间戳和审计字段，
        业务模型继承后即可复用这些公共列定义。
    """

    __abstract__ = True
