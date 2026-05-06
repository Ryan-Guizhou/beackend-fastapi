#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: tasks.py
@Create: 2026/5/5 14:04
@Desc: 调度任务函数定义
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger("app")


async def _log_task_start(task_name: str, job_code: str | None) -> None:
    """
    记录任务开始执行日志。
    Args:
        task_name: 任务函数名称。
        job_code: 调度任务编码。
    Returns:
        无。
    """
    logger.info("[%s] %s started at %s", job_code, task_name, datetime.now())


async def _log_task_end(task_name: str, job_code: str | None, result: str) -> str:
    """
    记录任务结束执行日志并返回结果。
    Args:
        task_name: 任务函数名称。
        job_code: 调度任务编码。
        result: 任务执行结果描述。
    Returns:
        str: 原始任务执行结果描述。
    """
    logger.info("[%s] %s finished at %s", job_code, task_name, datetime.now())
    return result


async def test_task(job_code: str | None = None, word: str | None = None, **kwargs) -> str:
    """
    Cron 示例测试任务。
    Args:
        job_code: 调度任务编码。
        word: 自定义测试文本。
        **kwargs: 其他扩展参数。
    Returns:
        str: 任务执行结果描述。
    """
    await _log_task_start("test_task", job_code)
    await asyncio.sleep(1)
    result = f"cron task executed successfully, word={word}, time={datetime.now()}"
    return await _log_task_end("test_task", job_code, result)


async def interval_task(job_code: str | None = None, seconds: int = 5, **kwargs) -> str:
    """
    Interval 示例测试任务。
    Args:
        job_code: 调度任务编码。
        seconds: 当前任务配置的执行间隔秒数，仅用于日志展示。
        **kwargs: 其他扩展参数。
    Returns:
        str: 任务执行结果描述。
    """
    await _log_task_start("interval_task", job_code)
    await asyncio.sleep(1)
    result = (
        f"interval task executed successfully, interval_seconds={seconds}, "
        f"time={datetime.now()}"
    )
    return await _log_task_end("interval_task", job_code, result)


async def date_task(job_code: str | None = None, remark: str | None = None, **kwargs) -> str:
    """
    Date 示例一次性测试任务。
    Args:
        job_code: 调度任务编码。
        remark: 一次性任务备注信息。
        **kwargs: 其他扩展参数。
    Returns:
        str: 任务执行结果描述。
    """
    await _log_task_start("date_task", job_code)
    await asyncio.sleep(1)
    result = f"date task executed successfully, remark={remark}, time={datetime.now()}"
    return await _log_task_end("date_task", job_code, result)
