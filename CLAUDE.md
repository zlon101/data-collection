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
| 移动端采集 | Airtest / uiautomator2 |
| 存储 | JSON 文件系统 (local_data/) |

## 目录结构

```
├── pyproject.toml              # uv workspace 根配置
├── backend/                    # FastAPI 后端
│   ├── api/                    # 路由定义
│   └── main.py                 # 应用入口
├── frontend/                   # Vue3 前端
│   ├── src/                    # 组件与 ECharts
│   └── package.json
├── common/                     # 共享工具 (file_manager.py)
├── ai_agent/                   # AI 分析 (LangChain)
├── collection_platform/
│   ├── browser_playwright/     # 网页自动化
│   └── app_airtest/            # App 自动化
├── visualization/              # 数据可视化
└── local_data/                 # 本地 JSON 存储 (不提交 Git)
    ├── raw/                    # 原始采集数据
    └── analyzed/               # AI 处理后的数据
```

## 常用命令

### 环境安装

```bash
uv sync                          # 安装所有 workspace 成员依赖
```

### 启动服务

```bash
# 后端 API 服务
uv run uvicorn backend.main:app --reload --port 8000

# 前端开发服务器
cd frontend && npm install && npm run dev
```

访问 `http://localhost:5173` 查看仪表盘，`http://localhost:8000/docs` 查看 API 文档。

### 运行测试

```bash
# Playwright 采集器测试
uv run pytest collection_platform/browser_playwright/test/

# Airtest 连接测试
uv run pytest collection_platform/app_airtest/tests/
```

### 前端构建

```bash
cd frontend && npm run build     # 生产构建
cd frontend && npm run preview   # 预览构建结果
```

## 架构要点

### 模块化解耦

每个子模块都是独立的 Python 包，通过 `uv sync` 建立的 workspace 符号链接实现跨模块导入。**不要使用 `sys.path.insert`**，直接通过包名导入，如 `import common`、`import ai_agent`。

### 数据流

1. 采集器 (browser_playwright / app_airtest) → 原始 JSON 存入 `local_data/raw/`
2. 后端调用 `ai_agent` 进行 LLM 分析 → 结果存入 `local_data/analyzed/`
3. 前端通过后端 API 读取分析结果并可视化

### 数据存储

采用 "文件即数据库" 设计，`common/file_manager.py` 是唯一的 I/O 入口。新增数据类型时应通过该模块操作，保持数据协议一致。

### 环境配置

所有配置在 `.env` 文件中，包括 LLM API 密钥、浏览器连接模式等。修改配置后需要重启服务。

### Playwright 浏览器模式

`.env` 中的 `BROWSER_MODE` 控制：
- `launch`: 启动新的 Chromium 实例
- `connect`: 连接到已有 Chrome (需先启动 `--remote-debugging-port`)
