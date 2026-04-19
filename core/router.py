#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: router.py
@Create: 2026/4/17 21:59
@Desc: 核心业务总路由
"""
from fastapi import APIRouter

from core.redis_manager.api import router as redis_router
from core.datasource_manager.api import router as datasource_router


# 核心业务模块的统一路由入口
router = APIRouter()

router.include_router(redis_router)