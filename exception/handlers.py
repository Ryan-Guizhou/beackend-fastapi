#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: handlers.py
@Create: 2026/4/18 00:20
@Desc: 全局异常处理器
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette import status

from base.base_schema import Response
from exception.errors import BusinessException, ValidationException


def register_exception_handlers(app: FastAPI) -> None:
    """
    注册全局异常处理器。

    说明：
        该函数将业务异常、请求参数校验异常以及未知异常统一注册到
        FastAPI 应用中，确保接口错误响应结构保持一致。

    Args:
        app: 当前 FastAPI 应用实例。
    """

    @app.exception_handler(BusinessException)
    async def handle_business_exception(
        request: Request,
        exc: BusinessException,
    ):
        """
        处理业务异常。

        Args:
            request: 当前请求对象。
            exc: 捕获到的业务异常对象。
        """
        return Response.common_failure(
            code=exc.code,
            message=exc.message,
        ).to_http_response(status_code=status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request,
        exc: RequestValidationError,
    ):
        """
        处理请求参数校验异常。

        Args:
            request: 当前请求对象。
            exc: FastAPI 参数校验异常对象。
        """
        wrapped = ValidationException()
        return Response.common_failure(
            code=wrapped.code,
            message=wrapped.message,
            data=exc.errors(),
        ).to_http_response(status_code=status.HTTP_402_PAYMENT_REQUIRED)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ):
        """
        处理未捕获的通用异常。

        Args:
            request: 当前请求对象。
            exc: 未预期异常对象。
        """
        return Response.failure(
            code=500,
            message="Internal server error",
        ).to_http_response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
