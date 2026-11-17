import json

from pydantic import BaseModel, Field

from ai_agent.agent_config import create_llm
from common.logger import log
from scrape_agent.browser_session import open_target_page
from scrape_agent.state import GraphState


class SchemaField(BaseModel):
    name: str
    selector: str = Field(description="相对父容器的 CSS 选择器")


class CssSchema(BaseModel):
    baseSelector: str = Field(description="单条列表项容器的 CSS 选择器")
    fields: list[SchemaField]
    next_button_selector: str = Field(
        default="",
        description="「下一页」按钮的 CSS 选择器；无需分页时为空字符串",
    )


class DetailSchema(BaseModel):
    detail_container_selector: str = Field(description="详情页主内容容器 CSS 选择器")
    fields: list[SchemaField]


def _build_list_query(state: GraphState) -> str:
    fields = "、".join(state["field_names"])
    scope = state.get("module_selector") or "整个页面"
    max_pages = int(state.get("max_pages") or 1)
    query = (
        f"这是「{scope}」的 HTML。"
        f"请识别其中重复的列表项，生成 CSS 抽取 schema。"
        f"每条记录的列表字段名必须完全是：{fields}。"
        "baseSelector 必须是可点击的单条列表项容器（例如外层 a 或 .List-box）。"
        "每个字段 selector 相对 baseSelector。"
    )
    if max_pages == 0 or max_pages > 1:
        query += (
            " 需要分页：必须给出可点击的「下一页」按钮 CSS 选择器 "
            "next_button_selector（相对整页，不要相对列表项）。"
        )
    else:
        query += " 只需当前页，next_button_selector 填空字符串。"
    if state.get("retry_count", 0) > 0 and state.get("scraper_config"):
        query += (
            "\n上次配置不符合用户预期，请更换更稳健的选择器。"
            f"\n上次配置: {json.dumps(state['scraper_config'], ensure_ascii=False)}"
        )
        if state.get("sample_data"):
            query += f"\n上次试抓样本: {json.dumps(state['sample_data'], ensure_ascii=False)}"
    return query


def _map_list_schema(schema: dict, url: str, module_selector: str, max_pages: int) -> dict:
    base = (schema.get("baseSelector") or "").strip()
    if not base:
        raise ValueError("未返回 baseSelector。")
    if base.startswith("/") or base.startswith("("):
        raise ValueError(f"期望 CSS 选择器，实际得到: {base}")

    if module_selector and module_selector not in base:
        container = f"{module_selector} {base}"
    else:
        container = base

    fields: dict[str, str] = {}
    for item in schema.get("fields") or []:
        name = item.get("name")
        selector = (item.get("selector") or "").strip()
        if name and selector:
            fields[name] = selector
    if not fields:
        raise ValueError("schema 没有可用 fields。")

    next_sel = (schema.get("next_button_selector") or "").strip()
    if (max_pages == 0 or max_pages > 1) and not next_sel:
        raise ValueError("指令需要多页采集，但未解析到下一页按钮选择器。")

    return {
        "url": url,
        "container_selector": container,
        "fields": fields,
        "next_button_selector": next_sel or None,
        "max_pages": max_pages,
    }


async def _llm_schema(model: type, system: str, user: str):
    llm = create_llm()
    structured = llm.with_structured_output(model)
    result = await structured.ainvoke(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
    if not isinstance(result, model):
        result = model.model_validate(result)
    return result.model_dump()


async def propose_config(state: GraphState) -> dict:
    url = state["url"]
    module_selector = (state.get("module_selector") or "").strip()
    max_pages = int(state.get("max_pages") or 1)
    enable_detail = bool(state.get("enable_detail"))
    log("通过 CDP 读取页面 HTML，使用 ai_agent.create_llm 生成字段配置...")

    async with open_target_page(url) as page:
        if module_selector:
            await page.wait_for_selector(module_selector, timeout=15000)
            html = await page.locator(module_selector).first.evaluate(
                "el => el.outerHTML"
            )
        else:
            await page.wait_for_load_state("domcontentloaded")
            html = await page.locator("body").first.evaluate("el => el.outerHTML")

        if not html:
            raise ValueError("未能读取页面 HTML。")

        list_schema = await _llm_schema(
            CssSchema,
            "你根据 HTML 生成列表抽取用的 CSS schema，只输出结构化结果。",
            f"{_build_list_query(state)}\n\nHTML:\n{html}",
        )
        config = _map_list_schema(list_schema, url, module_selector, max_pages)
        requested = set(state["field_names"])
        extra_missing = [name for name in state["field_names"] if name not in config["fields"]]
        if extra_missing:
            log(f"schema 缺少字段 {extra_missing}，将按已有字段继续", level="WARNING")
        config["fields"] = {
            k: v for k, v in config["fields"].items() if k in requested
        } or config["fields"]

        if enable_detail:
            log("列表项可能无真实 href，点击第一条进入详情并生成详情配置...")
            await page.wait_for_selector(config["container_selector"], timeout=15000)
            first = page.locator(config["container_selector"]).first
            await first.click()
            await page.wait_for_load_state("domcontentloaded")
            detail_html = await page.locator("body").first.evaluate("el => el.outerHTML")
            named = state.get("detail_field_names") or []
            field_hint = (
                f"详情字段名必须完全是：{'、'.join(named)}。"
                if named
                else "自行归纳详情页主要字段（如正文、来源），字段名用中文。"
            )
            detail_schema = await _llm_schema(
                DetailSchema,
                "你根据详情页 HTML 生成 CSS schema。",
                f"{field_hint}\nHTML:\n{detail_html}",
            )
            detail_fields = {
                item["name"]: item["selector"]
                for item in (detail_schema.get("fields") or [])
                if item.get("name") and item.get("selector")
            }
            if named:
                detail_fields = {
                    k: v for k, v in detail_fields.items() if k in set(named)
                } or detail_fields
            if not detail_fields:
                raise ValueError("未能生成详情页字段选择器。")
            config["enable_detail"] = True
            config["detail_entry"] = "click"
            config["detail_container_selector"] = detail_schema["detail_container_selector"]
            config["detail_fields"] = detail_fields
            try:
                await page.go_back(wait_until="domcontentloaded")
                await page.wait_for_selector(config["container_selector"], timeout=15000)
            except Exception as exc:
                log(f"从详情返回列表失败: {exc}", level="WARNING")
        else:
            config["enable_detail"] = False

    log(f"生成配置: {json.dumps(config, ensure_ascii=False)}")
    return {"scraper_config": config, "last_error": None}
