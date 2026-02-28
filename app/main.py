from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.db import get_conn, init_db
from app.schemas import (
    AnalyzeImageInput,
    AnalyzeImageOutput,
    CompetitorAnalysis,
    CompetitorRecord,
    CompetitorSynthesis,
    GeneratedPlan,
    MyProductInput,
    SimilaritySelection,
)
from app.services import (
    analyze_image,
    generate_plan,
    save_competitor,
    save_competitor_analysis,
    save_my_product,
    synthesize_competitors,
)

app = FastAPI(title="Memorial Listing Planner", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/competitors", status_code=201)
def create_or_update_competitor(payload: CompetitorRecord) -> dict[str, str]:
    save_competitor(payload)
    return {"status": "ok", "asin": payload.asin}


@app.post("/competitors/{asin}/analysis", status_code=201)
def upsert_competitor_analysis(asin: str, payload: CompetitorAnalysis) -> dict[str, str]:
    try:
        save_competitor_analysis(asin, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "asin": asin}


@app.post("/analyze/image", response_model=AnalyzeImageOutput)
def analyze_image_endpoint(payload: AnalyzeImageInput) -> AnalyzeImageOutput:
    return analyze_image(payload)


@app.post("/synthesis", response_model=CompetitorSynthesis)
def synthesis(payload: SimilaritySelection) -> CompetitorSynthesis:
    return synthesize_competitors(payload.selected_asins)


@app.post("/my-product", status_code=201)
def create_my_product(payload: MyProductInput) -> dict[str, int]:
    new_id = save_my_product(payload)
    return {"my_product_id": new_id}


@app.post("/generate/{my_product_id}", response_model=GeneratedPlan, status_code=201)
def generate(my_product_id: int, payload: SimilaritySelection) -> GeneratedPlan:
    with get_conn() as conn:
        exists = conn.execute("SELECT 1 FROM my_product WHERE id = ?", (my_product_id,)).fetchone()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Unknown my_product_id {my_product_id}")
    return generate_plan(my_product_id, payload.selected_asins)
