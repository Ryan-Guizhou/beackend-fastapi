# backend-fastapi

这是一个使用 `uv` 管理依赖的 Python / FastAPI 项目。

## 快速开始

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv sync
uv run python main.py
```

## 配置

项目配置使用 JSON5，按环境拆分在 `env` 目录下：

- `env/dev.json5`
- `env/uat.json5`
- `env/prod.json5`

通过 `ENV` 环境变量选择配置文件，未指定时默认使用 `dev`：

```powershell
$env:ENV="dev"
uv run python main.py
```

配置按模块聚合，例如 `app`、`database`、`redis`、`mongo`、`cache`、`jwt`、`log`、`scheduler`。代码中使用新结构读取配置：

```python
settings.redis.url
settings.mongo.db
settings.database.url
settings.app.port
```

## Redis 缓存

Redis 在 FastAPI `lifespan` 中初始化，并通过 `set_default_cache_manager()` 注册默认缓存管理器。业务代码使用装饰器时不需要显式传入 `cache_manager`。

典型用法：

```python
from utils.redis.cache_decorator import cacheable, cache_evict


@cacheable(cache_name="dict", key="active", ttl=3600, local_ttl=300, sync=True)
async def get_all_active_dict(...) -> list[DictInfo]:
    ...


@cache_evict(cache_name="dict", all_entries=True)
async def update_dict(...) -> DictInfo:
    ...
```

约定：

- `cache_name` 是一类缓存的统一前缀。
- 被 `@cacheable` 修饰的方法不要返回 ORM 对象，返回 Pydantic 模型、基础类型、列表或分页响应。
- 写操作优先清理缓存，由读操作回填缓存。
- 分页查询默认不缓存；稳定列表和详情查询可以缓存。

完整设计、装饰器参数、Key 规则和生产建议见 [FastAPI Redis 缓存组件使用说明](docs/fastapi-redis-cache-design.md)。

## 文档

- [uv 使用说明](docs/uv-guide.md)
- [Alembic 使用指南](docs/alembic-guide.md)
- [FastAPI 使用指南](docs/fastapi-guid.md)
- [Pydantic 使用指南](docs/pydantic-guid.md)
- [SQLAlchemy 使用指南](docs/sqlalchemy-guid.md)
- [FastAPI Redis 缓存组件使用说明](docs/fastapi-redis-cache-design.md)
- [Python Web 实战指南](docs/python-web-practice-guid.md)
- [Python 列表推导式指南](docs/list-comprehension-guide.md)
- [Python 内建函数指南](docs/builtin-functions-guide.md)
