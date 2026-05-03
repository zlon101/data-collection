# 轻量级全栈数据采集与分析工作站

本项目是一个基于 Python 和 Vue3 的全栈数据采集与 AI 分析平台，采用 **Monorepo (uv Workspace)** 架构设计，集成了网页抓取、移动端自动化、大模型结构化分析及数据可视化功能。

---

## 🚀 技术架构

### 1. 核心技术栈
| 模块 | 技术栈 | 说明 |
| --- | --- | --- |
| **包管理** | `uv` | 现代 Python 极速依赖管理，支持 Workspace 模式 |
| **后端** | **FastAPI** | 异步高性能 REST API，集成 Swagger 文档 |
| **前端** | **Vue3 + Vite + ECharts** | 响应式仪表盘，数据大屏展示 |
| **AI 引擎** | **LangChain** | 对接 Qwen/OpenAI，执行文章摘要、情感分析和实体提取 |
| **数据采集** | **Playwright / Airtest / uiautomator2** | 支持网页、Android App（微信等）的全自动化抓取 |
| **存储** | **JSON File System** | 轻量级"文件即数据库"设计，通过 `common` 模块统一调度 |

---

## 📁 目录结构 (Monorepo)

```text
├── pyproject.toml              # 根目录：uv Workspace 配置
├── .venv/                      # Workspace 共享 Python 虚拟环境
├── backend/                    # FastAPI 后端模块
│   ├── api/                    # 路由接口定义
│   └── main.py                 # 后端入口
├── frontend/                   # Vue3 前端模块 (Vite)
│   ├── src/                    # 页面组件与 ECharts 逻辑
│   └── package.json
├── common/                     # 共享工具模块
│   └── file_manager.py         # 统一的数据读写与 local_data 管理
├── ai_agent/                   # AI 分析模块 (LangChain)
├── collection_platform/        # 采集器集合
│   ├── browser_playwright/     # 网页自动化采集 (workspace member)
│   │   ├── browser_playwright/ # 可导入的 Python 包
│   │   │   ├── browser/        # 浏览器管理 (BrowserManager)
│   │   │   ├── puppeteer/      # 自动化采集工具
│   │   │   └── examples/       # 示例脚本
│   │   └── scripts/            # CLI 入口脚本
│   ├── app_airtest/            # App 自动化采集 (独立 venv，见下方说明)
│   ├── app_uiautomator2/       # App UI 自动化采集 (workspace member)
│   │   └── app_uiautomator2/   # 可导入的 Python 包
│   │       ├── lib/            # 爬虫框架
│   │       └── examples/       # 示例脚本
│   └── wx/                     # 微信公众号采集 (workspace member)
│       └── wx/                 # 可导入的 Python 包
├── visualization/              # 数据可视化模块
├── local_data/                 # 本地数据存储层 (不提交 Git)
│   ├── raw/                    # 采集的原始 JSON 数据
│   └── analyzed/               # LLM 处理后的结构化 JSON 数据
└── .env                        # 环境配置 (API Keys, 浏览器配置等)
```

---

## ✨ 核心功能

1.  **全渠道采集**：
    - **网页端**：利用 Playwright 模拟浏览器行为，绕过反爬机制。
    - **移动端**：基于 Airtest（独立环境）和 uiautomator2 采集微信公众号、APP 内容。
2.  **AI 自动化分析**：
    - 采集完成后自动触发 AI 分析。
    - 提取：核心人物/组织、情感倾向（正/负/中）、100 字摘要。
    - 支持 Mock 模式（未配置 API Key 时可演示全流程）。
3.  **可视化仪表盘**：
    - 展示文章总量统计。
    - ECharts 渲染情感分布饼图。
    - 核心实体词云/柱状图展示。
    - 文章列表及分析结果实时预览。

---

## 🛠️ 快速上手

### 1. 环境准备

```bash
# 安装 workspace 依赖
uv sync --all-packages
```

### 2. app_airtest 独立环境

由于 `airtest`/`pocoui` 依赖 `numpy<2.0`，与 workspace 的 `numpy>=2` 冲突，因此使用独立 venv：

```bash
# 创建独立虚拟环境并安装依赖
cd collection_platform/app_airtest
uv venv .venv
source .venv/bin/activate
uv pip install "airtest>=1.3.6" "pocoui>=1.0.94" "numpy<2"
```

### 3. 配置文件

```bash
cp .env.example .env
# 编辑 .env 配置 ALIBABA_API_KEY
```

### 4. 启动项目

**后端 (API Server)**：
```bash
uv run uvicorn backend.main:app --reload --port 8000
```

**前端 (Dashboard)**：
```bash
cd frontend
npm install
npm run dev
```
访问 `http://localhost:5173` 查看仪表盘。

---

## 📝 运行示例

### browser_playwright — 网页采集

通过 `uv run --package` 执行包内示例：

```bash
# 已打开的页面分页抓取
uv run --package browser-playwright python -m browser_playwright.examples.scrape_opened_page_pagination

# 列表+详情页合并抓取
uv run --package browser-playwright python -m browser_playwright.examples.scrape_list_with_detail

# LangChain 浏览器 Agent
uv run --package browser-playwright python collection_platform/browser_playwright/scripts/browser.py --task "去 Google 搜索"
```

### app_uiautomator2 — App 采集

```bash
uv run --package app-script python -m app_uiautomator2.examples.boss_universal_example
uv run --package app-script python -m app_uiautomator2.examples.zhilian_example
```

### wx — 微信公众号采集

```bash
uv run --package data-collection-platform python -m wx.get_articles
```

### app_airtest — 独立环境测试

```bash
collection_platform/app_airtest/.venv/bin/python collection_platform/app_airtest/tests/test_connection.py
```

---

## 🏗️ 架构要点

### 包结构设计

所有 workspace member 遵循 **目录名 = 包名** 原则：

| workspace member | 可导入包名 | 说明 |
|---|---|---|
| `browser_playwright/` | `browser_playwright` | 内部包含 `browser/`、`puppeteer/`、`examples/` 子包 |
| `app_uiautomator2/` | `app_uiautomator2` | 内部包含 `lib/`、`examples/` 子包 |
| `wx/` | `wx` | 微信公众号采集模块 |
| `ai_agent/` | `ai_agent` | LangChain AI 分析引擎 |
| `common/` | `common` | 共享工具模块 |
| `visualization/` | `visualization` | 数据可视化 |

### 依赖管理

- workspace member 之间的依赖使用 `>=` 范围约束，具体版本由 `uv.lock` 锁定
- 跨模块导入通过 `[tool.uv.sources]` 声明 `{ workspace = true }`
- **禁止使用 `sys.path.insert`**，所有导入通过 uv editable install 解析

### 数据流

1. 采集器 → 原始 JSON 存入 `local_data/raw/`
2. 后端调用 `ai_agent` 进行 LLM 分析 → 结果存入 `local_data/analyzed/`
3. 前端通过后端 API 读取分析结果并可视化

### Playwright 浏览器模式

`.env` 中的 `BROWSER_MODE` 控制：
- `launch`: 启动新的 Chromium 实例
- `connect`: 连接到已有 Chrome (需先启动 `--remote-debugging-port`)
