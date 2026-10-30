import json

# Path to your summary JSON file
with open("full_tracks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

summary = data.get("summary", {})

# Extract provinces where visited is True
visited_provinces = sorted(
    [
        province
        for province, details in summary.items()
        if isinstance(details, dict) and details.get("visited") is True
    ]
)

# Save the lean payload to public directory
output_data = {"visited": visited_provinces}

with open("public/visited-provinces.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(visited_provinces)} visited provinces: {visited_provinces}")
