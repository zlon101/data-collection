# Agent 指南

面向 Cursor / Claude 等 AI Agent 的仓库协作说明。

## 文档索引

| 文档 | 用途 |
|------|------|
| [开发规范.md](./开发规范.md) | 硬性编码规范（I/O、日志） |
| [技术方案.md](./技术方案.md) | 技术架构与方案 |
| [需求文档.md](./需求文档.md) | 产品需求 |
| `CLAUDE.md`（仓库根） | 详细架构、API、目录与运行约定 |
| `README.md`（仓库根） | 人类可读的项目说明与启动方式 |

## 必守规则（摘要）

完整条文以 [开发规范.md](./开发规范.md) 为准：

1. 文件读写必须通过 `common/file_manager.py`
2. 日志必须使用 `common.logger.log()`
3. 禁止 `sys.path.insert`；按 workspace 包名导入
4. 命令从仓库根目录执行（前端 `npm` 除外）

## Cursor Rules

规则文件在 `.cursor/rules/`（由项目维护，与本文档配合使用）：

| 文件 | 作用 |
|------|------|
| `project-core.mdc` | 始终生效：架构与硬性约定 |
| `python-standards.mdc` | `*.py`：类型与 I/O 示例 |
| `frontend-vue.mdc` | `frontend/**`：Vue3 + Ant Design Vue |
| `collector-packages.mdc` | `collection_platform/**`：采集包与 launcher |
| `docs-agents.mdc` | 文档维护约定：正文在 `docs/`，`AGENTS.md` 只引用 |

## 文档维护约定

- **正文与细则**一律写在 `docs/` 下维护与更新
- 根目录 `AGENTS.md` **只保留指向 `docs/` 的引用**，不堆叠完整正文
- 新增约定时：先改/增 `docs/`，再视需要在 `AGENTS.md` 增加一条链接
