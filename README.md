# Egg Price Decision Agent for SMEs

**MADT7204: Vibe Coding Project** — agentic assistant for **bakeries and restaurants** navigating **egg price volatility**, using **Thai official egg series** and **oil / energy trends** as a **leading indicator** for timing purchases.

## Problem Statement

Egg prices are **volatile**: outbreaks, feed costs, seasonality, and regulation move wholesale and retail quotes quickly. For SMEs, **total landed cost** also depends on **distribution and trucking**, which are tied to **fuel and oil-linked energy markets**. When diesel and oil benchmarks rise, **transport surcharges and supplier passthrough** often appear **before** egg spot prices fully adjust, so **oil price trends** can act as an **early signal** for **buy now** vs **wait**.

This project is a **Python + LangChain** stack: tool-calling agent, CSV data under `data/raw/` (Thai Egg Price Base / DIT-aligned), optional web search for oil context, and a **Streamlit** UI with a **reasoning trace** sidebar.

## Agent design

- **Entry point:** `agent/main.py` — `DecisionAgent` runs a bounded LLM **tool-calling loop** (LangChain) with optional **`gpt-4o`** or **`gemini-1.5-pro`** (see `.env.example`).
- **Tools:** `agent/tools/` — **`egg_price_lookup`** reads `data/raw/egg_prices.csv`; **`oil_price_indicator`** uses Tavily when `TAVILY_API_KEY` is set, else a placeholder.
- **Prompts:** `agent/prompts/system.md` — SME advisor behavior and buy/wait framing.
- **UI:** `app/main.py` — Streamlit chat plus **Reasoning trace** sidebar.
- **Full technical design:** [docs/architecture.md](docs/architecture.md)

## Setup

1. **Python 3.10+** recommended.

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Environment file (never commit `.env`):

```bash
copy .env.example .env
```

Set **`OPENAI_API_KEY`** . Optional: **`TAVILY_API_KEY`** for live oil/energy search.

4. **CLI** (repo root):

```bash
python agent/main.py
```

5. **Streamlit** (repo root):

```bash
streamlit run app/main.py
```

## Data sources

Historical egg quotes are read from **`data/raw/egg_prices.csv`**.

| Source | Role |
|--------|------|
| **DIT pricelist** | Official Bangkok-area tables via **`exportexcel.php`** — see scraper below |
| **Thai Egg Price Base–style CSV** | Same official series mindset; columns should include at least **`date`**, **`price_thb_per_kg`** (see `agent/tools/price_lookup.py`) |

### Scraper (`data/scripts/scrape_dit_egg_prices.py`)

**GET** **`exportexcel.php`** on [pricelist.dit.go.th](https://pricelist.dit.go.th) (tabular export, not the full `main_price.php` page). Query dates use **Buddhist Era** `dd/mm/BBBB`; omit `--day1` / `--day2` for ~last **90 days**.

```bash
python data/scripts/scrape_dit_egg_prices.py -o data/raw/egg_prices.csv
python data/scripts/scrape_dit_egg_prices.py -o data/raw/egg_prices.csv --append
```

Wholesale example: `--protype 2 --progroup W11000 --product-id W11027`. Defaults: retail **`P11027`** (ไข่ไก่ เบอร์ 2). **`price_thb_per_kg`** is estimated from THB/egg using **`--egg-grams`** (default 58).

Other ingestion helpers: `data/scripts/fetch_sample_data.py`.

## Documentation

- **Architecture & buy/wait logic:** [docs/architecture.md](docs/architecture.md)
- **Pitch deck:** [docs/pitch-deck.pdf](docs/pitch-deck.pdf)

## Team

| Student ID | Name | Role |
|------------|------|------|
| 6810424021 | Notapat Dachanabhirom | IT Lead |
| 6810414002 | Nittakarn Ratapisanpong | Mgmt Member |
| 6810424006 | Apisit Rattanasangsan | Mgmt Member |
| 6810424007 | Chanwit Sangsri | Mgmt Member |
| 6810424013 | Narongrit Bureeruk | Mgmt Member |
| 6810424026 | Bhumin Thiewsungnoen | Mgmt Member |

