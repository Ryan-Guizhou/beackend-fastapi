#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: audit.py
@Create: 2026/5/10 16:45
@Desc: 审计响应信息补全工具
"""

import time
from collections.abc import Iterable, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy import or_, select

from config.database import DbSession
from core.user.model import User

InfoT = TypeVar("InfoT", bound=BaseModel)

_USER_NAME_CACHE_TTL = 60
_USER_NAME_CACHE: dict[str, tuple[str, float]] = {}


def invalidate_user_name_cache(user_ids: Iterable[str]) -> None:
    """
    清理用户名称本地缓存。

    Args:
        user_ids: 需要清理的用户 ID 或用户编码。
    """
    for user_id in user_ids:
        if user_id:
            _USER_NAME_CACHE.pop(user_id, None)


async def get_user_name_map(db: DbSession, user_ids: Iterable[str]) -> dict[str, str]:
    """
    批量查询用户名称，并使用短 TTL 本地缓存减少重复查询。

    Args:
        db: 数据库会话。
        user_ids: 用户 ID 或用户编码集合。

    Returns:
        dict[str, str]: 用户 ID/编码到用户名称的映射。
    """
    now = time.monotonic()
    normalized_ids = {user_id for user_id in user_ids if user_id}
    result: dict[str, str] = {}
    missing_ids: set[str] = set()

    for user_id in normalized_ids:
        cached = _USER_NAME_CACHE.get(user_id)
        if cached and cached[1] > now:
            result[user_id] = cached[0]
            continue
        missing_ids.add(user_id)

    if not missing_ids:
        return result

    query_result = await db.execute(
        select(User.id, User.user_code, User.user_name).where(
            User.is_deleted.is_(False),
            or_(User.id.in_(missing_ids), User.user_code.in_(missing_ids)),
        )
    )
    expires_at = now + _USER_NAME_CACHE_TTL
    for user_id, user_code, user_name in query_result.all():
        if user_id:
            _USER_NAME_CACHE[user_id] = (user_name, expires_at)
            if user_id in missing_ids:
                result[user_id] = user_name
        if user_code:
            _USER_NAME_CACHE[user_code] = (user_name, expires_at)
            if user_code in missing_ids:
                result[user_code] = user_name

    return result


async def build_audit_infos(
        db: DbSession,
        items: Sequence[Any],
        schema_type: type[InfoT],
) -> list[InfoT]:
    """
    批量构建带创建人、更新人名称的响应模型。

    Args:
        db: 数据库会话。
        items: ORM 对象列表。
        schema_type: 响应模型类型。

    Returns:
        list[InfoT]: 已补全审计名称的响应对象列表。
    """
    user_ids = {
        user_id
        for item in items
        for user_id in (getattr(item, "create_id", None), getattr(item, "modify_id", None))
        if user_id
    }
    user_name_map = await get_user_name_map(db, user_ids)

    result: list[InfoT] = []
    for item in items:
        payload = schema_type.model_validate(item).model_dump()
        create_id = getattr(item, "create_id", None)
        modify_id = getattr(item, "modify_id", None)
        payload["create_id"] = create_id
        payload["modify_id"] = modify_id
        payload["creator"] = user_name_map.get(create_id)
        payload["modifier"] = user_name_map.get(modify_id)
        result.append(schema_type.model_validate(payload))
    return result


async def build_audit_info(
        db: DbSession,
        item: Any | None,
        schema_type: type[InfoT],
) -> InfoT | None:
    """
    构建单个带创建人、更新人名称的响应模型。

    Args:
        db: 数据库会话。
        item: ORM 对象。
        schema_type: 响应模型类型。

    Returns:
        InfoT | None: 已补全审计名称的响应对象。
    """
    if item is None:
        return None
    infos = await build_audit_infos(db, [item], schema_type)
    return infos[0]
