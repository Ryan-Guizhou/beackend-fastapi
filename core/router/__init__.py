#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: __init__.py
@Create: 2026/5/10 13:14
@Desc: 核心业务总路由
"""

from fastapi import APIRouter

from core.application.api import router as application_router
from core.auth.api import router as auth_router
from core.auth_log.api import router as auth_log_router
from core.dict.api import router as dict_router
from core.dict_item.api import router as dict_item_router
from core.function.api import router as function_router
from core.login_log.api import router as login_log_router
from core.menu.api import router as menu_router
from core.redis_manager.api import router as redis_router
from core.resource.api import router as resource_router
from core.role.api import router as role_router
from core.router.api import router as frontend_router
from core.user.api import router as user_router

router = APIRouter()

router.include_router(redis_router)
router.include_router(auth_router)
router.include_router(dict_router)
router.include_router(dict_item_router)
router.include_router(application_router)
router.include_router(auth_log_router)
router.include_router(login_log_router)
router.include_router(user_router)
router.include_router(role_router)
router.include_router(function_router)
router.include_router(menu_router)
router.include_router(frontend_router)
router.include_router(resource_router)
