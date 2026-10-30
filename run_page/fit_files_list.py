"""
Created on Mon Aug  3 16:31:50 2026

@author: irvin
"""

from pathlib import Path

# Adjust this path to wherever your backup FIT_OUT folder is located
# Example: Path("D:/running_page_backup/FIT_OUT") or Path("/mnt/c/Users/YourName/Desktop/FIT_OUT")
BACKUP_FIT_OUT = Path("FIT_OUT")
OUTPUT_TXT = Path("fit_files.txt")

if not BACKUP_FIT_OUT.exists():
    print(
        f"Error: Directory '{BACKUP_FIT_OUT}' not found. Please update BACKUP_FIT_OUT path."
    )
    exit(1)

# Find all .fit / .FIT files
fit_files = [f.name for f in BACKUP_FIT_OUT.iterdir() if f.suffix.lower() == ".fit"]

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.writelines(f"{filename}\n" for filename in fit_files)

print(
    f"Successfully recorded {len(fit_files)} file names into '{OUTPUT_TXT.resolve()}'"
)
