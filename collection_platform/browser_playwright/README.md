# 🤖 LangChain Browser Agent

一个模块化的浏览器自动化 Agent，基于 LangChain 和 Playwright 构建。

## ✨ 特性

- 🎯 **智能代理**: 基于 LLM 的自主决策和任务执行
- 🌐 **浏览器控制**: 完整的网页导航、点击、提取和截图能力
- 🔌 **灵活连接**: 支持启动新浏览器或连接现有 Chrome
- 🎯 **标签页查找**: 连接到指定 URL 的已打开标签页，直接操作
- 🤖 **步骤执行器**: 按步骤自动化操作浏览器，支持复杂工作流
- 🧩 **模块化架构**: 清晰的代码组织，易于扩展和维护
- 🔧 **可配置**: 通过环境变量或代码轻松配置
- 📊 **表格抓取**: 自动识别和抓取分页表格数据
- 🎨 **通用抓取器**: 支持自定义字段、分页、延迟配置的通用数据采集工具

## 📁 项目结构

```
agent-python/
├── .env.example                # 环境变量示例
├── .gitignore                  # Git 忽略配置
├── README.md                   # 本文件
├── requirements.txt            # 依赖包
├── TODO.md                     # TODO
├── examples/                   # 示例代码
│   ├── brower.py               # 浏览器示例
│   ├── browser_step_executor.py  # 浏览器步骤执行器示例
│   ├── existing_tab_scraper.py # 现有标签页抓取器示例
│   └── universal_scraper_agent.py # 通用抓取器Agent示例
├── lib/                        # 核心库
│   ├── main.py                 # 主入口
│   ├── browser/                # 浏览器管理模块
│   │   ├── __init__.py
│   │   ├── manager.py          # 浏览器管理器
│   │   └── detector.py         # CDP 检测器
│   ├── custom_agent/           # 自定义 Agent 模块
│   │   ├── __init__.py
│   │   ├── agent_config.py     # Agent 配置
│   │   └── agent_tools.py      # 自定义工具
│   ├── puppeteer/              # Puppeteer 工具模块
│   │   ├── __init__.py
│   │   ├── puppeteer_tools.py  # Playwright 工具包装
│   │   ├── README.md           # Puppeteer README
│   │   ├── browser_steps/      # 浏览器步骤模块
│   │   │   ├── __init__.py
│   │   │   └── step_executor.py # 步骤执行器
│   │   │   ├── __init__.py
│   │   │   ├── table_tools.py   # 表格工具
│   │   │   └── example.py       # 表格抓取示例
│   │   └── universal_scraper/  # 通用数据抓取模块
│   │       ├── __init__.py
│   │       ├── scraper.py       # 通用抓取核心
│   │       ├── tools.py         # LangChain工具集成
│   │       └── example.py       # 完整示例
│   └── visualization/          # 任务可视化模块
│       ├── __init__.py
│       ├── ARCHITECTURE.md     # 架构文档
│       ├── config.py           # 配置
│       ├── examples.py         # 示例
│       └── visualizer.py       # 可视化工具
├── scripts/                    # 脚本文件
│   ├── brower.py               # 浏览器脚本
│   └── scrape_table.py         # 表格抓取脚本
├── shell/                      # Shell 脚本
│   └── run_chrome.sh           # Chrome 启动脚本
└── test/                       # 测试文件
    ├── scrape_opened_page_pagination.py # 打开页面分页抓取测试
    ├── task_visualization.py   # 任务可视化测试
    ├── test_step_executor_segment.py # 步骤执行器分段测试
    ├── test_step_executor.py   # 步骤执行器测试
    ├── test_universal_scraper_opened.py # 打开页面通用抓取器测试
    └── test_universal_scraper.py # 通用抓取器测试
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
# 临时使用清华源安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Playwright 浏览器
playwright install chromium
```

> 类似于将依赖写入 package.json
pip freeze > requirements.txt

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

关键配置：
- `ALIBABA_API_KEY`: 阿里云 API 密钥
- `ALIBABA_API_URL`: API 端点
- `BROWSER_MODE`: 浏览器模式 (`launch` 或 `connect`)

### 3. 运行

#### example

```shell
# 1. 测试启动新浏览器
python run.py --mode launch --task "Go to google.com"

# 2. 测试连接已有 Chrome（需先启动 Chrome）
chrome.exe --remote-debugging-port=9222
python run.py --mode connect --task "Get page info"

# 3. 测试交互模式
python run.py --interactive

# 4. 运行示例
python lib/examples.py
```

#### 方式 1: 启动新浏览器

```bash
# 设置环境变量
export BROWSER_MODE=launch

# 运行
python lib/main.py
```

#### 方式 2: 连接已有 Chrome

```bash
# 1. 启动 Chrome（开启远程调试）
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"

# 2. 设置环境变量
export BROWSER_MODE=connect

# 3. 运行
python lib/main.py
```

## 📚 核心模块说明

### BrowserManager

浏览器生命周期管理器，支持两种模式：

```python
from browser import BrowserManager

# 模式 1: 启动新浏览器
async with BrowserManager(mode="launch", headless=False) as bm:
    browser = bm.get_browser()
    # ... 使用浏览器

# 模式 2: 连接已有 Chrome
async with BrowserManager(mode="connect") as bm:
    browser = bm.get_browser()
    # ... 使用浏览器
```

**特性:**
- ✅ 自动 CDP 端口检测
- ✅ 上下文管理器支持
- ✅ 优雅的资源清理
- ✅ 详细的状态信息

### Agent Config

简化 Agent 创建和配置：

```python
from agent_config import create_custom_agent

agent = create_custom_agent(
    tools=tools,
    model="qwen-plus",
    temperature=0.1
)
```

### CDP Detector

自动检测可用的 Chrome 调试端口：

```python
from browser.detector import find_chrome_cdp_url, get_chrome_pages

# 查找 Chrome
cdp_url = await find_chrome_cdp_url()

# 获取所有打开的页面
pages = await get_chrome_pages(cdp_url)
```

## 🎮 使用模式

### 单次执行模式（默认）

```bash
export RUN_MODE=single
python lib/main.py
```

执行一个预定义任务后退出。

### 交互模式

```bash
export RUN_MODE=interactive
python lib/main.py
```

持续接收用户输入，适合调试和实验。

## 💡 使用示例

### 浏览器控制示例

查看 `examples/brower.py` 了解更多用法：

```bash
python examples/brower.py
```

包含示例：
1. 启动新浏览器
2. 连接已有 Chrome
3. 自定义 CDP URL
4. 多任务执行
5. 获取浏览器信息
6. 错误处理
7. 使用自定义工具

### 通用数据抓取示例（新增⭐）

**快速测试**：
```bash
python test_universal_scraper.py
```

**完整示例**：
```bash
python lib/puppeteer/universal_scraper/example.py
```

**Agent集成**：
```bash
python examples/universal_scraper_agent.py
```

**示例：抓取SegmentFault文章列表**
```python
from browser import BrowserManager
from puppeteer import UniversalScraper, create_scraper_config

async def main():
    async with BrowserManager(mode="launch") as bm:
        page = await bm.get_or_create_page()
        
        config = create_scraper_config(
            url="https://segmentfault.com/",
            fields={
                "标题": "h3 a.text-body",
                "投票数量": ".num-card .font-size-16",
                "阅读数量": ".num-card.text-secondary .font-size-16"
            },
            container_selector=".list-group-item",
            next_button_selector="a.page-link[rel='next']",
            delay=5.0,
            max_pages=2
        )
        
        scraper = UniversalScraper(page, config)
        data = await scraper.scrape()
        scraper.save_to_json("output.json")
```

**详细文档**：
- 快速开始: `docs/universal_scraper_readme.md`
- 完整指南: `docs/universal_scraper_guide.md`

## 🔧 高级配置

### 自定义工具

```python
from langchain_core.tools import tool

@tool
def my_custom_tool(input: str) -> str:
    """Tool description"""
    return f"Processed: {input}"

# 添加到工具列表
tools = browser_tools + [my_custom_tool]
agent = create_custom_agent(tools=tools)
```

### 自定义 System Prompt

```python
custom_prompt = """
You are a specialized web scraper.
Focus on extracting structured data.
"""

agent = create_custom_agent(
    tools=tools,
    system_prompt=custom_prompt
)
```

### 远程 Chrome 连接

```python
# 连接到局域网内的 Chrome
async with BrowserManager(
    mode="connect",
    cdp_url="http://192.168.1.100:9222"
) as bm:
    # ...
```

## 📝 环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BROWSER_MODE` | 浏览器模式 | `connect` |
| `HEADLESS` | 无头模式 | `false` |
| `CDP_URL` | CDP 地址 | `None`（自动检测） |
| `AGENT_MODEL` | 模型名称 | `qwen-plus` |
| `AGENT_TEMPERATURE` | 温度参数 | `0.1` |
| `RUN_MODE` | 运行模式 | `single` |

## 🐛 常见问题

### Q: 连接 Chrome 失败？

**A:** 确保：
1. Chrome 已启动并开启远程调试
2. 端口正确（默认 9222）
3. 没有防火墙阻止连接

### Q: "Target closed" 错误？

**A:** 页面可能已关闭，确保在操作前页面存在。

### Q: 如何保留登录状态？

**A:** 使用 `connect` 模式连接到你正常使用的 Chrome（需要先关闭所有 Chrome 窗口）。

## 🆕 最新功能

### 🎯 标签页查找与连接（新增⭐）

连接到已打开的指定 URL 标签页，直接在上面操作，无需重新加载。

**核心功能**：
- ✅ 查找已打开的标签页（支持部分/精确匹配）
- ✅ 列出所有打开的页面信息
- ✅ 直接在已打开的页面上抓取数据
- ✅ 保留登录状态和浏览历史

**快速开始**：
```python
from browser import BrowserManager

# 连接到已打开的 SegmentFault 页面
async with BrowserManager(mode="connect") as bm:
    # 查找并连接到指定 URL 的标签页
    page = await bm.get_or_create_page(target_url="segmentfault.com")
    
    # 直接在这个页面上操作，无需导航
    print(await page.title())
```

**测试示例**：
```bash
# 测试新功能
python test_browser_manager.py

# 实战示例
python examples/existing_tab_scraper.py
```

**文档**：
- 📖 完整指南: `docs/browser_manager_new_features.md`

---

### 通用网页数据抓取器

支持自定义字段、灵活分页、延迟配置的通用数据采集工具。

**核心功能**：
- ✅ 自定义字段和CSS选择器
- ✅ 支持多种分页方式（按钮/URL参数）
- ✅ 页码范围控制
- ✅ 可配置延迟时间
- ✅ 提取元素属性（href、src等）
- ✅ 标准JSON格式输出
- ✅ 与LangChain Agent无缝集成

**快速开始**：
```bash
# 测试基础功能
python test_universal_scraper.py

# 查看完整示例
python lib/puppeteer/universal_scraper/example.py

# Agent集成
python examples/universal_scraper_agent.py
```

**文档**：
- 📖 详细指南: `docs/universal_scraper_guide.md`
- 🚀 快速开始: `docs/universal_scraper_readme.md`

---

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题，请提交 Issue。