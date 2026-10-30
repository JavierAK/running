"""Quick script to unzip any FIT files that are actually ZIP files."""

import zipfile
from pathlib import Path

gpx_dir = Path("FIT_OUT")
print()
for file_path in gpx_dir.glob("*.zip"):
    # Check if the file is secretly a zip file
    if zipfile.is_zipfile(file_path):
        print(f"Extracting ZIP payload inside: {file_path.name}")
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            # Extract contents to GPX_OUT
            zip_ref.extractall(gpx_dir)
        print(f"Done extracting {file_path.name}")
