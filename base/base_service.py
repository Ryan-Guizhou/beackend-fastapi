#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: base_service.py
@Create: 2026/4/18 0:48
@Desc: 通用基础服务类
"""
import logging
from typing import Any, ClassVar, Generic, Iterable, Optional, Sequence, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, desc, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from base.base_model import DBBaseModel

T = TypeVar("T", bound=DBBaseModel)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)

logger = logging.getLogger("app")


class BaseService(Generic[T, CreateSchemaT, UpdateSchemaT]):
    """
    通用基础服务类。

    说明：
        该类封装了常见的增删改查、分页、唯一性校验等通用逻辑，
        业务服务类只需指定 `model`，即可复用这些基础能力。
    """

    model: ClassVar[type[T]]

    @staticmethod
    def _chunked(items: Sequence[Any], batch_size: int) -> Iterable[Sequence[Any]]:
        """
        按固定大小切分批量数据。

        Args:
            items: 原始数据列表。
            batch_size: 每批大小，必须大于 0。

        Yields:
            Iterable[Sequence[Any]]: 按批次切分后的数据片段。
        """
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")
        for index in range(0, len(items), batch_size):
            yield items[index:index + batch_size]

    @classmethod
    def _base_query(cls) -> Select[tuple[T]]:
        """
        构造基础查询语句。

        Returns:
            Select[tuple[T]]: 默认过滤软删除数据的查询语句。
        """
        return select(cls.model).where(cls.model.is_deleted.is_(False))

    @classmethod
    def _apply_filters(
            cls,
            stmt: Select[Any],
            filters: Sequence[ColumnElement[bool]] | None = None,
    ) -> Select[Any]:
        """
        将筛选条件批量追加到查询语句中。

        Args:
            stmt: 原始查询语句。
            filters: 动态筛选条件列表。

        Returns:
            Select[Any]: 叠加筛选条件后的查询语句。
        """
        if filters:
            for condition in filters:
                stmt = stmt.where(condition)
        return stmt

    @classmethod
    async def create(
            cls,
            db: AsyncSession,
            data: CreateSchemaT,
            auto_commit: bool = True,
    ) -> T:
        """
        创建一条记录。

        Args:
            db: 异步数据库会话。
            data: 创建数据模型。
            auto_commit: 是否自动提交事务；在事务场景中应传 `False`。

        Returns:
            T: 创建成功后的 ORM 对象。
        """
        db_obj = cls.model(**data.model_dump())
        db.add(db_obj)
        try:
            if auto_commit:
                await db.commit()
            else:
                await db.flush()
            await db.refresh(db_obj)
            logger.info("%s created", cls.model.__name__)
            return db_obj
        except Exception:
            await db.rollback()
            logger.exception("%s create failed", cls.model.__name__)
            raise

    @classmethod
    async def batch_create(
            cls,
            db: AsyncSession,
            data_list: Sequence[CreateSchemaT | dict[str, Any]],
            auto_commit: bool = True,
            batch_size: int = 500,
    ) -> int:
        """
        批量新增记录。

        说明：
            该方法使用 SQLAlchemy 的批量插入能力，底层会走 `executemany`，
            比逐条 `add()` / `commit()` 更适合大批量写入场景。

        Args:
            db: 异步数据库会话。
            data_list: 待插入的数据列表，支持 Pydantic 模型或字典。
            auto_commit: 是否自动提交事务。
            batch_size: 单批写入数量。

        Returns:
            int: 成功写入的记录数量。
        """
        if not data_list:
            return 0

        payloads = [
            item.model_dump() if isinstance(item, BaseModel) else dict(item)
            for item in data_list
        ]

        try:
            for chunk in cls._chunked(payloads, batch_size):
                await db.execute(insert(cls.model), list(chunk))

            if auto_commit:
                await db.commit()
            else:
                await db.flush()

            logger.info(
                "%s batch created, count=%s, batch_size=%s",
                cls.model.__name__,
                len(payloads),
                batch_size,
            )
            return len(payloads)
        except Exception:
            await db.rollback()
            logger.exception("%s batch create failed", cls.model.__name__)
            raise

    @classmethod
    async def get_by_id(
            cls,
            db: AsyncSession,
            record_id: str,
    ) -> Optional[T]:
        """
        根据主键获取单条记录。

        Args:
            db: 异步数据库会话。
            record_id: 记录主键。

        Returns:
            Optional[T]: 命中时返回 ORM 对象，否则返回 `None`。
        """
        stmt = cls._base_query().where(cls.model.id == record_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def exists(
            cls,
            db: AsyncSession,
            filters: Sequence[ColumnElement[bool]] | None = None,
    ) -> bool:
        """
        判断记录是否存在。

        Args:
            db: 异步数据库会话。
            filters: 动态筛选条件列表。

        Returns:
            bool: 只要存在一条符合条件的记录即返回 `True`。
        """
        stmt = cls._apply_filters(select(func.count()).select_from(cls.model), filters)
        stmt = stmt.where(cls.model.is_deleted.is_(False))
        result = await db.execute(stmt)
        return (result.scalar_one() or 0) > 0

    @classmethod
    async def count(
            cls,
            db: AsyncSession,
            filters: Sequence[ColumnElement[bool]] | None = None,
    ) -> int:
        """
        统计符合条件的记录数量。

        Args:
            db: 异步数据库会话。
            filters: 动态筛选条件列表。

        Returns:
            int: 符合条件的记录总数。
        """
        stmt = cls._apply_filters(select(func.count()).select_from(cls.model), filters)
        stmt = stmt.where(cls.model.is_deleted.is_(False))
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)

    @classmethod
    async def get_all(
            cls,
            db: AsyncSession,
            filters: Sequence[ColumnElement[bool]] | None = None,
    ) -> list[T]:
        """
        获取符合条件的全部记录。

        Args:
            db: 异步数据库会话。
            filters: 动态筛选条件列表。

        Returns:
            list[T]: 查询得到的 ORM 对象列表。
        """
        stmt = cls._apply_filters(cls._base_query(), filters)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def page_list(
            cls,
            db: AsyncSession,
            page: int,
            page_size: int,
            filters: Sequence[ColumnElement[bool]] | None = None,
    ) -> tuple[list[T], int]:
        """
        分页查询记录。

        Args:
            db: 异步数据库会话。
            page: 当前页码，从 1 开始。
            page_size: 每页数量。
            filters: 动态筛选条件列表。

        Returns:
            tuple[list[T], int]: 当前页数据和总记录数。
        """
        stmt = cls._apply_filters(cls._base_query(), filters)
        total = await cls.count(db, filters)
        offset = (page - 1) * page_size
        result = await db.execute(
            stmt.order_by(desc(cls.model.create_time))
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return items, total

    @classmethod
    async def del_by_id(
            cls,
            db: AsyncSession,
            record_id: str,
            auto_commit: bool = True,
            hard: bool = False,
    ) -> bool:
        """
        根据主键删除记录。

        Args:
            db: 异步数据库会话。
            record_id: 记录主键。
            auto_commit: 是否自动提交事务。
            hard: `True` 表示物理删除，`False` 表示软删除。

        Returns:
            bool: 删除成功返回 `True`，未找到或删除失败返回 `False`。
        """
        db_obj = await cls.get_by_id(db, record_id)
        if not db_obj:
            logger.warning("%s delete skipped, record not found: %s", cls.model.__name__, record_id)
            return False

        try:
            if hard:
                await db.delete(db_obj)
            else:
                db_obj.is_deleted = True

            if auto_commit:
                await db.commit()
            else:
                await db.flush()

            logger.info("%s deleted: %s", cls.model.__name__, record_id)
            return True
        except Exception:
            await db.rollback()
            logger.exception("%s delete failed: %s", cls.model.__name__, record_id)
            return False

    @classmethod
    async def restore_by_id(
            cls,
            db: AsyncSession,
            record_id: str,
            auto_commit: bool = True,
    ) -> bool:
        """
        恢复已软删除的记录。

        Args:
            db: 异步数据库会话。
            record_id: 记录主键。
            auto_commit: 是否自动提交事务。

        Returns:
            bool: 恢复成功返回 `True`，否则返回 `False`。
        """
        stmt = select(cls.model).where(
            cls.model.id == record_id,
            cls.model.is_deleted.is_(True),
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            logger.warning("%s restore skipped, record not found: %s", cls.model.__name__, record_id)
            return False

        try:
            db_obj.is_deleted = False
            if auto_commit:
                await db.commit()
            else:
                await db.flush()
            await db.refresh(db_obj)
            logger.info("%s restored: %s", cls.model.__name__, record_id)
            return True
        except Exception:
            await db.rollback()
            logger.exception("%s restore failed: %s", cls.model.__name__, record_id)
            return False

    @classmethod
    async def update(
            cls,
            db: AsyncSession,
            record_id: str,
            data: UpdateSchemaT,
            auto_commit: bool = True,
    ) -> Optional[T]:
        """
        更新指定记录。

        Args:
            db: 异步数据库会话。
            record_id: 记录主键。
            data: 更新数据模型，仅处理显式传入字段。
            auto_commit: 是否自动提交事务。

        Returns:
            Optional[T]: 更新成功后返回 ORM 对象，未找到时返回 `None`。
        """
        db_obj = await cls.get_by_id(db, record_id)
        if not db_obj:
            logger.warning("%s update skipped, record not found: %s", cls.model.__name__, record_id)
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        try:
            if auto_commit:
                await db.commit()
            else:
                await db.flush()
            await db.refresh(db_obj)
            logger.info("%s updated: %s", cls.model.__name__, record_id)
            return db_obj
        except Exception:
            await db.rollback()
            logger.exception("%s update failed: %s", cls.model.__name__, record_id)
            raise

    @classmethod
    async def batch_update(
            cls,
            db: AsyncSession,
            data_list: Sequence[UpdateSchemaT | dict[str, Any]],
            auto_commit: bool = True,
            batch_size: int = 500,
            id_field: str = "id",
    ) -> int:
        """
        批量更新记录。

        说明：
            该方法使用 SQLAlchemy 2.x 的批量主键更新模式，
            会将多条更新语句合并为批量执行，适合批量修改场景。

        Args:
            db: 异步数据库会话。
            data_list: 待更新的数据列表，每项必须包含主键字段。
            auto_commit: 是否自动提交事务。
            batch_size: 单批更新数量。
            id_field: 主键字段名，默认使用 `id`。

        Returns:
            int: 实际参与更新的记录数量。
        """
        if not data_list:
            return 0

        payloads: list[dict[str, Any]] = []
        for item in data_list:
            payload = (
                item.model_dump(exclude_unset=True)
                if isinstance(item, BaseModel)
                else dict(item)
            )
            if id_field not in payload or payload[id_field] in (None, ""):
                raise ValueError(f"batch_update item must include `{id_field}`")
            if len(payload) == 1:
                continue
            payloads.append(payload)

        if not payloads:
            return 0

        try:
            for chunk in cls._chunked(payloads, batch_size):
                await db.execute(update(cls.model), list(chunk))

            if auto_commit:
                await db.commit()
            else:
                await db.flush()

            logger.info(
                "%s batch updated, count=%s, batch_size=%s",
                cls.model.__name__,
                len(payloads),
                batch_size,
            )
            return len(payloads)
        except Exception:
            await db.rollback()
            logger.exception("%s batch update failed", cls.model.__name__)
            raise

    @classmethod
    async def batch_delete(
            cls,
            db: AsyncSession,
            ids: Sequence[str],
            hard: bool = False,
            auto_commit: bool = True,
    ) -> tuple[int, int]:
        """
        批量删除记录。

        Args:
            db: 异步数据库会话。
            ids: 待删除的记录主键列表。
            hard: `True` 表示物理删除，`False` 表示软删除。
            auto_commit: 是否自动提交事务。

        Returns:
            tuple[int, int]: 成功数量和失败数量。
        """
        success_count = 0
        fail_count = 0

        try:
            for record_id in ids:
                db_obj = await cls.get_by_id(db, record_id)
                if db_obj:
                    if hard:
                        await db.delete(db_obj)
                    else:
                        db_obj.is_deleted = True
                    success_count += 1
                else:
                    fail_count += 1

            if success_count > 0:
                if auto_commit:
                    await db.commit()
                else:
                    await db.flush()

            logger.info(
                "%s batch delete finished, success=%s, fail=%s",
                cls.model.__name__,
                success_count,
                fail_count,
            )
            return success_count, fail_count
        except Exception:
            await db.rollback()
            logger.exception("%s batch delete failed", cls.model.__name__)
            raise

    @classmethod
    async def check_unique(
            cls,
            db: AsyncSession,
            field: str,
            value: Any,
            exclude_id: Optional[str] = None,
    ) -> bool:
        """
        检查某个字段值是否唯一。

        Args:
            db: 异步数据库会话。
            field: 待校验字段名。
            value: 待校验字段值。
            exclude_id: 更新场景下需要排除的记录主键。

        Returns:
            bool: `True` 表示唯一，`False` 表示已存在。
        """
        query = select(cls.model).where(
            getattr(cls.model, field) == value,
            cls.model.is_deleted.is_(False),
        )

        if exclude_id:
            query = query.where(cls.model.id != exclude_id)

        result = await db.execute(query)
        return result.scalar_one_or_none() is None

    @classmethod
    async def get_by_field(
            cls,
            db: AsyncSession,
            field: str,
            value: Any,
    ) -> Optional[T]:
        """
        根据字段值获取单条记录。

        Args:
            db: 异步数据库会话。
            field: 查询字段名。
            value: 查询字段值。

        Returns:
            Optional[T]: 命中时返回 ORM 对象，否则返回 `None`。
        """
        result = await db.execute(
            select(cls.model).where(
                getattr(cls.model, field) == value,
                cls.model.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()
