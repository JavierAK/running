import argparse
import json
import os

from config import JSON_FILE, SQL_FILE
from generator import Generator


def run_strava_sync(
    client_id,
    client_secret,
    refresh_token,
    sync_types: list | None = None,
    only_run=False,
    credentials_file=None,
):
    if sync_types is None:
        sync_types = []

    generator = Generator(SQL_FILE)
    generator.set_strava_config(
        client_id,
        client_secret,
        refresh_token,
        credentials_file=credentials_file,
    )

    if not only_run and len(sync_types) == 1 and sync_types[0] == "running":
        only_run = True

    generator.only_run = only_run
    generator.sync(False)

    activities_list = generator.load()
    with open(JSON_FILE, "w") as f:
        json.dump(activities_list, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client_id", nargs="?")
    parser.add_argument("client_secret", nargs="?")
    parser.add_argument("refresh_token", nargs="?")
    parser.add_argument(
        "--credentials-file",
        default=None,
        help="JSON file containing Strava credentials",
    )
    parser.add_argument("--only-run", dest="only_run", action="store_true")
    options = parser.parse_args()

    if options.credentials_file:
        if any((options.client_id, options.client_secret, options.refresh_token)):
            parser.error("Use --credentials-file or positional credentials, not both.")

        credentials_file = os.path.abspath(
            os.path.expanduser(options.credentials_file)
        )

        with open(credentials_file) as f:
            credentials = json.load(f)

        required = ("client_id", "client_secret", "refresh_token")
        if not all(credentials.get(key) for key in required):
            parser.error("The credentials file is missing required fields.")

        run_strava_sync(
            credentials["client_id"],
            credentials["client_secret"],
            credentials["refresh_token"],
            only_run=options.only_run,
            credentials_file=credentials_file,
        )
    else:
        if not all((options.client_id, options.client_secret, options.refresh_token)):
            parser.error(
                "Provide all three positional credentials or use --credentials-file."
            )

        run_strava_sync(
            options.client_id,
            options.client_secret,
            options.refresh_token,
            only_run=options.only_run,
        )
