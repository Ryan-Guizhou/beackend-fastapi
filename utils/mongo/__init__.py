#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: __init__.py
@Create: 2026/5/9
@Desc: Mongo 工具包初始化
"""

from utils.mongo.mongo_manager import ASCENDING, DESCENDING, MongoManager

__all__ = [
    "ASCENDING",
    "DESCENDING",
    "MongoManager",
]
