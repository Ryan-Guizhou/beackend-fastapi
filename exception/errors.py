#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: errors.py
@Create: 2026/4/18 00:20
@Desc: 自定义异常定义
"""
from base.base_schema import ErrorCode


class BusinessException(Exception):
    """
    业务异常基类。

    说明：
        该异常用于统一封装业务场景中的错误信息和错误码，
        便于在全局异常处理器中转换为标准响应格式。
    """

    def __init__(
        self,
        message: str,
        code: int = ErrorCode.FAILURE,
    ) -> None:
        """
        初始化业务异常。

        Args:
            message: 业务异常提示信息。
            code: 业务异常对应的错误码。
        """
        super().__init__(message)
        self.message = message
        self.code = int(code)


class ValidationException(BusinessException):
    """
    参数校验异常。

    说明：
        该异常用于标记请求参数、表单或业务输入校验失败的场景。
    """

    def __init__(
        self,
        message: str = "Request validation failed",
        code: int = ErrorCode.VALIDATE_ERROR,
    ) -> None:
        """
        初始化参数校验异常。

        Args:
            message: 校验失败提示信息。
            code: 校验失败对应的错误码。
        """
        super().__init__(
            message=message,
            code=code,
        )


class UnauthorizedException(BusinessException):
    """
    未授权异常。

    说明：
        该异常用于用户未登录、令牌无效或权限认证失败的场景。
    """

    def __init__(
        self,
        message: str = "Unauthorized",
        code: int = ErrorCode.AUTH_FAILURE,
    ) -> None:
        """
        初始化未授权异常。

        Args:
            message: 未授权提示信息。
            code: 未授权对应的错误码。
        """
        super().__init__(
            message=message,
            code=code,
        )
