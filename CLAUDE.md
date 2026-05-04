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
| AI 引擎 | LangChain + Qwen (DashScope) |
| 网页采集 | Playwright (CDP 连接 / Launch) |
| 移动端采集 | Airtest (独立 venv) / uiautomator2 (workspace) |
| OCR | rapidocr_onnxruntime (可选) |
| 存储 | JSON 文件系统 (local_data/) |

## 目录结构

```
├── pyproject.toml              # uv workspace 根配置
├── backend/                    # FastAPI 后端
├── frontend/                   # Vue3 前端
├── common/                     # 共享工具 (file_manager.py, ocr_tools.py)
├── ai_agent/                   # AI 分析 (LangChain)
├── collection_platform/
│   ├── browser_playwright/     # 网页自动化 (workspace member)
│   │   ├── browser/            # BrowserManager, CDP detector
│   │   ├── puppeteer/          # 采集工具
│   │   │   ├── universal_scraper/   # 通用网页爬虫
│   │   │   ├── merged_scraper/      # 列表+详情合并抓取
│   │   │   ├── network_intercept/   # API 网络拦截
│   │   │   ├── browser_steps/       # 步骤执行器
│   │   │   └── recruit_capture.py   # 招聘页面采集 (慢速滚动+截图)
│   │   ├── examples/           # 示例脚本
│   │   └── scripts/            # CLI 入口
│   ├── app_airtest/            # App 自动化 (独立 venv，numpy<2)
│   ├── app_uiautomator2/       # App UI 自动化 (workspace member)
│   │   ├── lib/                # 爬虫框架 (ListPageSpider, DetailPageSpider)
│   │   └── examples/           # 示例脚本
│   └── wx/                     # 微信公众号采集 (workspace member)
│       ├── get_articles.py     # 公众号文章采集
│       └── recruit_analyzer/   # 招聘文章分析 (采集→OCR→视觉→Markdown→投递判断)
├── visualization/              # 数据可视化 (Visualizer 类)
└── local_data/                 # 本地 JSON 存储 (不提交 Git)
    ├── raw/                    # 采集原始数据
    ├── analyzed/               # LLM 分析结果 (JSON + Markdown)
    └── screenshots/            # 页面截图
```

## 常用命令

### 环境安装

```bash
uv sync --all-packages             # 安装所有 workspace 成员依赖
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
# browser_playwright — 通过 --package 执行包内示例
uv run --package browser-playwright python -m browser_playwright.examples.scrape_opened_page_pagination
uv run --package browser-playwright python -m browser_playwright.examples.scrape_list_with_detail

# app_uiautomator2 — 通过 --package 执行包内示例
uv run --package app-script python -m app_uiautomator2.examples.boss_universal_example

# wx — 微信公众号采集
uv run --package data-collection-platform python -m wx.get_articles

# wx — 招聘文章完整分析
uv run --package data-collection-platform python -m wx.recruit_analyzer.analyze \
    --url "https://mp.weixin.qq.com/s?__biz=..."

# app_airtest 测试（使用独立 venv）
collection_platform/app_airtest/.venv/bin/python collection_platform/app_airtest/tests/test_connection.py
```

### 前端构建

```bash
cd frontend && npm run build
```

## 架构要点

### 包结构与导入规则

所有 workspace member 遵循 **目录名 = 包名**，通过 `pyproject.toml` 的 `[tool.setuptools]` + `package-dir` 映射：

| workspace member | 可导入包名 | 导入示例 |
|---|---|---|
| `browser_playwright/` | `browser_playwright` | `from browser_playwright.browser import BrowserManager` |
| `app_uiautomator2/` | `app_uiautomator2` | `from app_uiautomator2.lib import ListPageSpider` |
| `wx/` | `wx` | `from wx.recruit_analyzer.analyze import analyze_url` |
| `ai_agent/` | `ai_agent` | `from ai_agent.agent_config import create_llm` |
| `common/` | `common` | `from common import file_manager` |
| `visualization/` | `visualization` | `from visualization.visualizer import Visualizer` |

Workspace 成员之间的依赖使用 `[tool.uv.sources]` 声明 `{ workspace = true }`，具体版本由 `uv.lock` 锁定。**禁止使用 `sys.path.insert`**。

### 依赖环境

- **Workspace 成员**（browser_playwright、app_uiautomator2、wx、backend、ai_agent 等）：使用根目录 `uv sync --all-packages` 安装的 `.venv`。
- **app_airtest 独立 venv**：位于 `collection_platform/app_airtest/.venv`，因 `airtest`/`pocoui` 依赖 `numpy<2.0`，无法与 workspace 的 `numpy>=2` 共存。

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
