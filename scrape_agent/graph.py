from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from scrape_agent.nodes.full_scrape import full_scrape
from scrape_agent.nodes.parse_intent import parse_intent
from scrape_agent.nodes.propose_config import propose_config
from scrape_agent.nodes.review import review
from scrape_agent.nodes.sample_scrape import sample_scrape
from scrape_agent.state import GraphState


def _route_review(state: GraphState) -> Literal["full_scrape", "propose_config"]:
    if state.get("user_approved"):
        return "full_scrape"
    return "propose_config"


def build_graph():
    builder = StateGraph(GraphState)
    builder.add_node("parse_intent", parse_intent)
    builder.add_node("propose_config", propose_config)
    builder.add_node("sample_scrape", sample_scrape)
    builder.add_node("review", review)
    builder.add_node("full_scrape", full_scrape)

    builder.add_edge(START, "parse_intent")
    builder.add_edge("parse_intent", "propose_config")
    builder.add_edge("propose_config", "sample_scrape")
    builder.add_edge("sample_scrape", "review")
    builder.add_conditional_edges(
        "review",
        _route_review,
        {"full_scrape": "full_scrape", "propose_config": "propose_config"},
    )
    builder.add_edge("full_scrape", END)
    return builder.compile(checkpointer=MemorySaver())
