"""Oil / energy context as a leading indicator (search API or placeholder)."""

import os
from typing import Any, Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class OilIndicatorInput(BaseModel):
    query: str = Field(
        default="recent crude oil price trend and diesel fuel costs impact on food distribution",
        description="Search query for oil/energy trends relevant to egg logistics costs",
    )


def _tavily_search(query: str, max_results: int = 3) -> Optional[str]:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return None
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
    except ImportError:
        return None
    tool = TavilySearchResults(max_results=max_results, api_key=key)
    raw: Any = tool.invoke({"query": query})
    return str(raw)


class OilPriceIndicatorTool(BaseTool):
    name: str = "oil_price_indicator"
    description: str = (
        "Fetch a short summary of oil/energy price trends (proxy for transport and input cost "
        "pressure on eggs). Uses Tavily web search when TAVILY_API_KEY is set; otherwise returns "
        "a placeholder explaining configuration."
    )
    args_schema: type[BaseModel] = OilIndicatorInput

    def _run(self, query: str) -> str:
        hit = _tavily_search(query)
        if hit:
            return hit
        return (
            "[Placeholder] No live search configured. Set TAVILY_API_KEY in .env for oil/energy "
            "headlines. Qualitative note: sustained oil upshifts often precede or accompany "
            "higher delivered egg costs for SMEs relying on trucking."
        )
