import json
import os
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    load_dotenv()


def _masked_presence(name: str) -> str:
    value = os.getenv(name, "").strip()
    return "set" if value else "missing"


def _telegram_call(token: str, method: str) -> tuple[bool, str]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        with urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        return False, f"HTTP {exc.code}: {body}"
    except (URLError, TimeoutError) as exc:
        return False, str(exc)

    if payload.get("ok"):
        return True, json.dumps(payload.get("result", {}), ensure_ascii=False)
    return False, json.dumps(payload, ensure_ascii=False)[:300]


def _local_processes() -> list[str]:
    result = subprocess.run(
        ["ps", "ax", "-o", "pid=,command="],
        check=False,
        capture_output=True,
        text=True,
    )
    lines = []
    for line in result.stdout.splitlines():
        lowered = line.lower()
        if "bot.py" in lowered or "dosha-telegram-bot" in lowered:
            if "check_status.py" not in lowered:
                lines.append(line.strip())
    return lines


def main() -> int:
    _load_dotenv_if_available()

    print("Local process:")
    processes = _local_processes()
    if processes:
        for process in processes:
            print(f"  RUNNING: {process}")
    else:
        print("  NOT RUNNING")

    print("\nEnvironment:")
    for name in ("BOT_TOKEN", "REDIS_URL", "REDIS_PASSWORD", "RETENTION_HOURS"):
        print(f"  {name}: {_masked_presence(name)}")

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        print("\nTelegram:")
        print("  SKIPPED: BOT_TOKEN is missing")
        return 1

    ok, details = _telegram_call(token, "getMe")
    print("\nTelegram getMe:")
    print(f"  {'OK' if ok else 'ERROR'}: {details}")

    ok, details = _telegram_call(token, "getWebhookInfo")
    print("\nTelegram webhook:")
    print(f"  {'OK' if ok else 'ERROR'}: {details}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
