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
│   ├── browser_playwright/     # 网页自动化采集 (属于 workspace)
│   ├── app_airtest/            # App 自动化采集 (独立 venv，见下方说明)
│   └── app_uiautomator2/       # App UI 自动化采集 (属于 workspace)
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
# 安装 workspace 依赖（browser_playwright, app_uiautomator2, backend, ai_agent 等）
uv sync
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

### 运行 browser_playwright 示例

从项目根目录直接运行：
```bash
uv run python collection_platform/browser_playwright/examples/scrape_opened_page_pagination.py
uv run python collection_platform/browser_playwright/examples/scrape_list_with_detail.py
```

### 运行 app_airtest 测试

使用独立 venv 中的 Python：
```bash
collection_platform/app_airtest/.venv/bin/python collection_platform/app_airtest/tests/test_connection.py
```

### 运行 app_uiautomator2 示例

从项目根目录直接运行：
```bash
uv run python collection_platform/app_uiautomator2/examples/boss_universal_example.py
uv run python collection_platform/app_uiautomator2/examples/zhilian_example.py
```

---

## 🏗️ 架构优势

- **模块化解耦**：每个模块都是独立的 Python 包，支持跨项目导入。
- **路径无关导入**：不再使用 `sys.path.insert`，直接通过包名 `import backend` 或 `import ai_agent`。
- **高性能**：所有 Python 代码运行在同一个由 `uv` 管理的优化虚拟环境中。
- **可扩展性**：轻松添加新的采集器或分析模型，只需在 `common` 模块中保持数据协议一致。
