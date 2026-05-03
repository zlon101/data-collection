# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

轻量级全栈数据采集与分析工作站，采用 **uv Workspace Monorepo** 架构，集成网页抓取、移动端自动化、LLM 结构化分析及 Vue3 可视化仪表盘。

## 技术栈

| 模块 | 技术 |
|------|------|
| 包管理 | uv (workspace 模式) |
| 后端 | FastAPI (异步 REST API) |
| 前端 | Vue3 + Vite + ECharts |
| AI 引擎 | LangChain + Qwen/OpenAI |
| 网页采集 | Playwright |
| 移动端采集 | Airtest (独立 venv) / uiautomator2 (workspace) |
| 存储 | JSON 文件系统 (local_data/) |

## 目录结构

```
├── pyproject.toml              # uv workspace 根配置
├── backend/                    # FastAPI 后端
├── frontend/                   # Vue3 前端
├── common/                     # 共享工具 (file_manager.py)
├── ai_agent/                   # AI 分析 (LangChain)
├── collection_platform/
│   ├── browser_playwright/     # 网页自动化 (属于 workspace)
│   ├── app_airtest/            # App 自动化 (独立 venv，numpy<2)
│   └── app_uiautomator2/       # App UI 自动化 (属于 workspace)
├── visualization/              # 数据可视化
└── local_data/                 # 本地 JSON 存储 (不提交 Git)
```

## 常用命令

### 环境安装

```bash
uv sync                          # 安装 workspace 成员依赖
```

### 启动服务

```bash
# 后端 API 服务
uv run uvicorn backend.main:app --reload --port 8000

# 前端开发服务器
cd frontend && npm install && npm run dev
```

访问 `http://localhost:5173` 查看仪表盘，`http://localhost:8000/docs` 查看 API 文档。

### 运行示例

```bash
# browser_playwright 示例（从根目录直接运行）
uv run python collection_platform/browser_playwright/examples/scrape_opened_page_pagination.py
uv run python collection_platform/browser_playwright/examples/scrape_list_with_detail.py

# app_uiautomator2 示例
uv run python collection_platform/app_uiautomator2/examples/boss_universal_example.py

# app_airtest 测试（使用独立 venv）
collection_platform/app_airtest/.venv/bin/python collection_platform/app_airtest/tests/test_connection.py
```

### 前端构建

```bash
cd frontend && npm run build
```

## 架构要点

### 依赖环境

- **Workspace 成员**（browser_playwright、app_uiautomator2、backend、ai_agent 等）：使用根目录 `uv sync` 安装的 `.venv`。
- **app_airtest 独立 venv**：位于 `collection_platform/app_airtest/.venv`，因 `airtest`/`pocoui` 依赖 `numpy<2.0`，无法与 workspace 的 `numpy>=2` 共存。

### 模块化解耦

Workspace 成员通过 `uv sync` 建立的符号链接实现跨模块导入。**不要使用 `sys.path.insert`**，直接通过包名导入。

`collection_platform/*/examples/` 下的示例文件使用 `sys.path.insert` 以支持从根目录直接 `uv run python` 运行单个文件。

### 数据流

1. 采集器 → 原始 JSON 存入 `local_data/raw/`
2. 后端调用 `ai_agent` 进行 LLM 分析 → 结果存入 `local_data/analyzed/`
3. 前端通过后端 API 读取分析结果并可视化

### 数据存储

采用 "文件即数据库" 设计，`common/file_manager.py` 是唯一的 I/O 入口。新增数据类型时应通过该模块操作，保持数据协议一致。

### 环境配置

所有配置在 `.env` 文件中，包括 LLM API 密钥、浏览器连接模式等。

### Playwright 浏览器模式

`.env` 中的 `BROWSER_MODE` 控制：
- `launch`: 启动新的 Chromium 实例
- `connect`: 连接到已有 Chrome (需先启动 `--remote-debugging-port`)

### Python 类型声明规范

项目要求 Python `>=3.11.8`，所有类型声明**必须使用最新的 Python 3 语法**，禁止使用 `typing` 模块中的旧式别名：

| 场景 | 现代语法 (✅) | 旧式语法 (❌) |
|------|-------------|-------------|
| 内置泛型 | `list[str]`, `dict[str, int]`, `set[int]`, `tuple[int, str]` | `List[str]`, `Dict[str, int]`, `Set[int]`, `Tuple[int, str]` |
| 联合类型 | `str \| None`, `int \| float` | `Optional[str]`, `Union[int, float]` |
| 可调用 | `collections.abc.Callable[[int], str]` | `typing.Callable[[int], str]` |
| 类型别名 | `type UserId = int` (PEP 695, 3.12+) 或 `UserId: TypeAlias = int` | `UserId = int` |
| self 类型 | `Self` (PEP 673) | 字符串前引用 `"MyClass"` |
| 可选参数 | `def foo(x: int \| None = None)` | `def foo(x: Optional[int] = None)` |

**额外要求**：
- 使用 `collections.abc` 中的协议类型（`Callable`, `Iterator`, `Sequence`, `Mapping` 等），而非 `typing` 中的版本
- 函数返回值中的 `None` 必须显式声明：`def foo() -> None`
- 使用 `@override` 装饰器标注覆写方法（PEP 698, 3.12+）
- 优先使用 `@dataclass` 而非裸 `dict` 传输数据
