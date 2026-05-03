"""
Puppeteer integration for LangChain Agent
Provides browser automation capabilities to the agent.
"""

from .puppeteer_tools import get_browser_tools
from .universal_scraper import (
    UniversalScraper,
    ScraperConfig,
    FieldConfig,
    create_scraper_config,
    get_universal_scraping_tools
)
from .merged_scraper import (
    MergedScraper,
    MergedScraperConfig,
    NavigationMode,
    create_merged_scraper_config
)
from .browser_steps import (
    BrowserStepExecutor,
    StepConfig,
    StepType,
    create_navigate_step,
    create_click_step,
    create_input_step,
    create_select_step,
    create_extract_step,
    create_press_key_step,
    create_wait_step
)
from .network_intercept import (
    ApiCollector,
    ApiCollectorConfig,
)

__all__ = [
    "get_browser_tools",
    "get_universal_scraping_tools",
    "UniversalScraper",
    "ScraperConfig",
    "FieldConfig",
    "create_scraper_config",
    "MergedScraper",
    "MergedScraperConfig",
    "NavigationMode",
    "create_merged_scraper_config",
    "BrowserStepExecutor",
    "StepConfig",
    "StepType",
    "create_navigate_step",
    "create_click_step",
    "create_input_step",
    "create_select_step",
    "create_extract_step",
    "create_press_key_step",
    "create_wait_step",
    "ApiCollector",
    "ApiCollectorConfig",
]
