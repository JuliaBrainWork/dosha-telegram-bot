import os
import sys
from urllib.parse import quote

import requests
from dotenv import load_dotenv


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def main() -> int:
    load_dotenv()

    bot_token = _required_env("BOT_TOKEN")
    app_url = _required_env("VERCEL_URL").rstrip("/")
    webhook_secret = _required_env("WEBHOOK_SECRET")

    webhook_url = f"{app_url}/webhook/{quote(webhook_secret, safe='')}"
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/setWebhook",
        json={
            "url": webhook_url,
            "secret_token": webhook_secret,
            "drop_pending_updates": False,
        },
        timeout=20,
    )
    print(response.text)
    return 0 if response.ok and response.json().get("ok") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
