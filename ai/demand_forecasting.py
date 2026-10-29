"""Market activity demand forecasts shared with the Flask dashboard."""

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.models import forecast_market_demand
from app import create_app
from app.models import get_db


def main():
    parser = argparse.ArgumentParser(description="Forecast demand from local marketplace activity.")
    parser.add_argument("--season", choices=("summer", "winter", "spring", "autumn"), default="summer")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        forecasts = forecast_market_demand(get_db(), args.season)
    print(json.dumps(forecasts, indent=2))
    print("Scores are prototype estimates; they are not verified Zimbabwe-wide market statistics.")


if __name__ == "__main__":
    main()
