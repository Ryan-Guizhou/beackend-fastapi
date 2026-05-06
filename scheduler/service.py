#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/5/5 14:04
@Desc: 调度任务服务
"""
import importlib
import inspect
import json
import logging
import os
import socket
import traceback
from dataclasses import fields
from datetime import datetime, timedelta
from typing import Any, List, Dict

from apscheduler import AsyncScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from config.database import AsyncSessionLocal
from scheduler.model import (
    RunStatusChoices,
    SchedulerJob,
    SchedulerLog,
    StatusChoices,
    TriggerTypeEnum,
)

logger = logging.getLogger(__name__)


def _build_trigger(job_obj: SchedulerJob):
    """
    根据任务配置构建触发器。
    Args:
        job_obj: 调度任务 ORM 对象。
    Returns:
        Trigger | None: 构建成功时返回触发器对象，否则返回 `None`。
    """
    try:
        if job_obj.trigger_type == TriggerTypeEnum.CRON.value:
            if not job_obj.cron_expression:
                logger.error("cron expression is empty, job=%s", job_obj.code)
                return None

            parts = job_obj.cron_expression.split()
            if len(parts) != 5:
                logger.error(
                    "invalid cron expression, job=%s, expression=%s",
                    job_obj.code,
                    job_obj.cron_expression,
                )
                return None

            return CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )

        if job_obj.trigger_type == TriggerTypeEnum.INTERVAL.value:
            if not job_obj.interval_seconds or job_obj.interval_seconds <= 0:
                logger.error("invalid interval seconds, job=%s", job_obj.code)
                return None
            return IntervalTrigger(seconds=job_obj.interval_seconds)

        if job_obj.trigger_type == TriggerTypeEnum.DATE.value:
            if not job_obj.run_date:
                logger.error("run_date is empty, job=%s", job_obj.code)
                return None
            return DateTrigger(run_time=job_obj.run_date)

        logger.error("unsupported trigger type: %s", job_obj.trigger_type)
        return None
    except Exception:
        logger.exception("build scheduler trigger failed: %s", job_obj.code)
        return None


def _import_task_func(task_path: str):
    """
    动态导入任务函数。
    Args:
        task_path: 任务函数完整导入路径。
    Returns:
        Callable | None: 导入成功时返回函数对象，否则返回 `None`。
    """
    try:
        module_path, func_name = task_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except Exception:
        logger.exception("import scheduler task function failed: %s", task_path)
        return None


class SchedulerService:
    """
    调度任务服务。
    Args:
        无。
    Returns:
        无。
    """

    _instance = None

    def __new__(cls) -> "SchedulerService":
        """
        获取调度任务服务单例。
        Args:
            无。
        Returns:
            SchedulerService: 调度任务服务单例对象。
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = None
            cls._instance._running = False
        return cls._instance

    def get_scheduler(self) -> AsyncScheduler | None:
        """
        获取当前调度器实例。
        Args:
            无。
        Returns:
            AsyncScheduler | None: 已设置的调度器实例；未初始化时返回 `None`。
        """
        return self._scheduler

    def set_scheduler(self, scheduler: AsyncScheduler) -> None:
        """
        设置调度器实例并标记为运行中。
        Args:
            scheduler: APScheduler 异步调度器实例。
        Returns:
            无。
        """
        self._scheduler = scheduler
        self._running = True

    def is_running(self) -> bool:
        """
        判断调度器是否处于运行状态。
        Args:
            无。
        Returns:
            bool: 调度器已初始化且处于运行状态时返回 `True`，否则返回 `False`。
        """
        return self._running and self._scheduler is not None

    def set_running(self, running: bool) -> None:
        """
        设置调度器运行状态。
        Args:
            running: 是否处于运行中。
        Returns:
            无。
        """
        self._running = running
        if not running:
            self._scheduler = None

    async def load_jobs_from_db(self) -> None:
        """
        从数据库加载所有启用状态的任务到调度器。
        Args:
            无。
        Returns:
            无。
        """
        logger.info("start loading scheduler jobs from database")
        if not self._scheduler:
            logger.warning("scheduler is not initialized, skip loading jobs")
            return

        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SchedulerJob).where(
                        SchedulerJob.status == StatusChoices.ENABLED.value,
                        SchedulerJob.is_deleted.is_(False),
                    )
                )
                jobs = result.scalars().all()

            logger.info("found %s enabled scheduler jobs", len(jobs))
            load_success_count = 0
            load_fail_count = 0

            for job in jobs:
                success = await self.add_job(job)
                if success:
                    load_success_count += 1
                    logger.info("scheduler job loaded: %s", job.code)
                else:
                    load_fail_count += 1
                    logger.warning("scheduler job load failed: %s", job.code)

            await self._start_cleanup_job()
            logger.info(
                "scheduler jobs loaded finished, success=%s, failed=%s",
                load_success_count,
                load_fail_count,
            )
        except Exception:
            logger.exception("load scheduler jobs from database failed")

    async def add_job(self, job_obj: SchedulerJob) -> bool:
        """
        将任务注册到调度器。
        Args:
            job_obj: 调度任务 ORM 对象。
        Returns:
            bool: 注册成功返回 `True`，否则返回 `False`。
        """
        if not self._scheduler:
            logger.error("scheduler is not initialized")
            return False

        trigger = _build_trigger(job_obj)
        if not trigger:
            logger.error("failed to build trigger for job: %s", job_obj.code)
            return False

        task_func = _import_task_func(job_obj.task_func)
        if not task_func:
            logger.error("failed to import task function: %s", job_obj.task_func)
            return False

        try:
            args = json.loads(job_obj.task_args) if job_obj.task_args else []
            kwargs = json.loads(job_obj.task_kwargs) if job_obj.task_kwargs else {}
            if not isinstance(args, list):
                logger.error("task_args must be a JSON array, job=%s", job_obj.code)
                return False
            if not isinstance(kwargs, dict):
                logger.error("task_kwargs must be a JSON object, job=%s", job_obj.code)
                return False

            wrapper_func = self._create_job_wrapper(task_func, job_obj.code, args, kwargs)
            task_id = job_obj.code

            await self._scheduler.configure_task(task_id, func=wrapper_func)
            await self._scheduler.add_schedule(
                func_or_task_id=task_id,
                trigger=trigger,
                id=job_obj.code,
            )
            logger.info("scheduler job added: %s", job_obj.code)
            return True
        except Exception:
            logger.exception("add scheduler job failed: %s", job_obj.code)
            return False

    async def remove_job(self,job_code: str) -> bool:

        """从调度器移除"""
        if not self._scheduler:
            logger.error("scheduler is not initialized")
            return False
        try:
            await self._scheduler.remove_schedule(job_code)
            logger.info(f"任务{job_code}已从调度器移除")
            return True
        except Exception as e:
            logger.error(f"移除任务失败{job_code}:{str(e)}")
            return False

    async def run_job_now(self,job_code: str) -> bool:
        if self._scheduler:
            return False

        try:
            from sqlalchemy import select
            from config.database import AsyncSessionLocal
            from scheduler.model import SchedulerJob

            async with AsyncSessionLocal as db:
                result = await db.execute(
                    select(SchedulerJob).where(
                        SchedulerJob.code == job_code,SchedulerJob.is_deleted.is_(False)
                    )
                )
                job_obj = result.scalar_one_or_none()
                if job_obj:
                    # 解析参数
                    args = json.loads(job_obj.task_args) if job_obj.task_args else []
                    kwargs = json.loads(job_obj.task_kwargs) if job_obj.task_kwargs else {}
                    kwargs['job_code'] = job_obj.code

                    # 导入并执行任务函数
                    task_func = _import_task_func(job_obj.task_func)
                    if task_func:
                        await self._execute_job(task_func,job_code,args,kwargs)
                        logger.info(f"任务{job_code}已立即执行")
                        return True
            return False
        except Exception as e:
            logger.exception(f"立即执行任务失败 {job_code}:{str(e)} ")
            return False

    async def get_all_jobs(self) -> List[Dict[str,Any]]:
        if not self._scheduler:
            return []
        try:
            schedulers = await self._scheduler.get_schedules()
            return [{
                'id': scheduler.id,
                'next_run_time': scheduler.next_fire_time.isoformat() if scheduler.next_fire_time else None,
                'trigger': str(scheduler.trigger)
            } for scheduler in schedulers
            ]
        except Exception as e:
            logger.error(f"获取所有任务失败:{str(e)}")
            return []

    def _create_job_wrapper(
        self,
        task_func,
        job_code: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ):
        """
        为任务函数创建统一的执行包装器。
        Args:
            task_func: 实际任务函数对象。
            job_code: 任务编码。
            args: 任务位置参数列表。
            kwargs: 任务关键字参数字典。
        Returns:
            Callable: 可注册到调度器的异步包装函数。
        """

        async def wrapper() -> Any:
            return await self._execute_job(task_func, job_code, args, kwargs)

        return wrapper

    async def _execute_job(
        self,
        task_func,
        job_code: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        """
        执行任务并记录执行日志。
        Args:
            task_func: 实际任务函数对象。
            job_code: 任务编码。
            args: 任务位置参数列表。
            kwargs: 任务关键字参数字典。
        Returns:
            Any: 任务函数执行结果。
        """
        start_time = datetime.now()
        exception_info: Exception | None = None
        result: Any = None

        try:
            execution = task_func(*args, **kwargs)
            if inspect.isawaitable(execution):
                result = await execution
            else:
                result = execution
        except Exception as exc:
            exception_info = exc
            logger.exception("scheduler job execute failed: %s", job_code)

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        try:
            async with AsyncSessionLocal() as db:
                query_result = await db.execute(
                    select(SchedulerJob).where(SchedulerJob.code == job_code)
                )
                job_obj = query_result.scalar_one_or_none()

                if job_obj:
                    status = (
                        RunStatusChoices.FAILURE.value
                        if exception_info
                        else RunStatusChoices.SUCCESS.value
                    )
                    log = SchedulerLog(
                        job_id=job_obj.id,
                        job_name=job_obj.name,
                        job_code=job_obj.code,
                        trigger_type=job_obj.trigger_type,
                        status=status,
                        retry_count=0,
                        run_time=start_time,
                        end_time=end_time,
                        duration_ms=duration_ms,
                        result=None if result is None else str(result),
                        exception=None if exception_info is None else str(exception_info),
                        traceback=None if exception_info is None else traceback.format_exc(),
                        hostname=socket.gethostname(),
                        process_id=os.getpid(),
                    )

                    job_obj.last_run_status = status
                    job_obj.last_run_result = (
                        str(exception_info) if exception_info else None if result is None else str(result)
                    )
                    job_obj.total_run_count += 1
                    job_obj.last_run_time = end_time

                    if exception_info:
                        job_obj.failure_count += 1
                    else:
                        job_obj.success_count += 1

                    db.add(log)
                    await db.commit()

                    if job_obj.trigger_type == TriggerTypeEnum.DATE.value:
                        await self._cleanup_one_time_job(db, job_obj)
        except Exception as e:
            logger.exception("record scheduler job log failed: %s", job_code)

        if exception_info:
            raise exception_info
        return result

    async def _cleanup_one_time_job(self, db, job_obj: SchedulerJob) -> None:
        """
        清理已执行完成的一次性任务。
        Args:
            db: 当前数据库会话。
            job_obj: 调度任务 ORM 对象。
        Returns:
            无。
        """
        try:
            if self._scheduler:
                try:
                    await self._scheduler.remove_schedule(job_obj.code)
                except Exception:
                    logger.exception("remove one-time schedule failed: %s", job_obj.code)

            job_obj.is_deleted = True
            await db.commit()
            logger.debug("one-time scheduler job cleaned: %s", job_obj.code)
        except Exception:
            logger.exception("cleanup one-time job failed: %s", job_obj.code)

    async def _start_cleanup_job(self) -> None:
        """
        启动定期清理过期一次性任务的调度任务。
        Args:
            无。
        Returns:
            无。
        """
        if not self._scheduler:
            return

        cleanup_job_id = "_scheduler_cleanup"
        await self._scheduler.configure_task(
            cleanup_job_id,
            func=self._cleanup_expired_jobs_wrapper,
        )
        await self._scheduler.add_schedule(
            func_or_task_id=cleanup_job_id,
            trigger=CronTrigger(hour=3, minute=0),
            id=cleanup_job_id,
        )
        logger.info("scheduler cleanup job started")

    async def _cleanup_expired_jobs_wrapper(self) -> None:
        """
        清理过期一次性任务的包装函数。
        Args:
            无。
        Returns:
            无。
        """
        await self._cleanup_expired_jobs(days=7)

    async def _cleanup_expired_jobs(self, days: int = 7) -> int:
        """
        清理过期的一次性任务。
        Args:
            days: 删除多少天之前已过期的一次性任务。
        Returns:
            int: 本次清理的任务数量。
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(SchedulerJob).where(
                        SchedulerJob.trigger_type == TriggerTypeEnum.DATE.value,
                        SchedulerJob.run_date < cutoff,
                        SchedulerJob.is_deleted.is_(False),
                    )
                )
                expired_jobs = result.scalars().all()

                for job in expired_jobs:
                    if self._scheduler:
                        try:
                            await self._scheduler.remove_schedule(job.code)
                        except Exception:
                            logger.exception(
                                "remove expired schedule failed: %s",
                                job.code,
                            )
                    job.is_deleted = True

                await db.commit()
                if expired_jobs:
                    logger.info("expired one-time jobs cleaned: %s", len(expired_jobs))
                return len(expired_jobs)
        except Exception:
            logger.exception("cleanup expired scheduler jobs failed")
            return 0


scheduler_service = SchedulerService()
