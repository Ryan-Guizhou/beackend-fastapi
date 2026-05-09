# backend-fastapi 开发约定

本文档约束当前仓库内的代码生成、修改、注释、文档和依赖管理方式。

## 1. 基本原则

- 优先遵循项目已有目录结构、命名方式和工具封装。
- 修改代码前先阅读相关模块，不凭文件名猜实现。
- 改动保持聚焦，只处理当前任务相关文件。
- 不顺手重构无关代码，不格式化无关文件。
- 不删除或回退用户已有改动。
- 新增功能要接入现有配置、生命周期、日志和依赖管理方式。
- 代码以可维护为优先，不为了“通用”提前抽象。

## 2. Python 代码风格

- 使用 Python 3.10+ 类型标注。
- 优先使用 `str | None`、`list[str]`、`dict[str, Any]` 这类内置泛型写法。
- 异步 I/O 使用 `async/await`，不要在异步接口中引入阻塞调用。
- 函数参数较多时按项目现有风格换行。
- 业务判断保持直白，不写过度嵌套的表达式。
- 返回统一响应时使用 `base.base_schema.Response`。
- 数据库会话优先使用 `config.database.DbSession`。
- 不在 Router 中堆复杂业务逻辑，复杂逻辑下沉到 Service 层。

## 3. 文件头和注释

新增 Python 文件建议保留项目文件头格式：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Project: backend-fastapi
@Author: Mr Shu
@Contact: huanhuanshu48@gmail.com
@File: xxx.py
@Create: yyyy/m/d HH:mm
@Desc: 文件描述
"""
```

补全注释时按照 [`utils/security.py`](utils/security.py) 的样式：

```python
def func(arg: str) -> str:
    """
    功能描述。

    Args:
        arg: 参数说明。

    Returns:
        str: 返回值说明。
    """
```

注释要求：

- 使用中文。
- 使用 `Args`、`Returns`、`Raises`。
- 描述业务含义，不重复翻译代码。
- 简单变量赋值不写注释。
- 复杂分支、外部资源、事务、锁、缓存一致性需要说明。
- 不保留乱码注释。
- 不混用 `:param` 和 `Args` 风格；新补注释统一用 `Args`。

## 4. FastAPI 分层约定

常规模块结构：

```text
core/<module>
├── api.py       # 路由层
├── schema.py    # 请求/响应模型
├── model.py     # SQLAlchemy ORM 模型
└── service.py   # 业务服务层
```

### 4.1 Router 层

- 只负责参数接收、依赖注入、响应封装。
- 路由函数返回 `Response`。
- 路由参数使用 `Annotated`、`Path`、`Query`、`Body` 表达。
- 输入校验优先放在 Pydantic Schema 中。
- 唯一性检查、状态检查等小型校验可放 Router 私有函数。
- 不直接写复杂 SQL。

### 4.2 Service 层

- 继承和复用 `base.base_service.BaseService`。
- 负责业务规则、数据库访问和跨表操作。
- 数据库访问使用 SQLAlchemy async API。
- Service 方法需要明确传入 `AsyncSession` 或项目封装的数据库会话。
- 分页查询返回 `(items, total)` 这类明确结构。

### 4.3 Schema 层

- 使用 Pydantic v2。
- ORM 输出模型需要配置 `from_attributes=True`。
- 字段别名和前端字段名保持稳定。
- 更新模型使用 `exclude_unset=True`、`exclude_none=True` 过滤空值。

## 5. 数据库和迁移

- SQLAlchemy 模型统一继承 `config.database.Base`。
- 新增模型放在模块的 `model.py` 中，方便 Alembic 自动扫描。
- 数据库迁移使用 Alembic。
- 自动生成迁移后必须检查脚本内容。
- 字段重命名、表重命名、复杂索引不要直接相信 `autogenerate`。

常用命令：

```powershell
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1
```

## 6. Redis 使用约定

项目内 Redis 新代码优先使用 [`utils/redis`](utils/redis)。

生命周期中由 `main.py` 初始化：

- `RedisManager`
- `RedisService`
- `CacheManager`

应用运行时通过 `app.state` 获取：

- `app.state.redis_manager`
- `app.state.redis_service`
- `app.state.cache_manager`

缓存 Key 规则：

```text
<cache_name>:<raw_key>
```

分布式锁 Key：

```text
<cache_name>:lock:<raw_key>
```

约定：

- 不再新增统一全局 Redis `prefix`。
- `cache_name` 就是一类缓存的统一前缀。
- 写操作优先删缓存，读操作负责回填缓存。
- 本地缓存 TTL 应明显小于 Redis TTL。
- 强一致业务不要依赖二级缓存保证一致性。
- 旧的 `utils/redis_client.py` 只作为兼容遗留代码，不作为新代码首选。

## 7. Mongo 使用约定

项目内 Mongo 新代码使用 [`utils/mongo`](utils/mongo) 的 `MongoManager`。

生命周期中由 `main.py` 初始化：

- `MongoManager`

应用运行时通过以下对象获取：

```python
request.app.state.mongo_manager
```

配置项来自 `config.config.settings`：

- `MONGO_HOST`
- `MONGO_PORT`
- `MONGO_USER`
- `MONGO_PASSWORD`
- `MONGO_DB`
- `MONGO_AUTH_SOURCE`
- `MONGO_URL`

使用约定：

- 异步操作统一使用 `motor`。
- 常规 CRUD 优先复用 `MongoManager` 方法。
- 需要原生能力时通过 `mongo_manager.collection(name)` 获取集合。
- `_id` 查询使用 `MongoManager.object_id()` 转换。
- 多文档事务使用 `mongo_manager.transaction()`。
- Mongo 事务依赖副本集或分片集群，单机未启用事务时不要假设可用。

## 8. 生命周期管理

应用级资源统一放到 `main.py` 的 `lifespan` 中管理。

启动阶段：

```text
setup_logging
-> RedisManager.init
-> RedisService
-> CacheManager.start
-> MongoManager.init
-> Scheduler start
```

关闭阶段：

```text
Scheduler stop
-> CacheManager.stop
-> RedisManager.close
-> MongoManager.close
-> logging.shutdown
```

新增外部资源时必须：

- 在 `app.state` 注册。
- 在 `finally` 中释放。
- 释放顺序要考虑依赖关系。
- 启动失败时不能留下未关闭连接。

## 9. 配置管理

配置统一放在 [`config/config.py`](config/config.py) 的 `Settings` 中。

环境变量文件：

```text
env/dev.env
env/uat.env
env/prod.env
```

新增配置时：

- 在 `Settings` 中添加字段和默认值。
- 在三个环境文件中补对应配置。
- 需要拼接 URL 的配置放到 `build_urls()`。
- 不在业务代码中硬编码连接串、账号、密码。

## 10. 依赖管理

项目同时保留 `requirements.txt` 和 `pyproject.toml`。

新增依赖时：

```powershell
uv add <package>
```

如果先改了 `requirements.txt`，需要同步到 uv：

```powershell
uv add -r requirements.txt
uv sync --locked
```

约定：

- 不手工只改一个依赖文件。
- `uv.lock` 需要随 `pyproject.toml` 一起更新。
- 新增运行时依赖必须确认能导入。

## 11. 文档风格

文档放在 `docs/`。

写法参考：

- [`docs/alembic-guide.md`](docs/alembic-guide.md)
- [`docs/fastapi-redis-cache-design.md`](docs/fastapi-redis-cache-design.md)
- [`docs/python-web-practice-guid.md`](docs/python-web-practice-guid.md)

文档要求：

- 只写技术本身。
- 先说明边界，再给目录、接入方式、示例、注意事项。
- 示例代码必须匹配当前实现。
- 不写空泛总结。
- 不写营销式描述。
- Key、配置、命令要用代码块明确给出。

## 12. 测试和校验

改动后至少做相关校验：

```powershell
python -m compileall <changed-path>
```

涉及依赖时：

```powershell
uv sync --locked
```

涉及应用入口时：

```powershell
python -c "import main; print('ok')"
```

涉及数据库迁移时：

```powershell
alembic current
alembic upgrade head
```

如果由于本地服务未启动导致无法完成 Redis、Mongo、MySQL 连接测试，需要在结果中说明。

## 13. 禁止事项

- 不使用同步 Mongo / Redis 客户端写异步接口。
- 不在 Router 中创建 Redis、Mongo、数据库连接。
- 不在业务代码中硬编码环境配置。
- 不直接在强一致业务中依赖缓存结果。
- 不用 `KEYS` 扫描生产 Redis。
- 不吞掉异常后静默失败，除非调用方明确允许。
- 不为了补注释改动业务逻辑。
- 不提交 `.venv`、`__pycache__`、本地 IDE 临时文件。
- 不新增无用包装层。

