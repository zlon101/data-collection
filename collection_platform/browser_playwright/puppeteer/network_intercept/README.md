# network_intercept — API 响应采集模块

通过监听浏览器网络响应 + 自动点击分页按钮，采集分页 API 的 JSON 数据。

## 使用场景

页面中有分页表格/列表，数据来自某个 API 接口。不需要解析 DOM，直接拦截 API 响应即可拿到结构化数据。

## 核心组件

| 文件 | 说明 |
|------|------|
| `config.py` | `ApiCollectorConfig` 数据类，定义采集参数 |
| `api_collector.py` | `ApiCollector` 采集器，执行拦截 + 翻页 + 数据聚合 |

## 工作流程

```
1. 启动监听，等待用户手动操作触发 API 请求（如打开弹窗）
2. 捕获首次 API 响应，提取数据
3. 自动点击"下一页"按钮，捕获后续页响应
4. 达到 max_pages 或没有下一页时停止
5. 所有分页数据汇总到同一数组
```

## 快速开始

```python
from puppeteer.network_intercept import ApiCollectorConfig, ApiCollector

config = ApiCollectorConfig(
    url_pattern=r".*/api/articles.*",      # 匹配目标 API URL（正则）
    json_path="data.items",                # 响应 JSON 中数据列表的路径，留空则取整个响应
    next_button_selector=".next-btn",      # 下一页按钮的 CSS 选择器
    max_pages=5,                           # 最多采集页数，0 表示不限制
    timeout=10000,                         # 单次请求超时（毫秒）
    next_page_delay=500,                   # 点击下一页后等待时间（毫秒）
    data_format=None,                      # 可选的数据格式化回调
)

collector = ApiCollector(page, config)
all_data = await collector.collect_all_pages()

# 查看采集统计
stats = collector.get_stats()

# 保存到 JSON 文件
collector.save_to_json("output.json")
```

## ApiCollectorConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url_pattern` | `str` | 必填 | 目标 API 的 URL 正则表达式 |
| `json_path` | `str` | `""` | 响应 JSON 中数据路径，点号分隔，如 `"data.items"` |
| `next_button_selector` | `str` | `""` | 下一页按钮的 CSS 选择器，留空则不翻页 |
| `max_pages` | `int` | `0` | 最多采集页数，0 表示不限制 |
| `timeout` | `int` | `10000` | 单次请求超时时间（毫秒） |
| `next_page_delay` | `int` | `500` | 点击下一页后的等待时间（毫秒） |
| `data_format` | `Callable` | `None` | 数据格式化回调，签名 `(list[dict]) -> list[dict]` |

## json_path 示例

响应体：
```json
{
  "code": 200,
  "data": {
    "items": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
  }
}
```

- `json_path="data.items"` → 提取 `[{"id": 1, ...}, {"id": 2, ...}]`
- `json_path=""`（留空）→ 返回整个响应体作为单条数据

## 运行示例

```bash
uv run python collection_platform/browser_playwright/puppeteer/network_intercept/example.py
```

示例演示了连接已有微信公众号页面，采集分页 API 数据的完整流程。
