# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**编写代码时必须遵守 `docs/开发规范.md` 中的规则**，特别是：
- 文件读写操作必须通过 `common/file_manager.py` 中的方法
- 日志输出必须使用 `common/logger.log()`

## 项目概述

轻量级全栈数据采集与分析工作站，采用 **uv Workspace Monorepo** 架构，集成网页抓取、移动端自动化、LLM 结构化分析及 Vue3 可视化仪表盘。支持通过 API 触发采集任务、AI 分析、Job 管理及数据可视化。

## 技术栈

| 模块 | 技术 |
|------|------|
| 包管理 | uv (workspace 模式) |
| 后端 | FastAPI (异步 REST API) |
| 前端 | Vue3 + Vite + ECharts + Element Plus |
| AI 引擎 | LangChain + Qwen (DashScope) |
| 网页采集 | Playwright (CDP 连接 / Launch) |
| 移动端采集 | Airtest (独立 venv) / uiautomator2 (workspace) |
| OCR | rapidocr_onnxruntime (可选) |
| 存储 | JSON 文件系统 (local_data/) |

## 目录结构

```
├── pyproject.toml              # uv workspace 根配置
├── backend/                    # FastAPI 后端
│   ├── api/
│   │   └── routes.py           # 全部 REST 路由 (数据/Job/采集/配置)
│   ├── database/               # 轻量级文件数据库
│   │   ├── job/                # Job 已读记录 (read_keys.json)
│   │   └── crawler/            # 保存的爬虫配置 (config_*.json)
│   ├── log/                    # 采集任务日志
│   └── main.py                 # 后端入口
├── frontend/                   # Vue3 前端
│   └── src/
│       ├── api/
│       │   └── client.js       # API 请求封装
│       ├── views/
│       │   ├── Crawler.vue     # 采集任务主页
│       │   └── Query.vue       # 数据查询与分析
│       ├── components/
│       │   ├── AppCrawlerForm.vue      # App 采集表单 (入口)
│       │   ├── BossForm.vue            # Boss 直聘专用表单
│       │   ├── ZhilianForm.vue         # 智联招聘专用表单
│       │   ├── BrowserCrawlerForm.vue  # 浏览器采集表单
│       │   ├── ConfigSelector.vue      # 配置选择/保存/删除
│       │   ├── JobFileModal.vue        # Job 文件管理弹窗
│       │   └── LogModal.vue            # 日志查看弹窗
│       ├── App.vue
│       └── main.js
├── common/                     # 共享工具
│   ├── file_manager.py         # 统一文件 I/O
│   ├── logger.py               # 日志系统
│   ├── ocr_tools.py            # OCR 工具
│   └── path_utils.py           # 路径工具
├── ai_agent/                   # AI 分析 (LangChain)
│   ├── agent_config.py         # LLM 客户端配置
│   ├── agent_tools.py          # AI Agent 工具集
│   └── llm_client.py           # 文章结构化分析 (摘要/情感/实体)
├── collection_platform/
│   ├── browser_playwright/     # 网页自动化 (workspace member)
│   │   ├── browser/            # BrowserManager, CDP detector
│   │   ├── puppeteer/          # 采集工具
│   │   │   ├── universal_scraper/   # 通用网页爬虫
│   │   │   ├── merged_scraper/      # 列表+详情合并抓取
│   │   │   ├── network_intercept/   # API 网络拦截
│   │   │   ├── browser_steps/       # 步骤执行器
│   │   │   └── recruit_capture.py   # 招聘页面采集 (慢速滚动+截图)
│   │   ├── launcher.py         # 采集启动器 (供后端调用)
│   │   ├── examples/           # 示例脚本
│   │   └── scripts/            # CLI 入口
│   ├── app_airtest/            # App 自动化 (独立 venv，numpy<2)
│   │   ├── core/               # 设备管理、Poco 辅助
│   │   ├── scrapers/           # 微信 scraper、页面解析、OCR
│   │   └── tests/              # 连接测试
│   ├── app_uiautomator2/       # App UI 自动化 (workspace member)
│   │   ├── lib/                # 爬虫框架 (ListPageSpider, DetailPageSpider)
│   │   ├── launcher.py         # 采集启动器 (供后端调用)
│   │   ├── examples/           # Boss直聘/智联招聘示例
│   │   └── tools/
│   │       └── merge_job_data.py  # Job 数据合并去重
│   └── wx/                     # 微信公众号采集 (workspace member)
│       ├── get_articles.py     # 公众号文章采集
│       └── recruit_analyzer/   # 招聘文章分析
│           ├── analyze.py           # 主流程编排
│           ├── llm_operations.py    # LLM 视觉提取 + 投递判断
│           └── merge_parser.py      # LLM 智能合并多源内容
├── visualization/              # 数据可视化
│   ├── config.py               # 图表配置
│   ├── visualizer.py           # Visualizer 类 (柱状/折线/饼图/热力图/仪表盘)
│   └── examples.py             # 示例
└── local_data/                 # 本地 JSON 存储 (不提交 Git)
    ├── raw/                    # 采集原始数据
    ├── analyzed/               # LLM 分析结果 (JSON + Markdown)
    ├── job/                    # Job 招聘数据
    └── screenshots/            # 页面截图
```

## 后端 API 接口

### 数据管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/files` | 列举数据文件 (支持 source/data_type 过滤) |
| GET | `/api/data/{filename}` | 读取指定 JSON 文件 |
| POST | `/api/analyze` | 触发 AI 分析 (异步后台) |
| GET | `/api/analyze/status/{filename}` | 查询分析任务状态 |
| GET | `/api/summary` | 获取最新分析数据摘要 (情感/实体/时间线) |

### Job 管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/jobs` | 获取招聘数据 (自动排除已读) |
| POST | `/api/job/read` | 标记数据为已读 |
| DELETE | `/api/job/read` | 清空已读记录 |
| GET | `/api/job/files` | 列出 job 目录所有文件 |
| GET | `/api/job/files/{filename}` | 读取 job 文件内容 |
| DELETE | `/api/job/files/{filename}` | 删除 job 文件 |
| POST | `/api/job/merge` | 合并 job 文件并去重 |

### 采集任务
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/collector` | 触发采集 (app_uiautomator2 / browser_playwright) |
| POST | `/api/collector/{task_id}/cancel` | 取消采集任务 |
| GET | `/api/collector/tasks` | 列出所有采集任务 |
| GET | `/api/collector/status/{task_id}` | 查询任务状态 |
| GET | `/api/collector/logs/{task_id}` | 读取任务日志 |

### 配置管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/collector/config` | 保存爬虫配置 |
| GET | `/api/collector/configs` | 列出所有配置 |
| GET | `/api/collector/config/{config_name}` | 加载指定配置 |
| DELETE | `/api/collector/config/{config_name}` | 删除指定配置 |

## 前端页面与组件

### 页面
- **Crawler.vue** — 采集任务主页，支持选择采集类型 (App/浏览器)、填写参数、启动/停止任务、查看日志
- **Query.vue** — 数据查询与分析，支持浏览 raw/analyzed 数据、触发 AI 分析、可视化展示

### 组件
- **AppCrawlerForm.vue** — App 采集表单入口，按平台分发到 BossForm/ZhilianForm
- **BossForm.vue** — Boss 直聘专用表单 (搜索、筛选、黑名单等)
- **ZhilianForm.vue** — 智联招聘专用表单
- **BrowserCrawlerForm.vue** — 浏览器采集表单 (URL、选择器、分页等)
- **ConfigSelector.vue** — 配置的保存/加载/删除
- **JobFileModal.vue** — Job 文件管理 (列表/查看/删除/合并)
- **LogModal.vue** — 实时日志查看

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

# app_airtest 测试（独立 venv，所有命令从项目根执行）
uv run --directory collection_platform/app_airtest python3 tests/test_connection.py
uv run --directory collection_platform/app_airtest python3 -m main
uv run --directory collection_platform/app_airtest python3 -m scrapers.wechat_scraper --account 国资小新 --max 20
```

### 前端构建

```bash
cd frontend && npm run build
```

## 运行约定

**所有命令必须从项目根目录执行**。Workspace 成员通过 `uv run --package` 执行，app_airtest 通过 `uv run --directory` 执行。禁止先 `cd` 到子目录再执行（npm 项目除外）。

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

1. 采集器 → 原始 JSON 存入 `local_data/raw/` 或 `local_data/job/`
2. 后端调用 `ai_agent` 进行 LLM 分析 → 结果存入 `local_data/analyzed/`
3. 前端通过后端 API 读取分析结果并可视化
4. Job 数据支持已读标记、文件管理、合并去重

### 数据采集架构

采集任务通过后端 API 触发，在后台异步执行：
- **app_uiautomator2**: 通过 `launcher.py` 启动，支持 Boss/智联等平台，可在子进程中取消
- **browser_playwright**: 通过 `launcher.py` 启动，支持通用爬虫、列表+详情合并等模式
- 所有采集任务支持 **取消机制** (cancelling 状态标记)
- 采集日志按日期写入 `backend/log/` 目录

### 数据存储

采用 "文件即数据库" 设计，`common/file_manager.py` 是唯一的 I/O 入口。新增数据类型时应通过该模块操作，保持数据协议一致。

**所有文件操作必须通过 `common/file_manager.py`，禁止直接使用 `open()` / `Path.read_text()` / `Path.write_text()`：**
- JSON 读写：`write_json(data, filename, data_type)`（raw/analyzed 目录）或 `write_json_path(data, path)`（任意路径）；对应 `read_json` / `read_json_path`
- 文本读写：`write_text(content, path)` / `read_text(path)`
- 二进制读写：`write_bytes(data, path)` / `read_bytes(path)`
- 目录列举：`list_files(source, data_type)`（raw/analyzed）或 `list_json_files(directory)`（任意目录）
- 所有写入自动创建父目录（`mkdir -p`），读取时文件不存在返回 `None` 而非抛出异常

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
