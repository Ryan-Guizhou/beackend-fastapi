#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/4/17 22:00
@Desc: 用户业务服务层
"""

from datetime import datetime, timezone

from base.audit import build_audit_info, build_audit_infos, invalidate_user_name_cache
from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.user.model import User, UserStatus
from core.user.schema import UserCreate, UserInfo, UserPageRequest, UserUpdate


class UserService(BaseService[User, UserCreate, UserUpdate]):
    model = User

    @classmethod
    def login_block_reason(cls, user: User) -> str | None:
        """
        获取用户不可登录原因。

        Args:
            user: 用户 ORM 对象。

        Returns:
            str | None: 不可登录原因；允许登录时返回 None。
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not user.is_active():
            return "账号已禁用"
        if user.invalidate and user.invalidate <= now:
            return "账号已失效"
        return None

    @classmethod
    async def record_login_success(cls, db: DbSession, user: User) -> None:
        """
        记录登录成功状态。

        Args:
            db: 数据库会话。
            user: 用户 ORM 对象。
        """
        user.status = UserStatus.ENABLED.value
        user.lastest_login = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await db.refresh(user)

    @classmethod
    async def record_login_locked(cls, db: DbSession, user: User) -> None:
        """
        将用户标记为登录失败锁定状态。

        Args:
            db: 数据库会话。
            user: 用户 ORM 对象。
        """
        user.status = UserStatus.DISABLED.value
        await db.commit()
        await db.refresh(user)

    @classmethod
    async def create_user(cls, db: DbSession, data: UserCreate) -> UserInfo:
        for field, value, msg in (
            ("user_code", data.user_code, "登录账号已存在"),
            ("mobile_phone", data.mobile_phone, "手机号已存在"),
            ("email", data.email, "邮箱已存在"),
        ):
            if value and not await cls.check_unique(db, field, value):
                raise ValueError(msg)
        user = await cls.create(db, data)
        return await build_audit_info(db, user, UserInfo)

    @classmethod
    async def update_user(cls, db: DbSession, user_id: str, data: UserUpdate) -> UserInfo:
        if not await cls.get_by_id(db, user_id):
            raise ValueError("用户不存在")
        for field, value, msg in (
            ("user_code", data.user_code, "登录账号已存在"),
            ("mobile_phone", data.mobile_phone, "手机号已存在"),
            ("email", data.email, "邮箱已存在"),
        ):
            if value and not await cls.check_unique(db, field, value, exclude_id=user_id):
                raise ValueError(msg)
        user = await cls.update(db, user_id, data)
        if not user:
            raise ValueError("用户不存在")
        invalidate_user_name_cache([user.id, user.user_code])
        return await build_audit_info(db, user, UserInfo)

    @classmethod
    async def get_user_info(cls, db: DbSession, user_id: str) -> UserInfo | None:
        user = await cls.get_by_id(db, user_id)
        return await build_audit_info(db, user, UserInfo)

    @classmethod
    async def page_user_infos(cls, db: DbSession, data: UserPageRequest) -> PaginatedResponse[UserInfo]:
        filters = []
        if data.user_code:
            filters.append(cls.model.user_code == data.user_code)
        if data.user_name:
            filters.append(cls.model.user_name.ilike(f"%{data.user_name}%"))
        if data.mobile_phone:
            filters.append(cls.model.mobile_phone.ilike(f"%{data.mobile_phone}%"))
        if data.email:
            filters.append(cls.model.email.ilike(f"%{data.email}%"))
        if data.status is not None:
            filters.append(cls.model.status == data.status)

        items, total = await cls.page_list(db, data.page_index, data.page_size, filters)
        return PaginatedResponse(
            items=await build_audit_infos(db, items, UserInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )

    @classmethod
    async def del_by_id(
            cls,
            db: DbSession,
            record_id: str,
            auto_commit: bool = True,
            hard: bool = False,
    ) -> bool:
        """
        删除用户并清理用户名称缓存。
        """
        user = await cls.get_by_id(db, record_id)
        deleted = await super().del_by_id(db, record_id, auto_commit, hard)
        if deleted and user:
            invalidate_user_name_cache([user.id, user.user_code])
        return deleted

    @classmethod
    async def batch_delete(
            cls,
            db: DbSession,
            ids: list[str],
            hard: bool = False,
            auto_commit: bool = True,
    ) -> tuple[int, int]:
        """
        批量删除用户并清理用户名称缓存。
        """
        users = [user for user_id in ids if (user := await cls.get_by_id(db, user_id))]
        result = await super().batch_delete(db, ids, hard=hard, auto_commit=auto_commit)
        invalidate_user_name_cache(
            user_key
            for user in users
            for user_key in (user.id, user.user_code)
            if user_key
        )
        return result
