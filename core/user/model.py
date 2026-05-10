#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/4/17 22:00
@Desc: 用户数据模型
"""

from datetime import date, datetime, timezone
from enum import IntEnum

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class UserStatus(IntEnum):
    DISABLED = 0
    ENABLED = 1


class User(DBBaseModel):
    __tablename__ = "PEACH_USER"

    user_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="登录账号",
    )
    password: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="登录密码",
    )
    user_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="用户名称",
    )
    identity_code: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="证件号码",
    )
    invalidate: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="账号失效时间",
    )
    auth_mode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="认证方式",
    )
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=UserStatus.ENABLED.value,
        comment="用户状态",
    )
    unlock_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="解锁时间",
    )
    menu_style: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="菜单风格",
    )
    menu_role: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="默认菜单角色",
    )
    lastest_login: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后登录时间",
    )
    login_failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="登录失败次数",
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="生效日期",
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="失效日期",
    )
    mobile_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        comment="手机号",
    )
    email: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
        comment="邮箱",
    )
    is_modify: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="密码是否已修改",
    )
    password_modify_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="密码修改时间",
    )
    lock_reason: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="锁定原因",
    )

    def is_active(self) -> bool:
        return self.status == UserStatus.ENABLED.value

    def can_login(self) -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not self.is_active():
            return False
        if self.invalidate and self.invalidate <= now:
            return False
        if self.unlock_time and self.unlock_time > now:
            return False
        return True
