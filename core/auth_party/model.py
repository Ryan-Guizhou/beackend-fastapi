#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/10 13:22
@Desc: 文件描述
"""

from base.base_model import DBBaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped,mapped_column

class AuthParty(DBBaseModel):

    __tablename__ = "PEACH_AUTH_PARTY"

    role_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment='角色编码'
    )

    role_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment='角色类型'
    )

    party_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment='参与者代码'
    )

    party_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment='参与者类型'
    )
