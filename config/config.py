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
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from utils.file import get_base_dir


BASE_DIR = get_base_dir()
ENV_DIR = BASE_DIR / "env"


class Settings(BaseSettings):
    """
    项目配置模型。

    说明：
        该模型统一管理应用运行所需的环境变量和默认配置，
        包括基础应用信息、数据库配置、Redis 配置以及 JWT 配置。
    """

    ENV: Literal["dev", "uat", "prod"] = "dev"
    DEBUG: bool = Field(description="是否启用调试模式", default=True)

    APP_NAME: str = Field(description="项目名称", default="backend-fastapi")
    APP_HOST: str = Field(description="项目监听地址", default="0.0.0.0")
    APP_PORT: int = Field(description="项目端口号", default=8000)
    APP_VERSION: str = Field(description="项目版本", default="V1.0.0")
    APP_DESCRIPTION: str = Field(description="项目描述", default="backend-fastapi")

    # 数据库相关配置
    DB_HOST: str = Field(description="数据库主机地址", default="127.0.0.1")
    DB_PORT: int = Field(description="数据库端口", default=3306)
    DB_USER: str = Field(description="数据库用户名", default="root")
    DB_PASSWORD: str = Field(description="数据库密码", default="123456")
    DB_NAME: str = Field(description="数据库名称", default="backend-fastapi")
    DATABASE_URL: str | None = None

    # Redis 相关配置
    REDIS_HOST: str = Field(description="Redis 主机地址", default="127.0.0.1")
    REDIS_PORT: int = Field(description="Redis 端口", default=6379)
    REDIS_PASSWORD: str = Field(description="Redis 密码", default="123456")
    REDIS_DB: int = Field(description="Redis 数据库编号", default=0)
    REDIS_URL: str | None = None

    # 缓存配置
    CACHE_DEFAULT_EXPIRE: int = Field(description="默认缓存过期时间（秒）",default=300)
    CACHE_PREFIX: str = Field(description="缓存key前缀",default="peach-fastapi:")

    # JWT 配置
    JWT_SECRET_KEY: str = Field(
        description="JWT 密钥",
        default="_Ajb6-A-9XLdFs5SJNa5QCsDMP4rdsRTCUHrO37IA4c",
    )
    JWT_ALGORITHM: str = Field(description="JWT 算法", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        description="Access Token 过期时间，单位分钟",
        default=30,
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        description="Refresh Token 过期时间，单位天",
        default=7,
    )

    # 日志配置
    LOG_DIR: str = Field(description="日志目录", default="logs")
    LOG_LEVEL: str = Field(description="日志级别", default="INFO")
    LOG_BACKUP_COUNT: int = Field(description="日志保留天数", default=7)

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def build_urls(self) -> "Settings":
        """
        自动拼接数据库和 Redis 连接地址。

        Returns:
            Settings: 已补全连接地址的配置对象。
        """
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = (
                    f"redis://:{self.REDIS_PASSWORD}@"
                    f"{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
                )
            else:
                self.REDIS_URL = (
                    f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """
    根据当前环境变量加载配置文件。

    Returns:
        Settings: 已完成解析和缓存的配置对象。
    """
    env = os.getenv("ENV", "dev")
    env_file = ENV_DIR / f"{env}.env"
    return Settings(_env_file=env_file, _env_encoding="utf-8")


settings = get_settings()


if __name__ == "__main__":
    print(settings.model_dump())
