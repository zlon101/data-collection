# 轻量级全栈数据采集与分析工作站

本项目是一个基于 Python 和 Vue3 的全栈数据采集与 AI 分析平台，采用 **Monorepo (uv Workspace)** 架构设计，集成网页抓取、移动端自动化、大模型结构化分析及数据可视化功能。

---

## 技术架构

### 核心技术栈

| 模块 | 技术栈 | 说明 |
| --- | --- | --- |
| **包管理** | `uv` | 现代 Python 极速依赖管理，支持 Workspace 模式 |
| **后端** | **FastAPI** | 异步高性能 REST API，集成 Swagger 文档 |
| **前端** | **Vue3 + Vite + ECharts** | 响应式仪表盘，数据大屏展示 |
| **AI 引擎** | **LangChain + Qwen** | 对接 DashScope API，执行摘要、情感分析、实体提取、视觉识别 |
| **网页采集** | **Playwright** | CDP 连接已有 Chrome / 启动新实例，支持懒加载滚动、网络拦截 |
| **移动端采集** | **Airtest / uiautomator2** | Android App 自动化（微信公众号等） |
| **OCR** | **rapidocr_onnxruntime** | 中文文字识别（可选） |
| **存储** | **JSON File System** | 轻量级"文件即数据库"，通过 `common` 模块统一调度 |

---

## 目录结构

```text
├── pyproject.toml              # 根目录：uv Workspace 配置
├── .venv/                      # Workspace 共享 Python 虚拟环境
├── backend/                    # FastAPI 后端模块
│   ├── api/                    # 路由接口 (REST API)
│   └── main.py                 # 后端入口
├── frontend/                   # Vue3 前端模块 (Vite)
│   ├── src/                    # 页面组件与 ECharts 逻辑
│   └── package.json
├── common/                     # 共享工具模块
│   ├── file_manager.py         # 统一的数据读写与 local_data 管理
│   └── ocr_tools.py            # OCR 文字识别 (rapidocr_onnxruntime)
├── ai_agent/                   # AI 分析模块 (LangChain)
│   ├── agent_config.py         # LLM 创建与 Agent 配置 (create_llm)
│   ├── agent_tools.py          # 浏览器 Agent 工具集
│   └── llm_client.py           # 文章结构化分析 (摘要/情感/实体)
├── collection_platform/        # 采集器集合
│   ├── browser_playwright/     # 网页自动化 (workspace member)
│   │   ├── browser/            # 浏览器管理 (BrowserManager, CDP 检测)
│   │   ├── puppeteer/          # 采集工具集
│   │   │   ├── universal_scraper/   # 通用网页爬虫
│   │   │   ├── merged_scraper/      # 列表+详情合并抓取
│   │   │   ├── network_intercept/   # API 网络拦截采集
│   │   │   ├── browser_steps/       # 浏览器步骤执行器
│   │   │   ├── puppeteer_tools.py   # 通用工具函数
│   │   │   └── recruit_capture.py   # 微信招聘页面采集 (慢速滚动+截图)
│   │   ├── examples/           # 示例脚本
│   │   └── scripts/            # CLI 入口 (browser.py, docx2md.py)
│   ├── app_airtest/            # App 自动化 (独立 venv，numpy<2)
│   │   ├── core/               # 设备管理、Poco 辅助
│   │   ├── scrapers/           # 微信 scraper、页面解析、OCR
│   │   └── tests/              # 连接测试
│   ├── app_uiautomator2/       # App UI 自动化 (workspace member)
│   │   ├── lib/                # 爬虫框架
│   │   │   ├── list_page_spider.py          # 列表页流式爬虫
│   │   │   ├── detail_page_spider_universal.py  # 详情页解析
│   │   │   ├── universal_page_parser.py     # 通用页面解析器
│   │   │   └── exceptions.py                # 自定义异常
│   │   └── examples/           # Boss直聘/智联招聘示例
│   └── wx/                     # 微信公众号采集 (workspace member)
│       ├── get_articles.py     # 公众号文章采集
│       └── recruit_analyzer/   # 招聘文章分析
│           ├── analyze.py           # 主流程编排 (采集→OCR→视觉→合并→分析)
│           ├── llm_operations.py    # LLM 视觉提取 + 投递判断
│           └── merge_parser.py      # LLM 智能合并多源内容为 Markdown
├── visualization/              # 数据可视化模块
│   ├── config.py               # 图表配置
│   ├── visualizer.py           # Visualizer 类 (柱状/折线/饼图/热力图/仪表盘)
│   └── examples.py             # 示例
├── local_data/                 # 本地数据存储 (不提交 Git)
│   ├── raw/                    # 采集的原始 JSON 数据
│   ├── analyzed/               # LLM 处理后的结构化结果 (JSON + Markdown)
│   └── screenshots/            # 页面截图 (PNG)
└── .env                        # 环境配置 (API Keys, 浏览器配置等)
```

---

## 核心功能

1. **全渠道采集**：
   - **网页端**：Playwright 模拟浏览器，支持 CDP 连接、懒加载滚动、网络拦截
   - **移动端**：Airtest（独立环境）和 uiautomator2 采集微信公众号、APP 内容
2. **微信招聘文章分析**：
   - 慢速滚动触发图片懒加载 → 全页截图
   - OCR 识别截图文字（可选，rapidocr_onnxruntime）
   - 多模态 LLM（qwen-vl-max）从截图提取结构化信息
   - LLM（qwen-plus）智能合并 HTML + 视觉 + OCR 为结构化 Markdown
   - LLM 投递判断分析（是否建议投递简历）
3. **AI 自动化分析**：
   - 自动触发 LangChain 分析，提取核心实体、情感倾向、摘要
   - 支持 Mock 模式（未配置 API Key 时可演示全流程）
4. **可视化仪表盘**：
   - ECharts 渲染情感分布饼图、核心实体词云/柱状图
   - 文章列表及分析结果实时预览

---

## 快速上手

### 1. 环境安装

```bash
uv sync --all-packages
```

### 2. app_airtest 独立环境

由于 `airtest`/`pocoui` 依赖 `numpy<2.0`，与 workspace 的 `numpy>=2` 冲突，使用独立 venv：

```bash
cd collection_platform/app_airtest
uv venv .venv
source .venv/bin/activate
uv pip install "airtest>=1.3.6" "pocoui>=1.0.94" "numpy<2"
```

### 3. 配置文件

```bash
cp .env.example .env
# 编辑 .env 配置 ALIBABA_API_KEY、ALIBABA_API_URL 等
```

### 4. 启动服务

**后端 (API Server)**：
```bash
uv run uvicorn backend.main:app --reload --port 8000
```

**前端 (Dashboard)**：
```bash
cd frontend && npm install && npm run dev
```

访问 `http://localhost:5173` 查看仪表盘，`http://localhost:8000/docs` 查看 API 文档。

---

## 运行示例

### browser_playwright — 网页采集

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
# 公众号文章采集
uv run --package data-collection-platform python -m wx.get_articles

# 招聘文章完整分析（采集 → OCR → 视觉提取 → Markdown 合并 → 投递判断）
uv run --package data-collection-platform python -m wx.recruit_analyzer.analyze \
    --url "https://mp.weixin.qq.com/s?__biz=..."
```

### app_airtest — 独立环境测试

```bash
collection_platform/app_airtest/.venv/bin/python collection_platform/app_airtest/tests/test_connection.py
```

---

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

- **Workspace 成员**（browser_playwright、app_uiautomator2、wx、backend、ai_agent 等）：使用根目录 `uv sync --all-packages` 安装的 `.venv`
- **app_airtest 独立 venv**：位于 `collection_platform/app_airtest/.venv`，因 `airtest`/`pocoui` 依赖 `numpy<2.0`

### 数据流

1. 采集器 → 原始 JSON 存入 `local_data/raw/`
2. 后端调用 `ai_agent` 进行 LLM 分析 → 结果存入 `local_data/analyzed/`
3. 前端通过后端 API 读取分析结果并可视化

### 数据存储

采用"文件即数据库"设计，`common/file_manager.py` 是唯一的 I/O 入口。新增数据类型时应通过该模块操作，保持数据协议一致。

### Playwright 浏览器模式

`.env` 中的 `BROWSER_MODE` 控制：
- `launch`: 启动新的 Chromium 实例
- `connect`: 连接到已有 Chrome (需先启动 `--remote-debugging-port`)

### Python 类型声明规范

项目要求 Python `>=3.11.8`，所有类型声明**必须使用最新的 Python 3 语法**，禁止使用 `typing` 模块中的旧式别名：

| 场景 | 现代语法 | 旧式语法 |
|------|---------|---------|
| 内置泛型 | `list[str]`, `dict[str, int]` | `List[str]`, `Dict[str, int]` |
| 联合类型 | `str \| None`, `int \| float` | `Optional[str]`, `Union[int, float]` |
| 可调用 | `collections.abc.Callable[[int], str]` | `typing.Callable[[int], str]` |
| 类型别名 | `type UserId = int` (3.12+) | `UserId = int` |

**额外要求**：
- 使用 `collections.abc` 中的协议类型，而非 `typing` 中的版本
- 函数返回值中的 `None` 必须显式声明
- 优先使用 `@dataclass` 而非裸 `dict` 传输数据
