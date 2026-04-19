# 使用 uv 管理 Python / FastAPI 项目

这个项目使用 `uv` 管理 Python 版本、虚拟环境和依赖。

如果你平时用的是 `pip + venv + requirements.txt`，可以把 `uv` 理解成更快、更统一的一套工具。

推荐优先使用：

- `uv init` 创建项目
- `uv venv` 创建虚拟环境
- `uv add` / `uv remove` 管理依赖
- `uv sync` 安装或同步依赖
- `uv run` 运行脚本

`uv pip` 也能用，但它更适合兼容传统 `pip` 工作流。

## 1. 安装 uv

### Windows

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

说明：

- `-ExecutionPolicy ByPass`：临时绕过 PowerShell 执行策略
- `irm`：`Invoke-RestMethod`
- `iex`：`Invoke-Expression`

安装完成后检查版本：

```powershell
uv --version
```

## 2. 使用 uv 创建新项目

### 创建普通 Python 项目

```powershell
uv init my-project
cd my-project
```

### 创建 FastAPI 项目

```powershell
uv init backend-fastapi
cd backend-fastapi
uv add fastapi "uvicorn[standard]"
```

执行 `uv init` 后，通常会生成：

- `pyproject.toml`
- `.python-version`
- 示例代码文件

## 3. 创建和激活虚拟环境

### 创建默认虚拟环境

```powershell
uv venv
```

默认会在当前目录创建 `.venv`。

### 指定 Python 版本创建虚拟环境

```powershell
uv venv --python 3.10
```

### 激活虚拟环境

PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

CMD：

```cmd
.\.venv\Scripts\activate.bat
```

Git Bash：

```bash
source .venv/Scripts/activate
```

退出虚拟环境：

```powershell
deactivate
```

## 4. 推荐工作流：使用 uv 管理项目依赖

这是 `uv` 最推荐的方式，依赖会写入 `pyproject.toml`，并同步到锁文件。

### 安装依赖

```powershell
uv add requests
uv add fastapi
uv add "uvicorn[standard]"
```

### 安装开发依赖

```powershell
uv add --dev pytest
uv add --dev ruff
```

### 删除依赖

```powershell
uv remove requests
```

### 同步依赖到当前环境

```powershell
uv sync
```

适合以下场景：

- 新机器拉代码后安装依赖
- `pyproject.toml` 更新后重新同步环境
- 想确保虚拟环境和锁文件一致

### 刷新依赖 / 更新依赖

更新锁文件：

```powershell
uv lock
```

升级某个依赖：

```powershell
uv add --upgrade-package requests
```

升级全部可升级依赖并刷新锁文件：

```powershell
uv lock --upgrade
```

更新后再同步到虚拟环境：

```powershell
uv sync
```

## 5. 使用 uv pip 兼容传统 pip 工作流

如果你更习惯 `pip install`、`pip list`、`pip freeze` 这类命令，可以使用 `uv pip`。

注意：

- 一般先创建并激活虚拟环境再执行 `uv pip ...`
- `uv pip` 更像是 `pip` 的高速替代
- 做项目依赖管理时，仍然优先推荐 `uv add` / `uv sync`

### 安装依赖

```powershell
uv pip install requests
uv pip install fastapi uvicorn
```

### 从 requirements.txt 安装依赖

```powershell
uv pip install -r requirements.txt
```

### 卸载依赖

```powershell
uv pip uninstall requests
```

### 查看已安装依赖

```powershell
uv pip list
```

### 查看某个包信息

```powershell
uv pip show requests
```

### 导出当前环境依赖

```powershell
uv pip freeze
```

导出到文件：

```powershell
uv pip freeze > requirements.txt
```

## 6. 查看项目依赖

### 查看 `pyproject.toml` 中声明的依赖

直接查看项目配置文件：

```powershell
Get-Content .\pyproject.toml
```

### 查看当前环境已安装的依赖

```powershell
uv pip list
```

### 查看依赖树

```powershell
uv tree
```

这个命令适合排查：

- 某个包是被谁间接安装的
- 版本冲突来自哪个依赖链

## 7. 常用运行命令

### 运行 Python 脚本

```powershell
uv run python main.py
```

通常不需要手动激活虚拟环境，`uv run` 会自动使用项目环境。

### 运行 FastAPI

```powershell
uv run uvicorn main:app --reload
```

### 运行测试

```powershell
uv run pytest
```

### 运行格式化或检查工具

```powershell
uv run ruff check .
uv run ruff format .
```

## 8. requirements.txt 和 pyproject.toml 的区别

### 推荐方式

优先使用：

- `pyproject.toml`
- `uv.lock`

这是 `uv` 的标准项目管理方式，更适合团队协作和版本锁定。

### 兼容方式

如果项目还在使用 `requirements.txt`，也可以继续配合 `uv pip`：

```powershell
uv pip install -r requirements.txt
uv pip freeze > requirements.txt
```

简单理解：

- `pyproject.toml`：声明项目依赖
- `uv.lock`：锁定实际安装版本
- `requirements.txt`：传统依赖清单，兼容旧项目

## 9. 常用命令速查

| 场景 | 命令 |
| :--- | :--- |
| 安装 uv | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` |
| 创建项目 | `uv init my-project` |
| 创建虚拟环境 | `uv venv` |
| 指定 Python 创建环境 | `uv venv --python 3.10` |
| 激活环境（PowerShell） | `.\.venv\Scripts\Activate.ps1` |
| 安装项目依赖 | `uv add requests` |
| 安装开发依赖 | `uv add --dev pytest` |
| 删除依赖 | `uv remove requests` |
| 同步依赖 | `uv sync` |
| 更新锁文件 | `uv lock` |
| 升级全部依赖 | `uv lock --upgrade` |
| 安装 requirements.txt | `uv pip install -r requirements.txt` |
| 查看已安装依赖 | `uv pip list` |
| 查看单个包信息 | `uv pip show requests` |
| 导出依赖 | `uv pip freeze > requirements.txt` |
| 查看依赖树 | `uv tree` |
| 运行脚本 | `uv run python main.py` |
| 启动 FastAPI | `uv run uvicorn main:app --reload` |
| 运行测试 | `uv run pytest` |

## 10. 这个项目的基本使用方式

如果你是第一次拉取这个项目，推荐按下面执行：

```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv sync
uv run python main.py
```

如果后面新增了依赖：

```powershell
uv add requests
uv sync
```

如果只是想查看当前装了哪些包：

```powershell
uv pip list
uv tree
```
