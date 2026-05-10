#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: service.py
@Create: 2026/4/18 17:55
@Desc: 数据源管理服务
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar
from urllib.parse import urlparse

from config.config import settings

logger = logging.getLogger("app")


def format_size(size_bytes: int) -> str:
    """
    格式化字节大小。

    Args:
        size_bytes: 原始字节数。

    Returns:
        str: 适合展示的容量字符串。
    """
    if not size_bytes:
        return "0 bytes"
    if size_bytes >= 1024 ** 3:
        return f"{size_bytes / (1024 ** 3):.2f} GB"
    if size_bytes >= 1024 ** 2:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} bytes"


def parse_database_url(database_url: str | None) -> dict[str, Any] | None:
    """
    解析数据库连接地址。

    Args:
        database_url: 数据库连接字符串。

    Returns:
        dict[str, Any] | None: 解析成功时返回数据库连接信息，失败时返回 `None`。
    """
    if not database_url:
        return None

    parsed = urlparse(database_url)
    scheme = parsed.scheme.lower()
    if "postgresql" in scheme or "postgres" in scheme:
        db_type = "postgresql"
        default_port = 5432
    elif "mysql" in scheme:
        db_type = "mysql"
        default_port = 3306
    else:
        return None

    return {
        "db_type": db_type,
        "host": parsed.hostname or "localhost",
        "port": parsed.port or default_port,
        "user": parsed.username or "",
        "password": parsed.password or "",
        "database": parsed.path.lstrip("/") if parsed.path else "",
    }


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    """
    序列化数据库返回的单行数据。

    Args:
        row: 原始结果行。

    Returns:
        dict[str, Any]: 处理后的可 JSON 序列化结果。
    """
    serialized = dict(row)
    for key, value in serialized.items():
        if hasattr(value, "isoformat"):
            serialized[key] = value.isoformat()
        elif isinstance(value, bytes):
            serialized[key] = value.decode("utf-8", errors="replace")
        elif isinstance(value, (set, frozenset)):
            serialized[key] = list(value)
    return serialized


class DatabaseHandler(ABC):
    """数据库处理器抽象基类。"""

    @abstractmethod
    async def connect(self, database: str | None = None) -> bool:
        """建立数据库连接。"""

    @abstractmethod
    async def close(self) -> None:
        """关闭数据库连接。"""

    @abstractmethod
    async def get_database(self) -> list[dict[str, Any]]:
        """获取数据库列表。"""

    @abstractmethod
    async def create_database(self, name: str, **kwargs: Any) -> bool:
        """创建数据库。"""

    @abstractmethod
    async def drop_database(self, name: str) -> bool:
        """删除数据库。"""

    @abstractmethod
    async def get_schemas(self, database: str | None = None) -> list[dict[str, Any]]:
        """获取 schema 列表。"""

    @abstractmethod
    async def get_tables(self, database: str | None = None, schema_name: str | None = None) -> list[dict[str, Any]]:
        """获取表列表。"""

    @abstractmethod
    async def get_table_columns(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """获取列信息。"""

    @abstractmethod
    async def get_table_indexes(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """获取索引信息。"""

    @abstractmethod
    async def get_table_constraints(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """获取约束信息。"""

    @abstractmethod
    async def get_table_structure(
            self,
            table_name: str,
            database: str | None = None,
            schema_name: str | None = None,
    ) -> dict[str, Any]:
        """获取表结构。"""

    @abstractmethod
    async def get_table_ddl(self, table_name: str, schema_name: str | None = None) -> str:
        """获取建表语句。"""

    @abstractmethod
    async def get_views(self, database: str | None = None, schema_name: str | None = None) -> list[dict[str, Any]]:
        """获取视图列表。"""

    @abstractmethod
    async def get_view_structure(self, view_name: str, schema_name: str | None = None) -> dict[str, Any]:
        """获取视图结构。"""

    @abstractmethod
    async def get_view_definition(self, view_name: str, schema_name: str | None = None) -> str:
        """获取视图定义。"""

    @abstractmethod
    async def get_view_dependencies(self, view_name: str, schema_name: str | None = None) -> list[str]:
        """获取视图依赖。"""

    @abstractmethod
    async def query_data(
            self,
            table_name: str,
            schema_name: str | None = None,
            page: int = 1,
            page_size: int = 20,
            where: str | None = None,
            order_by: str | None = None,
    ) -> dict[str, Any]:
        """分页查询表数据。"""

    @abstractmethod
    async def execute_sql(self, sql: str, is_query: bool = True) -> dict[str, Any]:
        """执行 SQL。"""

    @abstractmethod
    async def insert_data(self, table_name: str, data: dict[str, Any], schema_name: str | None = None) -> dict[str, Any]:
        """插入数据。"""

    @abstractmethod
    async def update_data(self, table_name: str, data: dict[str, Any], where: str, schema_name: str | None = None) -> dict[str, Any]:
        """更新数据。"""

    @abstractmethod
    async def delete_data(self, table_name: str, where: str, schema_name: str | None = None) -> dict[str, Any]:
        """删除数据。"""

    @abstractmethod
    async def execute_ddl(self, sql: str, database: str | None = None, schema_name: str | None = None) -> dict[str, Any]:
        """执行 DDL。"""


class BaseDatabaseHandler(DatabaseHandler, ABC):
    """
    数据库处理器基础实现。

    提供连接参数保存、标识符转义、分页结果封装等公共能力，
    由具体数据库处理器继承复用。
    """

    identifier_quote: ClassVar[str] = '"'

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        """
        初始化数据库处理器的连接参数。

        Args:
            host: 数据库主机地址。
            port: 数据库端口。
            user: 数据库用户名。
            password: 数据库密码。
            database: 默认连接的数据库名称。
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn: Any = None

    @staticmethod
    def _empty_page_result(page: int = 1, page_size: int = 10) -> dict[str, Any]:
        """
        构造空分页结果。

        Args:
            page: 当前页码。
            page_size: 每页条数。

        Returns:
            dict[str, Any]: 统一格式的空结果集。
        """
        return {"columns": [], "rows": [], "total": 0, "page": page, "page_size": page_size}

    @staticmethod
    def _build_page_result(rows: list[dict[str, Any]], total: int, page: int, page_size: int) -> dict[str, Any]:
        """
        将查询结果封装为统一分页结构。

        Args:
            rows: 当前页原始记录。
            total: 总记录数。
            page: 当前页码。
            page_size: 每页条数。

        Returns:
            dict[str, Any]: 包含列名、记录、总数和分页信息的结果。
        """
        rows_list = [serialize_row(row) for row in rows]
        columns = list(rows_list[0].keys()) if rows_list else []
        return {"columns": columns, "rows": rows_list, "total": total, "page": page, "page_size": page_size}

    def _quote_identifier(self, name: str) -> str:
        """
        对数据库标识符进行转义并加引号。

        Args:
            name: 表名、字段名或 schema 名称。

        Returns:
            str: 转义后的标识符。
        """
        escaped = name.replace(self.identifier_quote, self.identifier_quote * 2)
        return f"{self.identifier_quote}{escaped}{self.identifier_quote}"

    def _qualified_name(self, table_name: str, schema_name: str | None = None) -> str:
        """
        构建带 schema 的完整对象名。

        Args:
            table_name: 表名或视图名。
            schema_name: schema 名称。

        Returns:
            str: 可直接用于 SQL 的完整对象名。
        """
        if schema_name:
            return f"{self._quote_identifier(schema_name)}.{self._quote_identifier(table_name)}"
        return self._quote_identifier(table_name)


class MySQLHandler(BaseDatabaseHandler):
    """
    MySQL 数据库处理器。

    基于 `aiomysql` 实现库、表、视图和数据操作能力。
    """

    identifier_quote = "`"

    async def connect(self, database: str | None = None) -> bool:
        """
        建立 MySQL 连接。

        Args:
            database: 可选的目标数据库名称，未传时使用默认库。

        Returns:
            bool: 连接是否成功。
        """
        try:
            import aiomysql

            self.conn = await aiomysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=database or self.database,
                charset="utf8mb4",
                connect_timeout=10,
                autocommit=True,
            )
            return True
        except Exception as exc:
            logger.error("Failed to connect to MySQL database: %s", exc)
            return False

    async def close(self) -> None:
        """关闭当前 MySQL 连接。"""
        if self.conn:
            self.conn.close()
            self.conn = None

    async def _execute_query(self, query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """
        执行查询语句并返回字典结果集。

        Args:
            query: SQL 查询语句。
            params: 查询参数。

        Returns:
            list[dict[str, Any]]: 查询结果列表。
        """
        import aiomysql

        async with self.conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def _execute_command(self, command: str, params: tuple[Any, ...] | None = None) -> int:
        """
        执行写操作 SQL 并返回影响行数。

        Args:
            command: 非查询 SQL。
            params: SQL 参数。

        Returns:
            int: 影响的记录数。
        """
        async with self.conn.cursor() as cursor:
            await cursor.execute(command, params or ())
            return cursor.rowcount

    async def get_database(self) -> list[dict[str, Any]]:
        """获取 MySQL 中的数据库列表及容量信息。"""
        try:
            if not await self.connect():
                return []
            query = """
                SELECT SCHEMA_NAME AS name,
                       DEFAULT_CHARACTER_SET_NAME AS encoding,
                       DEFAULT_COLLATION_NAME AS collation,
                       (
                           SELECT COUNT(*)
                           FROM information_schema.TABLES t
                           WHERE t.TABLE_SCHEMA = s.SCHEMA_NAME
                             AND t.TABLE_TYPE = 'BASE TABLE'
                       ) AS tables_count
                FROM information_schema.SCHEMATA s
                WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                ORDER BY SCHEMA_NAME
            """
            databases = await self._execute_query(query)
            for db in databases:
                size_result = await self._execute_query(
                    """
                    SELECT ROUND(SUM(data_length + index_length), 2) AS size_bytes
                    FROM information_schema.TABLES
                    WHERE table_schema = %s
                    """,
                    (db["name"],),
                )
                size_bytes = size_result[0]["size_bytes"] if size_result and size_result[0]["size_bytes"] else 0
                db["size_bytes"] = int(size_bytes or 0)
                db["size"] = format_size(db["size_bytes"])
            return databases
        except Exception as exc:
            logger.error("Failed to get MySQL databases: %s", exc)
            return []
        finally:
            await self.close()

    async def create_database(
            self,
            name: str,
            charset: str = "utf8mb4",
            collation: str = "utf8mb4_unicode_ci",
            **kwargs: Any,
    ) -> bool:
        """
        创建 MySQL 数据库。

        Args:
            name: 数据库名称。
            charset: 字符集。
            collation: 排序规则。
            **kwargs: 预留扩展参数。

        Returns:
            bool: 创建是否成功。
        """
        try:
            if not await self.connect():
                return False
            await self._execute_command(
                f"CREATE DATABASE {self._quote_identifier(name)} CHARACTER SET {charset} COLLATE {collation}"
            )
            return True
        except Exception as exc:
            logger.error("Failed to create MySQL database %s: %s", name, exc)
            raise
        finally:
            await self.close()

    async def drop_database(self, name: str) -> bool:
        """
        删除指定的 MySQL 数据库。

        Args:
            name: 数据库名称。

        Returns:
            bool: 删除是否成功。
        """
        try:
            if not await self.connect():
                return False
            await self._execute_command(f"DROP DATABASE {self._quote_identifier(name)}")
            return True
        except Exception as exc:
            logger.error("Failed to drop MySQL database %s: %s", name, exc)
            raise
        finally:
            await self.close()

    async def get_schemas(self, database: str | None = None) -> list[dict[str, Any]]:
        """
        获取 MySQL schema 列表。

        MySQL 中 schema 与 database 基本等价，这里直接复用数据库列表。
        """
        databases = await self.get_database()
        return [{"name": db["name"], "owner": None, "tables_count": db.get("tables_count", 0)} for db in databases]

    async def get_tables(self, database: str | None = None, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取指定 MySQL 数据库中的表列表。

        Args:
            database: 数据库名称。
            schema_name: schema 名称，MySQL 中等价于数据库名。

        Returns:
            list[dict[str, Any]]: 表基础信息列表。
        """
        try:
            db_name = database or schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT TABLE_SCHEMA AS schema_name,
                       TABLE_NAME AS table_name,
                       TABLE_TYPE AS table_type,
                       TABLE_ROWS AS row_count,
                       DATA_LENGTH AS data_length,
                       INDEX_LENGTH AS index_length,
                       (DATA_LENGTH + INDEX_LENGTH) AS total_size_bytes,
                       TABLE_COMMENT AS description
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """
            tables = await self._execute_query(query, (db_name,))
            for table in tables:
                table["total_size"] = format_size(table.get("total_size_bytes", 0) or 0)
            return tables
        except Exception as exc:
            logger.error("Failed to get MySQL tables: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_columns(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 MySQL 表字段信息。

        Args:
            table_name: 表名。
            schema_name: 数据库名。

        Returns:
            list[dict[str, Any]]: 字段信息列表。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT COLUMN_NAME AS column_name,
                       DATA_TYPE AS data_type,
                       IF(IS_NULLABLE = 'YES', TRUE, FALSE) AS is_nullable,
                       COLUMN_DEFAULT AS column_default,
                       CHARACTER_MAXIMUM_LENGTH AS character_maximum_length,
                       NUMERIC_PRECISION AS numeric_precision,
                       NUMERIC_SCALE AS numeric_scale,
                       ORDINAL_POSITION AS ordinal_position,
                       IF(COLUMN_KEY = 'PRI', TRUE, FALSE) AS is_primary_key,
                       IF(COLUMN_KEY = 'UNI', TRUE, FALSE) AS is_unique,
                       COLUMN_COMMENT AS description
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """
            return await self._execute_query(query, (db_name, table_name))
        except Exception as exc:
            logger.error("Failed to get MySQL table columns: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_indexes(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 MySQL 表索引信息。

        Args:
            table_name: 表名。
            schema_name: 数据库名。

        Returns:
            list[dict[str, Any]]: 索引信息列表。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT INDEX_NAME AS index_name,
                       INDEX_TYPE AS index_type,
                       GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS columns,
                       IF(NON_UNIQUE = 0, TRUE, FALSE) AS is_unique,
                       IF(INDEX_NAME = 'PRIMARY', TRUE, FALSE) AS is_primary
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                GROUP BY INDEX_NAME, INDEX_TYPE, NON_UNIQUE
                ORDER BY INDEX_NAME
            """
            indexes = await self._execute_query(query, (db_name, table_name))
            for idx in indexes:
                idx["definition"] = f"INDEX {idx['index_name']} ({idx['columns']})"
            return indexes
        except Exception as exc:
            logger.error("Failed to get MySQL table indexes: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_constraints(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 MySQL 表约束信息。

        Args:
            table_name: 表名。
            schema_name: 数据库名。

        Returns:
            list[dict[str, Any]]: 约束信息列表。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT tc.CONSTRAINT_NAME AS constraint_name,
                       tc.CONSTRAINT_TYPE AS constraint_type,
                       GROUP_CONCAT(kcu.COLUMN_NAME ORDER BY kcu.ORDINAL_POSITION) AS columns,
                       kcu.REFERENCED_TABLE_NAME AS referenced_table,
                       GROUP_CONCAT(kcu.REFERENCED_COLUMN_NAME ORDER BY kcu.ORDINAL_POSITION) AS referenced_columns
                FROM information_schema.TABLE_CONSTRAINTS tc
                LEFT JOIN information_schema.KEY_COLUMN_USAGE kcu
                  ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                 AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
                 AND tc.TABLE_NAME = kcu.TABLE_NAME
                WHERE tc.TABLE_SCHEMA = %s
                  AND tc.TABLE_NAME = %s
                GROUP BY tc.CONSTRAINT_NAME, tc.CONSTRAINT_TYPE, kcu.REFERENCED_TABLE_NAME
                ORDER BY tc.CONSTRAINT_TYPE, tc.CONSTRAINT_NAME
            """
            constraints = await self._execute_query(query, (db_name, table_name))
            for const in constraints:
                const["definition"] = f"{const['constraint_type']} ({const['columns'] or ''})"
            return constraints
        except Exception as exc:
            logger.error("Failed to get MySQL table constraints: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_structure(
            self,
            table_name: str,
            database: str | None = None,
            schema_name: str | None = None,
    ) -> dict[str, Any]:
        """
        获取 MySQL 表的完整结构信息。

        Args:
            table_name: 表名。
            database: 数据库名。
            schema_name: schema 名称，MySQL 中等价于数据库名。

        Returns:
            dict[str, Any]: 包含表、字段、索引和约束信息的结构结果。
        """
        db_name = database or schema_name or self.database
        tables = await self.get_tables(database=db_name, schema_name=db_name)
        table_info = next((t for t in tables if t["table_name"] == table_name), None)
        if not table_info:
            raise ValueError(f"Table {db_name}.{table_name} not found")
        columns = await self.get_table_columns(table_name, db_name)
        indexes = await self.get_table_indexes(table_name, db_name)
        constraints = await self.get_table_constraints(table_name, db_name)
        return {"table_info": table_info, "columns": columns, "indexes": indexes, "constraints": constraints}

    async def get_table_ddl(self, table_name: str, schema_name: str | None = None) -> str:
        """
        获取 MySQL 表的建表语句。

        Args:
            table_name: 表名。
            schema_name: 数据库名。

        Returns:
            str: `SHOW CREATE TABLE` 返回的 DDL 文本。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return "-- unable to connect database"
            result = await self._execute_query(f"SHOW CREATE TABLE {self._quote_identifier(table_name)}")
            if result:
                return result[0].get("Create Table", f"-- unable to get ddl for {table_name}")
            return f"-- unable to get ddl for {table_name}"
        except Exception as exc:
            logger.error("Failed to get MySQL table ddl %s: %s", table_name, exc)
            return f"-- get ddl failed: {exc}"
        finally:
            await self.close()

    async def get_views(self, database: str | None = None, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 MySQL 视图列表。

        Args:
            database: 数据库名。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 视图基础信息列表。
        """
        try:
            db_name = database or schema_name or self.database
            if not await self.connect(db_name):
                return []
            query = """
                SELECT TABLE_NAME AS view_name,
                       TABLE_SCHEMA AS schema_name,
                       VIEW_DEFINITION AS view_definition,
                       IS_UPDATABLE AS is_updatable,
                       CHECK_OPTION AS check_option,
                       'VIEW' AS view_type
                FROM information_schema.VIEWS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
            """
            result = await self._execute_query(query, (db_name,))
            for row in result:
                row["is_updatable"] = row.get("is_updatable") == "YES"
            return result
        except Exception as exc:
            logger.error("Failed to get MySQL views: %s", exc)
            return []
        finally:
            await self.close()

    async def _get_view_definition_internal(self, view_name: str) -> str:
        """
        获取视图定义的内部实现。

        Args:
            view_name: 视图名称。

        Returns:
            str: 视图 DDL 或错误提示文本。
        """
        try:
            result = await self._execute_query(f"SHOW CREATE VIEW {self._quote_identifier(view_name)}")
            if result:
                return result[0].get("Create View", f"-- unable to get view definition for {view_name}")
        except Exception as exc:
            logger.error("Failed to get MySQL view definition %s: %s", view_name, exc)
        return f"-- unable to get view definition for {view_name}"

    async def _get_view_dependencies_internal(self, view_name: str, schema_name: str) -> list[str]:
        """
        获取视图依赖的表列表。

        Args:
            view_name: 视图名称。
            schema_name: 数据库名。

        Returns:
            list[str]: 依赖的表名列表。
        """
        try:
            query = """
                SELECT DISTINCT REFERENCED_TABLE_NAME AS table_name
                FROM information_schema.VIEW_TABLE_USAGE
                WHERE VIEW_SCHEMA = %s
                  AND VIEW_NAME = %s
                  AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY REFERENCED_TABLE_NAME
            """
            result = await self._execute_query(query, (schema_name, view_name))
            return [row["table_name"] for row in result]
        except Exception as exc:
            logger.error("Failed to get MySQL view dependencies %s: %s", view_name, exc)
            return []

    async def get_view_structure(self, view_name: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        获取 MySQL 视图的完整结构信息。

        Args:
            view_name: 视图名称。
            schema_name: 数据库名。

        Returns:
            dict[str, Any]: 包含视图、字段、依赖和定义信息的结果。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                raise ValueError("Failed to connect database")
            view_query = """
                SELECT TABLE_NAME AS view_name,
                       TABLE_SCHEMA AS schema_name,
                       VIEW_DEFINITION AS view_definition,
                       IS_UPDATABLE AS is_updatable,
                       CHECK_OPTION AS check_option,
                       'VIEW' AS view_type
                FROM information_schema.VIEWS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
            """
            view_info = await self._execute_query(view_query, (db_name, view_name))
            if not view_info:
                raise ValueError(f"View {db_name}.{view_name} not found")
            view_data = view_info[0]
            view_data["is_updatable"] = view_data.get("is_updatable") == "YES"
            columns_query = """
                SELECT COLUMN_NAME AS column_name,
                       DATA_TYPE AS data_type,
                       IF(IS_NULLABLE = 'YES', TRUE, FALSE) AS is_nullable,
                       ORDINAL_POSITION AS ordinal_position,
                       COLUMN_COMMENT AS description
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """
            columns = await self._execute_query(columns_query, (db_name, view_name))
            definition_sql = await self._get_view_definition_internal(view_name)
            dependencies = await self._get_view_dependencies_internal(view_name, db_name)
            return {"view_info": view_data, "columns": columns, "dependencies": dependencies, "definition_sql": definition_sql}
        except Exception as exc:
            logger.error("Failed to get MySQL view structure %s: %s", view_name, exc)
            raise
        finally:
            await self.close()

    async def get_view_definition(self, view_name: str, schema_name: str | None = None) -> str:
        """
        获取 MySQL 视图定义。

        Args:
            view_name: 视图名称。
            schema_name: 数据库名。

        Returns:
            str: 视图定义 SQL。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return "-- unable to connect database"
            return await self._get_view_definition_internal(view_name)
        except Exception as exc:
            return f"-- get view definition failed: {exc}"
        finally:
            await self.close()

    async def get_view_dependencies(self, view_name: str, schema_name: str | None = None) -> list[str]:
        """
        获取 MySQL 视图依赖。

        Args:
            view_name: 视图名称。
            schema_name: 数据库名。

        Returns:
            list[str]: 依赖的对象名称列表。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return []
            return await self._get_view_dependencies_internal(view_name, db_name)
        except Exception:
            return []
        finally:
            await self.close()

    async def query_data(
            self,
            table_name: str,
            schema_name: str | None = None,
            page: int = 1,
            page_size: int = 20,
            where: str | None = None,
            order_by: str | None = None,
    ) -> dict[str, Any]:
        """
        分页查询 MySQL 表数据。

        Args:
            table_name: 表名。
            schema_name: 数据库名。
            page: 页码。
            page_size: 每页条数。
            where: 追加的 where 条件。
            order_by: 排序表达式。

        Returns:
            dict[str, Any]: 统一分页结果。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return self._empty_page_result(page, page_size)
            count_query = f"SELECT COUNT(*) AS total FROM {self._quote_identifier(table_name)}"
            if where:
                count_query += f" WHERE {where}"
            count_result = await self._execute_query(count_query)
            total = count_result[0]["total"] if count_result else 0
            offset = (page - 1) * page_size
            data_query = f"SELECT * FROM {self._quote_identifier(table_name)}"
            if where:
                data_query += f" WHERE {where}"
            if order_by:
                data_query += f" ORDER BY {order_by}"
            data_query += f" LIMIT {page_size} OFFSET {offset}"
            rows = await self._execute_query(data_query)
            return self._build_page_result(rows, total, page, page_size)
        except Exception as exc:
            logger.error("Failed to query MySQL data: %s", exc)
            return self._empty_page_result(page, page_size)
        finally:
            await self.close()

    async def execute_sql(self, sql: str, is_query: bool = True) -> dict[str, Any]:
        """
        执行自定义 MySQL SQL。

        Args:
            sql: 待执行 SQL。
            is_query: 是否为查询语句。

        Returns:
            dict[str, Any]: 执行结果摘要。
        """
        start_time = time.time()
        try:
            if not await self.connect():
                return {"success": False, "message": "database connection failed", "columns": None, "rows": None, "affected_rows": None, "execution_time": 0}
            if is_query:
                rows = await self._execute_query(sql)
                rows_list = [serialize_row(row) for row in rows]
                columns = list(rows_list[0].keys()) if rows_list else []
                return {"success": True, "message": f"query success, returned {len(rows_list)} rows", "columns": columns, "rows": rows_list, "affected_rows": None, "execution_time": round(time.time() - start_time, 3)}
            affected_rows = await self._execute_command(sql)
            return {"success": True, "message": f"execute success, affected {affected_rows} rows", "columns": None, "rows": None, "affected_rows": affected_rows, "execution_time": round(time.time() - start_time, 3)}
        except Exception as exc:
            logger.error("Failed to execute MySQL sql: %s", exc)
            return {"success": False, "message": str(exc), "columns": None, "rows": None, "affected_rows": 0, "execution_time": 0}
        finally:
            await self.close()

    async def insert_data(self, table_name: str, data: dict[str, Any], schema_name: str | None = None) -> dict[str, Any]:
        """
        向 MySQL 表插入一条记录。

        Args:
            table_name: 表名。
            data: 待插入字段和值。
            schema_name: 数据库名。

        Returns:
            dict[str, Any]: 插入结果。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ", ".join(["%s"] * len(values))
            quoted_columns = ", ".join(self._quote_identifier(column) for column in columns)
            query = f"INSERT INTO {self._quote_identifier(table_name)} ({quoted_columns}) VALUES ({placeholders})"
            affected_rows = await self._execute_command(query, tuple(values))
            return {"success": True, "message": "insert success", "affected_rows": affected_rows}
        except Exception as exc:
            logger.error("Failed to insert MySQL data: %s", exc)
            return {"success": False, "message": str(exc), "affected_rows": 0}
        finally:
            await self.close()

    async def update_data(self, table_name: str, data: dict[str, Any], where: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        更新 MySQL 表记录。

        Args:
            table_name: 表名。
            data: 待更新字段和值。
            where: 更新条件。
            schema_name: 数据库名。

        Returns:
            dict[str, Any]: 更新结果。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            set_clause = ", ".join(f"{self._quote_identifier(k)} = %s" for k in data.keys())
            query = f"UPDATE {self._quote_identifier(table_name)} SET {set_clause} WHERE {where}"
            affected_rows = await self._execute_command(query, tuple(data.values()))
            return {"success": True, "message": f"update success, affected {affected_rows} rows", "affected_rows": affected_rows}
        except Exception as exc:
            logger.error("Failed to update MySQL data: %s", exc)
            return {"success": False, "message": str(exc), "affected_rows": 0}
        finally:
            await self.close()

    async def delete_data(self, table_name: str, where: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        删除 MySQL 表记录。

        Args:
            table_name: 表名。
            where: 删除条件。
            schema_name: 数据库名。

        Returns:
            dict[str, Any]: 删除结果。
        """
        try:
            db_name = schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            query = f"DELETE FROM {self._quote_identifier(table_name)} WHERE {where}"
            affected_rows = await self._execute_command(query)
            return {"success": True, "message": f"delete success, affected {affected_rows} rows", "affected_rows": affected_rows}
        except Exception as exc:
            logger.error("Failed to delete MySQL data: %s", exc)
            return {"success": False, "message": str(exc), "affected_rows": 0}
        finally:
            await self.close()

    async def execute_ddl(self, sql: str, database: str | None = None, schema_name: str | None = None) -> dict[str, Any]:
        """
        执行 MySQL DDL 语句。

        Args:
            sql: DDL SQL。
            database: 数据库名。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 执行结果。
        """
        try:
            db_name = database or schema_name or self.database
            if not await self.connect(db_name):
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            await self._execute_command(sql)
            return {"success": True, "message": "ddl execute success", "affected_rows": 0}
        except Exception as exc:
            logger.error("Failed to execute MySQL ddl: %s", exc)
            return {"success": False, "message": f"ddl execute failed: {exc}", "affected_rows": 0}
        finally:
            await self.close()


class PostgresSQLHandler(BaseDatabaseHandler):
    """
    PostgreSQL 数据库处理器。

    基于 `asyncpg` 实现 PostgreSQL 的结构查询和数据操作能力。
    """

    identifier_quote = '"'

    async def connect(self, database: str | None = None) -> bool:
        """
        建立 PostgreSQL 连接。

        Args:
            database: 可选的目标数据库名称。

        Returns:
            bool: 连接是否成功。
        """
        try:
            import asyncpg

            self.conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=database or self.database,
                timeout=10,
            )
            return True
        except Exception as exc:
            logger.error("Failed to connect to PostgreSQL database: %s", exc)
            return False

    async def close(self) -> None:
        """关闭当前 PostgresSQL 连接。"""
        if self.conn:
            await self.conn.close()
            self.conn = None

    async def _execute_query(self, query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        """
        执行 PostgreSQL 查询语句。

        Args:
            query: SQL 查询语句。
            params: 查询参数。

        Returns:
            list[dict[str, Any]]: 字典格式的结果集。
        """
        records = await self.conn.fetch(query, *(params or ()))
        return [dict(record) for record in records]

    async def _execute_command(self, command: str, params: tuple[Any, ...] | None = None) -> int:
        """
        执行 PostgreSQL 写操作语句。

        Args:
            command: 非查询 SQL。
            params: SQL 参数。

        Returns:
            int: 影响行数。
        """
        status = await self.conn.execute(command, *(params or ()))
        try:
            return int(status.split()[-1])
        except Exception:
            return 0

    async def get_database(self) -> list[dict[str, Any]]:
        """获取 PostgreSQL 中的数据库列表及容量信息。"""
        try:
            if not await self.connect("postgres"):
                return []
            query = """
                SELECT d.datname AS name,
                       pg_catalog.pg_encoding_to_char(d.encoding) AS encoding,
                       pg_catalog.obj_description(d.oid, 'pg_database') AS description
                FROM pg_database d
                WHERE d.datistemplate = FALSE
                ORDER BY d.datname
            """
            databases = await self._execute_query(query)
            for db in databases:
                size_result = await self._execute_query("SELECT pg_database_size($1) AS size_bytes", (db["name"],))
                size_bytes = size_result[0]["size_bytes"] if size_result else 0
                db["size_bytes"] = int(size_bytes or 0)
                db["size"] = format_size(db["size_bytes"])
                db["tables_count"] = 0
            return databases
        except Exception as exc:
            logger.error("Failed to get PostgreSQL databases: %s", exc)
            return []
        finally:
            await self.close()

    async def create_database(
            self,
            name: str,
            owner: str | None = None,
            template: str | None = None,
            **kwargs: Any,
    ) -> bool:
        """
        创建 PostgreSQL 数据库。

        Args:
            name: 数据库名称。
            owner: 数据库所有者。
            template: 模板数据库名称。
            **kwargs: 预留扩展参数。

        Returns:
            bool: 创建是否成功。
        """
        try:
            if not await self.connect("postgres"):
                return False
            sql = f"CREATE DATABASE {self._quote_identifier(name)}"
            if owner:
                sql += f" OWNER {self._quote_identifier(owner)}"
            if template:
                sql += f" TEMPLATE {self._quote_identifier(template)}"
            await self._execute_command(sql)
            return True
        except Exception as exc:
            logger.error("Failed to create PostgreSQL database %s: %s", name, exc)
            raise
        finally:
            await self.close()

    async def drop_database(self, name: str) -> bool:
        """
        删除 PostgreSQL 数据库。

        Args:
            name: 数据库名称。

        Returns:
            bool: 删除是否成功。
        """
        try:
            if not await self.connect("postgres"):
                return False
            await self._execute_query(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = $1
                  AND pid <> pg_backend_pid()
                """,
                (name,),
            )
            await self._execute_command(f"DROP DATABASE {self._quote_identifier(name)}")
            return True
        except Exception as exc:
            logger.error("Failed to drop PostgreSQL database %s: %s", name, exc)
            raise
        finally:
            await self.close()

    async def get_schemas(self, database: str | None = None) -> list[dict[str, Any]]:
        """
        获取 PostgreSQL schema 列表。

        Args:
            database: 数据库名称。

        Returns:
            list[dict[str, Any]]: schema 信息列表。
        """
        try:
            if not await self.connect(database or self.database):
                return []
            query = """
                SELECT n.nspname AS name,
                       pg_catalog.pg_get_userbyid(n.nspowner) AS owner,
                       (
                           SELECT COUNT(*)
                           FROM pg_class c
                           WHERE c.relnamespace = n.oid
                             AND c.relkind = 'r'
                       ) AS tables_count
                FROM pg_namespace n
                WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
                  AND n.nspname NOT LIKE 'pg_toast%'
                  AND n.nspname NOT LIKE 'pg_temp_%'
                ORDER BY n.nspname
            """
            return await self._execute_query(query)
        except Exception as exc:
            logger.error("Failed to get PostgreSQL schemas: %s", exc)
            return []
        finally:
            await self.close()

    async def get_tables(self, database: str | None = None, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 PostgreSQL 表列表。

        Args:
            database: 数据库名称。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 表基础信息列表。
        """
        try:
            if not await self.connect(database or self.database):
                return []
            schema = schema_name or "public"
            query = """
                SELECT ns.nspname AS schema_name,
                       cls.relname AS table_name,
                       'BASE TABLE' AS table_type,
                       pg_stat_get_live_tuples(cls.oid) AS row_count,
                       pg_relation_size(cls.oid) AS data_length,
                       pg_indexes_size(cls.oid) AS index_length,
                       pg_total_relation_size(cls.oid) AS total_size_bytes,
                       pg_catalog.obj_description(cls.oid, 'pg_class') AS description
                FROM pg_class cls
                JOIN pg_namespace ns ON ns.oid = cls.relnamespace
                WHERE cls.relkind = 'r'
                  AND ns.nspname = $1
                ORDER BY cls.relname
            """
            tables = await self._execute_query(query, (schema,))
            for table in tables:
                table["total_size"] = format_size(table.get("total_size_bytes", 0) or 0)
            return tables
        except Exception as exc:
            logger.error("Failed to get PostgreSQL tables: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_columns(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 PostgreSQL 表字段信息。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 字段信息列表。
        """
        try:
            if not await self.connect():
                return []
            schema = schema_name or "public"
            query = """
                SELECT cols.column_name,
                       cols.data_type,
                       (cols.is_nullable = 'YES') AS is_nullable,
                       cols.column_default,
                       cols.character_maximum_length,
                       cols.numeric_precision,
                       cols.numeric_scale,
                       cols.ordinal_position,
                       EXISTS (
                           SELECT 1
                           FROM information_schema.table_constraints tc
                           JOIN information_schema.key_column_usage kcu
                             ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                          WHERE tc.constraint_type = 'PRIMARY KEY'
                            AND tc.table_schema = cols.table_schema
                            AND tc.table_name = cols.table_name
                            AND kcu.column_name = cols.column_name
                       ) AS is_primary_key,
                       FALSE AS is_unique,
                       pgd.description AS description
                FROM information_schema.columns cols
                LEFT JOIN pg_catalog.pg_statio_all_tables st
                  ON st.schemaname = cols.table_schema
                 AND st.relname = cols.table_name
                LEFT JOIN pg_catalog.pg_description pgd
                  ON pgd.objoid = st.relid
                 AND pgd.objsubid = cols.ordinal_position
                WHERE cols.table_schema = $1
                  AND cols.table_name = $2
                ORDER BY cols.ordinal_position
            """
            return await self._execute_query(query, (schema, table_name))
        except Exception as exc:
            logger.error("Failed to get PostgreSQL table columns: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_indexes(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 PostgreSQL 表索引信息。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 索引信息列表。
        """
        try:
            if not await self.connect():
                return []
            schema = schema_name or "public"
            query = """
                SELECT idx.indexname AS index_name,
                       CASE WHEN idx.indexdef ILIKE '% USING btree %' THEN 'btree' ELSE 'other' END AS index_type,
                       regexp_replace(split_part(split_part(idx.indexdef, '(', 2), ')', 1), '\s+', '', 'g') AS columns,
                       (idx.indexdef ILIKE '% UNIQUE INDEX %') AS is_unique,
                       (idx.indexname LIKE '%pkey') AS is_primary,
                       idx.indexdef AS definition
                FROM pg_indexes idx
                WHERE idx.schemaname = $1
                  AND idx.tablename = $2
                ORDER BY idx.indexname
            """
            return await self._execute_query(query, (schema, table_name))
        except Exception as exc:
            logger.error("Failed to get PostgreSQL table indexes: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_constraints(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 PostgreSQL 表约束信息。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 约束信息列表。
        """
        try:
            if not await self.connect():
                return []
            schema = schema_name or "public"
            query = """
                SELECT tc.constraint_name,
                       tc.constraint_type,
                       string_agg(kcu.column_name, ',' ORDER BY kcu.ordinal_position) AS columns,
                       ccu.table_name AS referenced_table,
                       string_agg(ccu.column_name, ',' ORDER BY kcu.ordinal_position) AS referenced_columns
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage ccu
                  ON tc.constraint_name = ccu.constraint_name
                 AND tc.table_schema = ccu.table_schema
                WHERE tc.table_schema = $1
                  AND tc.table_name = $2
                GROUP BY tc.constraint_name, tc.constraint_type, ccu.table_name
                ORDER BY tc.constraint_type, tc.constraint_name
            """
            constraints = await self._execute_query(query, (schema, table_name))
            for item in constraints:
                item["definition"] = f"{item['constraint_type']} ({item['columns'] or ''})"
            return constraints
        except Exception as exc:
            logger.error("Failed to get PostgreSQL table constraints: %s", exc)
            return []
        finally:
            await self.close()

    async def get_table_structure(
            self,
            table_name: str,
            database: str | None = None,
            schema_name: str | None = None,
    ) -> dict[str, Any]:
        """
        获取 PostgreSQL 表完整结构。

        Args:
            table_name: 表名。
            database: 数据库名称。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 包含表、字段、索引和约束的结构结果。
        """
        schema = schema_name or "public"
        tables = await self.get_tables(database=database, schema_name=schema)
        table_info = next((t for t in tables if t["table_name"] == table_name), None)
        if not table_info:
            raise ValueError(f"Table {schema}.{table_name} not found")
        columns = await self.get_table_columns(table_name, schema)
        indexes = await self.get_table_indexes(table_name, schema)
        constraints = await self.get_table_constraints(table_name, schema)
        return {"table_info": table_info, "columns": columns, "indexes": indexes, "constraints": constraints}

    async def get_table_ddl(self, table_name: str, schema_name: str | None = None) -> str:
        """
        获取 PostgreSQL 表 DDL。

        当前实现基于字段和主键约束动态拼装基础 `CREATE TABLE`，
        适合结构展示，不等同于 `pg_dump` 的完整输出。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            str: 建表语句或错误提示。
        """
        try:
            schema = schema_name or "public"
            columns = await self.get_table_columns(table_name, schema)
            if not columns:
                return f"-- unable to get ddl for {schema}.{table_name}"
            column_defs: list[str] = []
            for column in columns:
                line = f"    {self._quote_identifier(column['column_name'])} {column['data_type']}"
                if not column.get("is_nullable", True):
                    line += " NOT NULL"
                if column.get("column_default") is not None:
                    line += f" DEFAULT {column['column_default']}"
                column_defs.append(line)
            constraints = await self.get_table_constraints(table_name, schema)
            for constraint in constraints:
                if constraint["constraint_type"] == "PRIMARY KEY" and constraint.get("columns"):
                    column_defs.append(
                        f"    CONSTRAINT {self._quote_identifier(constraint['constraint_name'])} PRIMARY KEY ({constraint['columns']})"
                    )
            return f"CREATE TABLE {self._qualified_name(table_name, schema)} (\n" + ",\n".join(column_defs) + "\n);"
        except Exception as exc:
            logger.error("Failed to get PostgreSQL table ddl %s: %s", table_name, exc)
            return f"-- get ddl failed: {exc}"

    async def get_views(self, database: str | None = None, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取 PostgreSQL 视图列表。

        Args:
            database: 数据库名称。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 视图基础信息列表。
        """
        try:
            if not await self.connect(database or self.database):
                return []
            schema = schema_name or "public"
            query = """
                SELECT table_name AS view_name,
                       table_schema AS schema_name,
                       view_definition,
                       FALSE AS is_updatable,
                       NULL AS check_option,
                       'VIEW' AS view_type
                FROM information_schema.views
                WHERE table_schema = $1
                ORDER BY table_name
            """
            return await self._execute_query(query, (schema,))
        except Exception as exc:
            logger.error("Failed to get PostgreSQL views: %s", exc)
            return []
        finally:
            await self.close()

    async def get_view_structure(self, view_name: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        获取 PostgreSQL 视图完整结构。

        Args:
            view_name: 视图名称。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 包含视图、字段、依赖和定义的结果。
        """
        try:
            schema = schema_name or "public"
            if not await self.connect():
                raise ValueError("Failed to connect database")
            query = """
                SELECT table_name AS view_name,
                       table_schema AS schema_name,
                       view_definition,
                       FALSE AS is_updatable,
                       NULL AS check_option,
                       'VIEW' AS view_type
                FROM information_schema.views
                WHERE table_schema = $1
                  AND table_name = $2
            """
            result = await self._execute_query(query, (schema, view_name))
            if not result:
                raise ValueError(f"View {schema}.{view_name} not found")
            view_info = result[0]
            columns_query = """
                SELECT column_name,
                       data_type,
                       (is_nullable = 'YES') AS is_nullable,
                       ordinal_position,
                       NULL AS description
                FROM information_schema.columns
                WHERE table_schema = $1
                  AND table_name = $2
                ORDER BY ordinal_position
            """
            columns = await self._execute_query(columns_query, (schema, view_name))
            dependencies = await self.get_view_dependencies(view_name, schema)
            definition_sql = await self.get_view_definition(view_name, schema)
            return {"view_info": view_info, "columns": columns, "dependencies": dependencies, "definition_sql": definition_sql}
        except Exception as exc:
            logger.error("Failed to get PostgreSQL view structure %s: %s", view_name, exc)
            raise
        finally:
            await self.close()

    async def get_view_definition(self, view_name: str, schema_name: str | None = None) -> str:
        """
        获取 PostgreSQL 视图定义。

        Args:
            view_name: 视图名称。
            schema_name: schema 名称。

        Returns:
            str: `CREATE OR REPLACE VIEW` 语句或错误提示。
        """
        try:
            if not await self.connect():
                return "-- unable to connect database"
            schema = schema_name or "public"
            query = """
                SELECT definition
                FROM pg_views
                WHERE schemaname = $1
                  AND viewname = $2
            """
            result = await self._execute_query(query, (schema, view_name))
            if result:
                return f"CREATE OR REPLACE VIEW {self._qualified_name(view_name, schema)} AS\n{result[0]['definition']}"
            return f"-- unable to get view definition for {schema}.{view_name}"
        except Exception as exc:
            return f"-- get view definition failed: {exc}"
        finally:
            await self.close()

    async def get_view_dependencies(self, view_name: str, schema_name: str | None = None) -> list[str]:
        """
        获取 PostgreSQL 视图依赖。

        Args:
            view_name: 视图名称。
            schema_name: schema 名称。

        Returns:
            list[str]: 依赖的表或视图名称列表。
        """
        try:
            if not await self.connect():
                return []
            schema = schema_name or "public"
            query = """
                SELECT DISTINCT dep_ns.nspname || '.' || dep_cls.relname AS table_name
                FROM pg_rewrite rw
                JOIN pg_class view_cls ON rw.ev_class = view_cls.oid
                JOIN pg_namespace view_ns ON view_ns.oid = view_cls.relnamespace
                JOIN pg_depend dep ON dep.objid = rw.oid
                JOIN pg_class dep_cls ON dep.refobjid = dep_cls.oid
                JOIN pg_namespace dep_ns ON dep_ns.oid = dep_cls.relnamespace
                WHERE view_ns.nspname = $1
                  AND view_cls.relname = $2
                  AND dep_cls.relkind IN ('r', 'v', 'm')
            """
            result = await self._execute_query(query, (schema, view_name))
            return [row["table_name"] for row in result]
        except Exception as exc:
            logger.error("Failed to get PostgreSQL view dependencies %s: %s", view_name, exc)
            return []
        finally:
            await self.close()

    async def query_data(
            self,
            table_name: str,
            schema_name: str | None = None,
            page: int = 1,
            page_size: int = 20,
            where: str | None = None,
            order_by: str | None = None,
    ) -> dict[str, Any]:
        """
        分页查询 PostgreSQL 表数据。

        Args:
            table_name: 表名。
            schema_name: schema 名称。
            page: 页码。
            page_size: 每页条数。
            where: 追加查询条件。
            order_by: 排序表达式。

        Returns:
            dict[str, Any]: 统一分页结果。
        """
        try:
            if not await self.connect():
                return self._empty_page_result(page, page_size)
            qualified_name = self._qualified_name(table_name, schema_name or "public")
            count_query = f"SELECT COUNT(*) AS total FROM {qualified_name}"
            if where:
                count_query += f" WHERE {where}"
            count_result = await self._execute_query(count_query)
            total = count_result[0]["total"] if count_result else 0
            offset = (page - 1) * page_size
            data_query = f"SELECT * FROM {qualified_name}"
            if where:
                data_query += f" WHERE {where}"
            if order_by:
                data_query += f" ORDER BY {order_by}"
            data_query += f" LIMIT {page_size} OFFSET {offset}"
            rows = await self._execute_query(data_query)
            return self._build_page_result(rows, total, page, page_size)
        except Exception as exc:
            logger.error("Failed to query PostgreSQL data: %s", exc)
            return self._empty_page_result(page, page_size)
        finally:
            await self.close()

    async def execute_sql(self, sql: str, is_query: bool = True) -> dict[str, Any]:
        """
        执行自定义 PostgreSQL SQL。

        Args:
            sql: 待执行 SQL。
            is_query: 是否为查询语句。

        Returns:
            dict[str, Any]: 执行结果摘要。
        """
        start_time = time.time()
        try:
            if not await self.connect():
                return {"success": False, "message": "database connection failed", "columns": None, "rows": None, "affected_rows": None, "execution_time": 0}
            if is_query:
                rows = await self._execute_query(sql)
                rows_list = [serialize_row(row) for row in rows]
                columns = list(rows_list[0].keys()) if rows_list else []
                return {"success": True, "message": f"query success, returned {len(rows_list)} rows", "columns": columns, "rows": rows_list, "affected_rows": None, "execution_time": round(time.time() - start_time, 3)}
            affected_rows = await self._execute_command(sql)
            return {"success": True, "message": f"execute success, affected {affected_rows} rows", "columns": None, "rows": None, "affected_rows": affected_rows, "execution_time": round(time.time() - start_time, 3)}
        except Exception as exc:
            logger.error("Failed to execute PostgreSQL sql: %s", exc)
            return {"success": False, "message": str(exc), "columns": None, "rows": None, "affected_rows": 0, "execution_time": 0}
        finally:
            await self.close()

    async def insert_data(self, table_name: str, data: dict[str, Any], schema_name: str | None = None) -> dict[str, Any]:
        """
        向 PostgreSQL 表插入一条记录。

        Args:
            table_name: 表名。
            data: 待插入字段和值。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 插入结果。
        """
        try:
            if not await self.connect():
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ", ".join(f"${index}" for index in range(1, len(values) + 1))
            quoted_columns = ", ".join(self._quote_identifier(column) for column in columns)
            query = f"INSERT INTO {self._qualified_name(table_name, schema_name or 'public')} ({quoted_columns}) VALUES ({placeholders})"
            affected_rows = await self._execute_command(query, tuple(values))
            return {"success": True, "message": "insert success", "affected_rows": affected_rows}
        except Exception as exc:
            logger.error("Failed to insert PostgreSQL data: %s", exc)
            return {"success": False, "message": str(exc), "affected_rows": 0}
        finally:
            await self.close()

    async def update_data(self, table_name: str, data: dict[str, Any], where: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        更新 PostgreSQL 表记录。

        Args:
            table_name: 表名。
            data: 待更新字段和值。
            where: 更新条件。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 更新结果。
        """
        try:
            if not await self.connect():
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            set_clause = ", ".join(f"{self._quote_identifier(key)} = ${index}" for index, key in enumerate(data.keys(), start=1))
            query = f"UPDATE {self._qualified_name(table_name, schema_name or 'public')} SET {set_clause} WHERE {where}"
            affected_rows = await self._execute_command(query, tuple(data.values()))
            return {"success": True, "message": f"update success, affected {affected_rows} rows", "affected_rows": affected_rows}
        except Exception as exc:
            logger.error("Failed to update PostgreSQL data: %s", exc)
            return {"success": False, "message": str(exc), "affected_rows": 0}
        finally:
            await self.close()

    async def delete_data(self, table_name: str, where: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        删除 PostgreSQL 表记录。

        Args:
            table_name: 表名。
            where: 删除条件。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 删除结果。
        """
        try:
            if not await self.connect():
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            query = f"DELETE FROM {self._qualified_name(table_name, schema_name or 'public')} WHERE {where}"
            affected_rows = await self._execute_command(query)
            return {"success": True, "message": f"delete success, affected {affected_rows} rows", "affected_rows": affected_rows}
        except Exception as exc:
            logger.error("Failed to delete PostgreSQL data: %s", exc)
            return {"success": False, "message": str(exc), "affected_rows": 0}
        finally:
            await self.close()

    async def execute_ddl(self, sql: str, database: str | None = None, schema_name: str | None = None) -> dict[str, Any]:
        """
        执行 PostgreSQL DDL 语句。

        Args:
            sql: DDL SQL。
            database: 目标数据库。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 执行结果。
        """
        try:
            if not await self.connect(database or self.database):
                return {"success": False, "message": "database connection failed", "affected_rows": 0}
            await self._execute_command(sql)
            return {"success": True, "message": "ddl execute success", "affected_rows": 0}
        except Exception as exc:
            logger.error("Failed to execute PostgreSQL ddl: %s", exc)
            return {"success": False, "message": f"ddl execute failed: {exc}", "affected_rows": 0}
        finally:
            await self.close()


HANDLER_REGISTRY: dict[str, type[DatabaseHandler]] = {
    "mysql": MySQLHandler,
    "postgresql": PostgresSQLHandler,
}


def create_database_handler(
        db_type: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
) -> DatabaseHandler:
    """
    根据数据库类型创建对应的处理器。

    Args:
        db_type: 数据库类型，目前支持 `mysql` 和 `postgresql`。
        host: 数据库地址。
        port: 数据库端口。
        user: 用户名。
        password: 密码。
        database: 默认数据库名称。

    Returns:
        DatabaseHandler: 具体的数据库处理器实例。

    Raises:
        ValueError: 当数据库类型不受支持时抛出。
    """
    handler_class = HANDLER_REGISTRY.get(db_type.lower())
    if handler_class is None:
        raise ValueError(f"unsupported database type: {db_type}")
    return handler_class(host, port, user, password, database)


class AsyncDatabaseManagerService:
    """
    数据源管理服务。

    基于项目配置中的 `DATABASE_URL` 自动选择对应的数据库处理器，
    对外提供统一的异步数据源管理能力。
    """

    def __init__(self) -> None:
        """
        初始化数据源管理服务。

        Raises:
            ValueError: 当无法从配置中解析数据库连接信息时抛出。
        """
        db_info = parse_database_url(getattr(settings, "DATABASE_URL", None))
        if not db_info:
            raise ValueError("DATABASE_URL is not configured or unsupported")

        self._db_info = db_info
        self._handler = create_database_handler(
            db_type=db_info["db_type"],
            host=db_info["host"],
            port=db_info["port"],
            user=db_info["user"],
            password=db_info["password"],
            database=db_info["database"],
        )

    @staticmethod
    def get_database_configs() -> dict[str, Any] | None:
        """
        获取当前配置的数据库连接信息。

        Returns:
            dict[str, Any] | None: 解析后的连接配置，无配置时返回 `None`。
        """
        return parse_database_url(getattr(settings, "DATABASE_URL", None))

    async def get_database(self) -> dict[str, Any]:
        """
        获取当前处理器支持的数据库信息。

        Returns:
            dict[str, Any]: 底层处理器返回的数据库信息结果。
        """
        return await self._handler.get_database()

    async def create_database(self, database_name: str) -> dict[str, Any]:
        """
        创建数据库。

        Args:
            database_name: 数据库名称。

        Returns:
            dict[str, Any]: 底层处理器返回的创建结果。
        """
        return await self._handler.create_database(database_name)

    async def drop_database(self, database_name: str) -> dict[str, Any]:
        """
        删除数据库。

        Args:
            database_name: 数据库名称。

        Returns:
            dict[str, Any]: 底层处理器返回的删除结果。
        """
        return await self._handler.drop_database(database_name)

    async def get_schemas(self) -> list[dict[str, Any]]:
        """
        获取 schema 列表。

        Returns:
            list[dict[str, Any]]: schema 信息列表。
        """
        return await self._handler.get_schemas()

    async def get_tables(self, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取数据表列表。

        Args:
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 数据表信息列表。
        """
        return await self._handler.get_tables(schema_name)

    async def get_table_columns(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取数据表字段信息。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 字段信息列表。
        """
        return await self._handler.get_table_columns(table_name, schema_name)

    async def get_table_indexes(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取数据表索引信息。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 索引信息列表。
        """
        return await self._handler.get_table_indexes(table_name, schema_name)

    async def get_table_constraints(self, table_name: str, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取数据表约束信息。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 约束信息列表。
        """
        return await self._handler.get_table_constraints(table_name, schema_name)

    async def get_table_structure(self, table_name: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        获取数据表结构详情。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 表结构详情。
        """
        return await self._handler.get_table_structure(table_name, schema_name)

    async def get_table_ddl(self, table_name: str, schema_name: str | None = None) -> str:
        """
        获取数据表 DDL。

        Args:
            table_name: 表名。
            schema_name: schema 名称。

        Returns:
            str: DDL 文本。
        """
        return await self._handler.get_table_ddl(table_name, schema_name)

    async def get_views(self, schema_name: str | None = None) -> list[dict[str, Any]]:
        """
        获取视图列表。

        Args:
            schema_name: schema 名称。

        Returns:
            list[dict[str, Any]]: 视图信息列表。
        """
        return await self._handler.get_views(schema_name)

    async def get_view_structure(self, view_name: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        获取视图结构信息。

        Args:
            view_name: 视图名称。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 视图结构详情。
        """
        return await self._handler.get_view_structure(view_name, schema_name)

    async def get_view_definition(self, view_name: str, schema_name: str | None = None) -> str:
        """
        获取视图定义。

        Args:
            view_name: 视图名称。
            schema_name: schema 名称。

        Returns:
            str: 视图定义 SQL。
        """
        return await self._handler.get_view_definition(view_name, schema_name)

    async def get_view_dependencies(self, view_name: str, schema_name: str | None = None) -> list[str]:
        """
        获取视图依赖关系。

        Args:
            view_name: 视图名称。
            schema_name: schema 名称。

        Returns:
            list[str]: 依赖对象列表。
        """
        return await self._handler.get_view_dependencies(view_name, schema_name)

    async def query_data(
            self,
            table_name: str,
            schema_name: str | None = None,
            page: int = 1,
            page_size: int = 20,
            where: str | None = None,
            order_by: str | None = None,
    ) -> dict[str, Any]:
        """
        分页查询数据表数据。

        Args:
            table_name: 表名。
            schema_name: schema 名称。
            page: 页码。
            page_size: 每页条数。
            where: 查询条件。
            order_by: 排序表达式。

        Returns:
            dict[str, Any]: 分页查询结果。
        """
        return await self._handler.query_data(
            table_name=table_name,
            schema_name=schema_name,
            page=page,
            page_size=page_size,
            where=where,
            order_by=order_by,
        )

    async def execute_sql(self, sql: str, is_query: bool = True) -> dict[str, Any]:
        """
        执行自定义 SQL。

        Args:
            sql: 待执行 SQL。
            is_query: 是否为查询语句。

        Returns:
            dict[str, Any]: SQL 执行结果。
        """
        return await self._handler.execute_sql(sql, is_query=is_query)

    async def insert_data(self, table_name: str, data: dict[str, Any], schema_name: str | None = None) -> dict[str, Any]:
        """
        向指定数据表插入一条记录。

        Args:
            table_name: 表名。
            data: 待插入数据。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 插入结果。
        """
        return await self._handler.insert_data(table_name, data, schema_name)

    async def update_data(
            self,
            table_name: str,
            data: dict[str, Any],
            where: str,
            schema_name: str | None = None,
    ) -> dict[str, Any]:
        """
        更新指定数据表的记录。

        Args:
            table_name: 表名。
            data: 待更新数据。
            where: 更新条件。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 更新结果。
        """
        return await self._handler.update_data(table_name, data, where, schema_name)

    async def delete_data(self, table_name: str, where: str, schema_name: str | None = None) -> dict[str, Any]:
        """
        删除指定数据表的记录。

        Args:
            table_name: 表名。
            where: 删除条件。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 删除结果。
        """
        return await self._handler.delete_data(table_name, where, schema_name)

    async def execute_ddl(
            self,
            sql: str,
            database: str | None = None,
            schema_name: str | None = None,
    ) -> dict[str, Any]:
        """
        执行 DDL 语句。

        Args:
            sql: DDL SQL。
            database: 目标数据库名称。
            schema_name: schema 名称。

        Returns:
            dict[str, Any]: 执行结果。
        """
        return await self._handler.execute_ddl(sql, database, schema_name)

