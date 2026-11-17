from pydantic import BaseModel, Field

from ai_agent.agent_config import create_llm
from common.logger import log
from scrape_agent.state import GraphState


class ScrapeIntent(BaseModel):
    url: str = Field(description="要采集的网页 URL")
    module_selector: str = Field(
        description="页面模块 CSS 选择器；指令中未给出时为空字符串"
    )
    field_names: list[str] = Field(description="列表页字段名，保持用户原样")
    enable_detail: bool = Field(
        description="指令要求采集详情页或点击列表项进入详情时为 true"
    )
    detail_field_names: list[str] = Field(
        description="详情页字段名；未点名则空列表，由后续根据详情 HTML 推断"
    )
    max_pages: int = Field(
        description=(
            "要采集的页数：指令写「前N页」则为 N；"
            "写全部/不限页则为 0；未提及分页则为 1"
        )
    )


async def parse_intent(state: GraphState) -> dict:
    instruction = state["user_instruction"]
    log("解析用户指令...")
    llm = create_llm()
    structured = llm.with_structured_output(ScrapeIntent)
    intent = await structured.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "从用户采集指令中提取 url、模块 CSS 选择器、列表字段、是否采详情、详情字段、页数。"
                    "提到详情页、详情、点击列表项进入详情时 enable_detail=true。"
                    "列表字段与详情字段分开；未写详情字段时 detail_field_names 为空列表。"
                    "没有模块选择器时 module_selector 填空字符串。"
                    "页数：前2页→2，前N页→N，全部页→0，未提分页→1。"
                ),
            },
            {"role": "user", "content": instruction},
        ]
    )
    if not isinstance(intent, ScrapeIntent):
        intent = ScrapeIntent.model_validate(intent)

    if not intent.url:
        raise ValueError("未能从指令中解析出 URL，请补充目标网页地址。")
    if not intent.field_names:
        raise ValueError("未能从指令中解析出字段名，请补充要采集的字段。")
    max_pages = intent.max_pages
    if max_pages < 0:
        raise ValueError("页数不能为负数。")

    log(
        f"指令解析完成 url={intent.url} module={intent.module_selector or '(整页)'} "
        f"list_fields={intent.field_names} enable_detail={intent.enable_detail} "
        f"detail_fields={intent.detail_field_names} max_pages={max_pages}"
    )
    return {
        "url": intent.url,
        "module_selector": intent.module_selector,
        "field_names": intent.field_names,
        "enable_detail": intent.enable_detail,
        "detail_field_names": intent.detail_field_names,
        "max_pages": max_pages,
        "retry_count": 0,
        "user_approved": False,
    }
