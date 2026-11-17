# 轻量级全栈数据采集与分析工作站

Python + Vue3 的采集与分析 Monorepo（**uv Workspace**）：网页 / App 采集、LLM 结构化分析、招聘 Job 查询。架构与流程详见 [docs/技术方案.md](docs/技术方案.md)。

## 使用

- 采集 `https://xxx` 网页中 "近期报名"（`.div_ExamList.com_Box`） 模块的信息，包含 “标题”、“报名时间”、“状态”

- 采集  https://xxx 网页中列表数据，要求采集前2页数据，字段包含「标题」「时间」


## 技术栈

| 模块 | 技术 |
| --- | --- |
| 包管理 | uv workspace |
| 后端 | FastAPI |
| 前端 | Vue3 + Vite + **Ant Design Vue** + ECharts |
| LLM | LangChain `ChatOpenAI` → 阿里云百炼（`create_llm`，默认 qwen-plus） |
| 网页 | Playwright，CDP 连接已有 Chrome |
| 配置 Agent | LangGraph（`scrape_agent`） |
| 移动端 | Airtest（独立 venv）/ uiautomator2 |
| 存储 | `local_data/` JSON，`common/file_manager` |

## 核心流程

1. **调试 Chrome**：`./scripts/run_chrome.sh`（端口读 `.env` 的 `CDP_URL`），打开目标页  
2. **手动采集**：前端「爬虫」填参数 → `POST /api/collector` → `browser_playwright` / App launcher → `local_data/`  
3. **自然语言采集**：`scrape_agent` 解析指令 → 生成选择器 → 试抓确认 → 全量（分页 / 点击进详情）  
4. **查询**：前端「查询」读 `local_data/job`，筛选与已读  

数据流：采集器 → `raw` / `job` →（可选）`ai_agent` → `analyzed`。

## 目录（摘要）

```text
├── backend/                 FastAPI
├── frontend/                爬虫 / 查询 Tab
├── common/                  file_manager、logger
├── ai_agent/                create_llm
├── scrape_agent/            LangGraph CLI
├── collection_platform/
│   ├── browser_playwright/  CDP、UniversalScraper、MergedScraper
│   ├── app_uiautomator2/
│   ├── app_airtest/         独立 .venv
│   └── wx/
├── scripts/run_chrome.sh
└── local_data/              不提交 Git
```

完整说明：[docs/技术方案.md](docs/技术方案.md)。Agent 入口：[AGENTS.md](AGENTS.md)。

## 快速上手

```bash
uv sync --all-packages
cp .env.example .env    # 填写 ALIBABA_API_KEY、ALIBABA_API_URL、CDP_URL
```

启动调试 Chrome（与采集共用实例）：

```bash
./scripts/run_chrome.sh
```

```bash
uv run uvicorn backend.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

前端 `http://localhost:5173`，API `http://localhost:8000/docs`。

app_airtest 因 `numpy<2` 使用独立 venv，见 [docs/技术方案.md](docs/技术方案.md) 与下文示例。

## scrape_agent

Chrome 已开调试端口并打开目标页后：

```bash
uv run --package scrape-agent python -m scrape_agent \
  "采集 https://www.jdpta.com/index/apply 网页中「近期报名」（.div_ExamList.com_Box）模块的信息，包含「标题」「报名时间」「状态」"

uv run --package scrape-agent python -m scrape_agent \
  "采集 https://www.jdpta.com/newsList 网页中列表数据，要求采集前2页数据，字段包含「标题」「时间」"

uv run --package scrape-agent python -m scrape_agent \
  "采集 https://www.jdpta.com/newsList 列表及每条对应详情页，列表字段「标题」「时间」，详情补充正文"
```

终端展示试抓结果后输入 `y` 全量、`n` 重新解析配置。

## 其它示例

```bash
uv run --package browser-playwright python -m browser_playwright.examples.scrape_opened_page_pagination
uv run --package browser-playwright python -m browser_playwright.examples.scrape_list_with_detail

uv run --package app-script python -m app_uiautomator2.examples.boss_universal_example

uv run --package data-collection-platform python -m wx.get_articles

uv run --directory collection_platform/app_airtest python3 tests/test_connection.py
```

## 约定

- 命令在**仓库根**执行（`npm` 除外）  
- I/O 只走 `common/file_manager`，日志只走 `common.logger.log`  
- 禁止 `sys.path.insert`；LLM 用 `ai_agent.create_llm()`  
- 前端 UI 库是 **Ant Design Vue**，不是 Element Plus  
