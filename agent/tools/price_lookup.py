"""Local egg price history from CSV (sourced from Thai Egg Price Base–style exports)."""

from pathlib import Path

import pandas as pd
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# Primary column from Thai Egg Price Base–aligned feeds; legacy USD column still supported.
_PRICE_COLUMNS = ("price_thb_per_kg", "price_usd_per_dozen")


def _primary_price_column(df: pd.DataFrame) -> str | None:
    for col in _PRICE_COLUMNS:
        if col in df.columns:
            return col
    return None


class PriceLookupInput(BaseModel):
    last_n_weeks: int = Field(
        default=8,
        ge=1,
        le=104,
        description="How many most recent rows to summarize from egg_prices.csv",
    )


class PriceLookupTool(BaseTool):
    name: str = "egg_price_lookup"
    description: str = (
        "Read recent benchmark egg prices from Thailand's egg price reference data "
        "(exported to data/raw/egg_prices.csv, typically from Thai Egg Price Base). "
        "Use before advising buy/wait timing."
    )
    args_schema: type[BaseModel] = PriceLookupInput

    def _run(self, last_n_weeks: int = 8) -> str:
        path = _repo_root() / "data" / "raw" / "egg_prices.csv"
        if not path.exists():
            return f"No egg price file at {path}. Add data/raw/egg_prices.csv."
        df = pd.read_csv(path)
        if df.empty:
            return "egg_prices.csv is empty."
        if "date" in df.columns:
            df = df.sort_values("date")
        tail = df.tail(last_n_weeks)
        col = _primary_price_column(tail)
        if col:
            latest = float(tail[col].iloc[-1])
            earliest = float(tail[col].iloc[0])
            trend = "up" if latest > earliest else "down" if latest < earliest else "flat"
            src = tail["source"].iloc[-1] if "source" in tail.columns else "unknown"
            return (
                f"Source={src}. Rows={len(tail)}. Latest {col}={latest:.2f} vs "
                f"start of window={earliest:.2f} (trend: {trend}).\n{tail.to_csv(index=False)}"
            )
        return tail.to_csv(index=False)
