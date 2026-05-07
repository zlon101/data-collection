# Airtest + Poco 纯代码自动化完整指南
### macOS M1 · uv · Python 3.11.8 · 零 IDE 依赖

---

## 目录
1. [框架职责划分](#1-框架职责划分)
2. [环境准备](#2-环境准备)
3. [项目结构](#3-项目结构)
4. [设备连接](#4-设备连接)
5. [自动化与数据抓取实战模板](#5-自动化与数据抓取实战模板)
6. [纯代码调试技巧](#6-纯代码调试技巧)
7. [常见问题排查](#7-常见问题排查)

---

## 1. 框架职责划分

在无 IDE 的纯代码环境中，**必须先理解两个框架的边界**，错用工具是最常见的效率黑洞。

| 维度 | Airtest | Poco |
|---|---|---|
| **核心原理** | 基于 OpenCV 图像识别 + ADB 触控指令 | 基于 UI 控件树（AccessibilityService / UIAutomation）解析 |
| **擅长场景** | App 启动/关闭、基础系统级交互、截图断言、无控件树支持的游戏/H5 | **精准数据抓取**：节点文本、属性、层级结构 |
| **数据抓取能力** | ❌ 极弱（只能截图后做 OCR，不稳定） | ✅ 强（直接读取控件属性，毫秒级，100% 准确） |
| **稳定性** | 受分辨率/主题/截图质量影响 | 与 UI 渲染无关，只依赖控件树 |
| **典型 API** | `touch()`, `swipe()`, `exists()`, `snapshot()` | `poco("node").get_text()`, `.attr()`, `.child()` |

**核心原则**：启动 App、处理系统弹窗 → 用 Airtest；抓取页面数据、定位控件精确交互 → 用 Poco。

---

## 2. 环境准备

### 2.1 前置依赖（macOS M1）

```bash
# 安装 Homebrew（如已安装可跳过）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 ADB（强烈建议：不依赖 Airtest 内置的可能为 x86_64 的二进制）
brew install android-platform-tools

# 确认 ADB 路径（M1 Homebrew 默认安装到 /opt/homebrew/bin/adb）
which adb
adb version
```

> ⚠️ **M1 特别说明**：Airtest 内置了 ADB 二进制，但早期版本在 M1 上可能为 x86_64（通过 Rosetta 运行），稳定性存疑。
> 通过 Homebrew 安装系统级 ADB（ARM64 原生）后，在代码中显式指定路径，可彻底规避此问题（见 4.1 节）。

### 2.2 使用 uv 创建项目并安装依赖

```bash
# 从项目根目录执行
uv run --directory collection_platform/app_airtest uv venv .venv
uv run --directory collection_platform/app_airtest uv pip install "airtest>=1.3.0" "pocoui>=1.0.86"

# 确认安装成功
uv run --directory collection_platform/app_airtest python3 -c "import airtest; import poco; print('OK')"
```


## 3. 项目结构

```
airtest-automation/
├── pyproject.toml
├── uv.lock
├── config/
│   └── devices.py          # 设备连接配置
├── core/
│   ├── __init__.py
│   ├── device_manager.py   # 设备初始化封装
│   └── poco_helper.py      # Poco 工具函数封装
├── scrapers/
│   ├── __init__.py
│   └── app_scraper.py      # 具体数据抓取脚本
├── outputs/                # 抓取结果存储目录
│   └── .gitkeep
└── tests/
    └── test_connection.py  # 连接验证脚本
```

---

## 4. 设备连接

### 4.1 Android 设备连接（USB / WiFi）

core/device_manager.py

### 4.2 初始化 Poco 实例

core/poco_helper.py

## 5. 自动化与数据抓取实战模板

这是核心模板，展示 Airtest（负责 App 生命周期）与 Poco（负责精准数据抓取）的完整协作链路。
scrapers/app_scraper.py

## 6. 纯代码调试技巧

脱离 IDE 后，以下 4 种手段是调试的核心工具链。

### 6.1 在代码中打印 UI 树结构（最重要）

debug_utils.py

### 6.2 使用方式示例

```python
from debug_utils import dump_ui_tree, find_all_texts, print_node_info

# 在不知道节点结构时，先 dump 整棵树保存为文件
tree = dump_ui_tree(poco, "outputs/ui_tree_home.json")

# 快速列出页面上的所有文本
texts = find_all_texts(tree)
print("页面文本:", texts)

# 找到节点后，打印它的完整属性
target = poco(text="登录")
print_node_info(target)
```

### 6.3 借助原生工具获取节点信息（无 IDE 场景）

| 工具 | 使用场景 | 命令/方式 |
|---|---|---|
| **uiautomatorviewer**（Android SDK 自带） | 静态截图 + 节点树分析 | `$ANDROID_HOME/tools/bin/uiautomatorviewer` |
| **Appium Inspector** | 实时 UI 树浏览（GUI 工具，独立于 Appium Server）| 官网下载，连接 Appium Server 后使用 |
| **ADB Shell dumpsys** | 纯命令行，无需额外工具 | `adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml .` |
| **Android Studio Layout Inspector** | 精确查看层级、属性 | AS 内置，通过 USB 连接直接用 |

**ADB dump 一行命令（最轻量）：**
```bash
# 将当前屏幕 UI 树导出为 XML 并拉取到本地
adb shell uiautomator dump /sdcard/window_dump.xml
adb pull /sdcard/window_dump.xml ./outputs/
# 然后用任意文本编辑器搜索 resource-id / text 属性
```

### 6.4 截图辅助调试

```python
from airtest.core.api import snapshot

# 在关键步骤前后截图，保存到 outputs/ 目录
snapshot(filename="outputs/step_01_home.jpg")
# ... 执行操作 ...
snapshot(filename="outputs/step_02_after_click.jpg")
```

### 6.5 运行脚本

```bash
# 从项目根目录执行（所有命令统一入口）
uv run --directory collection_platform/app_airtest python3 -m main
uv run --directory collection_platform/app_airtest python3 -m main --mode manual
uv run --directory collection_platform/app_airtest python3 tests/test_connection.py

# 微信公众号采集
uv run --directory collection_platform/app_airtest python3 -m scrapers.wechat_scraper --account 国资小新 --max 20
```

---

## 7. 常见问题排查

| 现象 | 原因 | 解决方案 |
|---|---|---|
| `adb: device not found` | USB 调试未开启 / ADB 路径错误 | 开启「开发者选项 → USB 调试」；确认 `which adb` 路径 |
| `PocoTargetTimeout` | 节点 selector 写错 / 页面未加载完 | dump UI 树核对 resource-id；增大 timeout 参数 |
| `connect_device` 连接后立即断开 | M1 内置 ADB 版本不兼容 | 设置 `AIRTEST_ADB_PATH` 为 Homebrew ADB 路径 |
| Poco 抓取文本为空 | 节点是 WebView 内的 H5 元素 | 改用 `WebPoco`，或先 dump 树确认节点类型 |
| `start_app` 成功但 Poco 找不到节点 | App 启动后还在加载中 | 增加 `sleep(3.0)` 等待时间，或改用 `wait_for_appearance` |
| WiFi 连接不稳定 | ADB over WiFi 本身的局限 | USB 调试优先；必须 WiFi 时确保设备与 Mac 在同一子网 |

---

*生成日期：2026-04-01 | 适用版本：airtest ≥ 1.3.0，pocoui ≥ 1.0.86，Python 3.11.8，macOS M1*