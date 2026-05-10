#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 16:30
@Desc: 授权日志 Mongo 服务
"""

from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from base.base_schema import PaginatedResponse
from core.auth_log.schema import AuthLogCreate, AuthLogInfo, AuthLogPageRequest
from utils.mongo import DESCENDING, MongoManager


FIELD_ALIASES = {
    "trace_id": ("TRACE_ID", "traceId"),
    "action_type": ("ACTION_TYPE", "actionType"),
    "object_type": ("OBJECT_TYPE", "objectType"),
    "app_code": ("APP_CODE", "appCode"),
    "fiscal": ("FISCAL",),
    "operator_id": ("OPERATOR_ID", "operatorId"),
    "operator_code": ("OPERATOR_CODE", "operatorCode"),
    "operator_name": ("OPERATOR_NAME", "operatorName"),
    "target_party_code": ("TARGET_PARTY_CODE", "targetPartyCode", "USER_CODE", "USER_ID"),
    "target_party_type": ("TARGET_PARTY_TYPE", "targetPartyType"),
    "target_party_name": ("TARGET_PARTY_NAME", "targetPartyName", "USER_NAME"),
    "role_code": ("ROLE_CODE", "roleCode"),
    "role_type": ("ROLE_TYPE", "roleType"),
    "func_code": ("FUNC_CODE", "funcCode"),
    "resource_code": ("RESOURCE_CODE", "resourceCode"),
    "resource_type": ("RESOURCE_TYPE", "resourceType"),
    "before_data": ("BEFORE_DATA", "beforeData"),
    "after_data": ("AFTER_DATA", "afterData"),
    "auth_desc": ("AUTH_DESC", "authDesc", "AUTH_DESCRIBE"),
    "result": ("RESULT",),
    "fail_reason": ("FAIL_REASON", "failReason"),
    "client_ip": ("CLIENT_IP", "clientIp"),
    "user_agent": ("USER_AGENT", "userAgent"),
    "operate_time": ("OPERATE_TIME", "operateTime", "OPERAT_TIME"),
}


class AuthLogService:
    """
    授权日志服务。
    """

    collection_name = "peach_auth_log"

    @staticmethod
    def _normalize_document(document: dict[str, Any]) -> dict[str, Any]:
        document = dict(document)
        object_id = document.pop("_id", None)
        if object_id is not None:
            document["id"] = str(object_id)
        if "id" not in document and "ID" in document:
            document["id"] = document["ID"]

        for target_field, aliases in FIELD_ALIASES.items():
            if target_field in document:
                continue
            for alias in aliases:
                if alias in document:
                    document[target_field] = document[alias]
                    break
        return document

    @staticmethod
    def _build_compatible_filter(field: str, value: Any) -> dict[str, Any]:
        """
        构造兼容新旧字段命名的查询条件。
        """
        names = (field, *FIELD_ALIASES.get(field, ()))
        return {"$or": [{name: value} for name in names]}

    @staticmethod
    def _build_compatible_range_filter(field: str, range_filter: dict[str, Any]) -> dict[str, Any]:
        """
        构造兼容新旧字段命名的范围查询条件。
        """
        names = (field, *FIELD_ALIASES.get(field, ()))
        return {"$or": [{name: range_filter} for name in names]}

    @classmethod
    async def create_log(cls, mongo_manager: MongoManager, data: AuthLogCreate) -> AuthLogInfo:
        """
        写入授权日志。

        Args:
            mongo_manager: Mongo 管理器。
            data: 授权日志数据。

        Returns:
            AuthLogInfo: 写入后的授权日志。
        """
        payload = data.model_dump(by_alias=False)
        result = await mongo_manager.insert_one(cls.collection_name, payload)
        payload["id"] = str(result.inserted_id)
        return AuthLogInfo.model_validate(payload)

    @classmethod
    async def get_log_by_id(cls, mongo_manager: MongoManager, log_id: str) -> AuthLogInfo | None:
        """
        根据日志 ID 查询授权日志。
        """
        try:
            document = await mongo_manager.find_by_id(cls.collection_name, log_id)
        except InvalidId:
            document = await mongo_manager.find_one(
                cls.collection_name,
                {"$or": [{"id": log_id}, {"ID": log_id}]},
            )
        if not document:
            return None
        return AuthLogInfo.model_validate(cls._normalize_document(document))

    @classmethod
    async def page_logs(
            cls,
            mongo_manager: MongoManager,
            data: AuthLogPageRequest,
    ) -> PaginatedResponse[AuthLogInfo]:
        """
        分页查询授权日志。
        """
        and_filters: list[dict[str, Any]] = []
        for field in (
            "operator_code",
            "target_party_code",
            "target_party_type",
            "action_type",
            "object_type",
            "role_code",
            "trace_id",
        ):
            value = getattr(data, field)
            if value:
                and_filters.append(cls._build_compatible_filter(field, value))

        if data.start_time or data.end_time:
            time_filter: dict[str, Any] = {}
            if data.start_time:
                time_filter["$gte"] = data.start_time
            if data.end_time:
                time_filter["$lte"] = data.end_time
            and_filters.append(cls._build_compatible_range_filter("operate_time", time_filter))

        filter_ = {"$and": and_filters} if and_filters else {}
        skip = (data.page_index - 1) * data.page_size
        total = await mongo_manager.count(cls.collection_name, filter_)
        documents = await mongo_manager.find_many(
            cls.collection_name,
            filter_,
            sort=[("_id", DESCENDING)],
            skip=skip,
            limit=data.page_size,
        )
        return PaginatedResponse(
            items=[AuthLogInfo.model_validate(cls._normalize_document(item)) for item in documents],
            total=total,
            has_next=data.page_index * data.page_size < total,
        )

    @classmethod
    async def delete_log(cls, mongo_manager: MongoManager, log_id: str) -> bool:
        """
        删除单条授权日志。
        """
        try:
            filter_ = {"_id": ObjectId(log_id)}
        except InvalidId:
            filter_ = {"$or": [{"id": log_id}, {"ID": log_id}]}
        result = await mongo_manager.delete_one(cls.collection_name, filter_)
        return result.deleted_count > 0
