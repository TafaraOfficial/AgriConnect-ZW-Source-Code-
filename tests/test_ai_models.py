import pytest

from ai.models import (
    estimate_market_trend,
    forecast_demand,
    get_price_forecast,
    predict_crop_price,
    recommend_crops,
)


def test_price_forecast_covers_supported_crops_and_wraps_month():
    forecast = get_price_forecast(12)
    assert len(forecast) == 7
    assert {item["crop"] for item in forecast} == {
        "Tomatoes", "Maize", "Potatoes", "Beans", "Groundnuts", "Onions", "Cabbage"
    }
    assert all(item["month"] == 12 and item["price"] > 0 for item in forecast)


def test_price_prediction_rejects_unknown_crop_and_month():
    with pytest.raises(ValueError, match="Unsupported crop"):
        predict_crop_price("cassava", 7)
    with pytest.raises(ValueError, match="Month"):
        predict_crop_price("maize", 13)


def test_crop_recommendations_rank_with_scores_and_validate_weather():
    recommendations = recommend_crops(
        {"rainfall": 600, "temperature": 25}, "summer", "Harare"
    )
    assert len(recommendations) == 3
    assert recommendations == sorted(recommendations, key=lambda item: item["score"], reverse=True)
    assert all(0 <= item["score"] <= 100 for item in recommendations)
    with pytest.raises(ValueError, match="Rainfall"):
        recommend_crops({"rainfall": -1, "temperature": 25}, "summer", "Harare")


def test_demand_forecast_uses_order_and_stock_signals():
    forecasts = forecast_demand(
        [
            {"crop": "Maize", "stock": 100, "listing_count": 1, "order_count": 3, "units_requested": 50},
            {"crop": "Beans", "stock": 500, "listing_count": 5, "order_count": 0, "units_requested": 0},
        ],
        "summer",
    )
    assert forecasts[0]["crop"] == "Maize"
    assert forecasts[0]["confidence"] == "medium"
    assert forecasts[1]["confidence"] == "low"


def test_market_trend_is_labeled_illustrative():
    result = estimate_market_trend([{"crop": "maize", "category": "cereals"}])
    assert result["trend"] in {"rising", "falling", "stable"}
    assert "illustrative" in result["summary"].lower()
