from __future__ import annotations

import hashlib
import json
from typing import Any

from app.db import dumps_json, get_conn
from app.schemas import (
    AnalyzeImageInput,
    AnalyzeImageOutput,
    CompetitorAnalysis,
    CompetitorRecord,
    CompetitorSynthesis,
    GeneratedPlan,
    ImagePlan,
    ModulePlan,
    MyProductInput,
)


def _fake_embedding(text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [round(byte / 255, 4) for byte in digest[:16]]
    return dumps_json(values)


def save_competitor(record: CompetitorRecord) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO competitors (asin) VALUES (?) ON CONFLICT(asin) DO UPDATE SET updated_at=CURRENT_TIMESTAMP",
            (record.asin,),
        )
        competitor_id = conn.execute("SELECT id FROM competitors WHERE asin = ?", (record.asin,)).fetchone()["id"]

        conn.execute("DELETE FROM competitor_assets WHERE competitor_id = ?", (competitor_id,))
        conn.execute("DELETE FROM competitor_text WHERE competitor_id = ?", (competitor_id,))

        for image in record.inputs.images:
            conn.execute(
                "INSERT INTO competitor_assets (competitor_id, asset_type, module_index, blob_id) VALUES (?, ?, ?, ?)",
                (competitor_id, image.role, None, image.file_id),
            )
        for module in record.inputs.aplus_modules:
            conn.execute(
                "INSERT INTO competitor_assets (competitor_id, asset_type, module_index, blob_id) VALUES (?, ?, ?, ?)",
                (competitor_id, "aplus", module.module_index, module.image_file_id),
            )

        conn.execute(
            "INSERT INTO competitor_text (competitor_id, title_text, bullets_json, aplus_text_json) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(competitor_id) DO UPDATE SET title_text=excluded.title_text, bullets_json=excluded.bullets_json, aplus_text_json=excluded.aplus_text_json",
            (
                competitor_id,
                record.inputs.title,
                dumps_json(record.inputs.bullets),
                dumps_json([m.module_text for m in record.inputs.aplus_modules]),
            ),
        )

        if record.analysis:
            analysis_json = record.analysis.model_dump()
            embedding = _fake_embedding(json.dumps(analysis_json, sort_keys=True))
            conn.execute(
                "INSERT INTO competitor_analysis (competitor_id, analysis_json, embeddings) VALUES (?, ?, ?)"
                " ON CONFLICT(competitor_id) DO UPDATE SET analysis_json=excluded.analysis_json, embeddings=excluded.embeddings",
                (competitor_id, dumps_json(analysis_json), embedding),
            )


def save_competitor_analysis(asin: str, analysis: CompetitorAnalysis) -> None:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM competitors WHERE asin = ?", (asin,)).fetchone()
        if not row:
            raise ValueError(f"Unknown ASIN: {asin}")
        competitor_id = row["id"]
        embedding = _fake_embedding(analysis.model_dump_json())
        conn.execute(
            "INSERT INTO competitor_analysis (competitor_id, analysis_json, embeddings) VALUES (?, ?, ?)"
            " ON CONFLICT(competitor_id) DO UPDATE SET analysis_json=excluded.analysis_json, embeddings=excluded.embeddings",
            (competitor_id, analysis.model_dump_json(), embedding),
        )


def analyze_image(payload: AnalyzeImageInput) -> AnalyzeImageOutput:
    return AnalyzeImageOutput(
        file_id=payload.file_id,
        what_is_shown=payload.observed_elements,
        implied_claims=payload.implied_claims,
        overlay_copy_captured=payload.visible_overlay_copy,
        layout_template=payload.layout_template,
        typography_category_guess=payload.typography_category_guess,
        scene_tags=payload.scene_tags,
        style_tags=payload.style_tags,
    )


def save_my_product(payload: MyProductInput) -> int:
    with get_conn() as conn:
        cursor = conn.execute("INSERT INTO my_product DEFAULT VALUES")
        my_product_id = cursor.lastrowid
        for asset in payload.assets:
            conn.execute(
                "INSERT INTO my_product_assets (my_product_id, asset_type, file_id, text_description) VALUES (?, ?, ?, ?)",
                (my_product_id, asset.asset_type, asset.file_id, asset.text_description),
            )
        conn.execute(
            "INSERT INTO my_product_analysis (my_product_id, analysis_json) VALUES (?, ?)",
            (my_product_id, dumps_json({"notes": payload.notes})),
        )
        return int(my_product_id)


def synthesize_competitors(selected_asins: list[str]) -> CompetitorSynthesis:
    if not selected_asins:
        return CompetitorSynthesis(
            top_patterns=[],
            white_space_density_norms=[],
            typical_aplus_sequence=[],
            common_emotional_triggers=[],
            differentiation_gaps=[],
        )

    with get_conn() as conn:
        placeholders = ",".join("?" for _ in selected_asins)
        rows = conn.execute(
            f"SELECT ca.analysis_json FROM competitor_analysis ca JOIN competitors c ON c.id = ca.competitor_id WHERE c.asin IN ({placeholders})",
            tuple(selected_asins),
        ).fetchall()

    analyses = [json.loads(row["analysis_json"]) for row in rows]
    patterns = []
    triggers = []
    aplus_goals = []
    risks = []
    for analysis in analyses:
        patterns.extend(analysis.get("listing_copy", {}).get("title_patterns", []))
        triggers.extend([p.get("notes", "") for p in analysis.get("listing_copy", {}).get("bullet_patterns", [])])
        aplus_goals.extend([m.get("goal", "") for m in analysis.get("aplus_summary", [])])
        risks.extend(analysis.get("risks", []))

    return CompetitorSynthesis(
        top_patterns=sorted(set(patterns))[:10],
        white_space_density_norms=["mixed" if analyses else "unknown"],
        typical_aplus_sequence=[goal for goal in sorted(set(aplus_goals)) if goal],
        common_emotional_triggers=[trigger for trigger in sorted(set(triggers)) if trigger][:10],
        differentiation_gaps=[risk for risk in sorted(set(risks)) if risk][:10],
    )


def generate_plan(my_product_id: int, selected_asins: list[str]) -> GeneratedPlan:
    synthesis = synthesize_competitors(selected_asins)

    with get_conn() as conn:
        assets = conn.execute(
            "SELECT asset_type, file_id, text_description FROM my_product_assets WHERE my_product_id = ?",
            (my_product_id,),
        ).fetchall()

    by_type: dict[str, list[dict[str, Any]]] = {}
    for row in assets:
        by_type.setdefault(row["asset_type"], []).append(dict(row))

    image_plan = [
        ImagePlan(
            image_slot="main",
            selling_point="Deep memorial tone with premium chime detail",
            layout_template="hero_product_on_clean_background",
            overlay_copy_rules=["Minimal text", "No unsupported claim language"],
            typography_hierarchy=["H1 emotional hook", "H2 tangible feature"],
            scene_guidance="Use neutral backdrop or soft garden bokeh",
            props=["subtle floral accent"],
            people_guidance="No faces in main image",
            color_tone="black_gold_neutral",
        )
    ]

    if by_type.get("packaging"):
        image_plan.append(
            ImagePlan(
                image_slot="secondary_1",
                selling_point="Gift-ready packaging as conversion differentiator",
                layout_template="split_left_packaging_right_chime",
                overlay_copy_rules=["Short feature callouts", "Keep trust-oriented language"],
                typography_hierarchy=["H1 packaging benefit", "icons + microcopy"],
                scene_guidance="Lifestyle tabletop with clean light",
                props=["envelope", "gift_card"],
                people_guidance="Optional hands-only shot",
                color_tone="warm_neutral",
            )
        )

    aplus_plan = []
    for idx in range(1, 8):
        module_copy = ["" for _ in range(2)]
        # No-text-invention rule: leave copy empty when no explicit source text is provided.
        if by_type.get("product"):
            module_copy = ["Describe verifiable material or size", "Use grounded memorial positioning"]
        aplus_plan.append(
            ModulePlan(
                module_index=idx,
                objective="brand_story" if idx == 1 else "feature_education",
                layout="960x600_split" if idx % 2 == 0 else "960x600_full_bleed",
                copy_blocks=module_copy,
                suggested_headlines=["Memorial Wind Chime with Meaning"],
                micro_copy=["Avoid medical/guarantee claims"],
                imagery_guidance="Use only uploaded assets for this module type",
            )
        )

    return GeneratedPlan(
        optimized_title="Memorial Wind Chime for Sympathy Gift, Deep Tone Outdoor Hanging Chimes with Gift-Ready Presentation",
        bullet_points=[
            "Designed for remembrance moments with a calm, resonant tone.",
            "Balanced construction and finish focused on everyday display quality.",
            "Gift-friendly presentation supports thoughtful sympathy giving.",
            "Suitable for porch, garden, or memorial corner styling.",
            "Copy avoids unsupported claims and keeps trust-centered language.",
        ],
        image_plan=image_plan,
        aplus_plan=aplus_plan,
        differentiation_strategy={
            "copy_patterns_to_follow": synthesis.top_patterns,
            "avoid_patterns": ["cluttered overlays", "absolute guarantees"],
            "unique_angles": [
                "premium gift packaging",
                "memorial storytelling with restrained tone",
                "clean visual hierarchy",
            ],
        },
    )
