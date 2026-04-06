#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
App Spider Library
通用的 Android App 数据抓取框架
"""

from .list_page_spider import ListPageSpider, ListPageSpiderParam
from .universal_page_parser import UniversalPageParser
from .detail_page_spider_universal import DetailPageSpider as DetailPageSpiderUniversal
from .exceptions import (
    MultipleElementsError,
    ParseTimeoutError,
    BottomReachedError,
    ScrollFailedError
)

__version__ = "4.0.0"
__all__ = [
    "ListPageSpider",
    "ListPageSpiderParam",
    "UniversalPageParser",
    "DetailPageSpiderUniversal",
    "MultipleElementsError",
    "ParseTimeoutError",
    "BottomReachedError",
    "ScrollFailedError",
]
