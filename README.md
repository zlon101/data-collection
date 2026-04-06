# 轻量级全栈数据采集与分析工作站 - 技术架构方案

## 一、 系统架构设计

系统采用**前后端分离**架构，以 Python 后端为调度核心，通过本地文件系统（JSON）作为数据总线，串联采集、分析与展示三大模块。


### 2. 核心模块划分
1. **web前台**：与用户进行交互，修改配置文件，触发数据采集，展示数据等
2. **采集引擎 (Collectors)**：对接各类底层的自动化库，执行具体的 UI 交互和页面解析。
3. **AI 分析引擎 (Analyzer)**：读取原始 JSON，利用 LangChain 组装 Prompt，将非结构化文本转化为标准 JSON 字段。
4. **统一文件总线 (File System)**：作为轻量级的“数据库”，定义明确的文件命名规范（如 `原始数据` 和 `分析后数据` 隔离存放）。

---

## 二、 技术栈选型

| 模块 | 技术栈 | 选择理由 |
| --- | --- | --- |
| **基础环境** | macOS (M1), Python 3.11.8, `uv` | `uv` 是极速的 Python 依赖/环境管理器，M1 芯片性能强劲，完美适配本地开发。 |
| **后端框架** | **FastAPI** | 极简、性能极高、原生支持异步（非常适合 I/O 密集型的网络爬虫和 API 调用），自带 Swagger 文档。 |
| **Web 采集** | **Playwright** | 微软开源的现代化浏览器自动化工具，原生支持异步，绕过普通反爬机制能力强于 Requests。 |
| **APP 采集** | **uiautomator2** | 针对普通 App，基于 Android UIA 框架，速度快，适合结构化控件抓取。 |
| **微信采集** | **Airtest** | 针对微信等难以解析 UI 树的应用，基于图像识别进行操作和截图 OCR，兼容性好。 |
| **AI 框架** | **LangChain** | 封装了各种外部大模型（OpenAI/智谱等）的调用接口，其 `OutputParsers` 极其适合强制 LLM 输出 JSON。 |
| **前端框架** | **Vue3 + Vite + ECharts** | Vite 提供极速冷启动，ECharts 非常适合渲染基于 JSON 文件的统计图表。 |

---

## 三、 代码目录结构规划

推荐将前后端代码放在同一个大仓（Monorepo）下，方便一个人全栈开发。使用 `uv` 管理后端的虚拟环境。

```text
data_platform_workspace/
├── frontend/                     # Web 前端目录 (Vite + Vue3)
│   ├── package.json
│   ├── src/
│   │   ├── api/                  # 使用 fetch 调用后端接口
│   │   ├── components/           # ECharts 图表组件、通用组件
│   │   ├── views/                # 页面视图 (采集控制台、数据大屏等)
│   │   └── App.vue
├── backend/                      # Python FastAPI 后端目录
│   ├── pyproject.toml            # uv 项目依赖配置
│   ├── uv.lock                   # uv 锁定文件
│   ├── main.py                   # FastAPI 入口文件
│   ├── api/
│   │   └── routes.py             # 提供给前端调用的 REST 接口
│   │
│   └── utils/
│       └── file_manager.py       # JSON 文件的读写、重命名、归档等工具类
│
└── collection_platform/          # 数据采集模块
│   ├── app_airtest/              # 基于 airtest 采集app（微信公众号）上的数据
│   │
│   └── app_uiautomator2/         # 基于 uiautomator2 采集app上的数据
│   │
│   └── browser_playwright/       # 基于 playwright 采集浏览器网页上的数据
│
└── ai_agent/                     # 基于 LangChain 的 LLM 模块
│
└── local_data/                   # 核心：本地数据存储层 (不提交到Git)
    ├── raw/                      # 爬虫抓取的原始数据
    │   ├── web_20260403.json
    │   └── wechat_20260403.json
    └── analyzed/                 # 经过 LLM 处理并提取好的结构化数据
        ├── web_20260403_done.json
        └── wechat_20260403_done.json
```
---

## 四、 核心业务数据流转

1. **触发 (Trigger):** 页面上点击按钮触发采集
2. **采集 (Collect):** 不同的采集平台使用不同的方式
   - 微信公众号：代码位于 collection_platform/app_airtest
     1. Airtest 脚本通过 ADB 连接到 Mac M1 上的 Android 真机。
     2. 手动化打开微信 -> 进入公众号 -> 利用 Airtest 截图/读取文本。
     3. `utils/file_manager.py` 将获取的文本列表存储为 `local_data/raw/wechat_公众号A_20260403.json`。
   - 网页： 代码位于 collection_platform/browser_playwright
   - 其他app: 代码位于 collection_platform/app_uiautomator2
3. **分析 (Analyze):**
   - 采集完成后，回调触发 `analyzer/llm_client.py`。
   - LangChain 读取刚才的 raw JSON，注入 Prompt（例如：*“请分析以下文章，提取：1.核心人物 2.情感倾向(正/负/中) 3.摘要。请必须以严格的 JSON 格式返回”*）。
   - 解析 LLM 结果，验证 JSON 格式无误后，存入 `local_data/analyzed/wechat_公众号A_20260403_done.json`。
4. **展示 (Visualize):**
   - 用户在浏览器打开 Vue 页面。
   - 前端向 FastAPI 发起请求 `GET /api/data?source=wechat`。
   - FastAPI 读取 `analyzed` 目录下的 JSON，返回给前端。
   - 前端 Vue3 组件使用 ECharts 渲染“情感倾向饼图”和“核心人物词云”。
