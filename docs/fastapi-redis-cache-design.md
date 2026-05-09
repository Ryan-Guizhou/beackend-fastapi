# FastAPI Redis 缓存组件使用说明

> 面向当前 `backend-fastapi` 项目的 Redis 缓存组件说明。
> 代码位置：[`utils/redis`](../utils/redis)。

## 1. 组件边界

该组件提供一套异步 Redis 缓存封装，核心能力包括：

- Redis 连接生命周期管理
- JSON 序列化与反序列化
- 常用 Redis 数据结构操作
- L1 本地缓存 + L2 Redis 二级缓存
- 基于 Redis Pub/Sub 的本地缓存失效同步
- 基于 Redis 分布式锁的缓存击穿保护
- 类似 Spring Cache 的装饰器接口

组件不负责：

- 数据库事务一致性
- ORM 自动级联失效
- 强一致缓存同步
- 缓存指标采集
- TTL 随机抖动
- 大规模缓存分组的版本化失效

## 2. 文件说明

```text
utils/redis
├── redis_manager.py      # Redis 客户端创建、连接校验、关闭
├── redis_service.py      # Redis 通用操作、序列化、分布式锁、发布订阅
├── local_cache.py        # 进程内本地缓存，支持 TTL 和 LRU 淘汰
├── cache_manager.py      # 二级缓存读写、清理、失效广播
├── cache_decorator.py    # cacheable / cache_put / cache_evict / caching
└── __init__.py
```

### 2.1 `RedisManager`

职责：

- 通过 Redis URL 创建 `redis.asyncio.Redis` 客户端
- 设置连接池参数
- 初始化时执行 `ping()` 校验连接
- 应用关闭时释放连接

主要接口：

```python
manager = RedisManager("redis://localhost:6379/0")
await manager.init()
client = manager.client
await manager.close()
```

### 2.2 `RedisService`

职责：

- 封装 Redis 常用命令
- 统一 JSON 序列化
- 支持 `Pydantic BaseModel` 自动转换
- 支持按目标类型反序列化
- 提供分布式锁
- 提供发布订阅能力

当前初始化不使用统一全局 `prefix`：

```python
redis_service = RedisService(redis_manager.client)
```

Key 仅由调用方传入的片段拼接：

```python
redis_service.build_key("user_detail", 1)
# user_detail:1
```

### 2.3 `LocalCache`

职责：

- 提供进程内缓存
- 支持 TTL
- 支持最大容量限制
- 使用 `OrderedDict` 做 LRU 淘汰
- 使用 `asyncio.Lock` 保证协程并发安全

适合缓存：

- 热点详情
- 字典配置
- 短 TTL 查询结果

不适合缓存：

- 超大列表
- 大对象
- 强一致数据

### 2.4 `CacheManager`

职责：

- 编排 L1 / L2 缓存读取
- 编排缓存写入
- 处理 `None` 缓存
- 删除单个缓存
- 清空指定缓存分组
- 通过 Pub/Sub 通知其他实例清理 L1

读取顺序：

```text
LocalCache -> Redis -> 回源函数
```

写入顺序：

```text
Redis -> LocalCache
```

删除顺序：

```text
LocalCache -> Redis -> Pub/Sub 失效通知
```

### 2.5 `cache_decorator`

提供四个装饰器：

- `@cacheable`：读缓存，未命中时执行函数并写入缓存
- `@cache_put`：始终执行函数，执行后写入缓存
- `@cache_evict`：执行函数前或后删除缓存
- `@caching`：组合多个写入和删除操作

装饰器只支持 `async` 函数。

## 3. Key 规则

当前缓存 Key 以 `cache_name` 作为一类缓存的统一前缀。

### 3.1 普通缓存 Key

```text
<cache_name>:<raw_key>
```

示例：

```text
user_detail:1
user_list:page_1:size_20
dict_item:gender
tenant_permission:tenant_1:user_100
```

### 3.2 分布式锁 Key

`@cacheable(sync=True)` 使用以下锁 Key：

```text
<cache_name>:lock:<raw_key>
```

示例：

```text
user_detail:lock:1
```

### 3.3 清空缓存分组

`CacheManager.clear("user_detail")` 会扫描并删除：

```text
user_detail:*
```

本地缓存也会按 `user_detail:` 前缀清理。

### 3.4 命名建议

`cache_name` 表示缓存分组，应该稳定、明确、可读：

```text
user_detail
user_list
dict_item
config_value
tenant_permission
```

`raw_key` 表示具体业务维度：

```text
1
page_1:size_20
tenant_1:user_100
type_gender:enabled_1
```

不建议：

- `cache_name` 使用 `user`、`data`、`list` 这类模糊名称
- `raw_key` 直接使用 Python 对象字符串
- 多个业务含义混用同一个 `cache_name`
- 列表缓存不体现查询参数

## 4. FastAPI 接入

推荐在 `lifespan` 中初始化 Redis 和缓存管理器，并通过 `set_default_cache_manager()` 注册默认缓存管理器。注册后，业务 Service 使用缓存装饰器时不需要显式传入 `cache_manager`。

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.config import settings
from utils.redis.cache_decorator import set_default_cache_manager
from utils.redis.cache_manager import CacheManager
from utils.redis.redis_manager import RedisManager
from utils.redis.redis_service import RedisService


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_manager = RedisManager(settings.redis.url)
    await redis_manager.init()

    redis_service = RedisService(redis_manager.client)
    cache_manager = CacheManager(redis_service=redis_service)
    await cache_manager.start()

    app.state.redis_service = redis_service
    app.state.cache_manager = cache_manager
    set_default_cache_manager(cache_manager)

    try:
        yield
    finally:
        set_default_cache_manager(None)
        await cache_manager.stop()
        await redis_manager.close()


app = FastAPI(lifespan=lifespan)
```

关闭顺序必须是：

```text
CacheManager.stop() -> RedisManager.close()
```

否则 Pub/Sub 监听任务可能持有已经关闭的 Redis 连接。

## 5. 装饰器使用

装饰器会按以下顺序查找 `CacheManager`：

1. 函数参数中的 `cache_manager`
2. 类实例上的 `self.cache_manager`
3. 函数参数中的任意 `CacheManager` 实例
4. 应用启动时通过 `set_default_cache_manager()` 注册的默认实例

### 5.1 `@cacheable`

用于读操作缓存。

```python
from utils.redis.cache_decorator import cacheable


@cacheable(
    cache_name="user_detail",
    key="{user_id}",
    ttl=600,
    local_ttl=60,
    cache_none=True,
    sync=True,
)
async def get_user_detail(
    user_id: int,
) -> UserVO | None:
    return await load_user_from_db(user_id)
```

参数说明：

- `cache_name`：缓存分组名，也是缓存 Key 前缀
- `key`：基于函数参数格式化生成 `raw_key`
- `ttl`：Redis 过期时间，单位秒
- `local_ttl`：本地缓存过期时间，单位秒
- `cache_none`：是否缓存 `None`
- `sync`：是否启用分布式锁防缓存击穿
- `condition`：前置条件，不满足时跳过缓存逻辑
- `unless`：结果条件，满足时跳过写入缓存

执行流程：

```text
绑定函数参数
-> 构造 raw_key
-> 查 LocalCache
-> 查 Redis
-> 执行原函数
-> 写 Redis
-> 写 LocalCache
```

`sync=True` 时，缓存未命中后会先获取 Redis 锁，再执行回源逻辑。

### 5.2 `@cache_put`

用于写操作后刷新缓存。

```python
from utils.redis.cache_decorator import cache_put


@cache_put(
    cache_name="user_detail",
    key="{user_id}",
    ttl=600,
    local_ttl=60,
)
async def refresh_user_detail(
    user_id: int,
) -> UserVO:
    return await load_user_from_db(user_id)
```

执行流程：

```text
执行原函数
-> 检查 condition
-> 检查 unless
-> 写 Redis
-> 写 LocalCache
```

适合：

- 更新成功后返回最新对象
- 重新加载对象并同步刷新缓存

### 5.3 `@cache_evict`

用于删除缓存。

删除单个 Key：

```python
from utils.redis.cache_decorator import cache_evict


@cache_evict(
    cache_name="user_detail",
    key="{user_id}",
)
async def delete_user(
    user_id: int,
) -> None:
    await delete_user_from_db(user_id)
```

清空整个缓存分组：

```python
@cache_evict(
    cache_name="user_list",
    all_entries=True,
)
async def update_user_status(
    user_id: int,
) -> None:
    await update_status(user_id)
```

默认行为是函数成功执行后删除缓存。

如果设置 `before_invocation=True`，会先删除缓存再执行函数：

```python
@cache_evict(
    cache_name="user_detail",
    key="{user_id}",
    before_invocation=True,
)
```

`before_invocation=True` 适合必须提前清理缓存的场景；如果后续数据库操作失败，缓存已被删除。

### 5.4 `@caching`

用于一个函数触发多个缓存动作。

```python
from utils.redis.cache_decorator import CacheEvictOp, CachePutOp, caching


@caching(
    put=[
        CachePutOp(
            cache_name="user_detail",
            key="{user_id}",
            ttl=600,
            local_ttl=60,
        )
    ],
    evict=[
        CacheEvictOp(
            cache_name="user_list",
            all_entries=True,
        )
    ],
)
async def update_user(
    user_id: int,
    payload: UserUpdateDTO,
) -> UserVO:
    return await update_user_in_db(user_id, payload)
```

执行顺序：

```text
前置 evict
-> 执行原函数
-> put
-> 后置 evict
```

## 6. Service 层使用

当前项目推荐在 Service 层使用缓存装饰器。API 层只负责参数接收和 `Response` 包装，缓存不放在 API 层。

如果应用启动时已经调用 `set_default_cache_manager()`，类方法不需要传入 `cache_manager`：

```python
class UserService:
    @cacheable(
        cache_name="user_detail",
        key="{user_id}",
        ttl=600,
        local_ttl=60,
    )
    async def get_user_detail(self, user_id: int) -> UserVO | None:
        return await self.load_user_from_db(user_id)
```

如果业务 Service 持有 `self.cache_manager`，装饰器也可以自动识别。该方式适合独立测试或多缓存管理器并存的场景。

### 6.1 返回值约束

被 `@cacheable` 修饰的方法返回值必须可 JSON 序列化。推荐返回：

- Pydantic 输出模型
- `list[PydanticModel]`
- `PaginatedResponse[PydanticModel]`
- `dict`
- `list`
- `str`、`int`、`float`、`bool`、`None`

不要直接缓存 SQLAlchemy ORM 对象：

```python
# 不推荐：返回 ORM 对象，json.dumps() 无法稳定序列化
@cacheable(cache_name="dict", key="active", ttl=3600)
async def get_all_active_dict(db: DbSession) -> list[Dict]:
    ...
```

应先转换为 Pydantic 输出模型：

```python
@cacheable(cache_name="dict", key="active", ttl=3600, local_ttl=300, sync=True)
async def get_all_active_dict(db: DbSession) -> list[DictInfo]:
    dicts = await load_active_dicts(db)
    return [DictInfo.model_validate(item) for item in dicts]
```

### 6.2 查询和写入约定

当前项目约定：

- 稳定的非分页列表可以缓存。
- 详情查询可以缓存。
- 分页查询默认不缓存。
- 新增、修改、删除、批量状态变更使用 `@cache_evict` 或 `@caching` 清理缓存。
- 写操作优先删除缓存，由读操作重新回填。

## 7. 动态 Key

### 7.1 使用格式化字符串

```python
@cacheable(
    cache_name="user_list",
    key="page_{page}:size_{size}:keyword_{keyword}",
    ttl=300,
)
async def list_users(
    page: int,
    size: int,
    keyword: str,
) -> list[UserVO]:
    ...
```

### 7.2 使用 `key_builder`

```python
def build_user_list_key(page: int, size: int, keyword: str, **_) -> str:
    keyword = keyword.strip() or "all"
    return f"page_{page}:size_{size}:keyword_{keyword}"


@cacheable(
    cache_name="user_list",
    key_builder=build_user_list_key,
    ttl=300,
)
async def list_users(
    page: int,
    size: int,
    keyword: str,
) -> list[UserVO]:
    ...
```

`key` 和 `key_builder` 必须提供一个，不能同时为空。

## 8. 条件缓存

### 8.1 `condition`

`condition` 在读取缓存前执行。返回 `False` 时跳过全部缓存逻辑，直接执行原函数。

```python
@cacheable(
    cache_name="user_detail",
    key="{user_id}",
    condition=lambda user_id, **_: user_id > 0,
)
async def get_user_detail(user_id: int) -> UserVO | None:
    ...
```

适合：

- 参数非法时不缓存
- 特定请求上下文禁用缓存

### 8.2 `unless`

`unless` 在原函数执行后判断。返回 `True` 时不写入缓存。

```python
@cacheable(
    cache_name="report",
    key="{report_id}",
    unless=lambda result, **_: result is not None and result.status == "PROCESSING",
)
async def get_report(report_id: int) -> ReportVO | None:
    ...
```

适合：

- 处理中状态不缓存
- 失败结果不缓存
- 过大的结果不缓存

## 9. 类型恢复

`@cacheable` 会读取函数返回值类型注解，并将缓存中的 JSON 恢复为目标类型。

支持：

- `BaseModel`
- `list[T]`
- `set[T]`
- `tuple[T, ...]`
- `dict[K, V]`
- `Optional[T]`
- `T | None`

示例：

```python
@cacheable(cache_name="user_detail", key="{user_id}", ttl=600)
async def get_user_detail(
    user_id: int,
) -> UserVO | None:
    ...


@cacheable(cache_name="user_list", key="all", ttl=300)
async def list_users() -> list[UserVO]:
    ...
```

注意：

- 返回值没有类型注解时，缓存命中后返回 JSON 基础类型
- 自定义复杂对象需要先转换为可 JSON 序列化结构
- `datetime`、`Decimal`、`bytes` 等类型需要额外处理

## 10. 空值缓存

默认不缓存 `None`。

开启方式：

```python
@cacheable(
    cache_name="user_detail",
    key="{user_id}",
    ttl=120,
    cache_none=True,
)
```

内部实现：

```text
None -> __fastapi_cache_null__
__fastapi_cache_null__ -> None
```

建议：

- 空值缓存 TTL 设置短一些
- 不要对未校验的随机参数大量缓存空值
- 高风险接口应配合参数校验或布隆过滤器

## 11. 二级缓存一致性

当前实现是最终一致，不是强一致。

### 11.1 单 Key 删除

```text
当前实例删除 L1
-> 删除 Redis
-> 发布 evict 消息
-> 其他实例收到消息后删除各自 L1
```

### 11.2 分组清空

```text
当前实例按 <cache_name>: 清理 L1
-> Redis scan_iter <cache_name>:*
-> 批量删除 Redis Key
-> 发布 clear 消息
-> 其他实例按 <cache_name>: 清理 L1
```

### 11.3 一致性边界

不能保证：

- 数据库写入和缓存删除原子一致
- Pub/Sub 消息一定送达
- 任意瞬间所有实例 L1 都已同步删除

降低风险：

- `local_ttl` 明显小于 Redis `ttl`
- 写操作优先使用 `cache_evict`
- 强一致场景禁用 L1，甚至不使用缓存
- 关键写操作增加日志、重试或异步补偿

## 12. 击穿、穿透、雪崩

### 12.1 缓存击穿

热点 Key 过期后，大量请求同时回源。

处理方式：

```python
@cacheable(
    cache_name="user_detail",
    key="{user_id}",
    ttl=600,
    sync=True,
)
```

`sync=True` 会使用 Redis 分布式锁：

```text
<cache_name>:lock:<raw_key>
```

注意：

- 锁超时时间当前固定为 10 秒
- 回源逻辑耗时不应超过锁超时时间
- 锁只能降低并发回源，不能替代接口限流

### 12.2 缓存穿透

查询不存在的数据，每次都打到数据库。

处理方式：

- 开启 `cache_none=True`
- 参数合法性校验
- 高风险接口增加布隆过滤器

### 12.3 缓存雪崩

大量 Key 同时过期导致集中回源。

当前组件没有内置 TTL 抖动。

处理方式：

- 调用方设置不同业务的 TTL
- 对热点数据做预热
- 在上层接口增加限流
- 后续可在 `CacheManager.put()` 增加 TTL 随机偏移

## 13. 生产使用建议

### 13.1 TTL

建议：

```text
local_ttl < redis_ttl
local_ttl <= redis_ttl / 5
```

示例：

```text
用户详情 Redis TTL: 600s
用户详情 Local TTL: 60s

字典配置 Redis TTL: 1800s
字典配置 Local TTL: 300s

空值缓存 Redis TTL: 60s
空值缓存 Local TTL: 10s
```

### 13.2 更新策略

常见选择：

- 更新后返回完整最新对象：使用 `@cache_put`
- 更新后不确定影响范围：使用 `@cache_evict`
- 更新影响列表页：删除列表缓存分组
- 更新影响多个缓存：使用 `@caching`

优先建议：

```text
写操作优先删缓存，读操作负责回填缓存
```

### 13.3 缓存分组规模

`CacheManager.clear()` 会扫描 `<cache_name>:*`。

如果某个 `cache_name` 下 Key 数量很大，清空成本会升高。

建议：

- 控制单个缓存分组规模
- 列表缓存不要无限维度扩张
- 大规模分组后续改用版本号逻辑失效

### 13.4 监控指标

当前代码未内置指标。生产建议补充：

- L1 命中次数
- L2 命中次数
- 缓存未命中次数
- 回源耗时
- Redis 读写耗时
- 缓存删除次数
- 锁等待耗时
- Pub/Sub 监听异常

## 14. 常见问题

### 14.1 为什么没有全局 `app` 前缀

当前项目约定 `cache_name` 就是一类缓存的统一前缀。

例如：

```text
user_detail:1
user_detail:2
user_detail:lock:1
```

这样清理 `user_detail` 分组时只需要处理 `user_detail:*`。

### 14.2 多个环境共用 Redis 怎么办

如果开发、测试、生产共用同一个 Redis 实例，需要把环境写进 `cache_name`：

```text
dev_user_detail
test_user_detail
prod_user_detail
```

或者在更外层封装 `cache_name` 生成规则。

当前底层组件不再提供统一 `prefix`。

### 14.3 为什么 `clear()` 不直接用 `KEYS`

`KEYS` 在 Key 数量大时会阻塞 Redis。

当前使用 `scan_iter()` 迭代扫描：

```python
async for key in self.redis_service.scan_iter(pattern):
    keys.append(key)
```

扫描仍有成本，但比 `KEYS` 更适合生产环境。

### 14.4 Pub/Sub 丢消息怎么办

Redis Pub/Sub 不持久化消息。实例断线期间可能错过失效通知。

缓解方式：

- 本地缓存 TTL 设置短
- 强一致业务禁用本地缓存
- 后续改成 Redis Stream 或消息队列

### 14.5 什么时候不该使用这套缓存

不建议用于：

- 金额余额
- 库存扣减
- 订单状态强一致读取
- 权限变更后必须立即全局生效的场景
- 写入极高频且读取收益不明显的接口

## 15. 测试建议

建议覆盖以下路径：

1. `@cacheable` 未命中后回源并写缓存
2. `@cacheable` L1 命中
3. `@cacheable` L2 命中并回填 L1
4. `@cache_put` 写回缓存
5. `@cache_evict` 删除单个缓存
6. `@cache_evict(all_entries=True)` 清空缓存分组
7. `cache_none=True` 缓存空值
8. `condition=False` 跳过缓存
9. `unless=True` 跳过写入
10. `sync=True` 并发下只回源一次
11. Pub/Sub 失效消息清理其他实例 L1
12. `LocalCache` TTL 过期和 LRU 淘汰

## 16. 后续可扩展点

优先级较高的扩展：

- TTL 随机抖动
- 缓存指标埋点
- 本地 singleflight
- 缓存 Key 版本号
- Redis Stream 失效同步
- 批量 `mget` + 部分回源

版本号失效示例：

```text
user_list:v1:page_1
user_list:v2:page_1
```

清空分组时只提升版本号，不扫描删除历史 Key。
