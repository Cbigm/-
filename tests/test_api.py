from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_full_flow() -> None:
    competitor_payload = {
        "asin": "B0TEST1234",
        "inputs": {
            "title": "Memorial Wind Chime",
            "bullets": ["b1", "b2", "b3", "b4", "b5"],
            "images": [{"role": "main", "file_id": "img_1"}],
            "aplus_modules": [{"module_index": 1, "image_file_id": "ap_1", "module_text": ""}],
        },
    }
    response = client.post("/competitors", json=competitor_payload)
    assert response.status_code == 201

    analysis_payload = {
        "image_level": [
            {
                "file_id": "img_1",
                "selling_points": ["deep tone"],
                "overlay_copy": [{"text": "Memorial Gift", "position": "top_left", "style": "all_caps"}],
                "layout_template": "hero",
                "typography": {"headline_style": "sans", "weight": "bold", "hierarchy_notes": "clear"},
                "scene": {"location": "garden", "time": "day", "people": "none"},
                "style": {"tone": "premium", "background": "clean", "color_vibe": "neutral"},
            }
        ],
        "listing_copy": {
            "title_patterns": ["memorial gift"],
            "bullet_patterns": [{"type": "emotional_hook", "notes": "sympathy focus"}],
        },
        "aplus_summary": [{"module_index": 1, "goal": "brand_story", "notes": "intro"}],
        "overall_positioning": {
            "primary_angle": "healing",
            "secondary_angle": "gift",
            "price_tier_guess": "mid_high",
        },
        "risks": ["unsupported_claim_possible"],
    }

    response = client.post("/competitors/B0TEST1234/analysis", json=analysis_payload)
    assert response.status_code == 201

    product_payload = {
        "assets": [
            {"asset_type": "product", "file_id": "p1"},
            {"asset_type": "packaging", "text_description": "gift box"},
        ],
        "notes": "tone first",
    }
    response = client.post("/my-product", json=product_payload)
    assert response.status_code == 201
    product_id = response.json()["my_product_id"]

    response = client.post(f"/generate/{product_id}", json={"selected_asins": ["B0TEST1234"]})
    assert response.status_code == 201
    data = response.json()
    assert len(data["bullet_points"]) == 5
    assert data["aplus_plan"][0]["module_index"] == 1
