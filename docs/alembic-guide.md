# Alembic 使用指南

> 面向当前 `backend-fastapi` 项目的数据库迁移说明。
> 适用于日常建表、改字段、生成迁移脚本、执行迁移和排查常见问题。

## 1. Alembic 是什么

Alembic 是 SQLAlchemy 官方生态里的数据库迁移工具。

它主要解决两个问题：

- 把 ORM 模型变更转换成数据库结构变更脚本
- 让不同环境的数据库版本保持一致

简单理解：

- `model.py` 里改的是“目标结构”
- `alembic revision --autogenerate` 生成的是“变更脚本”
- `alembic upgrade` 执行的是“数据库升级”

## 2. 当前项目里的迁移约定

本项目已经做了以下约定：

- Alembic 配置文件是 [`alembic.ini`](../alembic.ini)
- 迁移环境文件是 [`alembic/env.py`](../alembic/env.py)
- 迁移脚本目录是 `alembic/versions`
- `env.py` 会自动扫描 `core`、`demo` 目录下所有 `model.py`
- 只要模型继承项目统一的 [`config.database.Base`](../config/database.py)，就会被纳入迁移元数据
- 数据库连接串运行时从 `settings.DATABASE_URL` 注入，不依赖 `alembic.ini` 里的占位值

这意味着：

- 新增 `core/order/model.py` 这类文件后，通常不需要再手动修改 `env.py`
- 只要模型被定义在 `model.py` 中，Alembic 自动迁移时就能感知到

## 3. 使用前提

执行迁移前，至少确认以下几点：

1. 已创建虚拟环境并安装依赖
2. 当前环境变量或 `env/*.env` 中的数据库配置正确
3. 目标数据库实例可连接
4. 你的模型类已经继承统一的 `Base`

常见启动方式：

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv sync
```

## 4. 常用命令

### 4.1 生成迁移脚本

```powershell
alembic revision --autogenerate -m "init"
```

适用场景：

- 新增表
- 删除表
- 新增字段
- 删除字段
- 修改字段类型
- 修改部分默认值

注意：

- 自动生成不是绝对可靠，生成后必须人工检查脚本
- 重命名表、重命名字段这类变更，Alembic 往往无法正确识别，通常会被识别成“删旧建新”

### 4.2 手动创建空迁移脚本

```powershell
alembic revision -m "manual fix"
```

适用场景：

- 需要写自定义 SQL
- 数据修复
- 字段重命名
- 表名变更
- 复杂索引调整

### 4.3 升级到最新版本

```powershell
alembic upgrade head
```

这是最常用的升级命令，表示执行到最新迁移版本。

### 4.4 升级到指定版本

```powershell
alembic upgrade <revision_id>
```

示例：

```powershell
alembic upgrade a1b2c3d4e5f6
```

### 4.5 回滚一个版本

```powershell
alembic downgrade -1
```

### 4.6 回滚到指定版本

```powershell
alembic downgrade <revision_id>
```

### 4.7 查看当前数据库版本

```powershell
alembic current
```

### 4.8 查看迁移历史

```powershell
alembic history
```

如果想看更详细的分支和版本信息：

```powershell
alembic history --verbose
```

### 4.9 查看有哪些升级步骤未执行

```powershell
alembic heads
alembic branches
```

适用场景：

- 排查多分支迁移
- 确认是否出现多个 head

## 5. 推荐操作流程

### 5.1 新增模型或修改表结构

1. 先修改 `model.py`
2. 确认模型继承自统一的 `Base`
3. 执行自动生成命令
4. 人工检查生成的迁移脚本
5. 执行 `alembic upgrade head`
6. 本地验证表结构和业务功能

### 5.2 典型流程示例

```powershell
alembic revision --autogenerate -m "add user table"
alembic upgrade head
```

### 5.3 团队协作流程建议

1. 拉取最新代码
2. 先执行 `alembic upgrade head`
3. 再开始开发新的模型变更
4. 提交代码时同时提交迁移脚本
5. 合并分支前检查是否产生多个 head

## 6. 自动生成时重点检查什么

生成迁移脚本后，至少检查以下内容：

- `op.create_table(...)` 是否符合预期
- `op.add_column(...)` / `op.drop_column(...)` 是否正确
- 字段类型是否正确
- 是否误删了原有表或字段
- 索引、唯一约束、检查约束是否完整
- `downgrade()` 是否可回滚

特别注意：

- 字段重命名通常要手写
- 表重命名通常要手写
- 数据迁移逻辑通常要手写
- 大表结构变更要评估锁表和执行时长

## 7. 当前项目下的模型发现规则

`env.py` 现在会自动扫描并导入以下目录中的 `model.py`：

- `core`
- `demo`

例如下面这些文件会被自动加载：

- `core/user/model.py`
- `core/order/model.py`
- `demo/custom/model.py`

如果后续你把模型放到了别的目录，比如：

- `plugins`
- `modules`
- `apps`

那么需要同步调整 [`alembic/env.py`](../alembic/env.py) 里的扫描目录列表。

## 8. 常见问题

### 8.1 执行 `revision --autogenerate` 但生成空脚本

常见原因：

- 模型没有继承统一的 `Base`
- 模型文件不在 `core` / `demo` 的 `model.py` 中
- 模型模块没有被 Alembic 加载
- 实际没有结构变化

排查方向：

- 检查模型基类
- 检查文件命名是否为 `model.py`
- 检查是否改的是 schema 而不是 ORM model

### 8.2 自动生成把“重命名字段”识别成“删旧建新”

这是 Alembic 的常见行为。

处理方式：

- 不要直接相信自动结果
- 改成手写迁移脚本
- 必要时使用 `op.alter_column(...)`

### 8.3 Windows 下 `alembic.ini` 中文注释报编码错误

在某些 Windows 环境下，`configparser` 会按 `gbk` 读取 `.ini` 文件。
如果 `alembic.ini` 使用 UTF-8 中文注释，可能出现 `UnicodeDecodeError`。

处理方式：

- `alembic.ini` 尽量只保留 ASCII 注释
- 中文说明放到 `.py` 文件或 `docs` 文档里

### 8.4 配置了异步数据库 URL，Alembic 还能用吗

可以，但 `env.py` 需要按异步引擎方式配置。

本项目已经处理好了这一点：

- 使用异步引擎创建连接
- 通过 `run_sync` 执行 Alembic 迁移上下文

### 8.5 执行迁移时报模型导入错误

这通常不是 Alembic 本身的问题，而是项目导入链的问题。

例如：

- 路由模块里有错误导入
- Pydantic schema 写法错误
- FastAPI 参数声明错误
- 配置对象属性名不一致

处理思路：

1. 先根据堆栈定位出错模块
2. 修复导入链上的真实错误
3. 再重新执行 Alembic 命令

## 9. 建议保留的日常命令清单

```powershell
alembic current
alembic history
alembic revision --autogenerate -m "your message"
alembic revision -m "manual migration"
alembic upgrade head
alembic downgrade -1
```

## 10. 一套最实用的日常模板

开发时最常见的一套流程：

```powershell
alembic current
alembic revision --autogenerate -m "add xxx"
alembic upgrade head
```

上线前建议至少再做一次：

```powershell
alembic history --verbose
alembic current
```

## 11. 结论

在这个项目里，Alembic 的正确使用方式可以概括成三句话：

1. 先改 ORM 模型，再生成迁移脚本
2. 自动生成后必须人工检查
3. 保证迁移脚本和业务代码一起提交
