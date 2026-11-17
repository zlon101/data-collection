# Agent 指南

面向 Cursor / Claude 等 AI Agent 的仓库协作说明。

## 文档索引

| 文档 | 用途 |
|------|------|
| [开发规范.md](./开发规范.md) | 硬性编码规范（I/O、日志） |
| [技术方案.md](./技术方案.md) | **当前架构与核心流程** |
| [需求文档.md](./需求文档.md) | 产品需求（与实现对照） |
| [README.md](../README.md) | 安装、启动、命令 |

根目录 `CLAUDE.md` 含 API 表，若与 [技术方案.md](./技术方案.md) 冲突，以技术方案和代码为准。

## 必守规则（摘要）

完整条文以 [开发规范.md](./开发规范.md) 为准：

1. 文件读写必须通过 `common/file_manager.py`
2. 日志必须使用 `common.logger.log()`
3. 禁止 `sys.path.insert`；按 workspace 包名导入
4. 命令从仓库根目录执行（前端 `npm` 除外）
5. 调百炼使用 `ai_agent.agent_config.create_llm()`，不要用 Crawl4AI LiteLLM

## Cursor Rules

`.cursor/rules/`：

| 文件 | 作用 |
|------|------|
| `project-core.mdc` | 始终生效：架构与硬性约定 |
| `python-standards.mdc` | `*.py` |
| `frontend-vue.mdc` | Vue3 + Ant Design Vue |
| `collector-packages.mdc` | 采集包 |
| `docs-agents.mdc` | 正文在 `docs/`，`AGENTS.md` 只引用 |

## scrape_agent

LangGraph CLI，流程见 [技术方案.md](./技术方案.md) §5.2。

```bash
./scripts/run_chrome.sh   # 先开调试 Chrome 并打开目标页

uv run --package scrape-agent python -m scrape_agent \
  "采集 https://www.jdpta.com/index/apply 网页中「近期报名」（.div_ExamList.com_Box）模块的信息，包含「标题」「报名时间」「状态」"

uv run --package scrape-agent python -m scrape_agent \
  "采集 https://www.jdpta.com/newsList 网页中列表数据，要求采集前2页数据，字段包含「标题」「时间」"

uv run --package scrape-agent python -m scrape_agent \
  "采集 https://www.jdpta.com/newsList 列表及每条对应详情页，列表字段「标题」「时间」，详情补充正文"
```

## 文档维护约定

- 说明性正文只在 `docs/` 更新  
- `AGENTS.md` 只保留链接  
- 架构变更先改 [技术方案.md](./技术方案.md)，再改 README 命令示例  
