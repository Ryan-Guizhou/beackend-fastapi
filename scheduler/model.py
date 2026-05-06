#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: model.py
@Create: 2026/5/5 14:04
@Desc: 调度任务 ORM 模型定义
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from base.base_model import DBBaseModel


class TriggerTypeEnum(str, Enum):
    """
    任务触发器类型枚举。
    Args:
        无。
    Returns:
        无。
    """

    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"

    @property
    def label(self) -> str:
        """
        获取触发器类型的中文名称。
        Args:
            无。
        Returns:
            str: 当前触发器类型对应的中文名称。
        """
        labels = {
            self.CRON.value: "Cron表达式",
            self.INTERVAL.value: "间隔执行",
            self.DATE.value: "指定时间",
        }
        return labels[self.value]

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """
        返回触发器类型的可选项列表。
        Args:
            无。
        Returns:
            list[tuple[str, str]]: 由枚举值与中文名称组成的元组列表。
        """
        return [(item.value, item.label) for item in cls]

    @classmethod
    def from_value(cls, value: str) -> "TriggerTypeEnum":
        """
        根据枚举值获取触发器类型。
        Args:
            value: 触发器类型枚举值。
        Returns:
            TriggerTypeEnum: 匹配到的触发器类型枚举成员。
        """
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"无效的触发器类型: {value}")


class StatusChoices(int, Enum):
    """
    调度任务状态枚举。
    Args:
        无。
    Returns:
        无。
    """

    DISABLED = 0
    ENABLED = 1
    PAUSED = 2

    @property
    def label(self) -> str:
        """
        获取任务状态的中文名称。
        Args:
            无。
        Returns:
            str: 当前任务状态对应的中文名称。
        """
        return {
            self.DISABLED.value: "禁用",
            self.ENABLED.value: "启用",
            self.PAUSED.value: "暂停",
        }[self.value]

    @classmethod
    def choices(cls) -> list[tuple[int, str]]:
        """
        返回任务状态的可选项列表。
        Args:
            无。
        Returns:
            list[tuple[int, str]]: 由状态值与中文名称组成的元组列表。
        """
        return [(item.value, item.label) for item in cls]

    @classmethod
    def from_value(cls, value: int) -> "StatusChoices":
        """
        根据状态值获取任务状态枚举。
        Args:
            value: 任务状态值。
        Returns:
            StatusChoices: 匹配到的任务状态枚举成员。
        """
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"无效的任务状态: {value}")

if __name__ == '__main__':
    print(StatusChoices.ENABLED.label)

class RunStatusChoices(str, Enum):
    """
    调度执行状态枚举。
    Args:
        无。
    Returns:
        无。
    """

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"

    @property
    def label(self) -> str:
        """
        获取执行状态的中文名称。
        Args:
            无。
        Returns:
            str: 当前执行状态对应的中文名称。
        """
        return {
            self.SUCCESS.value: "成功",
            self.FAILURE.value: "失败",
            self.RUNNING.value: "执行中",
        }[self.value]


class SchedulerJob(DBBaseModel):
    """
    调度任务 ORM 模型。
    Args:
        无。
    Returns:
        无。
    """

    __tablename__ = "peach_scheduler_job"

    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="任务名称",
    )
    code: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="任务编码",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="任务描述",
    )

    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TriggerTypeEnum.CRON.value,
        comment="触发器类型",
    )
    cron_expression: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="Cron 表达式",
    )
    interval_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="任务执行间隔时间(秒)",
    )
    run_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="指定执行时间",
    )

    task_func: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="任务函数路径",
    )
    task_args: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="任务位置参数(JSON 数组格式)",
    )
    task_kwargs: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="任务关键字参数(JSON 对象格式)",
    )

    status: Mapped[int] = mapped_column(
        Integer,
        default=StatusChoices.DISABLED.value,
        nullable=False,
        index=True,
        comment="任务状态(0-禁用,1-启用,2-暂停)",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        comment="任务优先级",
    )
    max_instances: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="最大实例数",
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        comment="最大重试次数",
    )
    retry_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="重试间隔时间(秒)",
    )
    timeout: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="任务超时时间(秒)",
    )
    coalesce: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否合并错过的执行",
    )
    allow_concurrent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否允许并发执行",
    )

    total_run_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总执行次数",
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="成功次数",
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="失败次数",
    )

    last_run_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后执行时间",
    )
    next_run_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="下次执行时间",
    )
    last_run_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="最后执行状态",
    )
    last_run_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="最后执行结果",
    )
    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    def __str__(self) -> str:
        """
        返回任务对象的字符串表示。
        Args:
            无。
        Returns:
            str: 由任务名称和任务编码组成的字符串。
        """
        return f"{self.name} ({self.code})"

    def is_enabled(self) -> bool:
        """
        判断任务是否为启用状态。
        Args:
            无。
        Returns:
            bool: 启用状态返回 `True`，否则返回 `False`。
        """
        return self.status == StatusChoices.ENABLED.value

    def is_paused(self) -> bool:
        """
        判断任务是否为暂停状态。
        Args:
            无。
        Returns:
            bool: 暂停状态返回 `True`，否则返回 `False`。
        """
        return self.status == StatusChoices.PAUSED.value

    def is_disabled(self) -> bool:
        """
        判断任务是否为禁用状态。
        Args:
            无。
        Returns:
            bool: 禁用状态返回 `True`，否则返回 `False`。
        """
        return self.status == StatusChoices.DISABLED.value

    def get_status_display(self) -> str:
        """
        获取任务状态的中文显示名称。
        Args:
            无。
        Returns:
            str: 当前任务状态对应的中文名称。
        """
        return StatusChoices(self.status).label


class SchedulerLog(DBBaseModel):
    """
    调度任务执行日志 ORM 模型。
    Args:
        无。
    Returns:
        无。
    """

    __tablename__ = "peach_scheduler_log"

    job_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
        comment="任务 ID",
    )
    job_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="任务名称",
    )
    job_code: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="任务编码",
    )
    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="触发器类型",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RunStatusChoices.RUNNING.value,
        index=True,
        comment="执行状态",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="当前重试次数",
    )
    run_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="开始执行时间",
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="执行结束时间",
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="执行耗时(毫秒)",
    )
    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="执行结果",
    )
    exception: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )
    traceback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="异常堆栈信息"
    )
    hostname: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="执行主机"
    )
    process_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="进程ID"
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息",
    )

    def is_success(self) -> bool:
        """
        判断执行日志是否为成功状态。
        Args:
            无。
        Returns:
            bool: 成功状态返回 `True`，否则返回 `False`。
        """
        return self.status == RunStatusChoices.SUCCESS.value

    def is_failure(self) -> bool:
        """
        判断执行日志是否为失败状态。
        Args:
            无。
        Returns:
            bool: 失败状态返回 `True`，否则返回 `False`。
        """
        return self.status == RunStatusChoices.FAILURE.value

    def is_running(self) -> bool:
        """
        判断是否正在运行
        Args:
            无。
        Returns:
            bool: 正在运行状态返回 `True`, 否则返回 `False`
        """
        return self.status == RunStatusChoices.RUNNING.value

    def get_status_display(self) -> str:
        """
        获取运行状态的显示名称
        Args:
            无。
        Returns:
            str: 当前任务状态对应的中文名称。
        """
        return RunStatusChoices(self.status).label