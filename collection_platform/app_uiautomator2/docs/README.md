# Android App 数据爬虫框架

一个通用的、可配置化的 Android App 数据抓取框架，基于 uiautomator2 实现，支持自动化滚动、智能去重、智能停止、列表页和详情页数据抓取等功能。

## 📋 目录

- [项目概述](#项目概述)
- [核心特性](#核心特性)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [项目架构](#项目架构)
- [核心模块](#核心模块)
- [使用指南](#使用指南)
- [配置示例](#配置示例)
- [高级功能](#高级功能)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

## 项目概述

本项目是一个基于 Python 和 uiautomator2 的通用 Android 应用数据爬虫框架，通过配置化的方式，可以快速实现对任意 Android App 的数据抓取。框架采用**容器解析方案**，确保数据准确性达到 100%。

### 适用场景

- 招聘类 App（Boss直聘、猎聘等）数据采集
- 电商类 App 商品信息抓取
- 社交类 App 内容采集
- 房产类 App（58同城、贝壳找房等）信息收集
- 任何具有列表页和详情页结构的 Android 应用

## 核心特性

### ✨ 基础功能

- ✅ **通用性强** - 适用于任何 Android App 的列表页面数据抓取
- ✅ **配置简单** - 只需提供包名和字段选择器即可快速上手
- ✅ **智能去重** - 支持多字段组合去重，避免重复数据
- ✅ **智能停止** - 自动检测无新数据，避免无效滚动
- ✅ **精确控制** - 按数据条数而非滚动次数控制抓取量
- ✅ **美化输出** - 使用 Rich 库提供友好的终端界面和进度显示
- ✅ **中断恢复** - 支持 Ctrl+C 中断并保存已抓取数据

### 🚀 高级功能

- ✅ **容器解析方案** - 基于 UI 层次结构，确保字段关联准确性 100%
- ✅ **详情页抓取** - 支持列表页 → 详情页的完整数据流程
- ✅ **分步执行器** - 支持复杂的操作流程（点击、滚动、输入、解析等）
- ✅ **回调函数** - 支持解析前后的自定义回调
- ✅ **自定义滚动** - 可扩展自定义滚动策略
- ✅ **多选择器类型** - 支持 resourceId、text、textContains、description 等多种选择器

## 环境要求

### 系统要求

- Python 3.7+
- MacOS / Linux / Windows
- Android 设备（USB 连接，开启 USB 调试）
- ADB 工具已配置

### Python 依赖

```
rich>=13.0.0
uiautomator2>=2.16.0
```

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd app-script

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 uiautomator2
pip install uiautomator2
pip install -U uiautodev -i https://pypi.doubanio.com/simple
```

### 2. 初始化设备

```bash
# 手机连接电脑，开启 USB 调试，执行初始化命令
python -m uiautomator2 init

# 执行成功后，手机上会出现一个小汽车图标的 App (ATX)
```

### 3. 获取页面元素选择器

```bash
# 启动 UI 元素检查工具
python -m weditor

# 访问 http://localhost:17310
# 在工具中找到目标元素的 resourceId
```

### 4. 运行示例

```bash
# 运行 Boss直聘列表页爬虫
python boss_spider_example.py

# 运行详情页爬虫示例
python detail_splider_example.py
```

## 项目架构

```
app-script/
├── generic_app_spider.py       # 核心爬虫类（列表页）
├── detail_page_spider.py       # 详情页爬虫扩展
├── boss_spider_example.py      # Boss直聘爬虫示例
├── detail_splider_example.py   # 详情页爬虫示例
├── requirements.txt            # 依赖包
├── Prompt.md                   # 提示文档
├── README.md                   # 说明文档（本文件）
└── lib/                        # 库文件目录（预留）
```

## 核心模块

### 1. GenericAppSpider（通用列表页爬虫）

**核心原理：容器解析方案**

传统方案的问题：
- 索引对齐容易出错
- 无法保证字段属于同一条数据
- 布局变化时易失效

容器解析方案的优势：
```python
# 1. 查找所有列表项容器
containers = device(resourceId="com.xxx:id/item_container")

# 2. 在每个容器内查找子元素
for container in containers:
    title = container.child(resourceId="com.xxx:id/title").get_text()
    price = container.child(resourceId="com.xxx:id/price").get_text()
    # 这些字段必然属于同一条数据！
```

优点：
- ✅ 最准确：利用 UI 层次结构，字段关联性 100% 正确
- ✅ 最稳定：不依赖索引对齐，不受元素数量影响
- ✅ 零错配：每个容器内的字段必然属于同一条数据
- ✅ 支持复杂布局：即使字段分布不规则也能正确解析

### 2. DetailPageSpider（详情页爬虫）

支持列表页 → 详情页的完整数据流程：

1. 抓取列表页基本信息
2. 依次点击每个列表项进入详情页
3. 解析详情页完整信息
4. 返回列表页继续下一项
5. 合并列表数据和详情数据

### 3. StepExecutor（分步执行器）

支持复杂操作流程的步骤化执行：

- **CLICK** - 点击元素
- **SCROLL** - 滚动页面
- **BACK** - 返回上一页
- **INPUT** - 输入文本
- **PARSE** - 解析数据
- **WAIT** - 等待

## 使用指南

### 基础使用：列表页爬虫

#### 1. 最简配置

```python
from generic_app_spider import GenericAppSpider

spider = GenericAppSpider(
    app_package="com.example.app",
    container_selector="com.example.app:id/item_container",  # 容器选择器
    selectors={
        "标题": "com.example.app:id/title",
        "内容": "com.example.app:id/content"
    }
)

spider.run()
```

#### 2. 完整配置

```python
spider = GenericAppSpider(
    app_package="com.hpbr.bosszhipin",           # App 包名
    container_selector="com.hpbr.bosszhipin:id/cl_card_container",  # 容器
    selectors={                                   # 字段选择器
        "职位名称": "com.hpbr.bosszhipin:id/tv_position_name",
        "薪资待遇": "com.hpbr.bosszhipin:id/tv_salary_statue",
        "公司名称": "com.hpbr.bosszhipin:id/tv_company_name"
    },
    max_items=100,                                # 最大数据条数
    scroll_sleep=2.5,                             # 滚动后等待时间（秒）
    unique_keys=["职位名称", "公司名称"],          # 去重字段组合
    output_prefix="boss_jobs",                    # 输出文件前缀
    title="Boss直聘职位爬虫",                     # 显示标题
    max_empty_scrolls=3                           # 连续3次无数据停止
)

spider.run()
```

### 参数说明

#### 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `app_package` | str | App 的包名，如 `com.hpbr.bosszhipin` |
| `container_selector` | str | 列表项容器的 resourceId（关键参数！） |
| `selectors` | Dict[str, str] | 字段选择器映射，key 为中文字段名，value 为 resourceId |

#### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_items` | int | 100 | 最大数据条数 |
| `scroll_sleep` | float | 2.5 | 滚动后等待时间（秒） |
| `unique_keys` | List[str] | 第一个字段 | 用于去重的字段列表 |
| `output_prefix` | str | "data" | 输出 JSON 文件名前缀 |
| `title` | str | "通用数据爬虫" | 爬虫显示标题 |
| `max_empty_scrolls` | int | 3 | 连续多少次无新数据时停止 |

### 智能停止机制

```python
# 场景1：明确需要 100 条数据
spider = GenericAppSpider(
    max_items=100,          # 精确抓取 100 条
    max_empty_scrolls=3     # 如果提前到底则停止
)

# 场景2：抓取所有可用数据（不知道有多少条）
spider = GenericAppSpider(
    max_items=99999,        # 设置很大的值
    max_empty_scrolls=3     # 依赖智能停止
)
# 优点：会自动抓到列表底部后停止
```

## 配置示例

### Boss直聘

```python
BOSS_CONFIG = {
    "app_package": "com.hpbr.bosszhipin",
    "container_selector": "com.hpbr.bosszhipin:id/cl_card_container",
    "selectors": {
        "职位名称": "com.hpbr.bosszhipin:id/tv_position_name",
        "薪资待遇": "com.hpbr.bosszhipin:id/tv_salary_statues",
        "公司名称": "com.hpbr.bosszhipin:id/tv_company_name",
        "工作地点": "com.hpbr.bosszhipin:id/tv_distance"
    },
    "max_items": 100,
    "scroll_sleep": 2.5,
    "unique_keys": ["职位名称", "公司名称"],
    "output_prefix": "boss_jobs"
}

spider = GenericAppSpider(**BOSS_CONFIG)
spider.run()
```

### 58同城租房

```python
WUBA_CONFIG = {
    "app_package": "com.wuba",
    "container_selector": "com.wuba:id/item_container",
    "selectors": {
        "标题": "com.wuba:id/title",
        "价格": "com.wuba:id/price",
        "位置": "com.wuba:id/location",
        "面积": "com.wuba:id/area"
    },
    "max_items": 200,
    "scroll_sleep": 3.0,
    "unique_keys": ["标题", "位置"],
    "output_prefix": "wuba_rent"
}
```

## 高级功能

### 1. 详情页数据抓取

```python
from generic_app_spider import GenericAppSpider
from detail_page_spider import DetailPageSpider
import uiautomator2 as u2

# Step 1: 抓取列表页数据
list_spider = GenericAppSpider(
    app_package="com.hpbr.bosszhipin",
    container_selector="com.hpbr.bosszhipin:id/cl_card_container",
    selectors={
        "职位名称": "com.hpbr.bosszhipin:id/tv_position_name",
        "公司名称": "com.hpbr.bosszhipin:id/tv_company_name"
    },
    max_items=10
)

list_spider.run()
list_data = list_spider.get_data()

# Step 2: 抓取详情页数据
detail_spider = DetailPageSpider(
    device=list_spider.device,
    list_container_selector="com.hpbr.bosszhipin:id/cl_card_container",
    detail_selectors={
        "职位描述": {
            "type": "resourceId",
            "value": "com.hpbr.bosszhipin:id/tv_job_description",
            "optional": False
        },
        "任职要求": {
            "type": "resourceId",
            "value": "com.hpbr.bosszhipin:id/tv_requirements",
            "optional": True
        }
    },
    click_wait=2.0,
    back_wait=1.5,
    max_items=10
)

# Step 3: 合并数据
full_data = detail_spider.crawl_details(list_data)
```

### 2. 使用回调函数

```python
def before_parse():
    """每次解析前执行"""
    print("准备解析当前页面...")

def after_parse(items):
    """每次解析后执行"""
    print(f"本次获取到 {len(items)} 条数据")
    for item in items:
        print(f"  - {item.get('职位名称', 'N/A')}")

spider.run(before_parse=before_parse, after_parse=after_parse)
```

### 3. 分步执行器

```python
from detail_page_spider import StepExecutor, StepType
import uiautomator2 as u2

device = u2.connect()
executor = StepExecutor(device)

# 定义操作步骤
steps = [
    # 点击搜索框
    {
        "type": StepType.CLICK.value,
        "selector_type": "resourceId",
        "selector_value": "com.hpbr.bosszhipin:id/search_box",
        "wait_after": 1.0
    },
    # 输入关键词
    {
        "type": StepType.INPUT.value,
        "selector_type": "resourceId",
        "selector_value": "com.hpbr.bosszhipin:id/search_input",
        "text": "Python工程师",
        "press_enter": True,
        "wait_after": 2.0
    },
    # 解析结果
    {
        "type": StepType.PARSE.value,
        "selectors": {
            "职位名称": {
                "type": "resourceId",
                "value": "com.hpbr.bosszhipin:id/tv_position_name"
            }
        }
    },
    # 返回
    {
        "type": StepType.BACK.value,
        "wait_after": 1.0
    }
]

# 执行步骤
context = executor.execute_steps(steps)
parsed_data = context.get("parsed_data", {})
```

### 4. 自定义滚动策略

```python
class CustomSpider(GenericAppSpider):
    def scroll_page(self):
        """自定义滚动逻辑"""
        if not self.device:
            return
        
        # 例如：更快的滚动
        screen_width, screen_height = self.device.window_size()
        start_y = int(screen_height * 0.95)
        end_y = int(screen_height * 0.1)
        x = int(screen_width / 2)
        
        self.device.swipe(x, start_y, x, end_y, duration=0.2)
        time.sleep(1.0)

spider = CustomSpider(...)
spider.run()
```

## 故障排查

### 问题1: 设备连接失败

**错误信息：**
```
✗ 未找到设备
```

**解决方案：**
```bash
# 1. 检查设备连接
adb devices

# 2. 重启 ADB
adb kill-server
adb start-server

# 3. 重新初始化
python -m uiautomator2 init
```

### 问题2: 未获取到数据

**可能原因：**
- container_selector 配置错误
- 字段 resourceId 不正确
- 页面未加载完成

**解决方案：**

```bash
# 1. 使用 weditor 重新确认元素
python -m weditor

# 2. 检查容器选择器
# 容器应该是包含所有字段的父元素

# 3. 增加等待时间
spider = GenericAppSpider(
    scroll_sleep=3.0,  # 增加到 3 秒
    ...
)
```

### 问题3: 数据重复

**解决方案：**

```python
# 检查 unique_keys 配置
spider = GenericAppSpider(
    unique_keys=["职位名称", "公司名称"],  # 使用组合键
    ...
)
```

### 问题4: 过早停止或过度滚动

**解决方案：**

```python
# 调整 max_empty_scrolls 参数
spider = GenericAppSpider(
    max_empty_scrolls=5,  # 列表加载慢时增大
    scroll_sleep=3.0,      # 增加等待时间
    ...
)
```

### 问题5: 容器选择器找不到

**错误信息：**
```
⚠ 未找到容器元素，请检查 container_selector 配置
```

**解决方案：**

1. 使用 weditor 工具仔细查看页面结构
2. 找到包含所有字段的**最小公共父容器**
3. 确保选择器格式正确：`包名:id/元素id`

```python
# ✅ 正确示例
container_selector = "com.hpbr.bosszhipin:id/cl_card_container"

# ❌ 错误示例
container_selector = "cl_card_container"  # 缺少包名
```

## 最佳实践

### 1. 容器选择器的选择

容器选择器是整个框架的核心，选择正确的容器至关重要：

**原则：**
- 选择包含所有目标字段的**最小公共父元素**
- 确保每个列表项都有这个容器
- 容器应该是独立的、完整的数据单元

**示例：**

```
ListView
├── ItemContainer1 (这是容器！)
│   ├── TextView (标题)
│   ├── TextView (价格)
│   └── TextView (位置)
├── ItemContainer2 (这是容器！)
│   ├── TextView (标题)
│   ├── TextView (价格)
│   └── TextView (位置)
```

### 2. 合理设置等待时间

```python
# 网络较慢的情况
spider = GenericAppSpider(
    scroll_sleep=3.0,  # 增加等待时间
    max_empty_scrolls=5  # 增加容忍度
)

# 网络较快的情况
spider = GenericAppSpider(
    scroll_sleep=1.5,  # 减少等待时间
    max_empty_scrolls=2  # 快速停止
)
```

### 3. 去重策略

```python
# 单字段去重（适合唯一性强的字段）
unique_keys=["职位名称"]

# 多字段组合去重（更准确）
unique_keys=["职位名称", "公司名称"]

# 复杂去重（自定义）
unique_keys=["标题", "价格", "位置"]
```

### 4. 测试先行

```python
# 先用小数据量测试
spider = GenericAppSpider(
    max_items=5,  # 只抓 5 条
    ...
)
spider.run()

# 确认无误后再大批量抓取
spider = GenericAppSpider(
    max_items=1000,
    ...
)
```

### 5. 数据保存策略

```python
# 方式1：自动保存（推荐）
spider.run()  # 自动保存为 JSON

# 方式2：获取数据后自定义处理
spider.run()
data = spider.get_data()

# 保存为 CSV
import csv
with open('output.csv', 'w', encoding='utf-8', newline='') as f:
    if data:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

# 保存到数据库
import sqlite3
conn = sqlite3.connect('data.db')
# ... 数据库操作
```

## 输出格式

数据自动保存为 JSON 格式，文件名格式：`{output_prefix}_{timestamp}.json`

**示例输出：**

```json
[
  {
    "职位名称": "Python开发工程师",
    "薪资待遇": "20-35K",
    "公司名称": "某科技公司",
    "工作地点": "北京-朝阳区"
  },
  {
    "职位名称": "数据分析师",
    "薪资待遇": "15-25K",
    "公司名称": "某数据公司",
    "工作地点": "北京-海淀区"
  }
]
```

## 技术原理

### 容器解析方案详解

**传统方案的问题：**

```python
# ❌ 传统索引对齐方案
titles = device(resourceId="xxx:id/title")
prices = device(resourceId="xxx:id/price")

for i in range(titles.count):
    title = titles[i].get_text()
    price = prices[i].get_text()  # 可能错位！
```

问题：
- 如果某个元素缺失，索引会错位
- 无法保证 title[0] 和 price[0] 属于同一条数据
- 布局变化时容易失效

**容器解析方案：**

```python
# ✅ 容器解析方案
containers = device(resourceId="xxx:id/container")

for container in containers:
    # 在容器内查找（关键：child 方法）
    title = container.child(resourceId="xxx:id/title").get_text()
    price = container.child(resourceId="xxx:id/price").get_text()
    # title 和 price 必然属于同一个 container！
```

优势：
- 利用 UI 的层次结构保证数据完整性
- 不依赖索引，不会错位
- 即使某些字段缺失也不影响其他数据
- 适应各种复杂布局

### 智能停止机制

```python
# 工作原理
empty_scroll_count = 0

while len(data) < max_items:
    new_items = parse_page()
    
    if new_items:
        data.extend(new_items)
        empty_scroll_count = 0  # 重置计数
    else:
        empty_scroll_count += 1  # 累加计数
        
        if empty_scroll_count >= max_empty_scrolls:
            print("已到底部，停止抓取")
            break
    
    scroll_page()
```

## 常见问题 FAQ

**Q1: 为什么必须提供 container_selector？**

A: 容器选择器是确保数据准确性的关键。它定义了数据的边界，保证每个容器内的字段属于同一条记录。

**Q2: 如何找到正确的 container_selector？**

A: 使用 `python -m weditor` 工具，在页面结构中找到包含所有目标字段的最小公共父元素的 resourceId。

**Q3: 支持哪些选择器类型？**

A: 支持 resourceId（推荐）、text、textContains、description、className 等。

**Q4: 可以不连接设备直接运行吗？**

A: 不可以。框架需要通过 ADB 连接真实的 Android 设备才能工作。

**Q5: 数据抓取速度慢怎么办？**

A: 可以减少 `scroll_sleep` 时间，但要确保页面有足够时间加载。建议先测试最小可用值。

**Q6: 支持模拟器吗？**

A: 支持。只要模拟器能被 ADB 检测到即可。

## 开发计划

- [ ] 支持多设备并行抓取
- [ ] 增加图片下载功能
- [ ] 支持代理配置
- [ ] 增加数据验证功能
- [ ] Web 管理界面
- [ ] 定时任务支持

## 贡献指南

欢迎提交 Issue 和 Pull Request！

提交 PR 前请确保：
1. 代码符合 PEP 8 规范
2. 添加了必要的注释
3. 更新了相关文档

## 许可证

MIT License

## 免责声明

本工具仅用于学习和研究目的。使用者需遵守相关法律法规和目标 App 的服务条款。请勿用于商业用途或大规模数据抓取。使用本工具产生的一切后果由使用者自行承担。

## 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 Issue
- 发送 Pull Request
- 邮件联系（如有）

---

**最后更新：** 2026-01-12
**版本：** 2.0
