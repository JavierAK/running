import argparse
import getpass

import garth

# Override HTTP headers to bypass Cloudflare 429 / bot detection
garth.client.sess.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get Garmin secret token for running_page"
    )
    parser.add_argument(
        "email", nargs="?", help="Email associated with your Garmin Connect account"
    )
    parser.add_argument(
        "password",
        nargs="?",
        help="Password associated with your Garmin Connect account",
    )
    parser.add_argument(
        "--is-cn",
        dest="is_cn",
        action="store_true",
        help="Set flag if your Garmin account is registered in China (garmin.cn)",
    )
    options = parser.parse_args()

    email = options.email or input("Garmin Email: ")
    password = options.password or getpass.getpass("Garmin Password: ")

    if options.is_cn:
        garth.configure(domain="garmin.cn", ssl_verify=False)

    # Prompt for 2FA/MFA code if Garmin requests verification
    try:

        garth.client.sess.headers.update({
         "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
            )
        })
        garth.login(
            email,
            password,
            prompt_mfa=lambda: input("Enter Garmin 2FA / Verification Code: "),
        )
    except TypeError:
        # Fallback for older Garth versions that don't support prompt_mfa parameter
        garth.login(email, password)

    secret_string = garth.client.dumps()
    print("\n--- GARMIN SECRET STRING START ---")
    print(secret_string)
    print("--- GARMIN SECRET STRING END ---\n")
