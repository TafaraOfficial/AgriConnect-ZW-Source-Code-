from ai.models import estimate_market_trend, get_price_forecast, predict_crop_price, recommend_crops


def test_price_forecast_has_crops():
    forecast = get_price_forecast()
    assert len(forecast) == 4
    assert {item["crop"] for item in forecast} == {"Tomatoes", "Maize", "Potatoes", "Beans"}


def test_crop_recommendation_produces_results():
    recommendations = recommend_crops({"rainfall": 100, "temperature": 30}, "summer", "harare")
    assert len(recommendations) == 3
    assert isinstance(recommendations, list)


def test_price_prediction_returns_value():
    value = predict_crop_price("maize", month=7)
    assert isinstance(value, float)
    assert value > 0


def test_market_trend_estimation():
    trend = estimate_market_trend([
        {"price": 120},
        {"price": 100},
        {"price": 90},
    ])
    assert trend["trend"] in {"stable", "upward", "strong", "soft"}
