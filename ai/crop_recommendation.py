"""Crop recommendations using the shared app model and CLI interface."""

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai.models import recommend_crops


def main():
    parser = argparse.ArgumentParser(description="Rank crops by illustrative weather suitability.")
    parser.add_argument("--rainfall", type=float, default=600, help="Expected seasonal rainfall in mm")
    parser.add_argument("--temperature", type=float, default=25, help="Average temperature in Celsius")
    parser.add_argument("--season", choices=("summer", "winter", "spring", "autumn"), default="summer")
    parser.add_argument("--province", default="Harare")
    args = parser.parse_args()
    results = recommend_crops(
        {"rainfall": args.rainfall, "temperature": args.temperature},
        args.season,
        args.province,
    )
    print(f"Top crop recommendations for {args.province} ({args.season}):")
    for result in results:
        print(f"- {result['crop']}: suitability score {result['score']:.1f}/100")
    print("Note: suitability is a decision-support estimate; verify locally with AGRITEX advice.")


if __name__ == "__main__":
    main()
