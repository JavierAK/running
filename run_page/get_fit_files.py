from pathlib import Path

from garminconnect import Garmin

EMAIL = "irving@bennett.com.pa"
PASSWORD = "DadQ!r5RDRx#8PjS"
MFA_CODE = "869888"  # Your active MFA code

OUTPUT_DIR = Path("FIT_OUT")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Logging into Garmin Connect...")

# Pass prompt_mfa callback to supply the token
client = Garmin(email=EMAIL, password=PASSWORD, prompt_mfa=lambda: MFA_CODE)

# Login will output/cache persistent session tokens in ~/.garminconnect/
client.login()

print("Login successful! Fetching recent activities...")
activities = client.get_activities(0, 50)

for activity in activities:
    activity_id = activity["activityId"]
    activity_name = activity.get("activityName", "Activity")
    start_time = activity.get("startTimeLocal", "")

    fit_path = OUTPUT_DIR / f"{activity_id}.fit"

    if fit_path.exists():
        print(f"Skipping {activity_id} ({activity_name}) - already downloaded.")
        continue

    print(
        f"Downloading FIT file for Activity {activity_id}: {activity_name} ({start_time})..."
    )
    try:
        fit_data = client.download_activity(
            activity_id, dl_fmt=Garmin.ActivityDownloadFormat.ORIGINAL
        )

        with open(fit_path, "wb") as f:
            f.write(fit_data)
        print(f"Saved: {fit_path}")
    except Exception as e:
        print(f"Failed to download {activity_id}: {e}")

print("\nAll activities downloaded to FIT_OUT!")
