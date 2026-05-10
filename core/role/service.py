#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 13:21
@Desc: 角色业务服务
"""

from base.audit import build_audit_info, build_audit_infos
from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.role.model import Role, RoleStatus
from core.role.schema import RoleCreate, RoleInfo, RolePageRequest, RoleUpdate


class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    model = Role

    @classmethod
    async def _check_role_unique(
            cls,
            db: DbSession,
            role_code: str,
            role_type: str,
            fiscal: int,
            exclude_id: str | None = None,
    ) -> bool:
        """
        校验角色业务键是否唯一。
        """
        filters = [
            cls.model.role_code == role_code,
            cls.model.role_type == role_type,
            cls.model.fiscal == fiscal,
        ]
        if exclude_id:
            filters.append(cls.model.id != exclude_id)
        return not await cls.exists(db, filters)

    @classmethod
    async def create_role(cls, db: DbSession, data: RoleCreate) -> RoleInfo:
        if not await cls._check_role_unique(db, data.role_code, data.role_type, data.fiscal):
            raise ValueError("角色编码、类型和年度组合已存在")
        role = await cls.create(db, data)
        return await build_audit_info(db, role, RoleInfo)

    @classmethod
    async def update_role(cls, db: DbSession, role_id: str, data: RoleUpdate) -> RoleInfo:
        if not await cls.get_by_id(db, role_id):
            raise ValueError("角色不存在")
        current = await cls.get_by_id(db, role_id)
        role_code = data.role_code or current.role_code
        role_type = data.role_type or current.role_type
        fiscal = data.fiscal if data.fiscal is not None else current.fiscal
        if not await cls._check_role_unique(db, role_code, role_type, fiscal, exclude_id=role_id):
            raise ValueError("角色编码、类型和年度组合已存在")
        role = await cls.update(db, role_id, data)
        if not role:
            raise ValueError("角色不存在")
        return await build_audit_info(db, role, RoleInfo)

    @classmethod
    async def get_role_info(cls, db: DbSession, role_id: str) -> RoleInfo | None:
        role = await cls.get_by_id(db, role_id)
        return await build_audit_info(db, role, RoleInfo)

    @classmethod
    async def list_active_roles(cls, db: DbSession) -> list[RoleInfo]:
        roles = await cls.get_all(db, [cls.model.status == RoleStatus.ENABLED.value])
        return await build_audit_infos(db, roles, RoleInfo)

    @classmethod
    async def page_role_infos(cls, db: DbSession, data: RolePageRequest) -> PaginatedResponse[RoleInfo]:
        filters = []
        if data.role_code:
            filters.append(cls.model.role_code == data.role_code)
        if data.role_name:
            filters.append(cls.model.role_name.ilike(f"%{data.role_name}%"))
        if data.role_type:
            filters.append(cls.model.role_type == data.role_type)
        if data.fiscal is not None:
            filters.append(cls.model.fiscal == data.fiscal)
        if data.status is not None:
            filters.append(cls.model.status == data.status)

        items, total = await cls.page_list(db, data.page_index, data.page_size, filters)
        return PaginatedResponse(
            items=await build_audit_infos(db, items, RoleInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )
