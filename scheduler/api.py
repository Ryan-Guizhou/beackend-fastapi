#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: api.py
@Create: 2026/5/5 14:04
@Desc: 调度任务接口定义
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import func, select
from base.base_schema import Response, PaginatedResponse
from config.database import DbSession
from scheduler.model import (
    SchedulerJob,
    SchedulerLog,
    StatusChoices,
    RunStatusChoices
)
from scheduler.schema import (
    SchedulerJobCreate,
    SchedulerSearch,
    SchedulerJobBatchDeleteIn,
    SchedulerJobBatchDeleteOut,
    SchedulerJobBatchUpdateStatusIn,
    SchedulerJobBatchUpdateStatusOut,
    SchedulerLogSearch,
    SchedulerLogDelete,
    SchedulerLogClean,
    SchedulerJobStatistics
)

from scheduler.service import scheduler_service

router = APIRouter(prefix="/scheduler", tags=["定时任务管理"])

logger = logging.getLogger(__name__)

def _build_job_response(job: SchedulerJob) -> dict[str, Any]:
    """
    构建调度任务响应数据。
    Args:
        job: 调度任务 ORM 对象。
    Returns:
        dict[str, Any]: 面向接口返回的任务信息字典。
    """
    return {
        "id": job.id,
        "name": job.name,
        "code": job.code,
        "description": job.description,
        "triggerType": job.trigger_type,
        "cronExpression": job.cron_expression,
        "intervalSeconds": job.interval_seconds,
        "runDate": job.run_date,
        "taskFunc": job.task_func,
        "taskArgs": job.task_args,
        "taskKwargs": job.task_kwargs,
        "status": job.status,
        "priority": job.priority,
        "maxInstances": job.max_instances,
        "maxRetries": job.max_retries,
        "retryIntervalSeconds": job.retry_interval_seconds,
        "timeout": job.timeout,
        "coalesce": job.coalesce,
        "allowConcurrent": job.allow_concurrent,
        "totalRunCount": job.total_run_count,
        "successCount": job.success_count,
        "failureCount": job.failure_count,
        "lastRunTime": job.last_run_time,
        "nextRunTime": job.next_run_time,
        "lastRunStatus": job.last_run_status,
        "lastRunResult": job.last_run_result,
        "remark": job.remark,
        "createTime": job.create_time,
        "modifyTime": job.modify_time,
        "statusDisplay": job.get_status_display(),
    }


def _build_log_response(log: SchedulerLog) -> dict[str, Any]:
    """
    构建调度日志响应数据。
    Args:
        log: 调度日志 ORM 对象。
    Returns:
        dict[str, Any]: 面向接口返回的日志信息字典。
    """
    return {
        "id": log.id,
        "jobId": log.job_id,
        "jobName": log.job_name,
        "jobCode": log.job_code,
        "triggerType": log.trigger_type,
        "status": log.status,
        "statusDisplay": log.get_status_display(),
        "retryCount": log.retry_count,
        "runTime": log.run_time,
        "endTime": log.end_time,
        "durationMs": log.duration_ms,
        "result": log.result,
        "exception": log.exception,
        "traceback": log.traceback,
        "hostname": log.hostname,
        "processId": log.process_id,
        "remark": log.remark,
        "createTime": log.create_time,
        "modifyTime": log.modify_time,
    }


@router.post("/job", response_model=Response, summary="创建定时任务")
async def create_scheduler_job(
    db: DbSession,
    data: SchedulerJobCreate,
) -> Response:
    """
    创建定时任务。
    Args:
        db: 数据库会话。
        data: 定时任务创建请求数据。
    Returns:
        Response: 创建结果响应对象。
    """
    result = await db.execute(
        select(SchedulerJob).where(
            SchedulerJob.code == data.code,
            SchedulerJob.is_deleted.is_(False),
        )
    )
    if result.scalar_one_or_none():
        return Response.failure(msg=f"任务编码已存在: {data.code}")

    payload = data.model_dump(exclude_none=True)
    payload.pop("group", None)
    job = SchedulerJob(**payload)
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if job.is_enabled() and scheduler_service.is_running():
        await scheduler_service.add_job(job)

    return Response.success(
        msg="添加定时任务成功",
        data=_build_job_response(job),
    )


@router.get("/job/all", response_model=Response, summary="获取所有定时任务(简化版)")
async def get_all_scheduler_job(
    db: DbSession,
) -> Response:
    """
    获取所有未删除的定时任务。
    Args:
        db: 数据库会话。
    Returns:
        Response: 包含任务列表的统一响应对象。
    """
    result = await db.execute(
        select(SchedulerJob)
        .where(SchedulerJob.is_deleted.is_(False))
        .order_by(SchedulerJob.priority.desc(), SchedulerJob.modify_time.desc())
    )
    jobs = result.scalars().all()
    return Response.success(
        data=[{
            "id": job.id,
            "name": job.name,
            "code": job.code,
            "triggerType": job.trigger_type,
            "status": job.status,
            "statusDisplay": job.get_status_display(),
        } for job in jobs]
    )


@router.get("/job/page_list", response_model=Response, summary="获取定时任务列表")
async def get_scheduler_job_list(
    db: DbSession,
    data: Annotated[SchedulerSearch, Depends()],
) -> Response:
    """
    分页获取定时任务列表。
    Args:
        db: 数据库会话。
        data: 定时任务分页查询参数。
    Returns:
        Response: 包含分页任务列表的统一响应对象。
    """
    filters = [SchedulerJob.is_deleted.is_(False)]
    if data.name:
        filters.append(SchedulerJob.name.ilike(f"%{data.name}%"))
    if data.code:
        filters.append(SchedulerJob.code.ilike(f"%{data.code}%"))
    if data.trigger_type:
        filters.append(SchedulerJob.trigger_type == data.trigger_type)
    if data.status is not None:
        filters.append(SchedulerJob.status == data.status)

    count_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(*filters)
    )
    total = count_result.scalar() or 0

    offset = (data.page_index - 1) * data.page_size
    result = await db.execute(
        select(SchedulerJob)
        .where(*filters)
        .order_by(SchedulerJob.priority.desc(), SchedulerJob.modify_time.desc())
        .offset(offset)
        .limit(data.page_size)
    )
    jobs = result.scalars().all()

    return Response.success(
        data={
            "items": [_build_job_response(job) for job in jobs],
            "total": total,
        }
    )


@router.delete("/job/batch_delete",response_model=Response,summary="批量删除定时任务")
async def batch_delete_scheduler_job(
    db: DbSession,
    data: SchedulerJobBatchDeleteIn
) -> Response:
    success_count = 0
    failed_count = []

    for job_id in data.ids:
        try:
            result = await db.execute(
                select(SchedulerJob).where(
                    SchedulerJob.id == job_id,SchedulerJob.is_deleted.is_(False),
                )
            )
            job = result.scalar_one_or_none()
            if job:
                if scheduler_service.is_running():
                    await scheduler_service.remove_job(job.code)
                job.is_deleted = True
                job.modify_time = datetime.now()
                success_count += 1

            else:
                logger.info("scheduler job missing or deleted: %s", job_id)
                failed_count.append(job_id)
        except Exception:
            logger.exception("batch delete scheduler job failed: %s", job_id)
            failed_count.append(job_id)
    await db.commit()
    return Response.success(
        data=SchedulerJobBatchDeleteOut(count=success_count,failed_ids=failed_count)
    )


@router.post("/job/batch/update_status",response_model=Response,summary="批量更新任务状态")
async def batch_update_scheduler_job_status(
        db: DbSession,
        data: SchedulerJobBatchUpdateStatusIn
) -> Response:
    result = await db.execute(
        select(SchedulerJob).where(
            SchedulerJob.id.in_(data.ids),
            SchedulerJob.is_deleted.is_(False),
        )
    )

    scheduler_job_list = result.scalars().all()
    if len(scheduler_job_list) == 0:
        return Response.success(
            data=SchedulerJobBatchUpdateStatusOut()
        )

    count = 0
    for scheduler_job in scheduler_job_list:
        scheduler_job.status = data.status
        count += 1

        if scheduler_service.is_running():
            if scheduler_job.is_enabled():
                await scheduler_service.add_job(scheduler_job)
            elif scheduler_job.is_paused():
                await scheduler_service.pause_job(scheduler_job.code)
            else:
                await scheduler_service.remove_job(scheduler_job.code)

    await db.commit()
    return Response.success(
        data=SchedulerJobBatchUpdateStatusOut(count=count)
    )


@router.get("/{job_id}",response_model=Response,summary="获取任务详细信息")
async def get_scheduler_job(
        db: DbSession,
        job_id: Annotated[str,Path(...,description="任务ID")]
) -> Response:
    result = await db.execute(
        select(SchedulerJob).where(
            SchedulerJob.id == job_id,
            SchedulerJob.is_deleted.is_(False),
        )
    )

    job = result.scalar_one_or_none()

    if not job:
        return Response.failure()
    return Response.success(
        data=_build_job_response(job)
    )

@router.get("/statistics/data",response_model=Response,summary="获取任务统计信息")
async def get_scheduler_job_statistics(
        db: DbSession
) -> Response:

    total_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(
            SchedulerJob.is_deleted.is_(False),
        )
    )

    total_jobs = total_result.scalar() or 0

    enabled_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(
            SchedulerJob.is_deleted.is_(False),
            SchedulerJob.status == StatusChoices.ENABLED.value
        )
    )

    enabled_jobs = enabled_result.scalar() or 0

    disabled_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(
            SchedulerJob.is_deleted.is_(False),
            SchedulerJob.status == StatusChoices.DISABLED.value
        )
    )

    disabled_jobs = disabled_result.scalar() or 0

    paused_result = await db.execute(
        select(func.count(SchedulerJob.id)).where(
            SchedulerJob.is_deleted.is_(False),
            SchedulerJob.status == StatusChoices.PAUSED.value
        )
    )

    paused_jobs = paused_result.scalar() or 0

    # 执行统计
    total_exec_result = await db.execute(
        select(func.count(SchedulerLog.id))
    )
    total_executions = total_exec_result.scalar() or 0

    success_exec_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(
            SchedulerLog.status == RunStatusChoices.SUCCESS.value,
        )
    )
    success_executions = success_exec_result.scalar() or 0

    failed_exec_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(
            SchedulerLog.status == RunStatusChoices.SUCCESS.value,
        )
    )
    failed_executions = failed_exec_result.scalar() or 0

    # 计算成功率
    success_rate = round(success_executions / total_executions * 100, 2) if total_executions > 0 else 0

    return Response.success(
        data=SchedulerJobStatistics(
            total_jobs=total_jobs,
            enabled_jobs=enabled_jobs,
            disabled_jobs=disabled_jobs,
            paused_jobs=paused_jobs,
            total_executions=total_executions,
            success_executions=success_executions,
            failed_executions=failed_executions,
            success_rate=success_rate,
        )
    )


@router.post("/job/execute/{job_id}",response_model=Response,summary="立即执行任务")
async def execute_scheduler_job(
        db: DbSession,
        job_id = Annotated[str,Path(...,description="任务ID")],
) -> Response:
    result = await db.execute(
        select(SchedulerJob).where(
            SchedulerJob.id == job_id,
            SchedulerJob.is_deleted.is_(False),
        )
    )

    scheduler_job = result.scalar_one_or_none()
    if not scheduler_job:
        return Response.failure(f"任务不存在:{job_id}");

    if not scheduler_service.is_running():
        return Response.failure("调度器未初始化")

    success = await scheduler_service.run_job_now(scheduler_job.code)

    if success:
        return Response.success(
            data=True,
            messages=f"任务{scheduler_job.name}将立即执行"
        )
    else:
        return Response.failure(
            data=False,
            messages=f"任务{scheduler_job.name}执行失败,可能任务未在调度器中"
        )


# ==================== SchedulerLog APIs ====================

log_router = APIRouter(prefix="/log",tags=["定时任务执行日志管理"])

@log_router.get("/page_list",response_model=Response,summary="获取任务执行日志列表")
async def get_scheduler_log_list(
        db: DbSession,
        data: Annotated[SchedulerLogSearch,Depends()],
) -> Response:
    """
    分页获取任务执行日志列表。
    Args:
        db: 数据库会话。
        data: 调度日志分页查询参数。
    Returns:
        Response: 包含分页日志列表的统一响应对象。
    """
    filters = [SchedulerLog.is_deleted.is_(False)]
    if data.job_id:
        filters.append(SchedulerLog.job_id == data.job_id)
    if data.job_code:
        filters.append(SchedulerLog.job_code == data.job_code)
    if data.job_name:
        filters.append(SchedulerLog.job_name.ilike(f"%{data.job_name}%"))
    if data.status:
        filters.append(SchedulerLog.status == data.status)
    if data.start_time:
        filters.append(SchedulerLog.run_time >= data.start_time)
    if data.end_time:
        filters.append(SchedulerLog.run_time <= data.end_time)

    count_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(*filters)
    )
    total = count_result.scalar() or 0

    offset = (data.page_index - 1) * data.page_size
    query = (
        select(SchedulerLog)
        .where(*filters)
        .order_by(SchedulerLog.run_time.desc())
        .offset(offset)
        .limit(data.page_size)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    has_next = data.page_index * data.page_size < total
    return Response.success(
        data=PaginatedResponse(
            items=[_build_log_response(log) for log in logs],
            total=total,
            has_next=has_next
        )
    )


@log_router.get("/by_job/{job_id}",response_model=Response,summary="获取指定任务的执行日志")
async def get_scheduler_logs_by_job(
        db: DbSession,
        job_id: Annotated[str,Path(...,description="任务ID")],
        page_size: Annotated[int,Query(...,ge=20,description="分页大小")],
        page_index: Annotated[int,Query(...,ge=1,description="第几页")]
) -> Response:

    count_result = await db.execute(
        select(func.count(SchedulerLog.id)).where(
            SchedulerLog.job_id == job_id,
            SchedulerLog.is_deleted.is_(False),
        )
    )

    total = count_result.scalar() or 0

    result = await db.execute(
        select(SchedulerLog).where(
            SchedulerLog.job_id == job_id,
            SchedulerLog.is_deleted.is_(False)
        ).order_by(SchedulerLog.run_time.desc())
        .offset((page_index - 1) * page_size)
        .limit(page_size)
    )

    logs = result.scalars().all()

    has_next = page_index * page_size < total

    return Response.success(
        data=PaginatedResponse(
            items=[_build_log_response(log) for log in logs],
            total=total,
            has_next=has_next
        )
    )


@log_router.get("/{log_id}",response_model=Response,summary="获取任务详情")
async def get_scheduler_log(
        db: DbSession,
        log_id: Annotated[str,Path(...,description="日志ID")]
) -> Response:
    result = await db.execute(
        select(SchedulerLog).where(
            SchedulerLog.id == log_id,
            SchedulerLog.is_deleted.is_(False),
        )
    )

    log = result.scalar_one_or_none()

    if not log:
        return Response.failure()

    return Response.success(
        data=[_build_log_response(log)]
    )


@log_router.delete("/batch/delete",response_model=Response,summary="批量删除执行日志")
async def batch_delete_scheduler(
        db: DbSession,
        data: SchedulerLogDelete
) -> Response:
    result = await db.execute(
        select(SchedulerLog).where(
            SchedulerLog.id.in_(data.ids),
            SchedulerLog.is_deleted.is_(False),
        )
    )

    logs = result.scalars().all()

    if not logs:
        return Response.failure()

    for log in logs:
        log.is_deleted = 1
    await db.commit()
    return Response.success()



@log_router.delete("/{log_id}", response_model=Response, summary="删除执行日志")
async def delete_scheduler(
        db: DbSession,
        log_id: Annotated[str,Path(...,description="执行日志ID")]
) -> Response:
    result = await db.execute(
        select(SchedulerLog).where(
            SchedulerLog.id == log_id,
            SchedulerLog.is_deleted.is_(False),
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        return Response.failure()
    log.is_deleted = 1
    await db.commit()
    return Response.success(msg="批量删除日志成功")


@log_router.post("/clean",response_model=Response,summary="清理旧日志")
async def clean_scheduler_logs(
        db: DbSession,
        data: SchedulerLogClean
) -> Response:

    cutoff_date = datetime.now() - timedelta(days=data.days)

    filters = [SchedulerLog.run_time < cutoff_date, SchedulerLog.is_deleted.is_(False)]
    if data.status:
        filters.append(SchedulerLog.status == data.status)
    result = await db.execute(
        select(SchedulerLog).where(*filters)
    )

    logs = result.scalars().all()
    count = 0

    for log in logs:
        log.is_deleted = 1
        count += 1
    await db.commit()
    return Response.success(
        data=count
    )


@router.get("/status",response_model=Response,summary="获取调度器状态")
async def get_scheduler_status() -> Response:
    is_running = scheduler_service.is_running()
    jobs = await scheduler_service.get_all_jobs() if is_running else []
    return Response.success(
        data=jobs
    )
