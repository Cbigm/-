from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ImageRole = Literal["main", "secondary"]
AssetType = Literal["main", "secondary", "aplus"]
ProductAssetType = Literal["product", "packaging", "gift_card", "envelope", "accessories"]


class ImageInput(BaseModel):
    role: ImageRole
    file_id: str


class APlusModuleInput(BaseModel):
    module_index: int = Field(ge=1, le=7)
    image_file_id: str
    module_text: str = ""


class CompetitorInputs(BaseModel):
    title: str = ""
    bullets: list[str] = Field(default_factory=lambda: ["", "", "", "", ""], min_length=5, max_length=5)
    images: list[ImageInput] = Field(default_factory=list, max_length=8)
    aplus_modules: list[APlusModuleInput] = Field(default_factory=list, max_length=7)

    @model_validator(mode="after")
    def validate_main_image_count(self) -> "CompetitorInputs":
        main_count = len([image for image in self.images if image.role == "main"])
        if main_count > 1:
            raise ValueError("Only one main image is allowed.")
        return self


class OverlayCopy(BaseModel):
    text: str
    position: str
    style: str


class TypographyNotes(BaseModel):
    headline_style: str
    weight: str
    hierarchy_notes: str


class SceneNotes(BaseModel):
    location: str
    time: str
    people: str


class StyleNotes(BaseModel):
    tone: str
    background: str
    color_vibe: str


class ImageLevelAnalysis(BaseModel):
    file_id: str
    selling_points: list[str]
    overlay_copy: list[OverlayCopy]
    layout_template: str
    typography: TypographyNotes
    scene: SceneNotes
    style: StyleNotes


class BulletPattern(BaseModel):
    type: str
    notes: str


class ListingCopyAnalysis(BaseModel):
    title_patterns: list[str]
    bullet_patterns: list[BulletPattern]


class APlusSummary(BaseModel):
    module_index: int
    goal: str
    notes: str


class PositioningSummary(BaseModel):
    primary_angle: str
    secondary_angle: str
    price_tier_guess: str


class CompetitorAnalysis(BaseModel):
    image_level: list[ImageLevelAnalysis]
    listing_copy: ListingCopyAnalysis
    aplus_summary: list[APlusSummary]
    overall_positioning: PositioningSummary
    risks: list[str]


class CompetitorRecord(BaseModel):
    asin: str
    inputs: CompetitorInputs
    analysis: CompetitorAnalysis | None = None


class ProductAssetInput(BaseModel):
    asset_type: ProductAssetType
    file_id: str | None = None
    text_description: str | None = None


class MyProductInput(BaseModel):
    assets: list[ProductAssetInput] = Field(default_factory=list)
    notes: str = ""


class ImagePlan(BaseModel):
    image_slot: str
    selling_point: str
    layout_template: str
    overlay_copy_rules: list[str]
    typography_hierarchy: list[str]
    scene_guidance: str
    props: list[str]
    people_guidance: str
    color_tone: str


class ModulePlan(BaseModel):
    module_index: int
    objective: str
    layout: str
    copy_blocks: list[str]
    suggested_headlines: list[str]
    micro_copy: list[str]
    imagery_guidance: str


class DifferentiationPlan(BaseModel):
    copy_patterns_to_follow: list[str]
    avoid_patterns: list[str]
    unique_angles: list[str]


class GeneratedPlan(BaseModel):
    optimized_title: str
    bullet_points: list[str] = Field(min_length=5, max_length=5)
    image_plan: list[ImagePlan]
    aplus_plan: list[ModulePlan]
    differentiation_strategy: DifferentiationPlan


class GeneratedPlanRecord(BaseModel):
    id: int
    my_product_id: int
    created_at: datetime
    plan_json: GeneratedPlan


class SimilaritySelection(BaseModel):
    selected_asins: list[str] = Field(default_factory=list, max_length=15)


class CompetitorSynthesis(BaseModel):
    top_patterns: list[str]
    white_space_density_norms: list[str]
    typical_aplus_sequence: list[str]
    common_emotional_triggers: list[str]
    differentiation_gaps: list[str]


class AnalyzeImageInput(BaseModel):
    file_id: str
    observed_elements: list[str]
    visible_overlay_copy: list[str] = Field(default_factory=list)
    layout_template: str
    typography_category_guess: str
    scene_tags: list[str]
    style_tags: list[str]
    implied_claims: list[str]


class AnalyzeImageOutput(BaseModel):
    file_id: str
    what_is_shown: list[str]
    implied_claims: list[str]
    overlay_copy_captured: list[str]
    layout_template: str
    typography_category_guess: str
    scene_tags: list[str]
    style_tags: list[str]
