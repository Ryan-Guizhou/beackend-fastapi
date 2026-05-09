#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: cache_decorator.py
@Create: 2026/5/9
@Desc: Redis 缓存装饰器
"""

from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar, cast, get_type_hints

from utils.redis.cache_manager import CacheManager

# 异步函数类型定义。
AsyncFunc = TypeVar("AsyncFunc", bound=Callable[..., Awaitable[Any]])
_default_cache_manager: CacheManager | None = None


def set_default_cache_manager(cache_manager: CacheManager | None) -> None:
    """
    设置装饰器默认使用的缓存管理器。

    Args:
        cache_manager: 缓存管理器实例，为 `None` 时清空默认缓存管理器。
    """
    global _default_cache_manager
    _default_cache_manager = cache_manager


@dataclass(frozen=True)
class CacheableOp:
    """
    可缓存操作配置。
    Args:
        cache_name: 缓存命名空间。
        key: 静态 Key 或格式化字符串。
        key_builder: 动态 Key 构建函数。
        ttl: Redis 过期时间，单位秒。
        local_ttl: 本地缓存过期时间，单位秒。
        cache_none: 是否缓存 `None`。
        condition: 执行缓存操作的前置条件。
        unless: 排除缓存结果的条件。
        sync: 是否启用分布式锁防止缓存击穿。
    """
    cache_name: str
    key: str | None = None
    key_builder: Callable[..., str] | None = None
    ttl: int = 300
    local_ttl: int | None = None
    cache_none: bool = False
    condition: Callable[..., bool] | None = None
    unless: Callable[..., bool] | None = None
    sync: bool = False


@dataclass(frozen=True)
class CachePutOp:
    """
    缓存写回操作配置。
    Args:
        cache_name: 缓存命名空间。
        key: 静态 Key 或格式化字符串。
        key_builder: 动态 Key 构建函数。
        ttl: Redis 过期时间，单位秒。
        local_ttl: 本地缓存过期时间，单位秒。
        cache_none: 是否缓存 `None`。
        condition: 执行写回的前置条件。
        unless: 排除写回结果的条件。
    """
    cache_name: str
    key: str | None = None
    key_builder: Callable[..., str] | None = None
    ttl: int = 300
    local_ttl: int | None = None
    cache_none: bool = False
    condition: Callable[..., bool] | None = None
    unless: Callable[..., bool] | None = None


@dataclass(frozen=True)
class CacheEvictOp:
    """
    缓存失效操作配置。
    Args:
        cache_name: 缓存命名空间。
        key: 静态 Key 或格式化字符串。
        key_builder: 动态 Key 构建函数。
        all_entries: 是否清空命名空间下全部缓存。
        before_invocation: 是否在函数执行前删除缓存。
        condition: 执行删除的前置条件。
    """
    cache_name: str
    key: str | None = None
    key_builder: Callable[..., str] | None = None
    all_entries: bool = False
    before_invocation: bool = False
    condition: Callable[..., bool] | None = None


def _resolve_cache_manager(arguments: dict[str, Any]) -> CacheManager:
    """
    解析缓存管理器。
    Args:
        arguments: 当前函数调用参数。
    Returns:
        CacheManager: 缓存管理器实例。
    Raises:
        ValueError: 未找到缓存管理器时抛出。
    """
    cache_manager = arguments.get("cache_manager")
    if isinstance(cache_manager, CacheManager):
        return cache_manager

    self_obj = arguments.get("self")
    if self_obj is not None and isinstance(getattr(self_obj, "cache_manager", None), CacheManager):
        return self_obj.cache_manager

    for value in arguments.values():
        if isinstance(value, CacheManager):
            return value

    if _default_cache_manager is not None:
        return _default_cache_manager

    raise ValueError(
        "未找到 CacheManager，请通过函数参数传入 cache_manager，"
        "或在应用启动时调用 set_default_cache_manager"
    )


def _invoke_callback(callback: Callable[..., Any], arguments: dict[str, Any], result: Any = None) -> Any:
    """
    执行条件或 Key 构建回调。
    Args:
        callback: 待执行回调。
        arguments: 当前函数调用参数。
        result: 函数执行结果。
    Returns:
        Any: 回调执行结果。
    """
    signature = inspect.signature(callback)
    params = signature.parameters

    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
        payload = dict(arguments)
        payload["result"] = result
        return callback(**payload)

    kwargs: dict[str, Any] = {}
    for name in params.keys():
        if name == "result":
            kwargs[name] = result
        elif name in arguments:
            kwargs[name] = arguments[name]

    return callback(**kwargs)


def _check_condition(condition: Callable[..., bool] | None, arguments: dict[str, Any], result: Any = None) -> bool:
    """
    检查缓存前置条件。
    Args:
        condition: 条件函数。
        arguments: 当前函数调用参数。
        result: 函数执行结果。
    Returns:
        bool: 可以继续执行缓存操作时返回 `True`。
    """
    if condition is None:
        return True
    return bool(_invoke_callback(condition, arguments, result))


def _check_unless(unless: Callable[..., bool] | None, arguments: dict[str, Any], result: Any = None) -> bool:
    """
    检查缓存排除条件。
    Args:
        unless: 排除条件函数。
        arguments: 当前函数调用参数。
        result: 函数执行结果。
    Returns:
        bool: 需要跳过缓存操作时返回 `True`。
    """
    if unless is None:
        return False
    return bool(_invoke_callback(unless, arguments, result))


def _build_raw_key(
        arguments: dict[str, Any],
        *,
        key: str | None,
        key_builder: Callable[..., str] | None,
) -> str:
    """
    构建业务原始缓存 Key。
    Args:
        arguments: 当前函数调用参数。
        key: 静态 Key 或格式化字符串。
        key_builder: 动态 Key 构建函数。
    Returns:
        str: 业务原始缓存 Key。
    """
    if key_builder is not None:
        return str(_invoke_callback(key_builder, arguments))

    if key is None:
        raise ValueError("key 和 key_builder 不能同时为空")

    return key.format(**arguments)


async def _do_cache_put(
        cache_manager: CacheManager,
        op: CachePutOp | CacheableOp,
        arguments: dict[str, Any],
        result: Any,
) -> None:
    """
    执行底层缓存写入。
    Args:
        cache_manager: 缓存管理器。
        op: 缓存写入配置。
        arguments: 当前函数调用参数。
        result: 函数执行结果。
    """
    if not _check_condition(op.condition, arguments, result):
        return

    if _check_unless(op.unless, arguments, result):
        return

    raw_key = _build_raw_key(arguments, key=op.key, key_builder=op.key_builder)
    await cache_manager.put(
        cache_name=op.cache_name,
        raw_key=raw_key,
        value=result,
        ttl=op.ttl,
        local_ttl=op.local_ttl,
        cache_none=getattr(op, "cache_none", False),
    )


async def _do_cache_evict(
        cache_manager: CacheManager,
        op: CacheEvictOp,
        arguments: dict[str, Any],
        result: Any = None,
) -> None:
    """
    执行底层缓存清理。
    Args:
        cache_manager: 缓存管理器。
        op: 缓存清理配置。
        arguments: 当前函数调用参数。
        result: 函数执行结果。
    """
    if not _check_condition(op.condition, arguments, result):
        return

    if op.all_entries:
        await cache_manager.clear(op.cache_name)
        return

    raw_key = _build_raw_key(arguments, key=op.key, key_builder=op.key_builder)
    await cache_manager.evict(op.cache_name, raw_key)


def cacheable(
        *,
        cache_name: str,
        key: str | None = None,
        key_builder: Callable[..., str] | None = None,
        ttl: int = 300,
        local_ttl: int | None = None,
        cache_none: bool = False,
        condition: Callable[..., bool] | None = None,
        unless: Callable[..., bool] | None = None,
        sync: bool = False,
) -> Callable[[AsyncFunc], AsyncFunc]:
    """
    读取缓存装饰器。
    Args:
        cache_name: 缓存命名空间。
        key: 静态 Key 或格式化字符串。
        key_builder: 动态 Key 构建函数。
        ttl: Redis 过期时间，单位秒。
        local_ttl: 本地缓存过期时间，单位秒。
        cache_none: 是否缓存 `None`。
        condition: 执行缓存操作的前置条件。
        unless: 排除缓存结果的条件。
        sync: 是否启用分布式锁防止缓存击穿。
    Returns:
        Callable[[AsyncFunc], AsyncFunc]: 包装后的异步函数。
    """
    op = CacheableOp(
        cache_name=cache_name,
        key=key,
        key_builder=key_builder,
        ttl=ttl,
        local_ttl=local_ttl,
        cache_none=cache_none,
        condition=condition,
        unless=unless,
        sync=sync,
    )

    def decorator(func: AsyncFunc) -> AsyncFunc:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("cacheable 仅支持 async 函数")

        signature = inspect.signature(func)
        return_type = get_type_hints(func).get("return")

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            arguments = dict(bound.arguments)

            cache_manager = _resolve_cache_manager(arguments)

            if not _check_condition(op.condition, arguments):
                return await func(*args, **kwargs)

            raw_key = _build_raw_key(arguments, key=op.key, key_builder=op.key_builder)

            hit, cached = await cache_manager.get(
                cache_name=op.cache_name,
                raw_key=raw_key,
                target_type=return_type,
                local_ttl=op.local_ttl,
            )
            if hit:
                return cached

            async def execute_and_cache():
                """
                执行原函数并写入缓存。
                """
                result = await func(*args, **kwargs)
                if _check_unless(op.unless, arguments, result):
                    return result

                await cache_manager.put(
                    cache_name=op.cache_name,
                    raw_key=raw_key,
                    value=result,
                    ttl=op.ttl,
                    local_ttl=op.local_ttl,
                    cache_none=op.cache_none,
                )
                return result

            if not op.sync:
                return await execute_and_cache()

            lock_key = cache_manager.redis_service.build_key(op.cache_name, "lock", raw_key)
            async with cache_manager.redis_service.lock(lock_key, expire=10):
                hit_again, cached_again = await cache_manager.get(
                    cache_name=op.cache_name,
                    raw_key=raw_key,
                    target_type=return_type,
                    local_ttl=op.local_ttl,
                )
                if hit_again:
                    return cached_again
                return await execute_and_cache()

        return cast(AsyncFunc, wrapper)

    return decorator


def cache_put(
        *,
        cache_name: str,
        key: str | None = None,
        key_builder: Callable[..., str] | None = None,
        ttl: int = 300,
        local_ttl: int | None = None,
        cache_none: bool = False,
        condition: Callable[..., bool] | None = None,
        unless: Callable[..., bool] | None = None,
) -> Callable[[AsyncFunc], AsyncFunc]:
    """
    缓存写回装饰器。
    Args:
        cache_name: 缓存命名空间。
        key: 静态 Key 或格式化字符串。
        key_builder: 动态 Key 构建函数。
        ttl: Redis 过期时间，单位秒。
        local_ttl: 本地缓存过期时间，单位秒。
        cache_none: 是否缓存 `None`。
        condition: 执行写回的前置条件。
        unless: 排除写回结果的条件。
    Returns:
        Callable[[AsyncFunc], AsyncFunc]: 包装后的异步函数。
    """
    op = CachePutOp(
        cache_name=cache_name,
        key=key,
        key_builder=key_builder,
        ttl=ttl,
        local_ttl=local_ttl,
        cache_none=cache_none,
        condition=condition,
        unless=unless,
    )

    def decorator(func: AsyncFunc) -> AsyncFunc:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("cache_put 仅支持 async 函数")

        signature = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            arguments = dict(bound.arguments)

            cache_manager = _resolve_cache_manager(arguments)
            result = await func(*args, **kwargs)
            await _do_cache_put(cache_manager, op, arguments, result)
            return result

        return cast(AsyncFunc, wrapper)

    return decorator


def cache_evict(
        *,
        cache_name: str,
        key: str | None = None,
        key_builder: Callable[..., str] | None = None,
        all_entries: bool = False,
        before_invocation: bool = False,
        condition: Callable[..., bool] | None = None,
) -> Callable[[AsyncFunc], AsyncFunc]:
    """
    缓存删除装饰器。
    Args:
        cache_name: 缓存命名空间。
        key: 静态 Key 或格式化字符串。
        key_builder: 动态 Key 构建函数。
        all_entries: 是否清空命名空间下全部缓存。
        before_invocation: 是否在函数执行前删除缓存。
        condition: 执行删除的前置条件。
    Returns:
        Callable[[AsyncFunc], AsyncFunc]: 包装后的异步函数。
    """
    op = CacheEvictOp(
        cache_name=cache_name,
        key=key,
        key_builder=key_builder,
        all_entries=all_entries,
        before_invocation=before_invocation,
        condition=condition,
    )

    def decorator(func: AsyncFunc) -> AsyncFunc:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("cache_evict 仅支持 async 函数")

        signature = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            arguments = dict(bound.arguments)

            cache_manager = _resolve_cache_manager(arguments)

            if op.before_invocation:
                await _do_cache_evict(cache_manager, op, arguments)

            result = await func(*args, **kwargs)

            if not op.before_invocation:
                await _do_cache_evict(cache_manager, op, arguments, result)

            return result

        return cast(AsyncFunc, wrapper)

    return decorator


def caching(
        *,
        put: list[CachePutOp] | None = None,
        evict: list[CacheEvictOp] | None = None,
) -> Callable[[AsyncFunc], AsyncFunc]:
    """
    复合缓存装饰器。
    Args:
        put: 写回操作列表。
        evict: 删除操作列表。
    Returns:
        Callable[[AsyncFunc], AsyncFunc]: 包装后的异步函数。
    """
    put_ops = put or []
    evict_ops = evict or []

    def decorator(func: AsyncFunc) -> AsyncFunc:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("caching 仅支持 async 函数")

        signature = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bound = signature.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            arguments = dict(bound.arguments)
            cache_manager = _resolve_cache_manager(arguments)

            for evict_op in evict_ops:
                if evict_op.before_invocation:
                    await _do_cache_evict(cache_manager, evict_op, arguments)

            result = await func(*args, **kwargs)

            for put_op in put_ops:
                await _do_cache_put(cache_manager, put_op, arguments, result)

            for evict_op in evict_ops:
                if not evict_op.before_invocation:
                    await _do_cache_evict(cache_manager, evict_op, arguments, result)

            return result

        return cast(AsyncFunc, wrapper)

    return decorator
