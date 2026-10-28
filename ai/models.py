import math
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression


BASE_DIR = Path(__file__).resolve().parent


def _load_price_history():
    data = {
        "month": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "tomatoes": [3.8, 4.1, 4.5, 4.9, 5.3, 5.6, 5.8, 5.4, 5.2, 4.8, 4.4, 4.7],
        "maize": [2.6, 2.8, 3.1, 3.4, 3.7, 4.1, 4.4, 4.6, 4.2, 3.9, 3.7, 3.8],
        "potatoes": [2.9, 3.3, 3.5, 3.8, 4.1, 4.4, 4.7, 4.8, 4.5, 4.2, 4.0, 4.1],
        "beans": [3.1, 3.5, 3.8, 4.0, 4.3, 4.5, 4.7, 4.6, 4.2, 3.9, 3.7, 3.9],
    }
    return pd.DataFrame(data)


def train_price_model():
    history = _load_price_history()
    models = {}
    for crop in ["tomatoes", "maize", "potatoes", "beans"]:
        model = LinearRegression()
        X = history[["month"]]
        y = history[crop]
        model.fit(X, y)
        models[crop] = model
    return models


def predict_crop_price(crop_name, month=7):
    crop_key = crop_name.strip().lower()
    models = train_price_model()
    if crop_key not in models:
        raise ValueError(f"Unsupported crop: {crop_name}")
    value = models[crop_key].predict(pd.DataFrame({"month": [month]}))[0]
    return round(float(value), 2)


def get_price_forecast():
    history = _load_price_history()
    forecast = []
    for crop in ["tomatoes", "maize", "potatoes", "beans"]:
        model = LinearRegression()
        model.fit(history[["month"]], history[crop])
        next_month = len(history) + 1
        next_price = model.predict(pd.DataFrame({"month": [next_month]}))[0]
        forecast.append({"crop": crop.title(), "price": round(float(next_price), 2)})
    return forecast


def recommend_crops(weather, season, province):
    crop_profiles = {
        "maize": {"water": 1.0, "warm": 1.0, "summer": 1.2},
        "groundnuts": {"water": 0.8, "warm": 1.0, "summer": 1.1},
        "soybeans": {"water": 0.7, "warm": 0.9, "summer": 1.0},
        "tomatoes": {"water": 1.3, "warm": 1.2, "summer": 1.0},
        "beans": {"water": 0.9, "warm": 0.9, "summer": 0.9},
    }
    score = {}
    rainfall = float(weather.get("rainfall", 0) or 0)
    temperature = float(weather.get("temperature", 0) or 0)
    season_key = (season or "").strip().lower()
    province_key = (province or "").strip().lower()

    for crop, profile in crop_profiles.items():
        water_score = 1 if rainfall >= 40 else 0.5
        temp_score = 1 if 18 <= temperature <= 33 else 0.6
        season_score = profile.get(season_key, 1.0)
        province_bonus = 1.0 if province_key and province_key in {"harare", "bulawayo", "masvingo", "midlands", "manicaland", "matabeleland north", "matabeleland south"} else 0.9
        score[crop] = (water_score * 0.4 + temp_score * 0.3 + season_score * 0.3) * province_bonus

    ranked = sorted(score.items(), key=lambda item: item[1], reverse=True)
    top_three = [crop.title() for crop, _ in ranked[:3]]
    return top_three


def predict_demand_for_crop(crop_name, rainfall, season):
    rainfall_value = float(rainfall or 0)
    season_factor = {"summer": 1.2, "winter": 0.8, "autumn": 1.0, "spring": 1.1}.get((season or "").strip().lower(), 1.0)

    crop_factor = {
        "maize": 1.25,
        "tomatoes": 1.15,
        "beans": 1.0,
        "groundnuts": 1.1,
        "soybeans": 1.05,
    }.get((crop_name or "").strip().lower(), 1.0)

    score = max(0, min(100, (rainfall_value * 0.6 + 50) * crop_factor * season_factor))
    return round(score, 2)


def estimate_market_trend(listings):
    if not listings:
        return {"summary": "No market data available yet.", "trend": "stable", "average_price": 0.0}

    prices = [float(item.get("price", 0) or 0) for item in listings]
    avg_price = sum(prices) / len(prices)
    if avg_price >= 120:
        trend = "strong"
    elif avg_price >= 80:
        trend = "upward"
    elif avg_price >= 50:
        trend = "stable"
    else:
        trend = "soft"

    return {
        "summary": f"Average listed price is US$ {avg_price:.2f} across {len(listings)} active listings.",
        "trend": trend,
        "average_price": round(avg_price, 2),
    }
