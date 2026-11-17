from langgraph.types import interrupt

from scrape_agent.state import GraphState


def review(state: GraphState) -> dict:
    approved = interrupt(
        {
            "sample_data": state.get("sample_data") or [],
            "scraper_config": state.get("scraper_config") or {},
        }
    )
    if approved:
        return {"user_approved": True}
    retry = int(state.get("retry_count") or 0) + 1
    return {"user_approved": False, "retry_count": retry}
