#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: schema.py
@Create: 2026/5/5 14:04
@Desc: 文件描述
"""

from datetime import datetime
from typing import Optional, List
from pydantic import field_validator,Field

from base.base_schema import PaginatedRequest, ApiInSchema, ApiOutSchema


class SchedulerJobBase(ApiInSchema):
    """定时任务基础Schema"""
    name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    code: str = Field(..., min_length=1, max_length=128, description="任务编码")
    description: Optional[str] = Field(None, description="任务描述")
    group: str = Field(default="default", max_length=64, description="任务分组")
    trigger_type: str = Field(..., description="触发器类型：cron/interval/date")
    cron_expression: Optional[str] = Field(None, max_length=128, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔时间（秒）")
    run_date: Optional[datetime] = Field(None, description="指定执行时间")
    task_func: str = Field(..., max_length=256, description="任务函数路径")
    task_args: Optional[str] = Field(None, description="任务位置参数（JSON）")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数（JSON）")
    status: int = Field(default=0, description="任务状态：0-禁用，1-启用，2-暂停")
    priority: int = Field(default=0, description="任务优先级")
    max_instances: int = Field(default=1, ge=1, description="最大实例数")
    max_retries: int = Field(default=0, ge=0, description="错误重试次数")
    retry_interval_seconds: int = Field(None, ge=0, description="重试间隔时间")
    timeout: Optional[int] = Field(None, ge=1, description="超时时间（秒）")
    coalesce: bool = Field(default=True, description="是否合并执行")
    allow_concurrent: bool = Field(default=False, description="是否允许并发执行")
    remark: Optional[str] = Field(None, description="备注信息")


    @field_validator('trigger_type')
    @classmethod
    def validate_trigger_type(cls,v):
        if v not in ['cron', 'interval', 'date']:
            raise ValueError('触发器类型必须是 cron、interval或date')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls,v):
        if v not in [0,1,2]:
            raise ValueError('状态必须是0(禁用),1(启用),2(暂停)')

    @field_validator('code')
    @classmethod
    def validate_code(cls,v):
        if not v:
            raise ValueError('任务编码不能为空')
        if not v.replace('_','').isalnum():
            raise ValueError('任务编码只能包含字母、数字和下划线')
        return v


class SchedulerJobCreate(SchedulerJobBase):
    """定时任务创建Schema"""

    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v, info):
        """验证 Cron 表达式"""
        if info.data.get('trigger_type') == 'cron' and not v:
            raise ValueError('Cron 类型任务必须提供 cron_expression')
        return v

    @field_validator('interval_seconds')
    @classmethod
    def validate_interval_seconds(cls, v, info):
        """验证间隔时间"""
        if info.data.get('trigger_type') == 'interval' and not v:
            raise ValueError('Interval 类型任务必须提供 interval_seconds')
        return v

    @field_validator('run_date')
    @classmethod
    def validate_run_date(cls, v, info):
        """验证指定时间"""
        if info.data.get('trigger_type') == 'date' and not v:
            raise ValueError('Date 类型任务必须提供 run_date')
        return v


class SchedulerJobUpdate(ApiInSchema):
    """定时任务更新Schema - 所有字段可选"""
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="任务名称")
    code: Optional[str] = Field(None, min_length=1, max_length=128, description="任务编码")
    description: Optional[str] = Field(None, description="任务描述")
    group: Optional[str] = Field(None, max_length=64, description="任务分组")
    trigger_type: Optional[str] = Field(None, description="触发器类型")
    cron_expression: Optional[str] = Field(None, max_length=128, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔时间（秒）")
    run_date: Optional[datetime] = Field(None, description="指定执行时间")
    task_func: Optional[str] = Field(None, max_length=256, description="任务函数路径")
    task_args: Optional[str] = Field(None, description="任务位置参数（JSON）")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数（JSON）")
    status: Optional[int] = Field(None, description="任务状态")
    priority: Optional[int] = Field(None, description="任务优先级")
    max_instances: Optional[int] = Field(None, ge=1, description="最大实例数")
    max_retries: Optional[int] = Field(None, ge=0, description="错误重试次数")
    retry_interval_seconds: int = Field(None, ge=0, description="重试间隔时间")
    timeout: Optional[int] = Field(None, ge=1, description="超时时间（秒）")
    coalesce: Optional[bool] = Field(None, description="是否合并执行")
    allow_concurrent: Optional[bool] = Field(None, description="是否允许并发执行")
    remark: Optional[str] = Field(None, description="备注信息")

class SchedulerJobStatistics(ApiOutSchema):
    """任务统计输出"""
    total_jobs: int = Field(..., description="总任务数")
    enabled_jobs: int = Field(..., description="启用任务数")
    disabled_jobs: int = Field(..., description="禁用任务数")
    paused_jobs: int = Field(..., description="暂停任务数")
    total_executions: int = Field(..., description="总执行次数")
    success_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    success_rate: float = Field(..., description="成功率")

class SchedulerSearch(PaginatedRequest):
    code: Optional[str] = Field(None, min_length=1, max_length=128, description="任务编码")
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="任务名称")
    trigger_type: Optional[str] = Field(None, description="触发器类型")
    status: Optional[int] = Field(None, description="任务状态")


class SchedulerJobBatchDeleteIn(ApiInSchema):
    """批量删除输入"""
    ids: List[str] = Field(..., description="任务ID列表")

class SchedulerJobBatchDeleteOut(ApiOutSchema):
    """批量删除输出"""
    count: int = Field(..., description="删除成功数量")
    failed_ids: List[str] = Field(default=[], description="删除失败的ID列表")


class SchedulerJobBatchUpdateStatusIn(ApiInSchema):
    """批量更新状态输入"""
    ids: List[str] = Field(..., description="任务ID列表")
    status: int = Field(..., description="目标状态：0-禁用，1-启用，2-暂停")


class SchedulerJobBatchUpdateStatusOut(ApiOutSchema):
    """批量更新状态输出"""
    count: int = Field(..., description="更新成功数量")



class SchedulerLogSearch(PaginatedRequest):
    job_id: Optional[str] = Field(None,alias="jobId",description="任务ID")
    job_code: Optional[str] = Field(None,alias="jobCode",description="任务编码")
    job_name: Optional[str] = Field(None,alias="jobName",description="任务名称")
    status: Optional[str] = Field(None,description="执行状态")
    start_time: Optional[datetime] = Field(None,alias="startTime",description="开始时间")
    end_time: Optional[datetime] = Field(None,alias="endTime",description="结束时间")

class SchedulerLogDelete(ApiInSchema):
    ids: List[str] = Field(...,description="日志ID列表")

class SchedulerLogClean(ApiInSchema):
    days: int = Field(...,ge=1,description="保留最近几天的日志")
    status: Optional[str] = Field(None,description="只清理指定状态的日志")
