# Architecture — Egg Price Decision Agent

## Repository alignment

This codebase follows the course layout: **`agent/`** (entry + tools + prompts), **`app/`** (Streamlit UI), **`data/raw/`** and **`data/scripts/`**, **`docs/`** (`architecture.md`, `pitch-deck.pdf`), **`notebooks/`** (optional EDA), plus **`.env.example`**, **`.gitignore`**, and **`README.md`** at the repo root.

## Purpose

The agent helps bakeries and restaurants decide **when to buy eggs** under volatile prices by combining:

1. **Local egg price history** from **Thai Egg Price Base** (or compatible exports in CSV under `data/raw/`, surfaced via `egg_price_lookup`).
2. **Oil and energy trend context** (via `oil_price_indicator`, optionally backed by web search).

## High-level flow

1. The operator describes **inventory**, **usage**, and **constraints** in natural language (Streamlit chat or CLI).
2. A **system prompt** (`agent/prompts/system.md`) frames the assistant as an SME advisor and requires concise, actionable output.
3. The **LLM** (`gpt-4o` or `gemini-1.5-pro`, configured in `.env`) runs a **tool-calling loop** implemented in `DecisionAgent` (`agent/main.py`):
   - The model may call zero or more tools per turn until it returns a final answer without tool calls.
   - Each tool call and observation is recorded in a **reasoning trace** for transparency in the UI sidebar.

## Oil prices as a leading indicator

Egg prices move with **feed, flock, and regulatory** factors, but for many SMEs the **delivered cost** is strongly tied to **diesel and broader oil markets**: hauling feed, eggs, and processed goods is fuel-intensive. When **oil trends up** or stay elevated, distributors often pass through **freight surcharges** before spot egg quotes fully reflect the shock. The agent therefore treats **oil/energy direction** as an **early signal** of **incoming pressure on landed egg cost**, not as a perfect predictor.

**Buy now vs wait (conceptual):**

- **Buy now** may be suggested when recent **egg prices are rising** or volatile *and* **oil/energy indicators suggest continued transport cost pressure**, while the operation is **low on cover** relative to usage (stated by the user).
- **Wait** may be suggested when **egg prices are soft or stable** *and* **oil/energy pressure is easing**, assuming the user still has **enough days of cover** for their risk tolerance.

The model must still **ground** recommendations in tool outputs where possible; when search is not configured, the oil tool returns a **placeholder** and the agent should qualify uncertainty.

## Components

| Area | Role |
|------|------|
| `agent/main.py` | `DecisionAgent`: LLM + bounded tool loop + trace |
| `agent/tools/price_lookup.py` | Reads `data/raw/egg_prices.csv` (Thai Egg Price Base–aligned) |
| `agent/tools/oil_indicator.py` | Tavily-backed search when `TAVILY_API_KEY` is set; else placeholder |
| `app/main.py` | Streamlit chat UI and trace sidebar |
| `data/scripts/` | `scrape_dit_egg_prices.py` (DIT `exportexcel.php`), `fetch_sample_data.py` |
| `notebooks/` | Optional Jupyter EDA / prototyping |

## Course deliverables

- **`docs/pitch-deck.pdf`** (or **`docs/pitch-deck.pptx`**): final pitch deck for the project (repository includes a minimal PDF placeholder to satisfy path expectations).

## Extension points

- Run `data/scripts/scrape_dit_egg_prices.py` on a schedule (or manual refresh) to populate `data/raw/egg_prices.csv` via DIT **`exportexcel.php`** (tabular export from **[pricelist.dit.go.th](https://pricelist.dit.go.th)**).
- Add tools for **supplier quotes**, **contracts**, or **internal COGS** targets.
- Add evaluation harnesses (golden questions + expected tool usage) under `tests/` when you introduce CI.
