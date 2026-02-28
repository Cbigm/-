# Memorial Wind Chime Listing Planner (Codex-Friendly)

This app implements a strict two-phase workflow:

1. **Competitor ingestion + analysis** into a structured database.
2. **My-product ingestion + strategy generation** for title, bullets, images, and A+ modules.

## Why this is Codex-friendly

- Stable JSON schemas using Pydantic models.
- Explicit endpoint boundaries for ingestion, analysis, synthesis, and generation.
- Hard rules enforced in generation logic:
  - No unsupported claim language.
  - Do not assume missing assets exist.
  - Keep A+ module copy empty when no source text/assets support invention.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

## Endpoints

- `POST /competitors` — upsert competitor with ASIN, listing text, images, A+ modules.
- `POST /competitors/{asin}/analysis` — store normalized competitor analysis JSON.
- `POST /analyze/image` — image-level analysis normalization helper (JSON-in/JSON-out).
- `POST /synthesis` — cross-competitor synthesis for selected ASINs.
- `POST /my-product` — ingest own product assets/notes.
- `POST /generate/{my_product_id}` — generate full listing strategy.

## Database tables

Implemented tables match requested structure:

- `competitors`
- `competitor_assets`
- `competitor_text`
- `competitor_analysis` (+ simple embedding placeholder)
- `my_product`
- `my_product_assets`
- `my_product_analysis`
- `generated_plans`

## Schema mapping

Core competitor schema is represented in:

- `app/schemas.py::CompetitorRecord`
- `app/schemas.py::CompetitorAnalysis`

Generation output schema is represented in:

- `app/schemas.py::GeneratedPlan`

