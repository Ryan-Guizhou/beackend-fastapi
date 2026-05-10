#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/4/18 17:55
@Desc: 文件描述
"""

import logging

from fastapi import APIRouter

from base.base_schema import Response
from core.datasource_manager.service import AsyncDatabaseManagerService

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/datasource_manager",tags=["数据库管理"])

@router.get("/configs",response_model=Response,summary="获取数据库配置列表")
async def get_database_config():
    result = AsyncDatabaseManagerService.get_database_configs()
    return Response.success(data=result)

@router.post("/{db_name}/test",response_model=Response,summary="测试数据库连接")
async def test_database_connection(db_name: str) -> Response:
    service = AsyncDatabaseManagerService(db_name)
    result = await service.test_connection()
    return Response.success(data=result)
