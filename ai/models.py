"""Shared, deterministic AI/ML services used by the app and command-line scripts.

Price regression is trained on the bundled illustrative Zimbabwe price series.
Demand and crop recommendations are transparent prototype scoring models, not
substitutes for field agronomy or verified wholesale-market data.
"""

import math
import csv
import os
import tempfile
from functools import lru_cache
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression


PRICE_HISTORY_PATH = Path(__file__).resolve().parent / "market_price_history.csv"
PRICE_CROPS = ("tomatoes", "maize", "potatoes", "beans", "groundnuts", "onions", "cabbage")


def _load_price_history():
    frame = pd.read_csv(PRICE_HISTORY_PATH)
    required = {"month", *PRICE_CROPS}
    if not required.issubset(frame.columns) or len(frame) < 12:
        raise ValueError("Market price history must contain 12 months and all supported crops.")
    if frame[list(required)].isnull().any().any():
        raise ValueError("Market price history contains missing values.")
    return frame


def load_price_history():
    """Return the editable seasonal training dataset as plain records."""
    return _load_price_history().to_dict(orient="records")


def save_price_history(records):
    """Validate, persist, and retrain price models from 12 monthly observations."""
    if len(records) != 12:
        raise ValueError("The training dataset must contain exactly 12 monthly rows.")

    normalized = []
    for expected_month, record in enumerate(records, start=1):
        try:
            month = int(record["month"])
            prices = {crop: float(record[crop]) for crop in PRICE_CROPS}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Each row must include a month and a numeric price for every crop.") from exc

        if month != expected_month:
            raise ValueError("Dataset months must be complete and ordered from 1 through 12.")
        if any(not math.isfinite(price) or price <= 0 for price in prices.values()):
            raise ValueError("Crop prices must be finite numbers greater than zero.")
        normalized.append({"month": month, **prices})

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            newline="",
            encoding="utf-8",
            dir=PRICE_HISTORY_PATH.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            writer = csv.DictWriter(temporary_file, fieldnames=["month", *PRICE_CROPS])
            writer.writeheader()
            writer.writerows(normalized)
        os.replace(temporary_path, PRICE_HISTORY_PATH)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    train_price_models.cache_clear()
    train_price_models()
    return normalized


def _month_features(month):
    month_value = int(month)
    if month_value < 1 or month_value > 12:
        raise ValueError("Month must be between 1 and 12.")
    return pd.DataFrame({"month_sin": [math.sin(2 * math.pi * month_value / 12)],
                         "month_cos": [math.cos(2 * math.pi * month_value / 12)]})


@lru_cache(maxsize=1)
def train_price_models():
    """Fit seasonal price models once from the bundled illustrative dataset."""
    history = _load_price_history()
    months = history["month"].astype(int).tolist()
    features = pd.DataFrame({
        "month_sin": [math.sin(2 * math.pi * month / 12) for month in months],
        "month_cos": [math.cos(2 * math.pi * month / 12) for month in months],
    })
    models = {}
    for crop in PRICE_CROPS:
        model = LinearRegression()
        model.fit(features, history[crop].astype(float))
        models[crop] = model
    return models


def predict_crop_price(crop_name, month=7):
    """Return an illustrative USD price per kg for a supported crop and month."""
    crop_key = str(crop_name).strip().lower()
    if crop_key not in PRICE_CROPS:
        raise ValueError(f"Unsupported crop: {crop_name}")
    value = train_price_models()[crop_key].predict(_month_features(month))[0]
    return round(max(0.0, float(value)), 2)


def get_price_forecast(month=None):
    """Forecast crop prices for the requested month (defaults to next month)."""
    if month is None:
        from datetime import date
        month = date.today().month % 12 + 1
    _month_features(month)
    return [
        {"crop": crop.title(), "price": predict_crop_price(crop, month), "unit": "kg", "month": int(month)}
        for crop in PRICE_CROPS
    ]


def recommend_crops(weather, season, province):
    """Rank crops using explainable rainfall, temperature, and season suitability."""
    try:
        rainfall = float(weather.get("rainfall", 0) or 0)
        temperature = float(weather.get("temperature", 0) or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Rainfall and temperature must be numeric.") from exc
    if not 0 <= rainfall <= 2000:
        raise ValueError("Rainfall must be between 0 and 2000 mm.")
    if not -10 <= temperature <= 60:
        raise ValueError("Temperature must be between -10 and 60 °C.")

    profiles = {
        "maize": {"rain_min": 400, "rain_opt": 650, "temp_min": 18, "temp_max": 32, "seasons": {"summer"}},
        "groundnuts": {"rain_min": 350, "rain_opt": 550, "temp_min": 20, "temp_max": 32, "seasons": {"summer"}},
        "soybeans": {"rain_min": 450, "rain_opt": 700, "temp_min": 20, "temp_max": 30, "seasons": {"summer"}},
        "sorghum": {"rain_min": 250, "rain_opt": 450, "temp_min": 20, "temp_max": 35, "seasons": {"summer"}},
        "beans": {"rain_min": 350, "rain_opt": 600, "temp_min": 16, "temp_max": 28, "seasons": {"summer", "winter"}},
        "tomatoes": {"rain_min": 300, "rain_opt": 500, "temp_min": 18, "temp_max": 30, "seasons": {"summer", "winter"}},
        "sugarcane": {"rain_min": 800, "rain_opt": 1200, "temp_min": 22, "temp_max": 35, "seasons": {"summer"}},
    }
    season_key = str(season or "").strip().lower()
    province_key = str(province or "").strip().lower()
    if season_key not in {"summer", "winter", "spring", "autumn"}:
        raise ValueError("Choose summer, winter, spring, or autumn.")

    rankings = []
    for crop, profile in profiles.items():
        rain_score = max(0.0, 1.0 - abs(rainfall - profile["rain_opt"]) / max(profile["rain_opt"], 1))
        temp_mid = (profile["temp_min"] + profile["temp_max"]) / 2
        temp_score = max(0.0, 1.0 - abs(temperature - temp_mid) / 20)
        season_score = 1.0 if season_key in profile["seasons"] else 0.65
        total = (rain_score * 0.5 + temp_score * 0.3 + season_score * 0.2) * 100
        if province_key and province_key not in {"harare", "bulawayo", "manicaland", "mashonaland central", "mashonaland east", "mashonaland west", "masvingo", "midlands", "matabeleland north", "matabeleland south"}:
            total *= 0.9
        rankings.append((crop.title(), round(total, 1)))
    return [{"crop": crop, "score": score} for crop, score in sorted(rankings, key=lambda row: row[1], reverse=True)[:3]]


_DEMAND_PRIORS = {
    "maize": 92, "tomatoes": 86, "potatoes": 82, "beans": 78,
    "groundnuts": 72, "onions": 76, "cabbage": 75, "soybeans": 68,
    "sorghum": 64, "sugarcane": 58, "compound d fertilizer": 78,
    "free-range eggs": 83, "broiler chickens": 84,
}
_SEASON_FACTORS = {"summer": 1.08, "winter": 0.96, "spring": 1.03, "autumn": 1.0}


def forecast_market_demand(db, season="summer"):
    """Use actual local listing and order aggregates to forecast demand."""
    records = db.execute(
        """
        SELECT l.crop, SUM(l.quantity) AS stock, COUNT(DISTINCT l.id) AS listing_count,
               COALESCE(SUM(o.order_count), 0) AS order_count,
               COALESCE(SUM(o.units_requested), 0) AS units_requested
        FROM listings AS l
        LEFT JOIN (
            SELECT listing_id, COUNT(*) AS order_count, SUM(quantity) AS units_requested
            FROM orders
            WHERE status IN ('pending', 'accepted')
            GROUP BY listing_id
        ) AS o ON o.listing_id = l.id
        WHERE l.status = 'active'
        GROUP BY LOWER(l.crop)
        ORDER BY LOWER(l.crop)
        """
    ).fetchall()
    return forecast_demand([dict(row) for row in records], season)


def forecast_demand(market_records, season="summer"):
    """Score available crops using listing, stock, and actual order request signals."""
    season_factor = _SEASON_FACTORS.get(str(season or "").strip().lower(), 1.0)
    forecasts = []
    for record in market_records:
        crop = str(record.get("crop", "")).strip()
        if not crop:
            continue
        key = crop.lower()
        aliases = (
            ("maize", "maize"), ("tomato", "tomatoes"), ("potato", "potatoes"),
            ("bean", "beans"), ("groundnut", "groundnuts"), ("onion", "onions"),
            ("cabbage", "cabbage"), ("compound d", "compound d fertilizer"),
            ("egg", "free-range eggs"), ("broiler", "broiler chickens"),
        )
        prior_key = next((canonical for token, canonical in aliases if token in key), key)
        prior = _DEMAND_PRIORS.get(prior_key, 60)
        orders = max(0, int(record.get("order_count", 0) or 0))
        units_requested = max(0, float(record.get("units_requested", 0) or 0))
        stock = max(0, float(record.get("stock", 0) or 0))
        listings = max(1, int(record.get("listing_count", 1) or 1))
        order_signal = min(20.0, orders * 2.0 + units_requested / max(stock, 1) * 30.0)
        supply_signal = min(12.0, stock / listings / 100.0)
        score = max(0.0, min(100.0, (prior + order_signal - supply_signal) * season_factor))
        forecasts.append({
            "crop": crop,
            "score": round(score, 1),
            "order_count": orders,
            "confidence": "medium" if orders else "low",
            "source": "market activity" if orders else "demo baseline; no orders recorded",
        })
    return sorted(forecasts, key=lambda item: (-item["score"], item["crop"].lower()))[:5]


def predict_demand_for_crop(crop_name, rainfall=0, season="summer"):
    """Compatibility helper for a single crop score with a rainfall adjustment."""
    try:
        rainfall_value = float(rainfall or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Rainfall must be numeric.") from exc
    if not 0 <= rainfall_value <= 2000:
        raise ValueError("Rainfall must be between 0 and 2000 mm.")
    result = forecast_demand([{"crop": crop_name}], season)
    if not result:
        return 0.0
    rainfall_factor = 0.95 + min(rainfall_value, 2000) / 2000 * 0.1
    return round(min(100.0, result[0]["score"] * rainfall_factor), 1)


def estimate_market_trend(listings):
    """Compare available produce with the illustrative previous-month price series."""
    relevant = [item for item in listings if str(item.get("category", "")).lower() not in {"inputs", "livestock"}]
    matched = [str(item.get("crop", "")).strip().lower() for item in relevant]
    crops = [crop for crop in PRICE_CROPS if any(crop in name for name in matched)]
    if not crops:
        crops = ["tomatoes", "maize", "potatoes", "beans"]
    from datetime import date
    month = date.today().month
    previous_month = month - 1 or 12
    history = _load_price_history().set_index("month")
    current_average = sum(float(history.loc[month, crop]) for crop in crops) / len(crops)
    previous_average = sum(float(history.loc[previous_month, crop]) for crop in crops) / len(crops)
    change = ((current_average - previous_average) / previous_average * 100) if previous_average else 0.0
    trend = "rising" if change > 2 else "falling" if change < -2 else "stable"
    return {
        "summary": f"Illustrative produce price index is {trend} {abs(change):.1f}% month-on-month.",
        "trend": trend,
        "average_price": round(current_average, 2),
        "change_percent": round(change, 1),
        "source": "bundled illustrative monthly price series",
    }
