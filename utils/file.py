#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: file.py
@Create: 2026/4/16 22:14
@Desc: 文件路径工具
"""
from pathlib import Path


def get_base_dir() -> str:
    """
    获取项目根目录。

    Returns:
        str: 当前项目的根目录路径。
    """
    path = Path(__file__).resolve().parent.parent
    return path


def get_file_path(filePath: str) -> str:
    """
    获取指定文件的完整路径。

    Args:
        filePath: 相对于项目根目录的文件路径。

    Returns:
        str: 拼接后的完整文件路径。
    """
    return f"{get_base_dir()}/{filePath}"
