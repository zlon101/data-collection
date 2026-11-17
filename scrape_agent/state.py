from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    user_instruction: str
    url: str
    module_selector: str
    field_names: list[str]
    detail_field_names: list[str]
    enable_detail: bool
    max_pages: int
    scraper_config: dict[str, Any]
    sample_data: list[dict[str, Any]]
    user_approved: bool
    output_path: str | None
    last_error: str | None
    retry_count: int
