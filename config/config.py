#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: config.py
@Create: 2026/4/16 22:02
@Desc: 项目配置
"""

import os
from functools import lru_cache
from typing import Any, Literal

import json5
from pydantic import BaseModel, Field, model_validator

from utils.file import get_base_dir


BASE_DIR = get_base_dir()
ENV_DIR = BASE_DIR / "env"


class AppConfig(BaseModel):
    """
    应用基础配置。
    Args:
        无。
    Returns:
        无。
    """

    name: str = Field(default="backend-fastapi", description="项目名称")
    host: str = Field(default="0.0.0.0", description="项目监听地址")
    port: int = Field(default=8000, description="项目端口号")
    version: str = Field(default="V1.0.0", description="项目版本")
    description: str = Field(default="backend-fastapi", description="项目描述")


class DatabaseConfig(BaseModel):
    """
    数据库配置。
    Args:
        无。
    Returns:
        无。
    """

    host: str = Field(default="127.0.0.1", description="数据库主机地址")
    port: int = Field(default=3306, description="数据库端口")
    user: str = Field(default="root", description="数据库用户名")
    password: str = Field(default="123456", description="数据库密码")
    name: str = Field(default="backend-fastapi", description="数据库名称")
    url: str | None = Field(default=None, description="数据库连接地址")

    @model_validator(mode="after")
    def build_url(self) -> "DatabaseConfig":
        """
        自动拼接数据库连接地址。
        Returns:
            DatabaseConfig: 补全连接地址后的数据库配置。
        """
        if not self.url:
            self.url = (
                f"mysql+aiomysql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        return self


class RedisConfig(BaseModel):
    """
    Redis 配置。
    Args:
        无。
    Returns:
        无。
    """

    host: str = Field(default="127.0.0.1", description="Redis 主机地址")
    port: int = Field(default=6379, description="Redis 端口")
    password: str = Field(default="", description="Redis 密码")
    db: int = Field(default=0, description="Redis 数据库编号")
    url: str | None = Field(default=None, description="Redis 连接地址")

    @model_validator(mode="after")
    def build_url(self) -> "RedisConfig":
        """
        自动拼接 Redis 连接地址。
        Returns:
            RedisConfig: 补全连接地址后的 Redis 配置。
        """
        if not self.url:
            if self.password:
                self.url = f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
            else:
                self.url = f"redis://{self.host}:{self.port}/{self.db}"
        return self


class MongoConfig(BaseModel):
    """
    MongoDB 配置。
    Args:
        无。
    Returns:
        无。
    """

    host: str = Field(default="127.0.0.1", description="MongoDB 主机地址")
    port: int = Field(default=27017, description="MongoDB 端口")
    user: str = Field(default="", description="MongoDB 用户名")
    password: str = Field(default="", description="MongoDB 密码")
    db: str = Field(default="backend-fastapi", description="MongoDB 数据库名称")
    auth_source: str = Field(default="admin", description="MongoDB 认证数据库")
    url: str | None = Field(default=None, description="MongoDB 连接地址")

    @model_validator(mode="after")
    def build_url(self) -> "MongoConfig":
        """
        自动拼接 MongoDB 连接地址。
        Returns:
            MongoConfig: 补全连接地址后的 MongoDB 配置。
        """
        if not self.url:
            if self.user and self.password:
                self.url = (
                    f"mongodb://{self.user}:{self.password}"
                    f"@{self.host}:{self.port}/{self.db}"
                    f"?authSource={self.auth_source}"
                )
            else:
                self.url = f"mongodb://{self.host}:{self.port}/{self.db}"
        return self


class CacheConfig(BaseModel):
    """
    缓存配置。
    Args:
        无。
    Returns:
        无。
    """

    default_expire: int = Field(default=300, description="默认缓存过期时间，单位秒")
    prefix: str = Field(default="peach-fastapi:", description="缓存 Key 前缀")


class JwtConfig(BaseModel):
    """
    JWT 配置。
    Args:
        无。
    Returns:
        无。
    """

    secret_key: str = Field(
        default="_Ajb6-A-9XLdFs5SJNa5QCsDMP4rdsRTCUHrO37IA4c",
        description="JWT 密钥",
    )
    algorithm: str = Field(default="HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(default=30, description="Access Token 过期时间")
    refresh_token_expire_minutes: int = Field(default=10080, description="Refresh Token 过期时间")
    login_failure_lock_threshold: int = Field(default=5, description="登录失败锁定阈值")
    login_failure_lock_minutes: int = Field(default=30, description="登录失败锁定时长")


class LogConfig(BaseModel):
    """
    日志配置。
    Args:
        无。
    Returns:
        无。
    """

    dir: str = Field(default="logs", description="日志目录")
    level: str = Field(default="INFO", description="日志级别")
    backup_count: int = Field(default=7, description="日志保留天数")


class SchedulerConfig(BaseModel):
    """
    调度配置。
    Args:
        无。
    Returns:
        无。
    """

    enabled: bool = Field(default=True, description="是否启用任务调度")


class Settings(BaseModel):
    """
    项目配置模型。
    Args:
        无。
    Returns:
        无。
    """

    env: Literal["dev", "uat", "prod"] = "dev"
    debug: bool = Field(default=True, description="是否启用调试模式")
    app: AppConfig = Field(default_factory=AppConfig, description="应用配置")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis 配置")
    mongo: MongoConfig = Field(default_factory=MongoConfig, description="MongoDB 配置")
    cache: CacheConfig = Field(default_factory=CacheConfig, description="缓存配置")
    jwt: JwtConfig = Field(default_factory=JwtConfig, description="JWT 配置")
    log: LogConfig = Field(default_factory=LogConfig, description="日志配置")
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig, description="调度配置")

def _load_json5_config(env: str) -> dict[str, Any]:
    """
    加载指定环境的 JSON5 配置文件。
    Args:
        env: 环境名称。
    Returns:
        dict[str, Any]: 配置字典。
    Raises:
        FileNotFoundError: 配置文件不存在时抛出。
    """
    config_file = ENV_DIR / f"{env}.json5"
    with config_file.open("r", encoding="utf-8") as file:
        return json5.load(file)


@lru_cache
def get_settings() -> Settings:
    """
    根据当前环境变量加载配置文件。
    Returns:
        Settings: 已完成解析和缓存的配置对象。
    """
    env = os.getenv("ENV", "dev")
    config_data = _load_json5_config(env)
    return Settings.model_validate(config_data)


settings = get_settings()


if __name__ == "__main__":
    print(settings.model_dump())
