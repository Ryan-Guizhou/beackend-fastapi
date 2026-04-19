#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: router.py
@Create: 2026/4/17 22:06
@Desc: 演示模块总路由
"""
from fastapi import APIRouter

from demo.custom.api import router as custom_router


# 演示模块统一路由入口
router = APIRouter()

# 注册自定义演示路由
router.include_router(custom_router)
