#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/10 22:40
@Desc: 登录日志 Mongo 服务
"""

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from base.base_schema import PaginatedResponse
from core.login_log.schema import LoginLogCreate, LoginLogInfo, LoginLogPageRequest
from core.user.model import User
from utils.mongo import DESCENDING, MongoManager


class LoginLogService:
    """
    登录日志服务。
    """

    collection_name = "peach_login_log"

    @staticmethod
    def _normalize_document(document: dict[str, Any]) -> dict[str, Any]:
        document = dict(document)
        object_id = document.pop("_id", None)
        if object_id is not None:
            document["id"] = str(object_id)
        return document

    @staticmethod
    def _user_snapshot(user: User | None) -> dict[str, Any]:
        """
        构造登录用户快照。

        Args:
            user: 用户 ORM 对象。

        Returns:
            dict[str, Any]: 可用于溯源和分析的用户信息。
        """
        if user is None:
            return {}
        return {
            "userId": user.id,
            "userCode": user.user_code,
            "userName": user.user_name,
            "status": user.status,
            "authMode": user.auth_mode,
            "lastestLogin": user.lastest_login,
        }

    @classmethod
    async def create_log(cls, mongo_manager: MongoManager, data: LoginLogCreate) -> LoginLogInfo:
        """
        写入登录日志。

        Args:
            mongo_manager: Mongo 管理器。
            data: 登录日志数据。

        Returns:
            LoginLogInfo: 写入后的登录日志。
        """
        payload = data.model_dump(by_alias=False)
        result = await mongo_manager.insert_one(cls.collection_name, payload)
        payload["id"] = str(result.inserted_id)
        return LoginLogInfo.model_validate(payload)

    @classmethod
    async def record_login(
            cls,
            mongo_manager: MongoManager | None,
            *,
            trace_id: str | None,
            user_code: str,
            user: User | None,
            success: bool,
            fail_reason: str | None,
            client_ip: str | None,
            user_agent: str | None,
            request_path: str,
            request_method: str,
            failed_count: int | None = None,
            locked: bool = False,
            access_jti: str | None = None,
            refresh_jti: str | None = None,
    ) -> None:
        """
        记录登录事件。

        Args:
            mongo_manager: Mongo 管理器。
            trace_id: 请求追踪 ID。
            user_code: 登录账号。
            user: 命中的用户。
            success: 是否登录成功。
            fail_reason: 失败原因。
            client_ip: 客户端 IP。
            user_agent: User-Agent。
            request_path: 请求路径。
            request_method: 请求方法。
            failed_count: 当前失败次数。
            locked: 是否触发锁定。
            access_jti: Access Token 标识。
            refresh_jti: Refresh Token 标识。
        """
        if mongo_manager is None:
            return
        await cls.create_log(
            mongo_manager,
            LoginLogCreate(
                traceId=trace_id,
                userCode=user_code,
                success=success,
                result="SUCCESS" if success else "FAILURE",
                failReason=fail_reason,
                failedCount=failed_count,
                locked=locked,
                clientIp=client_ip,
                userAgent=user_agent,
                requestPath=request_path,
                requestMethod=request_method,
                accessJti=access_jti,
                refreshJti=refresh_jti,
                user=cls._user_snapshot(user),
                operateTime=datetime.now(timezone.utc),
            ),
        )

    @classmethod
    async def get_log_by_id(cls, mongo_manager: MongoManager, log_id: str) -> LoginLogInfo | None:
        """
        根据日志 ID 查询登录日志。
        """
        try:
            document = await mongo_manager.find_by_id(cls.collection_name, log_id)
        except InvalidId:
            document = await mongo_manager.find_one(cls.collection_name, {"id": log_id})
        if not document:
            return None
        return LoginLogInfo.model_validate(cls._normalize_document(document))

    @classmethod
    async def page_logs(
            cls,
            mongo_manager: MongoManager,
            data: LoginLogPageRequest,
    ) -> PaginatedResponse[LoginLogInfo]:
        """
        分页查询登录日志。
        """
        filters: dict[str, Any] = {}
        if data.user_code:
            filters["user_code"] = data.user_code
        if data.success is not None:
            filters["success"] = data.success
        if data.client_ip:
            filters["client_ip"] = data.client_ip
        if data.start_time or data.end_time:
            time_filter: dict[str, Any] = {}
            if data.start_time:
                time_filter["$gte"] = data.start_time
            if data.end_time:
                time_filter["$lte"] = data.end_time
            filters["operate_time"] = time_filter

        skip = (data.page_index - 1) * data.page_size
        total = await mongo_manager.count(cls.collection_name, filters)
        documents = await mongo_manager.find_many(
            cls.collection_name,
            filters,
            sort=[("_id", DESCENDING)],
            skip=skip,
            limit=data.page_size,
        )
        return PaginatedResponse(
            items=[LoginLogInfo.model_validate(cls._normalize_document(item)) for item in documents],
            total=total,
            has_next=data.page_index * data.page_size < total,
        )

    @classmethod
    async def delete_log(cls, mongo_manager: MongoManager, log_id: str) -> bool:
        """
        删除单条登录日志。
        """
        try:
            filter_ = {"_id": ObjectId(log_id)}
        except InvalidId:
            filter_ = {"id": log_id}
        result = await mongo_manager.delete_one(cls.collection_name, filter_)
        return result.deleted_count > 0
