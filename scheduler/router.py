#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: router.py
@Create: 2026/5/5 14:04
@Desc: 文件描述
"""

from fastapi import APIRouter
from scheduler.api import router as scheduler_router
from scheduler.api import log_router as log_router

router = APIRouter()
router.include_router(scheduler_router)
router.include_router(log_router)