# Android App 数据爬虫框架 v3.0

基于 uiautomator2 的通用 Android 应用数据抓取框架，采用模块化设计，支持列表页和详情页数据抓取。

## 🎯 核心特性

- ✅ **模块化设计** - 三个独立模块，职责清晰
- ✅ **容器解析方案** - 基于 UI 层次结构，数据准确性 100%
- ✅ **智能去重** - 支持多字段组合去重
- ✅ **智能停止** - 自动检测列表底部
- ✅ **进度显示** - Rich 库美化输出
- ✅ **易于扩展** - 简单的 API 设计

## 📦 项目结构

```
app-script/
├── lib/                           # 核心库
│   ├── __init__.py               # 模块导出
│   ├── generic_page_spider.py    # 通用页面解析器
│   ├── list_page_spider.py       # 列表页爬虫
│   └── detail_page_spider.py     # 详情页爬虫
├── examples/                      # 示例代码
│   ├── generic_page_example.py   # 通用页面解析示例
│   ├── boss_list_example.py      # Boss直聘列表页示例
│   └── boss_detail_example.py    # Boss直聘详情页示例
├── docs/                          # 文档
│   ├── README.md                 # 详细文档
│   └── API.md                    # API 文档
├── requirements.txt               # 依赖
└── README.md                      # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
uv sync

# 手机连接电脑，开启usb调试，执行命令
uv run -m uiautomator2 init
# 执行成功后，手机上会出现一个小汽车图标的 App (ATX)。

# 执行命令，查看页面元素
uv run uiauto.dev
```

### 2. 启动 UI 检查工具

```bash
python -m weditor
# 访问 http://localhost:17310

pip install -U uiautodev -i https://pypi.doubanio.com/simple
uiauto.dev
```

### 3. 运行示例

```bash
# 通用页面解析
cd examples
python generic_page_example.py

# 列表页抓取
python boss_list_example.py

# 列表页 + 详情页
python boss_detail_example.py
```

## 💡 核心模块

### 1. GenericPageSpider - 通用页面解析器

**功能：** 解析当前页面数据，返回 JSON 对象

**使用场景：**
- 解析单个页面
- 作为其他爬虫的基础组件

**示例：**
```python
from lib import GenericPageSpider

spider = GenericPageSpider(
    device=device,
    selectors={
        "标题": "com.xxx:id/title",
        "价格": "com.xxx:id/price"
    }
)

data = spider.parse()  # 返回 {"标题": "...", "价格": "..."}
```

### 2. ListPageSpider - 列表页爬虫

**功能：** 抓取列表页数据，支持滚动、去重、智能停止

**使用场景：**
- 抓取商品列表
- 抓取职位列表
- 抓取文章列表

**示例：**
```python
from lib import ListPageSpider

spider = ListPageSpider(
    device=device,
    container_selector="com.xxx:id/item_container",
    selectors={
        "标题": "com.xxx:id/title",
        "价格": "com.xxx:id/price"
    },
    max_items=100
)

data = spider.crawl()  # 返回列表数据
spider.save_to_json("data.json")
```

### 3. DetailPageSpider - 详情页爬虫

**功能：** 点击列表项 -> 抓取详情 -> 返回列表 -> 继续下一项

**使用场景：**
- 需要详情页完整信息
- 列表页信息不完整

**示例：**
```python
from lib import ListPageSpider, DetailPageSpider

# 1. 先抓取列表
list_spider = ListPageSpider(...)
list_data = list_spider.crawl()

# 2. 再抓取详情
detail_spider = DetailPageSpider(
    device=device,
    detail_selectors={
        "详细描述": "com.xxx:id/description"
    }
)

full_data = detail_spider.crawl_details(
    list_data=list_data,
    container_selector="com.xxx:id/item_container"
)
```

## 📖 配置说明

### 选择器配置

支持两种格式：

**简单格式：**
```python
selectors={
    "标题": "com.xxx:id/title",
    "价格": "com.xxx:id/price"
}
```

**完整格式：**
```python
selectors={
    "标题": {
        "type": "resourceId",      # 选择器类型
        "value": "com.xxx:id/title",
        "optional": False           # 是否可选
    }
}
```

### 支持的选择器类型

- `resourceId` - 资源 ID（推荐）
- `text` - 文本匹配
- `textContains` - 文本包含
- `description` - 描述
- `className` - 类名

## 🎓 使用教程

### 场景 1：只抓取列表页

```python
import uiautomator2 as u2
from lib import ListPageSpider

device = u2.connect()
device.app_start("com.example.app")

spider = ListPageSpider(
    device=device,
    container_selector="com.example.app:id/item_container",
    selectors={
        "标题": "com.example.app:id/title",
        "价格": "com.example.app:id/price"
    },
    max_items=50
)

data = spider.crawl()
spider.save_to_json("list_data.json")
```

### 场景 2：列表页 + 详情页

```python
import uiautomator2 as u2
from lib import ListPageSpider, DetailPageSpider

device = u2.connect()
device.app_start("com.example.app")

CONTAINER = "com.example.app:id/item_container"

# 1. 列表页
list_spider = ListPageSpider(
    device=device,
    container_selector=CONTAINER,
    selectors={
        "标题": "com.example.app:id/title"
    },
    max_items=20
)
list_data = list_spider.crawl()

# 2. 详情页
detail_spider = DetailPageSpider(
    device=device,
    detail_selectors={
        "详细描述": "com.example.app:id/description"
    }
)

full_data = detail_spider.crawl_details(
    list_data=list_data,
    container_selector=CONTAINER
)

# 保存
import json
with open("full_data.json", "w", encoding="utf-8") as f:
    json.dump(full_data, f, ensure_ascii=False, indent=2)
```

## 🔧 常见问题

### Q1: 如何找到容器选择器？

使用 `python -m weditor` 工具，找到包含所有字段的**最小公共父元素**的 resourceId。

### Q2: 数据解析错误怎么办？

1. 检查容器选择器是否正确
2. 使用 weditor 确认字段的 resourceId
3. 增加 `wait_before_parse` 等待时间

### Q3: 如何调试？

在示例代码中添加：
```python
console.print("[yellow]当前数据：[/yellow]")
console.print(data)
```

## 📚 更多文档

- [详细文档](./docs/README.md) - 完整的使用说明
- [API 文档](./docs/API.md) - API 详细参考
- [示例代码](./examples/) - 更多示例

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

MIT License

## ⚠️ 免责声明

本工具仅用于学习和研究目的。使用者需遵守相关法律法规和目标 App 的服务条款。

---

**版本：** 3.0.0  
**更新日期：** 2026-01-12
