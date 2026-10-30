import sys
from pathlib import Path

# Try importing the parser used by running_page
try:
    import fitparse
except ImportError:
    print("Installing fitparse...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "fitparse"])
    import fitparse

FIT_DIR = Path("GPX_OUT")  # Or FIT_OUT depending on where your files are stored

fit_files = list(FIT_DIR.glob("*.fit")) + list(FIT_DIR.glob("*.FIT"))

if not fit_files:
    print(f"No .fit files found in {FIT_DIR.resolve()}")
    sys.exit(0)

print(f"Checking {len(fit_files)} file(s) in {FIT_DIR}...\n")

for fit_path in fit_files[:5]:  # Inspect first 5 files
    print(f"--- File: {fit_path.name} ---")

    # 1. Check file size
    size = fit_path.stat().st_size
    print(f"File size: {size} bytes")

    # 2. Inspect first few bytes (Header check)
    with open(fit_path, "rb") as f:
        header_bytes = f.read(14)
        if (
            b"HTML" in header_bytes
            or b"doctype" in header_bytes.lower()
            or b"{" in header_bytes
        ):
            print("❌ ERROR: File is actually HTML/JSON text, not a binary FIT file!")
            continue

    # 3. Try decoding with fitparse
    try:
        fitfile = fitparse.FitFile(str(fit_path))
        messages = list(fitfile.get_messages())
        print(
            f"✅ FIT Header Valid. Decoded {len(messages)} data records successfully."
        )

        # Check for Session / Activity data
        sessions = [m for m in messages if m.name == "session"]
        if sessions:
            for s in sessions:
                data = s.as_dict()
                print(
                    f"   -> Sport: {data.get('sport')}, Distance: {data.get('total_distance')}m, Start: {data.get('start_time')}"
                )
        else:
            print("   ⚠️ Warning: File parsed but contains no 'session' message.")

    except Exception as e:
        print(f"❌ FIT Parse Failed: {type(e).__name__} - {e}")
    print()
