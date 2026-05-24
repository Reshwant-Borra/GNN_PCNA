"""
Wormhole Client — runs on Advay's machine.

Watches the bot's DM for messages containing a wormhole receive code.
When one arrives, opens a new terminal window and runs:
    wormhole receive <code>

The progress bar is native to wormhole — no extra work needed.

Setup (one-time):
    pip install telethon
    Get api_id + api_hash from https://my.telegram.org/apps
    Set env vars:
        TELEGRAM_API_ID=<id>
        TELEGRAM_API_HASH=<hash>
        WORMHOLE_BOT_USERNAME=<bot_username_without_@>

Run:
    python agents/wormhole_client.py
    (keep it running in the background; first run prompts Telegram login)
"""
from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Load from .wormhole_client.env if present
_env_file = REPO_ROOT / ".wormhole_client.env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

BOT_USERNAME      = os.environ.get("WORMHOLE_BOT_USERNAME", "")
TELEGRAM_API_ID   = os.environ.get("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "")

_CODE_RE = re.compile(r"wormhole receive\s+([0-9]+(?:-[a-z]+){2})", re.IGNORECASE)


RECEIVE_DIR = Path.home() / "wormhole_received"


def _open_terminal(cmd: str) -> None:
    RECEIVE_DIR.mkdir(exist_ok=True)
    system = platform.system()
    if system == "Windows":
        try:
            subprocess.Popen(["wt", "--", "cmd", "/k", f"cd /d \"{RECEIVE_DIR}\" && {cmd}"])
        except FileNotFoundError:
            subprocess.Popen(f'start cmd /k "cd /d "{RECEIVE_DIR}" && {cmd}"', shell=True)
    elif system == "Darwin":
        apple_script = f'tell application "Terminal" to do script "cd {RECEIVE_DIR} && {cmd}"'
        subprocess.Popen(["osascript", "-e", apple_script])
    else:
        for term in ("gnome-terminal", "x-terminal-emulator", "xterm", "konsole"):
            try:
                subprocess.Popen([term, "--", "bash", "-c", f"cd {RECEIVE_DIR} && {cmd}; exec bash"])
                return
            except FileNotFoundError:
                continue
        print(f"[wormhole_client] No terminal emulator found. Run manually:\n  {cmd}")


def _check_deps() -> None:
    missing = []
    if not TELEGRAM_API_ID:
        missing.append("TELEGRAM_API_ID")
    if not TELEGRAM_API_HASH:
        missing.append("TELEGRAM_API_HASH")
    if not BOT_USERNAME:
        missing.append("WORMHOLE_BOT_USERNAME")
    if missing:
        raise SystemExit(
            "[wormhole_client] Missing env vars: " + ", ".join(missing) + "\n"
            "  Get api_id + api_hash from https://my.telegram.org/apps\n"
            "  WORMHOLE_BOT_USERNAME is the bot's @username without the @"
        )
    try:
        import telethon  # noqa: F401
    except ImportError:
        raise SystemExit(
            "[wormhole_client] telethon not installed.\n"
            "  pip install telethon"
        )


def main() -> None:
    _check_deps()

    from telethon import TelegramClient, events

    session_path = REPO_ROOT / ".wormhole_client_session"
    client = TelegramClient(
        str(session_path),
        int(TELEGRAM_API_ID),
        TELEGRAM_API_HASH,
    )

    @client.on(events.NewMessage(from_users=BOT_USERNAME))
    async def _on_message(event):
        text = event.raw_text or ""
        m = _CODE_RE.search(text)
        if not m:
            return
        code = m.group(1)
        receive_cmd = f"wormhole receive {code}"
        print(f"[wormhole_client] Code received: {code} — opening terminal")
        _open_terminal(receive_cmd)

    print(f"[wormhole_client] Listening for wormhole codes from @{BOT_USERNAME} ...")
    print("[wormhole_client] First run will prompt for your Telegram phone number.")
    with client:
        client.run_until_disconnected()


if __name__ == "__main__":
    main()
