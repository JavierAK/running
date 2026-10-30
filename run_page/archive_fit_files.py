import shutil
from pathlib import Path

# Base paths inside WSL
HOME = Path.home()
RUNNING_PAGE_DIR = HOME / "running_page"

SRC_FIT_OUT = RUNNING_PAGE_DIR / "FIT_OUT"
TARGET_FIT_DONE = RUNNING_PAGE_DIR / "FIT_DONE"
LIST_FILE = RUNNING_PAGE_DIR / "run_page" / "fit_files.txt"

# Ensure target directory exists
TARGET_FIT_DONE.mkdir(parents=True, exist_ok=True)


def archive_from_list():
    if not LIST_FILE.exists():
        print(f"Error: List file '{LIST_FILE}' not found.")
        return

    if not SRC_FIT_OUT.exists():
        print(f"Error: Source directory '{SRC_FIT_OUT}' does not exist.")
        return

    # Read processed file names from txt file
    with open(LIST_FILE, "r", encoding="utf-8") as f:
        processed_filenames = set(line.strip() for line in f if line.strip())

    print(f"Loaded {len(processed_filenames)} target filenames from {LIST_FILE.name}")

    moved_count = 0
    missing_count = 0

    # Scan active FIT_OUT for matches
    for filename in processed_filenames:
        src_file = SRC_FIT_OUT / filename

        # Check case-insensitively if exact filename isn't matched
        if not src_file.exists():
            alt_src = (
                SRC_FIT_OUT / filename.upper()
                if filename.islower()
                else SRC_FIT_OUT / filename.lower()
            )
            if alt_src.exists():
                src_file = alt_src

        if src_file.exists():
            dest_file = TARGET_FIT_DONE / src_file.name

            # Move file to FIT_DONE
            if not dest_file.exists():
                shutil.move(str(src_file), str(dest_file))
            else:
                # If already present in FIT_DONE, remove duplicate from FIT_OUT
                src_file.unlink()

            moved_count += 1
        else:
            missing_count += 1

    print("\n==================================================")
    print("Archive Summary:")
    print(f"-> Successfully moved to FIT_DONE: {moved_count}")
    print(f"-> Not found in FIT_OUT (skipped): {missing_count}")
    print(f"-> Remaining in FIT_OUT: {len(list(SRC_FIT_OUT.glob('*.fit')))}")
    print("==================================================")


if __name__ == "__main__":
    archive_from_list()
