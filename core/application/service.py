#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 16:00
@Desc: 应用业务服务
"""

from base.audit import build_audit_info, build_audit_infos
from base.base_schema import PaginatedResponse
from base.base_service import BaseService
from config.database import DbSession
from core.application.model import Application, ApplicationStatus
from core.application.schema import ApplicationCreate, ApplicationInfo, ApplicationPageRequest, ApplicationUpdate


class ApplicationService(BaseService[Application, ApplicationCreate, ApplicationUpdate]):
    model = Application

    @classmethod
    async def create_application(cls, db: DbSession, data: ApplicationCreate) -> ApplicationInfo:
        if not await cls.check_unique(db, "app_code", data.app_code):
            raise ValueError(f"应用编码 {data.app_code} 已存在")
        if not await cls.check_unique(db, "app_name", data.app_name):
            raise ValueError(f"应用名称 {data.app_name} 已存在")
        app = await cls.create(db, data)
        return await build_audit_info(db, app, ApplicationInfo)

    @classmethod
    async def update_application(cls, db: DbSession, app_id: str, data: ApplicationUpdate) -> ApplicationInfo:
        app = await cls.get_by_id(db, app_id)
        if not app:
            raise ValueError("应用不存在")
        if data.app_code and not await cls.check_unique(db, "app_code", data.app_code, exclude_id=app_id):
            raise ValueError(f"应用编码 {data.app_code} 已存在")
        if data.app_name and not await cls.check_unique(db, "app_name", data.app_name, exclude_id=app_id):
            raise ValueError(f"应用名称 {data.app_name} 已存在")
        updated = await cls.update(db, app_id, data)
        if not updated:
            raise ValueError("应用不存在")
        return await build_audit_info(db, updated, ApplicationInfo)

    @classmethod
    async def get_application_info(cls, db: DbSession, app_id: str) -> ApplicationInfo | None:
        app = await cls.get_by_id(db, app_id)
        return await build_audit_info(db, app, ApplicationInfo)

    @classmethod
    async def list_active_applications(cls, db: DbSession) -> list[ApplicationInfo]:
        items = await cls.get_all(db, [cls.model.status == ApplicationStatus.ENABLED.value])
        return await build_audit_infos(db, items, ApplicationInfo)

    @classmethod
    async def page_application_infos(
            cls,
            db: DbSession,
            data: ApplicationPageRequest,
    ) -> PaginatedResponse[ApplicationInfo]:
        filters = []
        if data.app_code:
            filters.append(cls.model.app_code == data.app_code)
        if data.app_name:
            filters.append(cls.model.app_name.ilike(f"%{data.app_name}%"))
        if data.app_type:
            filters.append(cls.model.app_type == data.app_type)
        if data.status is not None:
            filters.append(cls.model.status == data.status)

        items, total = await cls.page_list(db, data.page_index, data.page_size, filters)
        return PaginatedResponse(
            items=await build_audit_infos(db, items, ApplicationInfo),
            total=total,
            has_next=data.page_index * data.page_size < total,
        )
