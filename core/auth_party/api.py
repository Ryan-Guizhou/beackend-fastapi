#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/10 13:22
@Desc: 文件描述
"""
import logging

from fastapi import APIRouter, Depends, Path

from base.base_schema import Response


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/auth_party', tags=['角色授权管理'])

# @router.post('', response_model=Response)
# async def
