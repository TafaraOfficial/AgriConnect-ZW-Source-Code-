"""Deterministic, repeatable marketplace data used for local demonstrations."""

LOCATIONS = ("Harare", "Gweru", "Mutare", "Masvingo", "Bulawayo")

# Crop/item, category, unit, base price in USD, available quantity, description.
PRODUCTS = (
    ("Maize grain", "cereals", "kg", 0.42, 850, "Clean, dry white maize grain from the 2026 harvest."),
    ("Fresh tomatoes", "vegetables", "kg", 0.95, 180, "Firm, ripe tomatoes packed in ventilated crates."),
    ("Table potatoes", "vegetables", "kg", 0.78, 260, "Washed medium-grade potatoes suitable for household and catering use."),
    ("Sugar beans", "legumes", "kg", 2.45, 120, "Sorted, dry sugar beans with minimal foreign matter."),
    ("Shelled groundnuts", "legumes", "kg", 2.10, 95, "Locally grown shelled groundnuts, packed for food use."),
    ("Fresh onions", "vegetables", "kg", 0.88, 210, "Cured brown onions with good storage quality."),
    ("Green cabbage", "vegetables", "head", 0.55, 240, "Fresh field-grown cabbage, sold by the head."),
    ("Free-range eggs", "livestock", "dozen", 2.80, 75, "Farm-fresh medium eggs, carefully packed by the dozen."),
    ("Broiler chickens", "livestock", "bird", 5.50, 42, "Healthy dressed broiler chickens, sold individually."),
    ("Compound D fertilizer", "inputs", "50 kg bag", 34.00, 36, "Compound D basal fertilizer, sealed 50 kg bags. Check packaging on collection."),
)

LOCATION_FACTORS = {
    "Harare": 1.08,
    "Gweru": 0.98,
    "Mutare": 1.02,
    "Masvingo": 0.94,
    "Bulawayo": 1.05,
}


def iter_demo_products():
    """Yield 50 stable product listings (10 items in each of 5 markets)."""
    for item_index, (name, category, unit, base_price, stock, description) in enumerate(PRODUCTS):
        for location_index, location in enumerate(LOCATIONS):
            yield {
                "key": f"demo-{item_index + 1:02d}-{location_index + 1:02d}",
                "title": f"{name} - {location}",
                "crop": name,
                "category": category,
                "description": description,
                "quantity": stock + location_index * 7,
                "unit": unit,
                "price": round(base_price * LOCATION_FACTORS[location], 2),
                "location": location,
                "seller_index": 2 if category == "inputs" else location_index % 2,
            }
