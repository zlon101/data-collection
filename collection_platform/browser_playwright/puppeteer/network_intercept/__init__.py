"""
网络拦截模块 — 采集分页 API 响应数据。
"""

from .config import ApiCollectorConfig
from .api_collector import ApiCollector

__all__ = [
    'ApiCollectorConfig',
    'ApiCollector',
]
