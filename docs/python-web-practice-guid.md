# FastAPI + Pydantic + SQLAlchemy Python Web 开发实践指南

> 这份文档讲的不是单个技术点，而是三者如何组合起来做一个真实可维护的 Python Web 项目。  
> 如果你已经看过：
> - [FastAPI 指南](C:/coding/backend-fastapi/docs/fastapi-guid.md:1)
> - [Pydantic 指南](C:/coding/backend-fastapi/docs/pydantic-guid.md:1)
> - [SQLAlchemy 指南](C:/coding/backend-fastapi/docs/sqlalchemy-guid.md:1)
>
> 那这份文档可以理解为“工程落地版”。

## 1. 三个技术各自负责什么

先把边界划清楚，不然后面项目结构一定会乱。

### 1.1 FastAPI 负责什么

FastAPI 负责：

- HTTP 路由
- 请求分发
- 依赖注入
- 生命周期
- 中间件
- 异常处理
- OpenAPI 文档

你可以把它理解成：

> Web 框架外壳。

### 1.2 Pydantic 负责什么

Pydantic 负责：

- 请求参数校验
- 响应结构约束
- 配置加载
- DTO / Schema 定义

你可以把它理解成：

> 输入输出边界的结构化工具。

### 1.3 SQLAlchemy 负责什么

SQLAlchemy 负责：

- 数据库模型
- 查询
- 持久化
- 事务

你可以把它理解成：

> 数据存储访问层。

### 1.4 一句话分工

- FastAPI 管“请求怎么进来”
- Pydantic 管“数据长什么样”
- SQLAlchemy 管“数据怎么存和怎么查”

## 2. 三者协作的整体架构

```mermaid
flowchart TD
    A[Client Request] --> B[FastAPI Router]
    B --> C[Pydantic Request Schema]
    B --> D[Depends get_db / get_current_user]
    C --> E[Service Layer]
    D --> E
    E --> F[SQLAlchemy ORM / Core]
    F --> E
    E --> G[Pydantic Response Schema]
    G --> H[Client Response]
```

这张图最重要的意思是：

- 请求先经过 FastAPI
- 输入由 Pydantic 校验
- 业务逻辑在 Service 层
- 数据访问由 SQLAlchemy 处理
- 返回时再由 Pydantic 约束输出

## 3. 为什么项目不能把三者写在一个文件里

很多初学者最开始会这么写：

```python
@app.post("/users")
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(username=data.username, email=data.email)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserVO.model_validate(user)
```

这段代码看起来没错，但一旦项目变大，就会出现问题：

- 路由文件越来越长
- 数据库逻辑到处复制
- 响应结构到处重复
- 权限校验散落
- 很难测试

所以一定要分层。

## 4. 推荐的项目结构

这是比较适合中小型到中大型 API 项目的结构。

```text
app/
  api/
    router.py
    deps.py
    v1/
      auth_api.py
      user_api.py
      order_api.py
  service/
    auth_service.py
    user_service.py
    order_service.py
  models/
    base.py
    user.py
    order.py
  schemas/
    common.py
    auth.py
    user.py
    order.py
  repository/
    user_repository.py
    order_repository.py
  config/
    settings.py
    database.py
  middleware/
    request_log.py
  exception/
    errors.py
    handlers.py
  utils/
    security.py
  main.py
```

### 4.1 每个目录建议放什么

`api/`

- 路由
- 依赖
- 接口层

`service/`

- 业务逻辑
- 流程编排

`models/`

- SQLAlchemy ORM 模型

`schemas/`

- Pydantic 请求/响应模型

`repository/`

- 可选层
- 如果项目数据库逻辑很复杂，可以抽出来

`config/`

- Settings
- 数据库初始化

`middleware/`

- 请求日志
- request id
- 通用请求级逻辑

`exception/`

- 自定义异常
- 全局异常处理器

## 5. 更小项目可以怎么简化

如果项目不大，可以收缩成这样：

```text
app/
  api/
    user_api.py
  service/
    user_service.py
  models/
    user.py
  schemas/
    user.py
  config/
    settings.py
    database.py
  main.py
```

原则不是“目录越多越高级”，而是：

> 结构要能支撑维护，不要为了分层而分层。

## 6. 一个请求在项目里怎么流转

以“创建用户”为例。

```mermaid
sequenceDiagram
    participant C as Client
    participant A as user_api.py
    participant P as UserCreate
    participant S as UserService
    participant D as AsyncSession
    participant M as User ORM
    participant R as UserVO

    C->>A: POST /users + JSON
    A->>P: 参数校验
    P-->>A: 结构化数据
    A->>S: create_user(data, db)
    S->>M: 构造 User 实体
    S->>D: add / commit / refresh
    D-->>S: ORM 对象
    S-->>A: User
    A->>R: response_model 序列化
    A-->>C: JSON Response
```

## 7. 一个完整的最小样例

### 7.1 配置层 `settings.py`

```python
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "demo"
    DEBUG: bool = True
    DATABASE_URL: str = "mysql+aiomysql://root:123456@127.0.0.1:3306/demo"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

### 7.2 数据库层 `database.py`

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 7.3 ORM 模型 `models/user.py`

```python
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

### 7.4 Pydantic 模型 `schemas/user.py`

```python
from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr


class UserVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
```

### 7.5 业务层 `service/user_service.py`

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate


class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, data: UserCreate) -> User:
        user = User(username=data.username, email=data.email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.is_deleted.is_(False))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
```

### 7.6 路由层 `api/user_api.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.user import UserCreate, UserVO
from app.service.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserVO)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    return await UserService.create_user(db, data)


@router.get("/{user_id}", response_model=UserVO)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user
```

### 7.7 启动入口 `main.py`

```python
from fastapi import FastAPI

from app.api.user_api import router as user_router
from app.config.settings import settings

app = FastAPI(title=settings.APP_NAME)
app.include_router(user_router)
```

## 8. 为什么这套结构合理

### 8.1 Route 只负责“接”和“回”

路由层做的事应该很克制：

- 接收参数
- 注入依赖
- 调用 Service
- 返回结果

不应该在这里堆：

- 大量数据库操作
- 复杂业务判断
- 权限规则拼装

### 8.2 Service 负责“做事”

Service 层最适合承载：

- 业务规则
- 流程编排
- 跨模型操作
- 调多个 repository

### 8.3 Schema 负责“数据边界”

Schema 层负责：

- 请求模型
- 响应模型
- 分页模型
- 统一响应结构

不要把：

- ORM 模型
- 业务对象
- 配置对象

都混在一起。

### 8.4 ORM 负责“持久化”

ORM 模型只表达：

- 表结构
- 字段关系
- 数据库层语义

不要把：

- 前端返回格式
- 接口文档字段含义
- 复杂业务规则

硬塞到 ORM 里。

## 9. 真实开发中最常见的 Schema 划分

以用户模块为例，推荐至少拆成：

```python
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class UserQuery(BaseModel):
    page_index: int = 1
    page_size: int = 20
    keyword: str | None = None


class UserVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
```

为什么不要只写一个 `UserSchema`：

- 创建需要密码
- 返回不能带密码
- 更新字段通常可选
- 查询参数和实体字段不是一回事

## 10. 一个分页接口的实际写法

### 10.1 Query Schema

```python
from pydantic import BaseModel, Field


class UserQuery(BaseModel):
    page_index: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    keyword: str | None = None
```

### 10.2 Service

```python
from sqlalchemy import select, func


class UserService:
    @staticmethod
    async def get_page(db: AsyncSession, query: UserQuery) -> tuple[list[User], int]:
        filters = [User.is_deleted.is_(False)]
        if query.keyword:
            filters.append(User.username.like(f"%{query.keyword}%"))

        total_stmt = select(func.count(User.id)).where(*filters)
        total = (await db.execute(total_stmt)).scalar_one()

        stmt = (
            select(User)
            .where(*filters)
            .order_by(User.id.desc())
            .offset((query.page_index - 1) * query.page_size)
            .limit(query.page_size)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return rows, total
```

### 10.3 Route

```python
from fastapi import Depends


@router.get("/")
async def user_page(query: UserQuery = Depends(), db: AsyncSession = Depends(get_db)):
    rows, total = await UserService.get_page(db, query)
    return {"total": total, "rows": [UserVO.model_validate(item) for item in rows]}
```

为什么这样拆：

- Query 模型负责参数校验
- Service 负责查询逻辑
- Route 负责拼响应

## 11. 一个登录接口的实际写法

### 11.1 Schema

```python
class LoginForm(BaseModel):
    username: str
    password: str


class TokenVO(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### 11.2 Service

```python
class AuthService:
    @staticmethod
    async def login(db: AsyncSession, data: LoginForm) -> TokenVO:
        user = await UserService.get_by_username(db, data.username)
        if not user:
            raise ValueError("username or password invalid")

        if not verify_password(data.password, user.password):
            raise ValueError("username or password invalid")

        token = create_access_token({"sub": str(user.id)})
        return TokenVO(access_token=token)
```

### 11.3 Route

```python
@router.post("/login", response_model=TokenVO)
async def login(data: LoginForm, db: AsyncSession = Depends(get_db)):
    return await AuthService.login(db, data)
```

这样做的好处：

- 路由不关心密码校验细节
- token 结构由 schema 管
- 数据访问和安全逻辑可测试

## 12. 一个“当前用户”接口的实际写法

### 12.1 依赖

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    user_id = decode_token(token)
    user = await UserService.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="invalid token")
    return user
```

### 12.2 Route

```python
@router.get("/me", response_model=UserVO)
async def me(current_user = Depends(get_current_user)):
    return current_user
```

这里体现的是：

- 认证逻辑放依赖
- 路由只声明它需要“当前用户”

## 13. 实际项目里什么时候加 Repository 层

不是所有项目都必须要 `repository/`。

### 13.1 不需要的场景

- 项目不大
- 查询逻辑不复杂
- Service 层足够清晰

### 13.2 需要的场景

- 多模块复用同一批数据库操作
- 查询逻辑特别复杂
- 想把业务逻辑和数据访问再分开
- 团队偏向 DDD / Repository 风格

### 13.3 一句话建议

- 小中型项目：Route + Service + Model + Schema 就够了
- 大型项目：再考虑 Repository

## 14. 实际开发中的中间件样例

### 14.1 请求日志中间件

```python
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import uuid


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.time()

        response = await call_next(request)

        duration = round((time.time() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        print(request.method, request.url.path, response.status_code, duration)
        return response
```

适合放中间件的原因：

- 每个请求都要记录
- 与业务接口无关

## 15. 实际开发中的异常处理样例

### 15.1 自定义业务异常

```python
class BusinessError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
```

### 15.2 全局异常处理

```python
from fastapi.responses import JSONResponse


@app.exception_handler(BusinessError)
async def business_error_handler(request, exc: BusinessError):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "msg": exc.message, "data": None},
    )
```

这样做的好处：

- 接口返回结构统一
- 不用每个路由都手写 try/except

## 16. 实际开发中的测试样例

### 16.1 覆盖数据库依赖

```python
def override_get_db():
    yield test_db


app.dependency_overrides[get_db] = override_get_db
```

### 16.2 覆盖登录用户依赖

```python
def override_get_current_user():
    return FakeUser(id=1, username="admin", role="admin")


app.dependency_overrides[get_current_user] = override_get_current_user
```

### 16.3 测试接口

```python
def test_user_me():
    response = client.get("/me")
    assert response.status_code == 200
```

## 17. 开发中最常见的错误分层

错误一：

- 路由里直接写所有 SQL

错误二：

- 把 SQLAlchemy 模型直接当请求模型

错误三：

- 把 Pydantic 模型直接当 ORM 模型使用

错误四：

- 把业务规则塞进 validator 或 Depends

错误五：

- 每个接口都自己创建数据库连接

## 18. 一套比较稳的工程原则

1. FastAPI 负责 Web 层，不负责业务核心
2. Pydantic 负责边界数据，不负责持久化
3. SQLAlchemy 负责数据库，不负责请求校验
4. 路由层保持薄
5. Service 层负责流程编排
6. 依赖注入负责上下文准备
7. 生命周期负责全局资源初始化
8. 中间件负责请求级横切逻辑

## 19. 同步还是异步，在这套组合里怎么选

如果你项目是：

- FastAPI
- SQLAlchemy 异步驱动
- Redis 异步客户端
- 外部 HTTP 也是异步

那建议：

- 全链路异步

如果你项目是：

- 管理后台
- 并发不高
- 团队更熟同步风格

那也完全可以：

- FastAPI + 同步 SQLAlchemy

重点不是“异步更高级”，而是：

> 整体风格一致，比局部追求异步更重要。

## 20. 这份文档最终想解决什么问题

这份文档的目标不是教你某个单独 API，而是帮你建立这样一种工程认知：

- 一个 Python Web 项目为什么要分层
- FastAPI、Pydantic、SQLAlchemy 三者怎么配合最顺
- 实际开发时代码应该放哪
- 请求从进来到出去，中间应该经过哪些层
- 怎样写出来的项目更清晰、更好维护、更容易测试

如果你愿意，下一步我可以继续补一份更偏“模板化”的文档：

`从 0 到 1 搭一个 FastAPI + Pydantic + SQLAlchemy 项目`

它会更像脚手架教程，直接告诉你每个文件怎么建、每一步先做什么。 

## 21. 通用响应模型怎么设计

这一部分是很多项目都会遇到的问题：

- 接口到底要不要统一包一层
- 分页响应怎么定义
- 成功和失败是否统一结构
- 什么场景不适合强行包成统一格式

先说结论：

- 大多数后台管理系统、BFF、内部接口，统一响应结构通常更稳
- 下载流、文件流、第三方 webhook 回调类接口，不一定适合强包一层

### 21.1 最常见的统一响应结构

最常见的结构通常是：

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

这种结构的价值是：

- 前端处理逻辑统一
- 错误码语义统一
- 日志和监控更容易归类
- 异常处理器更容易统一返回

### 21.2 一个基础通用响应模型

可以把它放在：

```text
app/schemas/common.py
```

示例：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: T | None = None
```

使用方式：

```python
class UserVO(BaseModel):
    id: int
    username: str


resp = ApiResponse[UserVO](
    data=UserVO(id=1, username="tom"),
)
```

这个模型适合：

- 单对象返回
- 列表返回
- 登录返回 token
- 创建、详情、更新类接口

### 21.3 分页响应模型

分页响应通常值得单独建模，不建议每个接口手写：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class PageData(BaseModel, Generic[T]):
    total: int
    rows: list[T]
    page_index: int
    page_size: int


class PageResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: PageData[T]
```

示例：

```python
class UserVO(BaseModel):
    id: int
    username: str


data = PageData[UserVO](
    total=100,
    rows=[UserVO(id=1, username="tom")],
    page_index=1,
    page_size=20,
)

resp = PageResponse[UserVO](data=data)
```

这样做的好处是：

- 分页结构统一
- 接口文档统一
- 前端不用猜字段名

### 21.4 登录和简单状态接口的响应模型

不是所有接口都返回复杂对象，但也不建议全部裸字典。

例如：

```python
class TokenVO(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StatusVO(BaseModel):
    success: bool = True
```

再包一层：

```python
ApiResponse[TokenVO]
ApiResponse[StatusVO]
```

这样文档和类型提示会更稳定。

### 21.5 一个更完整的 `common.py` 示例

```python
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: T | None = None


class PageData(BaseModel, Generic[T]):
    total: int = Field(..., ge=0)
    rows: list[T]
    page_index: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)


class PageResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: PageData[T]
```

### 21.6 路由里怎么用统一响应模型

```python
@router.get("/{user_id}", response_model=ApiResponse[UserVO])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    return ApiResponse[UserVO](data=UserVO.model_validate(user))
```

分页接口：

```python
@router.get("/", response_model=PageResponse[UserVO])
async def user_page(query: UserQuery = Depends(), db: AsyncSession = Depends(get_db)):
    rows, total = await UserService.get_page(db, query)
    return PageResponse[UserVO](
        data=PageData[UserVO](
            total=total,
            rows=[UserVO.model_validate(item) for item in rows],
            page_index=query.page_index,
            page_size=query.page_size,
        )
    )
```

### 21.7 失败响应要不要也统一

建议统一。

比如业务异常统一返回：

```json
{
  "code": 40001,
  "msg": "username already exists",
  "data": null
}
```

这样前端更容易做统一处理：

- `code == 0` 视为成功
- 非 0 视为业务失败

但要注意区分两层语义：

- HTTP 状态码
- 业务错误码

推荐做法：

- HTTP 状态码表达协议层结果
- `code` 表达业务层语义

例如：

- 参数错误用 `400`
- 未登录用 `401`
- 无权限用 `403`
- 未找到用 `404`
- 服务端异常用 `500`

同时响应体里保留业务 `code` 和 `msg`。

### 21.8 哪些接口不建议强行套统一响应模型

不太适合统一包裹的场景：

- 文件下载
- 流式响应
- 图片、Excel、PDF 导出
- WebSocket
- 第三方要求固定返回格式的 webhook

这些场景更重要的是遵循协议本身，而不是强行追求统一 JSON 包装。

## 22. 通用响应模型和异常处理怎么配合

如果你用了统一响应结构，那么异常处理器最好和它一致。

例如：

```python
from fastapi.responses import JSONResponse


@app.exception_handler(BusinessError)
async def business_error_handler(request, exc: BusinessError):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "msg": exc.message,
            "data": None,
        },
    )
```

这样能保证：

- 正常返回结构统一
- 失败返回结构也统一
- 前端不需要两套解析逻辑

如果继续往前走一步，还可以约定：

- 成功统一 `code = 0`
- 业务错误从 `40000` 段开始
- 权限错误从 `40100` / `40300` 段开始

这样项目规模变大后更容易维护。

## 23. 这个文档里还值得补的几个工程点

除了统一响应模型，这份文档还建议补上下面几类实践意识。

### 23.1 事务边界要尽量稳定

一个请求里，最好尽量只有一个明确事务边界。

不推荐：

- 路由里 `commit` 一次
- Service A `commit` 一次
- Service B 又 `commit` 一次

因为这样会导致：

- 事务难以回滚完整
- 业务组合很难保持一致性

更推荐：

- Service 负责执行业务
- 上层统一决定什么时候提交事务

### 23.2 通用基类和通用字段

真实项目里通常会有一批重复字段：

- `id`
- `created_at`
- `updated_at`
- `created_by`
- `updated_by`
- `is_deleted`

这类字段建议抽成 ORM mixin 或基类。

示例：

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

这样能减少重复，也方便统一规范。

### 23.3 配置不要只拆“模块”，还要拆“生命周期”

如果项目有热更新配置需求，配置不只要按模块拆，还要按是否可变拆。

例如：

- `AppSettings`
- `InfraSettings`
- `SecuritySettings`
- `RuntimeFeatureSettings`

这样更容易区分：

- 启动时固定配置
- 运行时可刷新配置

### 23.4 请求 ID 最好贯穿日志、异常、响应

文档前面已经有请求日志中间件，但实践里更稳的做法是把 `request_id` 贯穿下去：

- 请求日志带 `request_id`
- 异常日志带 `request_id`
- 响应头返回 `X-Request-ID`

这样查问题时才能把一次请求完整串起来。

### 23.5 安全边界要明确

不要把这些职责混在一起：

- `Depends` 负责拿当前用户和上下文
- Service 负责业务权限判断
- Pydantic 负责数据格式校验

比如：

- token 解析适合放依赖里
- “当前用户是否能修改这条订单” 更适合放 Service

## 24. 一套更完整的 `schemas/common.py` 示例

如果你准备把统一响应模型真正落到项目里，可以从这样一个版本开始：

```python
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: T | None = None


class PageData(BaseModel, Generic[T]):
    total: int = Field(..., ge=0, description="总条数")
    rows: list[T] = Field(default_factory=list, description="当前页数据")
    page_index: int = Field(..., ge=1, description="页码")
    page_size: int = Field(..., ge=1, description="每页条数")


class PageResponse(BaseModel, Generic[T]):
    code: int = 0
    msg: str = "success"
    data: PageData[T]


class ErrorResponse(BaseModel):
    code: int
    msg: str
    data: None = None
```

这套模型适合：

- 管理后台接口
- 前后端分离项目
- BFF 层
- 内部管理系统 API

如果你的项目非常偏 REST 原教旨主义，也可以选择不统一包裹成功响应，而只统一错误响应。  
但如果你的团队更重视：

- 前端接入一致性
- 错误处理一致性
- 文档一致性

那么统一响应模型通常是更稳的选择。
