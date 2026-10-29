"""Command-line price forecast using the same model as the Flask dashboard."""

import argparse
import sys
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.models import get_price_forecast, predict_crop_price


def main():
    parser = argparse.ArgumentParser(description="Forecast illustrative Zimbabwe crop prices.")
    parser.add_argument("--month", type=int, default=date.today().month % 12 + 1, help="Forecast month (1-12)")
    parser.add_argument("--crop", choices=("tomatoes", "maize", "potatoes", "beans", "groundnuts", "onions", "cabbage"))
    args = parser.parse_args()
    if args.crop:
        print(f"{args.crop.title()} forecast for month {args.month}: US$ {predict_crop_price(args.crop, args.month):.2f}/kg")
        return
    for item in get_price_forecast(args.month):
        print(f"{item['crop']:<12} US$ {item['price']:.2f}/{item['unit']} (month {item['month']})")
    print("Note: forecasts use the bundled illustrative price dataset, not live Zimbabwe market quotes.")


if __name__ == "__main__":
    main()
