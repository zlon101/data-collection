"""
列表页与详情页合并抓取器
List and Detail Page Merged Scraper
"""

from .config import (
    DetailEntryMode,
    MergedScraperConfig,
    NavigationMode,
    create_merged_scraper_config,
)
from .merged_scraper import MergedScraper

__all__ = [
    "MergedScraper",
    "MergedScraperConfig",
    "NavigationMode",
    "DetailEntryMode",
    "create_merged_scraper_config",
]
