# SQLAlchemy 使用指南

> 基于 SQLAlchemy 2.0 官方文档整理，面向后端项目和 FastAPI 场景。  
> 官方文档入口：
> - https://docs.sqlalchemy.org/
> - https://docs.sqlalchemy.org/en/20/tutorial/
> - https://docs.sqlalchemy.org/en/20/orm/quickstart.html
> - https://docs.sqlalchemy.org/en/20/core/
> - https://docs.sqlalchemy.org/en/20/orm/
> - https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

## 1. 先建立整体认知

SQLAlchemy 不只是“ORM 工具”，它实际上由两层组成：

1. Core
   - 负责 SQL 表达式、表定义、连接执行
   - 更接近原生 SQL
   - 适合复杂查询、底层控制、批量操作
2. ORM
   - 负责把“表”映射成“Python 类”
   - 适合业务建模、对象关系管理、日常 CRUD

简单理解：

- `Engine` 管连接池
- `Connection` 管一次底层连接
- `Session` 管一次 ORM 事务上下文
- `Table` 是 Core 世界里的表
- `Model` 是 ORM 世界里的类
- `select()/insert()/update()/delete()` 是统一的 SQL 构造入口

## 2. SQLAlchemy 架构图

```mermaid
flowchart TD
    A[业务代码 / API / Service] --> B[Session / AsyncSession]
    A --> C[Core SQL Expression]
    B --> D[ORM Model]
    B --> E[select insert update delete]
    C --> E
    D --> E
    E --> F[Engine / AsyncEngine]
    F --> G[Connection Pool]
    G --> H[(MySQL / PostgreSQL / SQLite)]
```

上图可以这样理解：

- 业务代码通常不会直接操作数据库驱动
- SQLAlchemy 会帮你做 SQL 构造、连接池管理、对象映射
- ORM 和 Core 最终都会落到 Engine，再由 Engine 去访问数据库

## 3. ORM 核心对象关系图

```mermaid
classDiagram
    class Engine {
      +connect()
      +begin()
    }

    class Session {
      +add()
      +delete()
      +commit()
      +rollback()
      +execute()
      +get()
      +refresh()
      +flush()
    }

    class Base {
    }

    class User {
      +id
      +username
      +email
    }

    class Dept {
      +id
      +name
    }

    Engine <-- Session
    Base <|-- User
    Base <|-- Dept
    User --> Dept : relationship
```

## 4. 什么时候用 Core，什么时候用 ORM

### 4.1 适合用 ORM 的场景

- 业务系统的日常增删改查
- 表之间关系比较多
- 想用类和对象表达领域模型
- 想减少重复 SQL
- 需要统一的模型结构和类型提示

### 4.2 适合用 Core 的场景

- 动态 SQL 很多
- 批量导入、批量更新
- 报表、统计、复杂聚合
- 需要更贴近 SQL 的控制
- 只想拿字典结果，不想构造成 ORM 对象

### 4.3 实战建议

- 80% 的常规业务接口用 ORM
- 20% 的复杂查询和批量写操作用 Core
- 不要为了“纯粹”而强行全 ORM 或全 SQL

## 5. 什么时候用同步，什么时候用异步

这个问题很重要。

### 5.1 适合同步 SQLAlchemy 的场景

- 脚本工具
- 后台任务
- 管理命令
- 单线程定时任务
- 传统 Flask / Django 风格项目
- 团队对异步还不熟

特点：

- 写法简单
- 调试简单
- 学习成本低
- 对低并发管理系统通常足够

### 5.2 适合异步 SQLAlchemy 的场景

- FastAPI 全链路异步项目
- 单机高并发 API 服务
- 请求里要同时做多个 I/O 操作
  - 数据库
  - Redis
  - HTTP 调用
  - MQ
- 已经使用 `async def` 路由和异步依赖

特点：

- 更适合高并发 I/O 场景
- 能减少线程阻塞
- 需要团队理解异步模型
- 代码复杂度会更高

### 5.3 不要混着乱用

错误思路：

- FastAPI 路由是 `async def`
- 数据库却还是同步 Session
- 然后整个请求里到处阻塞

这不是不能用，而是收益会很差。

推荐原则：

1. 如果项目整体是同步风格，就全同步
2. 如果项目整体是异步风格，就数据库也异步
3. 不要同一个业务层里同步异步混着写

### 5.4 一句话判断

- “管理后台、小系统、脚本”优先同步
- “高并发 API、FastAPI 全异步架构”优先异步

## 6. 安装

基础安装：

```bash
pip install sqlalchemy
```

常见驱动：

MySQL：

```bash
pip install sqlalchemy pymysql aiomysql
```

PostgreSQL：

```bash
pip install sqlalchemy psycopg[binary] asyncpg
```

SQLite：

```bash
pip install sqlalchemy aiosqlite
```

## 7. 连接 URL

### 7.1 MySQL

同步：

```python
mysql+pymysql://root:123456@127.0.0.1:3306/demo
```

异步：

```python
mysql+aiomysql://root:123456@127.0.0.1:3306/demo
```

### 7.2 PostgreSQL

同步：

```python
postgresql+psycopg://postgres:123456@127.0.0.1:5432/demo
```

异步：

```python
postgresql+asyncpg://postgres:123456@127.0.0.1:5432/demo
```

### 7.3 SQLite

同步：

```python
sqlite:///./test.db
```

异步：

```python
sqlite+aiosqlite:///./test.db
```

## 8. Engine 是什么

`Engine` 是 SQLAlchemy 和数据库之间最核心的桥梁之一。

它负责：

- 维护连接池
- 创建数据库连接
- 执行 SQL
- 作为 Session 的底层绑定对象

同步 Engine：

```python
from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://root:123456@127.0.0.1:3306/demo",
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

异步 Engine：

```python
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    "mysql+aiomysql://root:123456@127.0.0.1:3306/demo",
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

参数解释：

- `echo=True`
  - 控制是否打印 SQL
  - 开发环境常开，生产建议关
- `pool_pre_ping=True`
  - 每次从连接池拿连接前先探活
  - 可以避免“连接已断开但池里还留着旧连接”
- `pool_recycle=3600`
  - 连接使用超过指定秒数后回收
  - 常用于避免 MySQL 长连接超时

## 9. Core 基础

### 9.1 定义表

```python
from sqlalchemy import MetaData, Table, Column, Integer, String, Boolean

metadata = MetaData()

user_table = Table(
    "sys_user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(50), nullable=False, unique=True),
    Column("email", String(100)),
    Column("is_deleted", Boolean, nullable=False, default=False),
)
```

这里每个对象的含义：

- `MetaData()`
  - 表结构的注册中心
  - 可以理解成“这一批表定义都挂在这里”
- `Table(...)`
  - 定义一张表
- `Column(...)`
  - 定义一个字段

### 9.2 建表和删表

```python
metadata.create_all(engine)
metadata.drop_all(engine)
```

方法含义：

- `create_all(engine)`
  - 按当前 `metadata` 中注册的表去建表
- `drop_all(engine)`
  - 把当前 `metadata` 中注册的表删掉

说明：

- 生产环境通常不直接依赖它做迁移
- 正式项目更推荐 Alembic

### 9.3 反射已有表

```python
from sqlalchemy import MetaData, Table

metadata = MetaData()
user_table = Table("sys_user", metadata, autoload_with=engine)
```

方法含义：

- `autoload_with=engine`
  - 不手写字段定义
  - 直接从数据库读取表结构

适用场景：

- 接手老项目
- 做数据管理平台
- 动态读取数据库结构

## 10. Core CRUD

### 10.1 插入

```python
from sqlalchemy import insert

stmt = insert(user_table).values(username="tom", email="tom@test.com")

with engine.begin() as conn:
    conn.execute(stmt)
```

解释：

- `insert(user_table)`
  - 构造一条插入语句
- `.values(...)`
  - 指定待插入数据
- `engine.begin()`
  - 打开一个事务连接
  - 代码块成功结束自动提交
- `conn.execute(stmt)`
  - 执行 SQL

### 10.2 批量插入

```python
rows = [
    {"username": "tom", "email": "tom@test.com"},
    {"username": "jack", "email": "jack@test.com"},
]

with engine.begin() as conn:
    conn.execute(insert(user_table), rows)
```

为什么这种写法常用：

- 它会走批量执行路径
- 通常比一条条执行更高效

### 10.3 查询

```python
from sqlalchemy import select

stmt = select(user_table).where(user_table.c.is_deleted.is_(False))

with engine.connect() as conn:
    result = conn.execute(stmt)
    rows = result.mappings().all()
```

这里几个方法的含义：

- `select(user_table)`
  - 查询这张表
- `.where(...)`
  - 追加过滤条件
- `user_table.c.is_deleted`
  - `c` 表示 column collection，也就是表字段集合
- `.is_(False)`
  - 布尔判断，通常比 `== False` 更规范
- `engine.connect()`
  - 获取一个普通连接，不自动开启提交事务
- `result.mappings().all()`
  - 按字典结果返回全部记录

### 10.4 `Result` 常见读取方法

- `result.all()`
  - 返回全部结果，通常是元组列表
- `result.first()`
  - 取第一条，没有就返回 `None`
- `result.scalar()`
  - 取第一行第一列
- `result.scalar_one()`
  - 必须正好一条，否则抛异常
- `result.scalar_one_or_none()`
  - 一条返回值，没有返回 `None`
- `result.mappings().all()`
  - 返回字典风格结果

什么时候用：

- 查 ORM 对象：通常用 `scalars()`
- 查单列统计值：通常用 `scalar_one()`
- 查字典结果：通常用 `mappings()`

### 10.5 更新

```python
from sqlalchemy import update

stmt = (
    update(user_table)
    .where(user_table.c.id == 1)
    .values(username="new_name")
)

with engine.begin() as conn:
    result = conn.execute(stmt)
    print(result.rowcount)
```

解释：

- `update(user_table)`
  - 构造更新语句
- `rowcount`
  - 影响行数

### 10.6 删除

```python
from sqlalchemy import delete

stmt = delete(user_table).where(user_table.c.id == 1)

with engine.begin() as conn:
    result = conn.execute(stmt)
    print(result.rowcount)
```

### 10.7 原生 SQL

```python
from sqlalchemy import text

stmt = text("SELECT * FROM sys_user WHERE username = :username")

with engine.connect() as conn:
    result = conn.execute(stmt, {"username": "tom"})
    rows = result.mappings().all()
```

为什么用 `text()`：

- SQLAlchemy 能识别这是原生 SQL
- 可以安全绑定参数

不要这样写：

```python
sql = f"SELECT * FROM sys_user WHERE username = '{username}'"
```

因为这样有 SQL 注入风险。

## 11. ORM 基础

### 11.1 Base

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

含义：

- `Base` 是所有 ORM 模型的父类
- 所有模型都会继承它
- 它维护一份 `Base.metadata`

### 11.2 定义模型

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

字段解释：

- `__tablename__`
  - 这个类映射到哪张表
- `Mapped[int]`
  - ORM 映射字段的类型标注
- `mapped_column(...)`
  - 真正的列定义
- `primary_key=True`
  - 主键
- `unique=True`
  - 唯一约束
- `index=True`
  - 索引
- `nullable=True`
  - 是否可空
- `default=...`
  - 默认值

### 11.3 建表

```python
Base.metadata.create_all(engine)
```

含义：

- 根据所有继承 `Base` 的模型统一建表

## 12. Session 是什么

可以把 `Session` 理解成：

- ORM 的工作单元
- 一次事务上下文
- 对象状态管理器

它不只是“数据库连接”。

它还负责：

- 追踪对象变化
- flush
- commit
- rollback
- refresh
- 查询结果和 ORM 对象绑定

### 12.1 Session 工厂

```python
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
```

参数解释：

- `bind=engine`
  - 把 Session 绑定到 Engine
- `autoflush=False`
  - 查询前不自动 flush
- `autocommit=False`
  - 需要手动 commit
- `expire_on_commit=False`
  - 提交后对象属性不自动失效

### 12.2 一个请求里的 Session 流程图

```mermaid
sequenceDiagram
    participant API as API/Service
    participant S as Session
    participant DB as Database

    API->>S: 创建 Session
    API->>S: add / execute / get
    S->>DB: flush 或 execute SQL
    API->>S: commit()
    S->>DB: COMMIT
    API->>S: close()
```

### 12.3 查询

```python
from sqlalchemy import select

with SessionLocal() as session:
    users = session.execute(select(User)).scalars().all()
```

方法解释：

- `session.execute(...)`
  - 执行 SQLAlchemy 表达式
- `.scalars()`
  - 把结果提取成单列对象流
  - 这里因为查询的是 `User`，所以得到的是 `User` 对象
- `.all()`
  - 全部加载成列表

### 12.4 新增

```python
with SessionLocal() as session:
    user = User(username="tom", email="tom@test.com")
    session.add(user)
    session.commit()
    session.refresh(user)
```

方法解释：

- `session.add(user)`
  - 把对象加入当前 Session 管理
- `session.commit()`
  - 提交事务
- `session.refresh(user)`
  - 从数据库重新加载对象
  - 常用于拿到数据库生成的最新值

### 12.5 修改

```python
with SessionLocal() as session:
    user = session.get(User, 1)
    if user:
        user.username = "new_name"
        session.commit()
```

为什么这里没有 `update(...)`：

- ORM 风格更常见的是“先查对象，再改属性，再提交”

### 12.6 删除

```python
with SessionLocal() as session:
    user = session.get(User, 1)
    if user:
        session.delete(user)
        session.commit()
```

### 12.7 回滚

```python
with SessionLocal() as session:
    try:
        user = User(username="tom")
        session.add(user)
        session.commit()
    except Exception:
        session.rollback()
        raise
```

`rollback()` 的含义：

- 事务失败时撤销本次事务中的数据库变更

## 13. ORM 查询

### 13.1 全部查询

```python
stmt = select(User)
users = session.execute(stmt).scalars().all()
```

### 13.2 主键查询

```python
user = session.get(User, 1)
```

`get()` 的特点：

- 专门按主键查
- 语义最清晰
- 命中 Session 身份映射时可能直接复用对象

### 13.3 条件查询

```python
stmt = select(User).where(User.username == "tom")
user = session.execute(stmt).scalar_one_or_none()
```

### 13.4 多条件

```python
stmt = select(User).where(
    User.is_deleted.is_(False),
    User.username.like("%tom%"),
)
```

### 13.5 排序

```python
stmt = select(User).order_by(User.id.desc())
```

### 13.6 分页

```python
page = 1
page_size = 20

stmt = (
    select(User)
    .where(User.is_deleted.is_(False))
    .offset((page - 1) * page_size)
    .limit(page_size)
)
```

### 13.7 统计

```python
from sqlalchemy import func

stmt = select(func.count(User.id)).where(User.is_deleted.is_(False))
total = session.execute(stmt).scalar_one()
```

### 13.8 指定字段

```python
stmt = select(User.id, User.username)
rows = session.execute(stmt).all()
```

适用场景：

- 列表页只需要部分字段
- 不想构造成完整 ORM 对象

### 13.9 别名

```python
from sqlalchemy.orm import aliased

UserAlias = aliased(User)
stmt = select(UserAlias).where(UserAlias.username == "tom")
```

适用场景：

- 自连接
- 多次引用同一张表

### 13.10 子查询

```python
subq = select(User.id).where(User.username.like("t%")).subquery()
stmt = select(User).where(User.id.in_(select(subq.c.id)))
```

## 14. 关系映射

### 14.1 一对多

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import relationship


class Dept(Base):
    __tablename__ = "sys_dept"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    users: Mapped[list["User"]] = relationship(back_populates="dept")


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    dept_id: Mapped[int | None] = mapped_column(ForeignKey("sys_dept.id"))

    dept: Mapped[Dept | None] = relationship(back_populates="users")
```

理解方式：

- 一个部门对应多个用户
- 一个用户只属于一个部门

### 14.2 一对一

```python
class UserProfile(Base):
    __tablename__ = "sys_user_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id"), unique=True)
    avatar: Mapped[str | None] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="profile")


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))

    profile: Mapped[UserProfile | None] = relationship(back_populates="user", uselist=False)
```

`uselist=False` 的含义：

- 告诉 ORM 这个关系是单对象，不是列表

### 14.3 多对多

```python
from sqlalchemy import Table, Column, ForeignKey

user_role = Table(
    "sys_user_role",
    Base.metadata,
    Column("user_id", ForeignKey("sys_user.id"), primary_key=True),
    Column("role_id", ForeignKey("sys_role.id"), primary_key=True),
)
```

### 14.4 关系图

```mermaid
erDiagram
    DEPT ||--o{ USER : has
    USER ||--|| USER_PROFILE : owns
    USER }o--o{ ROLE : grants
```

## 15. 加载策略

### 15.1 懒加载

```python
user = session.get(User, 1)
print(user.dept)
```

特点：

- 访问到关系属性时再查库
- 容易产生 N+1 问题

### 15.2 `selectinload`

```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.roles))
users = session.execute(stmt).scalars().all()
```

特点：

- 主查询一次
- 关联对象再统一查一次
- 一对多、多对多场景常用

### 15.3 `joinedload`

```python
from sqlalchemy.orm import joinedload

stmt = select(User).options(joinedload(User.dept))
users = session.execute(stmt).scalars().unique().all()
```

特点：

- join 一次查出
- 多对一、一对一更常见
- 可能产生重复主对象，因此常要 `unique()`

### 15.4 `subqueryload`

```python
from sqlalchemy.orm import subqueryload

stmt = select(User).options(subqueryload(User.roles))
```

### 15.5 `raiseload`

```python
from sqlalchemy.orm import raiseload

stmt = select(User).options(raiseload(User.roles))
```

适用场景：

- 你想强制避免隐式懒加载
- 一旦误访问未预加载关系就直接报错

## 16. Join、聚合、统计

普通 join：

```python
stmt = select(User, Dept).join(Dept, User.dept_id == Dept.id)
```

关系 join：

```python
stmt = select(User).join(User.dept)
```

外连接：

```python
stmt = select(User, Dept).outerjoin(User.dept)
```

聚合：

```python
from sqlalchemy import func

stmt = (
    select(User.dept_id, func.count(User.id).label("user_count"))
    .group_by(User.dept_id)
)
```

适用场景：

- 报表
- 统计接口
- 分组分析

## 17. 事务

### 17.1 Connection 事务

```python
with engine.begin() as conn:
    conn.execute(insert(user_table).values(username="tom"))
```

### 17.2 Session 事务

```python
with SessionLocal() as session:
    with session.begin():
        session.add(User(username="tom"))
```

### 17.3 嵌套事务

```python
with SessionLocal() as session:
    with session.begin():
        with session.begin_nested():
            pass
```

适用场景：

- 外层一个大事务
- 内层部分逻辑需要 savepoint

## 18. flush、commit、refresh、expire

### 18.1 `flush()`

- 把当前修改同步到数据库
- 但事务还没提交
- 常用于先拿数据库生成的主键

```python
user = User(username="tom")
session.add(user)
session.flush()
print(user.id)
```

### 18.2 `commit()`

- 提交事务
- 修改正式生效

### 18.3 `refresh()`

- 从数据库重新加载对象

```python
session.refresh(user)
```

### 18.4 `expire()`

- 让对象属性失效
- 下次访问时重新查库

```python
session.expire(user)
```

## 19. 批量操作

### 19.1 批量插入

```python
from sqlalchemy import insert

rows = [
    {"username": "u1"},
    {"username": "u2"},
]

with SessionLocal() as session:
    session.execute(insert(User), rows)
    session.commit()
```

### 19.2 批量更新

```python
from sqlalchemy import update

rows = [
    {"id": 1, "username": "u1_new"},
    {"id": 2, "username": "u2_new"},
]

with SessionLocal() as session:
    session.execute(update(User), rows)
    session.commit()
```

什么时候优先批量模式：

- 导入 Excel / CSV
- 初始化数据
- 批量同步第三方系统数据
- 批量修复脚本

## 20. 异步用法

### 20.1 异步 Engine 和 Session

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

async_engine = create_async_engine(
    "mysql+aiomysql://root:123456@127.0.0.1:3306/demo",
    echo=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
```

### 20.2 异步查询

```python
async with AsyncSessionLocal() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
```

### 20.3 异步新增

```python
async with AsyncSessionLocal() as session:
    user = User(username="tom")
    session.add(user)
    await session.commit()
    await session.refresh(user)
```

### 20.4 异步事务

```python
async with AsyncSessionLocal() as session:
    async with session.begin():
        session.add(User(username="tom"))
```

### 20.5 异步方法的理解

- `await session.execute(...)`
  - 执行数据库 I/O，需要等待
- `await session.commit()`
  - 提交事务，需要等待
- `await session.refresh(user)`
  - 重新加载对象，需要等待

## 21. FastAPI 集成

数据库依赖：

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

为什么这样写：

- 每个请求拿一个独立 Session
- 请求结束自动关闭
- 避免跨请求复用 Session

路由使用：

```python
from fastapi import Depends
from sqlalchemy import select


@router.get("/users")
async def user_list(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

Service 示例：

```python
class UserService:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
```

## 22. 项目结构建议

```mermaid
flowchart TB
    A[config/database.py] --> B[engine / sessionmaker]
    B --> C[models/*.py]
    B --> D[deps/get_db]
    D --> E[api/router.py]
    E --> F[service/*.py]
    F --> C
```

推荐目录：

```text
app/
  config/
    database.py
  models/
    base.py
    user.py
    dept.py
  schemas/
    user.py
  services/
    user_service.py
  api/
    user_api.py
  deps/
    database.py
```

## 23. 高级能力

### 23.1 Hybrid Property

```python
from sqlalchemy.ext.hybrid import hybrid_property


class User(Base):
    __tablename__ = "sys_user"

    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))

    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

适用场景：

- Python 对象上要访问
- SQL 查询里也要表达

### 23.2 事件

```python
from sqlalchemy import event


@event.listens_for(User, "before_insert")
def before_insert(mapper, connection, target):
    target.username = target.username.strip()
```

适用场景：

- 插入前统一处理字段
- 更新前清洗数据
- 做审计和日志

### 23.3 混入类

```python
from datetime import datetime
from sqlalchemy import DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

适用场景：

- 多个模型共用相同字段
- 统一时间戳
- 统一软删除

## 24. 常见异常

```python
from sqlalchemy.exc import IntegrityError, DBAPIError
```

常见类型：

- `IntegrityError`
  - 唯一键冲突、外键冲突
- `DBAPIError`
  - 驱动层错误
- `OperationalError`
  - 连接失败、超时、数据库不可达
- `NoResultFound`
  - 预期有结果但没找到
- `MultipleResultsFound`
  - 预期单条但查出多条

示例：

```python
try:
    session.commit()
except IntegrityError:
    session.rollback()
    raise ValueError("用户名已存在")
```

## 25. 性能建议

1. 列表页尽量只查需要的字段
2. 批量写入优先 `insert(table), rows`
3. 避免 N+1，优先 `selectinload()` 或 `joinedload()`
4. 高并发异步项目避免在 `async def` 里混用同步数据库访问
5. 生产环境建议 `pool_pre_ping=True`
6. 大报表、复杂统计优先 Core 或原生 SQL
7. 对分页字段、排序字段、关联字段建立索引

## 26. Alembic 和 SQLAlchemy 的关系

SQLAlchemy 负责：

- 建模
- 连接数据库
- 执行查询
- 管理事务

Alembic 负责：

- 表结构迁移
- 版本管理
- schema 变更发布

常见命令：

```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## 27. 一个完整异步 CRUD 示例

模型：

```python
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

Service：

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, username: str, email: str | None = None) -> User:
        user = User(username=username, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_page(db: AsyncSession, page: int, page_size: int) -> dict:
        total_stmt = select(func.count(User.id)).where(User.is_deleted.is_(False))
        total = (await db.execute(total_stmt)).scalar_one()

        stmt = (
            select(User)
            .where(User.is_deleted.is_(False))
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return {"total": total, "rows": rows}
```

这段代码体现了哪些点：

- `select()` 是统一查询入口
- `scalar_one_or_none()` 适合查单条
- 统计和分页通常分开查
- 异步 Session 需要 `await`

## 28. 学习顺序建议

建议按这个顺序学习：

1. 先理解 `Engine`、`Session`、`Base`
2. 学会 `select()`、`insert()`、`update()`、`delete()`
3. 学会 ORM 模型定义
4. 学会 `commit / rollback / flush / refresh`
5. 学会关系映射
6. 学会加载策略
7. 学会同步和异步的选型
8. 最后再学事件、混入、性能优化

## 29. 官方文档索引

- Unified Tutorial  
  https://docs.sqlalchemy.org/en/20/tutorial/
- ORM Quick Start  
  https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- ORM Querying Guide  
  https://docs.sqlalchemy.org/en/20/orm/queryguide/
- Relationship Configuration  
  https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
- AsyncIO Extension  
  https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Session Basics  
  https://docs.sqlalchemy.org/en/20/orm/session_basics.html

## 30. 这份文档解决什么问题

这份文档重点解决的是：

- SQLAlchemy 整体结构是什么
- Core 和 ORM 怎么分工
- 每个常见方法大致是什么意思
- 什么时候该用同步，什么时候该用异步
- FastAPI 项目里通常怎么组织
- 出现查询、关系、事务时应该怎么想

如果你还要继续细化，我建议下一步从下面几个专题中选一个继续深挖：

1. ORM 查询大全
2. AsyncSession 最佳实践
3. 关系映射和加载策略专题
4. Core 复杂 SQL 专题
5. SQLAlchemy + Alembic 迁移专题

## 31. ORM 和 Core 能不能联合使用

可以，而且这恰恰是 SQLAlchemy 最有价值的地方之一。

SQLAlchemy 2.0 的设计本来就是“Core 和 ORM 共用一套表达式系统”，所以：

- 你可以用 ORM 模型去构造 `select(User)`
- 也可以在 ORM 的 `Session` 里执行 Core 的 `insert/update/delete/text`
- 还可以在同一个事务里同时处理 ORM 对象和 Core SQL

### 31.1 最常见的联合方式

#### 方式一：用 ORM 模型写查询表达式

```python
stmt = select(User).where(User.is_deleted.is_(False))
result = session.execute(stmt)
users = result.scalars().all()
```

这本质上已经是“ORM + Core 表达式联合使用”。

#### 方式二：在 Session 中执行 Core DML

```python
from sqlalchemy import insert

rows = [
    {"username": "u1", "email": "u1@test.com"},
    {"username": "u2", "email": "u2@test.com"},
]

with SessionLocal() as session:
    session.execute(insert(User), rows)
    session.commit()
```

适用场景：

- 批量新增
- 初始化数据
- 导入任务

#### 方式三：ORM 查对象，Core 做批量更新

```python
from sqlalchemy import update, select

with SessionLocal() as session:
    user = session.get(User, 1)
    print(user.username)

    session.execute(
        update(User).where(User.id == 1).values(username="new_name")
    )
    session.commit()
```

#### 方式四：ORM 事务里执行原生 SQL

```python
from sqlalchemy import text

with SessionLocal() as session:
    session.execute(text("UPDATE sys_user SET is_deleted = 1 WHERE id = :id"), {"id": 1})
    session.commit()
```

### 31.2 联合使用的好处

1. 业务层仍然保留 ORM 的可读性
2. 批量写入和复杂 SQL 仍然能利用 Core 的性能和灵活性
3. 不需要为了“纯 ORM”而把复杂统计写得很别扭
4. 不需要为了“纯 SQL”而放弃模型关系和对象表达能力

### 31.3 联合使用时最需要注意什么

#### 注意一：同一个事务里尽量只用同一个 Session

推荐：

```python
with SessionLocal() as session:
    session.add(User(username="tom"))
    session.execute(text("UPDATE sys_dept SET name = name WHERE id = 1"))
    session.commit()
```

不要这样拆：

- 一边用 `session`
- 一边又自己开 `engine.connect()`
- 最后你会得到两个不同的事务上下文

#### 注意二：Core DML 直接改库时，Session 中已有对象可能“过期”或“脏”

例子：

```python
user = session.get(User, 1)
session.execute(update(User).where(User.id == 1).values(username="core_name"))
print(user.username)
```

这里的 `user.username` 可能还是旧值，因为：

- ORM 对象已经在 Session 身份映射里了
- 你又用 Core 直接更新了数据库
- 这个对象未必立刻自动刷新

解决方式：

```python
session.refresh(user)
```

或者：

```python
session.expire(user)
```

#### 注意三：批量 DML 不等于 ORM 对象状态同步

像下面这种：

```python
session.execute(update(User), [{"id": 1, "username": "u1"}])
```

它更偏底层批量写入，不会像逐个 ORM 对象赋值那样完整触发对象状态管理。

所以如果你的逻辑强依赖：

- 对象状态跟踪
- relationship 自动同步
- 事件回调
- 单对象生命周期

就不要滥用批量 DML。

#### 注意四：原生 SQL 和 Core SQL 要特别注意参数绑定

推荐：

```python
session.execute(text("SELECT * FROM sys_user WHERE id = :id"), {"id": 1})
```

不要：

```python
sql = f"SELECT * FROM sys_user WHERE id = {user_id}"
```

#### 注意五：复杂查询可以用 Core，返回业务时再转成 schema

这通常是很实用的组合：

- 查询层：Core / text / 聚合 SQL
- 返回层：Pydantic schema / DTO

### 31.4 一个更实际的联合使用案例

场景：

- 用户列表页用 ORM
- 导入用户时用 Core 批量插入
- 用户统计报表用 Core 聚合

```python
class UserService:
    @staticmethod
    async def get_user_page(db: AsyncSession, page: int, page_size: int):
        stmt = (
            select(User)
            .where(User.is_deleted.is_(False))
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return (await db.execute(stmt)).scalars().all()

    @staticmethod
    async def batch_import_users(db: AsyncSession, rows: list[dict]):
        await db.execute(insert(User), rows)
        await db.commit()

    @staticmethod
    async def count_by_dept(db: AsyncSession):
        stmt = (
            select(User.dept_id, func.count(User.id).label("total"))
            .where(User.is_deleted.is_(False))
            .group_by(User.dept_id)
        )
        return (await db.execute(stmt)).all()
```

结论：

- ORM 和 Core 不但可以联合使用，而且应该按场景合理组合
- 关键不是“能不能混用”，而是“是否清楚事务边界、对象状态和刷新时机”

## 32. Session 生命周期和对象状态

这部分是很多人一开始最容易模糊的地方。

### 32.1 Session 生命周期

一个典型的 Session 生命周期是：

1. 创建 Session
2. 执行查询或写操作
3. flush
4. commit 或 rollback
5. close

图示：

```mermaid
stateDiagram-v2
    [*] --> SessionCreated
    SessionCreated --> Working
    Working --> Flushed
    Flushed --> Committed
    Flushed --> RolledBack
    Committed --> Closed
    RolledBack --> Closed
```

### 32.2 ORM 对象的几种状态

#### `transient`

- 刚创建出来
- 还没加入 Session

```python
user = User(username="tom")
```

#### `pending`

- 已经 `add()` 到 Session
- 还没 flush 到数据库

```python
session.add(user)
```

#### `persistent`

- 已经在 Session 中
- 且数据库里已有对应记录

```python
session.flush()
```

#### `detached`

- 对象原来属于某个 Session
- 但这个 Session 已关闭或对象已分离

常见触发方式：

```python
session.close()
```

### 32.3 `session.close()` 做了什么

- 释放数据库连接
- 结束当前 Session 生命周期
- 对象可能变成 detached

这也是为什么不应该把 ORM 对象到处跨层长期传递。

### 32.4 `merge()` 的使用场景

当你手里有一个 detached 对象，需要重新纳入当前 Session 时，可以用：

```python
merged_user = session.merge(user)
session.commit()
```

适用场景：

- 对象来自旧 Session
- 序列化后又还原
- 你希望重新挂回当前 Session

## 33. 查询结果方法大全

这部分专门解决“这些方法名我看得懂，但不知道差别”的问题。

### 33.1 `all()`

```python
rows = session.execute(stmt).all()
```

含义：

- 拿全部结果
- 常见是元组列表

### 33.2 `first()`

```python
row = session.execute(stmt).first()
```

含义：

- 拿第一条
- 没有就返回 `None`
- 多条也不会报错

### 33.3 `one()`

```python
row = session.execute(stmt).one()
```

含义：

- 必须正好一条
- 0 条或多条都抛异常

### 33.4 `one_or_none()`

```python
row = session.execute(stmt).one_or_none()
```

含义：

- 0 条返回 `None`
- 1 条返回这条
- 多条抛异常

### 33.5 `scalar()`

```python
value = session.execute(stmt).scalar()
```

含义：

- 取第一行第一列
- 更偏“随手取一个值”

### 33.6 `scalar_one()`

```python
value = session.execute(stmt).scalar_one()
```

含义：

- 必须正好一条结果
- 然后取第一列

### 33.7 `scalar_one_or_none()`

```python
value = session.execute(stmt).scalar_one_or_none()
```

含义：

- 0 条返回 `None`
- 1 条返回第一列
- 多条抛异常

### 33.8 `scalars()`

```python
users = session.execute(select(User)).scalars().all()
```

含义：

- 把结果流压平成“单列对象流”
- 查询 ORM 模型时非常常用

### 33.9 `mappings()`

```python
rows = session.execute(stmt).mappings().all()
```

含义：

- 返回字典风格结果
- 适合 Core 查询、统计查询、报表查询

### 33.10 `unique()`

```python
users = session.execute(stmt).scalars().unique().all()
```

适用场景：

- `joinedload()` 导致主对象重复
- 需要按主对象去重

### 33.11 一张判断表

| 需求 | 推荐方法 |
| --- | --- |
| 查全部 ORM 对象 | `scalars().all()` |
| 查第一条，可无结果 | `first()` |
| 查单条，必须唯一 | `one()` / `scalar_one()` |
| 查单条，没有就空 | `one_or_none()` / `scalar_one_or_none()` |
| 查统计值 | `scalar_one()` |
| 查字典结果 | `mappings().all()` |

## 34. 关系映射进阶

### 34.1 `back_populates` 和 `backref` 的区别

`back_populates`：

- 双方都显式声明
- 结构更清晰
- 大项目更推荐

`backref`：

- 一边写，另一边自动生成
- 写起来短
- 大项目里可读性略弱

推荐：

- 团队项目优先 `back_populates`

### 34.2 `cascade`

常见写法：

```python
children: Mapped[list["Child"]] = relationship(
    back_populates="parent",
    cascade="all, delete-orphan",
)
```

含义：

- 父对象变化时，子对象跟着一起处理
- `delete-orphan` 表示脱离父对象的子对象也删除

适用场景：

- 明确的父子附属关系
- 比如订单和订单明细

### 34.3 `passive_deletes`

适用场景：

- 你希望数据库自己通过外键 `ON DELETE CASCADE` 来删除
- ORM 不主动逐条处理子对象

### 34.4 什么时候用中间表，什么时候用 Association Object

纯中间表适合：

- 只有两个外键
- 不需要额外字段

Association Object 适合：

- 中间关系本身还有业务字段
- 比如用户和角色之间还有 `granted_at`、`granted_by`

## 35. 异步 ORM 的限制和常见坑

### 35.1 异步不等于数据库更快

异步带来的收益是：

- 更好的并发 I/O 利用率

不是：

- 单条 SQL 本身执行更快

慢 SQL 还是要靠：

- 索引
- SQL 优化
- 表设计

### 35.2 异步项目里懒加载更容易踩坑

因为懒加载本质上会触发额外数据库 I/O。

在异步 ORM 中，更推荐：

- 显式预加载
- `selectinload()`
- `joinedload()`

而不是走隐式懒加载。

### 35.3 不要在 `async def` 里混用同步 Session

坏处：

- 阻塞事件循环
- 吞掉异步收益

### 35.4 异步适合什么，不适合什么

适合：

- API 服务
- 多 I/O 协同
- Redis + DB + HTTP 并存的请求链路

不适合：

- 简单脚本
- 管理命令
- 小型单体后台为了“追新”硬切异步

## 36. 数据库方言差异

虽然 SQLAlchemy 帮你统一了很多接口，但不同数据库仍然有差异。

### 36.1 MySQL

特点：

- 常见于业务系统
- 对 JSON 支持较普及
- 长连接超时问题要更关注

注意：

- `pool_recycle` 常常更重要

### 36.2 PostgreSQL

特点：

- 类型系统更强
- JSONB、数组、CTE、窗口函数体验更好
- 更适合复杂查询和分析型场景

### 36.3 SQLite

特点：

- 轻量
- 适合本地开发和简单测试

注意：

- 不要把 SQLite 的表现完全等同于 MySQL/PostgreSQL
- 测试行为可能和生产库不一致

## 37. Alembic 实战注意事项

### 37.1 `--autogenerate` 不是万能的

它通常能识别：

- 新表
- 新字段
- 基本索引和约束变化

但对这些场景要小心：

- 字段重命名
- 表重命名
- 复杂类型变更
- 数据迁移

### 37.2 重命名字段时不要盲信自动迁移

自动生成有时会把“重命名”识别成：

- 删除旧字段
- 新增新字段

这会导致数据丢失风险。

### 37.3 生产环境迁移建议

1. 先在测试环境演练
2. 检查生成的 migration 脚本
3. 对大表变更评估锁表风险
4. 数据迁移和结构迁移尽量分开

## 38. 测试怎么做

### 38.1 为什么要单独讲测试

因为 SQLAlchemy 测试里最容易踩的是：

- Session 隔离
- 事务回滚
- 测试库和生产库行为不一致

### 38.2 基本原则

1. 每个测试用例尽量隔离
2. 用独立测试数据库
3. 不要和开发库共用数据

### 38.3 常见测试思路

#### 方式一：每个测试新建数据再清理

优点：

- 简单直观

缺点：

- 慢

#### 方式二：事务回滚隔离

思路：

- 测试前开启事务
- 测试结束统一 rollback

适合：

- ORM Service 测试
- 接口测试

### 38.4 SQLite 测试要谨慎

如果生产是 MySQL / PostgreSQL：

- SQLite 只能做一部分轻量测试
- 不能完全替代真实数据库测试

尤其是这些差异明显：

- JSON
- 外键行为
- 类型系统
- 事务细节

## 39. 官方文档进一步阅读建议

如果你已经读到这里，下一步建议重点看官方这些章节：

- Session 状态管理  
  https://docs.sqlalchemy.org/en/20/orm/session_state_management.html
- ORM 查询结果与加载策略  
  https://docs.sqlalchemy.org/en/20/orm/queryguide/
- 关系配置  
  https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
- Cascades  
  https://docs.sqlalchemy.org/en/20/orm/cascades.html
- 异步 ORM  
  https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- ORM-enabled DML  
  https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html

## 40. 现在这份文档的定位

到这里，这份文档已经覆盖：

- 入门认知
- Core
- ORM
- Session
- 查询结果方法
- 关系映射
- 加载策略
- 事务
- 同步与异步选型
- FastAPI 集成
- ORM 和 Core 联合使用
- 异步限制与常见坑
- Alembic 基础与注意事项
- 测试建议

如果还要继续往下扩，最值得单独拆出来写的专题是：

1. ORM 查询大全
2. 关系映射与加载策略大全
3. AsyncSession 与 FastAPI 实战
4. Core 复杂 SQL 与报表查询
5. Alembic 迁移实战清单

## 41. 约束、索引和命名规范

这一部分很重要，因为它决定的不是“代码能不能跑”，而是：

- 数据库层能不能真正兜底
- 查询能不能跑得稳
- Alembic 迁移是否容易维护

很多初学者会把校验都写在接口层，但生产环境里，数据库约束仍然是最后一道边界。

### 41.1 为什么不能只靠业务代码校验

比如你在 Service 里写了：

```python
existing = session.scalar(select(User).where(User.username == username))
if existing:
    raise ValueError("username exists")
```

这只能减少大部分重复数据，但不能完全防住并发写入。

两个请求同时进来时：

1. 请求 A 查询发现不存在
2. 请求 B 查询也发现不存在
3. 两边都尝试插入

如果数据库没有唯一约束，重复数据还是会写进去。

所以：

- 业务层校验负责提前发现问题
- 数据库约束负责最终兜底

### 41.2 单列唯一约束和索引

最常见的例子是用户名唯一：

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
```

这里有两个点：

- `unique=True`
  - 生成唯一约束
- `index=True`
  - 生成普通索引

说明：

- 唯一约束主要保证数据不重复
- 索引主要提升查询性能

很多数据库在唯一约束背后也会创建索引，但从“语义表达”上，仍然建议明确区分“我要限制唯一”和“我要优化查询”。

### 41.3 组合唯一约束

很多业务里，唯一性不是单字段，而是组合字段。

比如：

- 同一个部门下用户名唯一
- 同一天内同一渠道订单号唯一

示例：

```python
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "sys_user"
    __table_args__ = (
        UniqueConstraint("dept_id", "username", name="uq_user_dept_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dept_id: Mapped[int] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
```

适用场景：

- 局部唯一
- 租户内唯一
- 多字段联合去重

### 41.4 普通索引和组合索引

不是所有字段都要加索引。  
真正值得关注的是：

- 查询条件字段
- 排序字段
- join 关联字段
- 高频过滤字段

示例：

```python
from sqlalchemy import Index, String


class User(Base):
    __tablename__ = "sys_user"
    __table_args__ = (
        Index("ix_user_status_created_at", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
```

解释：

- 单列索引适合简单过滤
- 组合索引适合“经常一起出现”的条件

例如：

```sql
where status = 'enabled' order by created_at desc
```

这类查询就很可能受益于组合索引。

### 41.5 `CheckConstraint`

适合做数据库层的基本合法性限制。

例如：

- 金额不能小于 0
- 状态值必须符合约定范围

```python
from sqlalchemy import CheckConstraint, Numeric


class Product(Base):
    __tablename__ = "product"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_product_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
```

注意：

- `CheckConstraint` 能增强数据质量
- 但复杂业务规则不要强行塞进数据库 check

### 41.6 外键约束

外键的核心作用不是“为了 ORM”，而是：

- 保证引用关系真实存在
- 防止孤儿数据

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Dept(Base):
    __tablename__ = "sys_dept"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    dept_id: Mapped[int] = mapped_column(ForeignKey("sys_dept.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)

    dept: Mapped["Dept"] = relationship()
```

这里要区分两件事：

- `ForeignKey`
  - 数据库层约束
- `relationship`
  - ORM 层对象关系

前者保证数据完整性，后者提高代码访问体验。

### 41.7 为什么推荐统一命名规范

如果你不显式命名，数据库可能自动生成约束名。  
短期看没问题，长期会遇到两个麻烦：

- Alembic migration 可读性差
- 不同环境自动生成名称可能不一致

推荐在 `MetaData` 上统一配置 `naming_convention`：

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


convention = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
```

适用价值：

1. 迁移脚本更稳定
2. 约束名更可读
3. 团队协作更统一

## 42. 常用列类型和自定义类型

这一部分解决两个问题：

1. SQLAlchemy 里常见数据库类型怎么选
2. 什么时候值得自定义类型

### 42.1 常见基础类型

最常见的字段类型包括：

- `String`
- `Text`
- `Integer`
- `BigInteger`
- `Boolean`
- `DateTime`
- `Date`
- `Numeric`
- `JSON`
- `Enum`

示例：

```python
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Article(Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
```

几个常见判断：

- 短文本用 `String`
- 长文本用 `Text`
- 金额优先 `Numeric`，不要用 `Float`
- 时间字段优先明确用 `DateTime`

### 42.2 `Numeric` 为什么比 `Float` 更适合金额

`Float` 是二进制浮点数，会有精度误差。  
金额、结算、积分换算这类字段，更适合：

```python
Numeric(10, 2)
```

配合 Python 的：

```python
Decimal
```

这样能减少精度问题。

### 42.3 `Enum`

当一个字段取值范围固定时，`Enum` 会比裸字符串更清晰。

```python
from enum import Enum
from sqlalchemy import Enum as SAEnum


class UserStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status_enum"),
        nullable=False,
        default=UserStatus.ENABLED,
    )
```

适用场景：

- 状态字段
- 类型字段
- 审批流节点类别

### 42.4 `JSON`

适合半结构化数据，比如：

- 扩展属性
- 第三方回调原始报文
- 配置快照

```python
from sqlalchemy import JSON


class EventLog(Base):
    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
```

注意：

- `JSON` 很方便，但不能替代表结构设计
- 高频过滤、排序、关联字段不要全塞进 JSON

### 42.5 UUID

如果项目使用 UUID 主键或业务 ID，可以直接映射类型。

```python
import uuid
from sqlalchemy import Uuid


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
```

适用场景：

- 分布式系统
- 不希望暴露自增 ID
- 需要更容易跨系统生成 ID

### 42.6 自定义类型 `TypeDecorator` 是什么

当内置类型不够，或者你希望：

- 统一字段转换逻辑
- 统一存储格式
- 屏蔽数据库细节

这时可以用 `TypeDecorator`。

### 42.7 一个最常见的自定义类型例子

比如你想在数据库里存字符串，但在 Python 里统一操作枚举值或值对象。

```python
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator


class LowerCaseString(TypeDecorator):
    impl = String(255)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return value.strip().lower()

    def process_result_value(self, value, dialect):
        return value
```

使用：

```python
class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(LowerCaseString(), nullable=False, unique=True)
```

意义：

- 写入数据库前自动清洗
- 模型层不用每次重复处理

### 42.8 什么时候值得自定义类型

适合：

- 邮箱、手机号、标准编码格式统一
- 加解密字段封装
- 特殊 ID 类型映射
- JSON 字段统一包装

不太适合：

- 只是某一个字段的临时处理
- 只有单个模型会用到的小逻辑

## 43. Session 配置项和行为理解

前面已经讲过 Session 的基本用法，但在真实项目里，很多“为什么会这样”的问题，其实都和 Session 配置有关。

### 43.1 `autoflush`

默认情况下，SQLAlchemy 在某些查询前会自动 `flush`。

这意味着：

- 你虽然还没 `commit`
- 但 Session 里挂着的变更，可能会先被同步到数据库事务里

示例理解：

```python
user = User(username="tom")
session.add(user)

# 这里执行查询时，可能会先触发 autoflush
session.execute(select(User).where(User.username == "tom"))
```

这不是提交，只是把内存中的变更先发到当前事务里。

适用理解：

- `autoflush=True` 更符合 ORM 默认行为
- 复杂流程里如果你非常确定不想提前 flush，可以局部关闭

### 43.2 `expire_on_commit`

这是很多人第一次用时最迷惑的配置之一。

默认情况下，`commit()` 之后对象可能会被“过期”：

- 属性还在
- 但下次访问时，SQLAlchemy 可能尝试重新从数据库加载

在同步项目里这通常还能接受。  
在异步项目里，这个行为更容易导致困惑。

所以很多 FastAPI 异步项目会写：

```python
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
```

这样提交后对象仍能直接使用，不容易触发额外加载。

### 43.3 `autocommit` 为什么不推荐再理解成旧写法

SQLAlchemy 2.0 的事务模型更强调显式事务边界。  
不要再沿用早期那种“自动提交心智模型”。

更推荐的理解是：

- 一次请求
- 一个 Session
- 一个明确的事务边界

要么：

- 成功后 `commit`

要么：

- 异常后 `rollback`

### 43.4 `session.begin()`

手动管理事务时，`session.begin()` 很清晰。

```python
with SessionLocal() as session:
    with session.begin():
        session.add(User(username="tom"))
```

含义：

- 进入块时开启事务
- 出错自动回滚
- 正常结束自动提交

异步写法：

```python
async with AsyncSessionLocal() as session:
    async with session.begin():
        session.add(User(username="tom"))
```

### 43.5 FastAPI 里推荐怎样配置 Session

同步项目常见写法：

```python
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
```

异步项目常见写法：

```python
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
```

为什么很多项目会关掉 `autoflush`：

- 行为更可控
- 减少“查询时偷偷 flush”的困惑

为什么很多项目会关掉 `expire_on_commit`：

- 提交后对象更容易继续使用
- 尤其适合 FastAPI 返回响应前还要访问对象属性

### 43.6 一个请求里的推荐事务边界

比较实用的原则是：

1. 路由层拿到 Session
2. Service 层使用 Session
3. 一次请求里尽量保持一个事务边界
4. 不要在底层函数里随意 `commit`

更稳的做法通常是：

- Service 内部负责 `flush`
- 更上层统一决定何时 `commit`

这样更利于：

- 多步骤业务组合
- 事务一致性控制
- 测试回滚

## 44. ORM DML 进阶

这里的 DML 指的是：

- `insert`
- `update`
- `delete`

SQLAlchemy 2.0 里，ORM 和 Core 的 DML 风格已经更统一了。

### 44.1 为什么除了 `session.add()` 还要学 DML

`session.add()` 很适合常规单对象写入。  
但这些场景更适合 DML：

- 批量写入
- 批量更新
- 只更新某几个字段
- 希望配合 `returning`
- 希望减少 ORM 对象构建成本

### 44.2 `insert()`

```python
from sqlalchemy import insert


stmt = insert(User).values(username="tom", email="tom@example.com")
session.execute(stmt)
session.commit()
```

它更接近 SQL：

```sql
insert into sys_user ...
```

适用场景：

- 脚本
- 批量写
- 不需要完整 ORM 生命周期

### 44.3 批量插入

```python
stmt = insert(User)
session.execute(
    stmt,
    [
        {"username": "tom"},
        {"username": "jack"},
    ],
)
session.commit()
```

优点：

- 比循环 `add()` 更适合批量场景
- 更接近数据库批量写入能力

### 44.4 `update()`

```python
from sqlalchemy import update


stmt = (
    update(User)
    .where(User.id == 1)
    .values(username="tom_new")
)
session.execute(stmt)
session.commit()
```

适合：

- 直接按条件更新
- 不想先查出 ORM 对象再改

### 44.5 `delete()`

```python
from sqlalchemy import delete


stmt = delete(User).where(User.is_deleted.is_(True))
session.execute(stmt)
session.commit()
```

适合：

- 批量删除
- 清理任务
- 后台批处理

### 44.6 `returning()`

有些数据库支持在写入后直接返回字段。

```python
stmt = (
    insert(User)
    .values(username="tom")
    .returning(User.id, User.username)
)
row = session.execute(stmt).first()
session.commit()
```

意义：

- 写入后直接拿回主键或其他字段
- 减少额外查询

常见适用场景：

- 创建记录后立即返回 id
- 更新后回显关键字段

注意：

- 不同数据库方言支持程度不同

### 44.7 Upsert 思路

很多项目会有这种需求：

- 有就更新
- 没有就插入

这通常被叫做：

- upsert
- insert on conflict
- insert on duplicate key update

SQLAlchemy 能表达这类能力，但写法会受数据库方言影响：

- PostgreSQL
- MySQL
- SQLite

都不完全一样。

所以实战上要记住：

- upsert 是高频需求
- 但它不是完全跨数据库统一的简单语法

如果你的项目强依赖 upsert，通常要围绕具体数据库单独写一节规范。

## 45. 查询加载控制进阶

前面已经讲了 `selectinload()`、`joinedload()` 等加载策略。  
这里再补几种更细的“取什么”和“怎么取”控制方式。

### 45.1 `load_only()`

当模型字段很多，但你只需要其中几列时，可以只加载必要字段。

```python
from sqlalchemy.orm import load_only


stmt = select(User).options(load_only(User.id, User.username))
users = session.execute(stmt).scalars().all()
```

意义：

- 减少查询列
- 减少对象加载成本

适合：

- 列表页
- 下拉框
- 轻量查询

### 45.2 `defer()` 和 `undefer()`

有些字段很大，比如：

- 富文本
- 大 JSON
- 大文本日志

可以默认延迟加载。

```python
from sqlalchemy.orm import defer


stmt = select(Article).options(defer(Article.content))
articles = session.execute(stmt).scalars().all()
```

如果某个场景又确实需要它，再显式 `undefer()`。

适用场景：

- 大字段偶尔才会用到
- 列表页不需要正文详情

### 45.3 `contains_eager()`

当你已经手动写了 `join`，但又希望 SQLAlchemy 把结果映射回关系字段，可以用它。

```python
from sqlalchemy.orm import contains_eager


stmt = (
    select(User)
    .join(User.dept)
    .options(contains_eager(User.dept))
)
rows = session.execute(stmt).scalars().all()
```

适用场景：

- 你要自己控制 join 条件
- 同时又想保留 ORM 关系填充能力

### 45.4 `load_only` 和响应模型优化

在 FastAPI 项目里，很多接口只返回：

- `id`
- `name`
- `status`

这类场景不要默认整行 ORM 对象全量加载。  
可以考虑：

1. `load_only()`
2. 直接查指定列
3. `mappings()` 拿字典结果

如何选：

- 还需要 ORM 对象关系能力时，用 `load_only()`
- 只是简单列表返回时，直接查列通常更轻

## 46. 并发控制和锁

只会写事务还不够，真实项目里还会遇到“并发更新冲突”。

比如：

- 两个请求同时扣库存
- 两个请求同时审核同一条记录
- 两个请求同时修改余额

这时要理解锁和并发控制。

### 46.1 为什么事务不等于自动解决并发问题

事务保证的是：

- 一组操作的原子性
- 提交和回滚边界

但它不自动保证：

- 你的业务不会被并发覆盖

例如两个事务都读到同样的库存值，然后都扣减，仍然可能产生竞争问题。

### 46.2 悲观锁 `with_for_update()`

悲观锁的思路是：

- 我先把这行锁住
- 别的事务先别动

```python
stmt = (
    select(Product)
    .where(Product.id == product_id)
    .with_for_update()
)
product = session.execute(stmt).scalar_one()
```

适合场景：

- 库存扣减
- 余额变更
- 严格串行的关键写操作

理解：

- 先查
- 查的时候加锁
- 在同一个事务里完成修改

注意：

- 不同数据库对锁的实现细节不同
- 锁范围和等待行为要结合数据库方言理解

### 46.3 乐观锁

乐观锁的思路不是“先锁住”，而是：

- 允许并发修改尝试发生
- 提交时检查版本是否被别人改过

最常见方式是版本号字段。

```python
from sqlalchemy.orm import Mapped, mapped_column


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    __mapper_args__ = {
        "version_id_col": version,
    }
```

效果上可以理解为：

- 查询时拿到 `version=1`
- 更新时带条件 `where version=1`
- 如果别人已经改成 `version=2`
- 当前更新就会失败

适合场景：

- 冲突概率不高
- 更关注吞吐量
- 不想频繁持有数据库锁

### 46.4 悲观锁和乐观锁怎么选

悲观锁更适合：

- 冲突概率高
- 更新必须强一致
- 单次操作很关键

乐观锁更适合：

- 冲突概率低
- 更关注吞吐量
- 可以接受重试

### 46.5 库存扣减的一个理解案例

假设商品库存是 10。

错误思路：

1. 查询库存 = 10
2. Python 里减 1
3. 更新回去

两个请求同时做时，就可能都读到 10。

更稳的方案通常有两种：

1. 事务 + `with_for_update()`
2. 直接写条件更新 SQL

例如：

```python
stmt = (
    update(Product)
    .where(Product.id == product_id, Product.stock > 0)
    .values(stock=Product.stock - 1)
)
result = session.execute(stmt)
```

如果受影响行数为 0，就说明扣减失败。

这类写法的价值是：

- 把并发判断尽量下推到数据库
- 减少“先查再改”的竞争窗口

## 47. 这一轮补充解决了什么

到这里，这份文档又往前补了几类很常见但一开始容易忽略的内容：

- 约束、索引、命名规范
- 常用类型和自定义类型
- Session 配置项
- ORM DML 进阶
- 查询加载控制
- 并发控制和锁

如果你现在的目标是“能把 SQLAlchemy 用在真实项目里，而且尽量少踩中后期坑”，那么这些内容是很值得尽早掌握的。
