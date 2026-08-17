#!/usr/bin/env python3
"""
live_type_demo.py - Live-types real GNN project code into the focused VS Code
editor at a human pace, as if someone were writing it by hand.

There is no "VS Code MCP" connected, so this drives the editor the robust way:
synthetic keystrokes (pynput) into whichever window is focused. To make the
typed text come out byte-clean it temporarily disables VS Code's autocomplete /
auto-closing / auto-indent, and RESTORES your settings.json on exit or abort.

Usage:
    python live_type_demo.py                 # 20 min, 8s countdown, fresh scratch file
    python live_type_demo.py --minutes 5     # shorter run
    python live_type_demo.py --target current  # type into the already-focused editor

Abort at any time:  press F12.
While running: keep the VS Code editor focused and don't touch the keyboard.
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time

from pynput.keyboard import Controller, Key, Listener

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Real GNN-PCNA source files to type, in a deliberate order (model training
# first, then agents / research-os internals). Paths are relative to REPO_ROOT.
CURATED = [
    "Desktop/GNN_PCNA/scripts/train_phase3.py",
    "Desktop/GNN_PCNA/scripts/run_baselines.py",
    "Desktop/GNN_PCNA/scripts/generate_labels.py",
    "Desktop/GNN_PCNA/scripts/sequence_clustering.py",
    "agents/orchestrator.py",
    "agents/ingest.py",
    "research_os/agents/science_evaluation.py",
    "research_os/memory/store.py",
    "paper_engine/figures/render.py",
    "research_os/__main__.py",
]

# Settings that make literal typing reproduce the source exactly.
PATCH = {
    "editor.quickSuggestions": False,
    "editor.suggestOnTriggerCharacters": False,
    "editor.acceptSuggestionOnEnter": "off",
    "editor.acceptSuggestionOnCommitCharacter": False,
    "editor.tabCompletion": "off",
    "editor.autoIndent": "none",
    "editor.autoClosingBrackets": "never",
    "editor.autoClosingQuotes": "never",
    "editor.autoSurround": "never",
    "editor.formatOnType": False,
    "editor.parameterHints.enabled": False,
}

ABORT = threading.Event()
kb = Controller()


# --------------------------------------------------------------------------- #
# settings.json patch / restore
# --------------------------------------------------------------------------- #
def find_settings():
    """Return (path, exists). Prefer an existing settings.json; otherwise return
    a creatable path inside an existing Code/User directory."""
    appdata = os.environ.get("APPDATA", "")
    candidates = []
    for folder in ("Code", "Code - Insiders"):
        user_dir = os.path.join(appdata, folder, "User")
        p = os.path.join(user_dir, "settings.json")
        if os.path.isfile(p):
            return p, True
        if os.path.isdir(user_dir):
            candidates.append(p)
    return (candidates[0], False) if candidates else (None, False)


def strip_jsonc(text):
    """Tolerant JSONC -> JSON: drop // and /* */ comments and trailing commas."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(^|[^:])//[^\n]*", lambda m: m.group(1), text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return text


def patch_settings():
    """Merge PATCH into settings.json. Returns (path, original_bytes, created)
    or None. `created` is True when we made the file (restore deletes it)."""
    path, exists = find_settings()
    if not path:
        print("  [settings] no Code/User dir found - skipping patch.")
        return None
    original = None
    data = {}
    if exists:
        try:
            original = open(path, "rb").read()
            data = json.loads(strip_jsonc(original.decode("utf-8-sig")) or "{}")
            if not isinstance(data, dict):
                raise ValueError("settings root is not an object")
        except Exception as e:  # noqa: BLE001
            print(f"  [settings] could not parse settings.json ({e}) - skipping.")
            return None
    data.update(PATCH)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    verb = "created" if not exists else "patched"
    print(f"  [settings] {verb} {path} (will restore on exit)")
    return (path, original, not exists)


def restore_settings(state):
    if not state:
        return
    path, original, created = state
    try:
        if created:
            os.remove(path)
            print(f"  [settings] removed {path} (restored to absent)")
        else:
            with open(path, "wb") as f:
                f.write(original)
            print(f"  [settings] restored {path}")
    except Exception as e:  # noqa: BLE001
        print(f"  [settings] WARNING: failed to restore {path}: {e}")


# --------------------------------------------------------------------------- #
# keystroke helpers
# --------------------------------------------------------------------------- #
def tap(key):
    kb.press(key)
    kb.release(key)


def newline():
    """Dismiss any popup, then go to a fresh clean line at column 0."""
    tap(Key.esc)          # close suggestion widget if any
    time.sleep(0.015)
    tap(Key.enter)
    time.sleep(0.015)
    # With autoIndent=none there is nothing to clear, but be defensive: select
    # any auto-inserted indent (Home, Shift+End) and forward-delete it. At the
    # end of the document an empty selection + Delete is a harmless no-op.
    tap(Key.home)
    tap(Key.home)
    with kb.pressed(Key.shift):
        tap(Key.end)
    tap(Key.delete)


def type_char(ch):
    try:
        kb.type(ch)
    except Exception:  # noqa: BLE001 - skip anything the backend can't emit
        pass


# --------------------------------------------------------------------------- #
# content
# --------------------------------------------------------------------------- #
def banner(rel):
    bar = "# " + "=" * 60
    return [bar, f"#  {rel}", bar, ""]


def gather_lines():
    """Yield (line) strings from curated files; fall back to a glob if needed."""
    files = [f for f in CURATED if os.path.isfile(os.path.join(REPO_ROOT, f))]
    if not files:
        for root, _, names in os.walk(REPO_ROOT):
            if os.sep + "." in root:
                continue
            for n in sorted(names):
                if n.endswith(".py"):
                    files.append(os.path.relpath(os.path.join(root, n), REPO_ROOT))
            if len(files) >= 15:
                break
    lines = []
    for rel in files:
        lines.extend(banner(rel))
        with open(os.path.join(REPO_ROOT, rel), encoding="utf-8", errors="replace") as f:
            for raw in f.read().splitlines():
                lines.append(raw.replace("\t", "    ").rstrip("\r"))
        lines.extend(["", "", ""])
    return lines


# --------------------------------------------------------------------------- #
# typing engine
# --------------------------------------------------------------------------- #
def type_line(line, base):
    for ch in line:
        if ABORT.is_set():
            return
        type_char(ch)
        d = random.uniform(base * 0.6, base * 1.8)
        if ch in ",;:)]}":
            d += random.uniform(0.02, 0.08)
        if ch == " ":
            d *= 0.6
        time.sleep(d)


def run(lines, duration, base):
    start = time.time()
    typed_lines = 0
    first = True
    idx = 0
    n = len(lines)
    while not ABORT.is_set():
        if time.time() - start >= duration:
            break
        line = lines[idx % n]
        if idx >= n and idx % n == 0:
            # wrapped around (extremely unlikely within the time budget)
            type_line("# --- (continuing) ---", base)
        if not first:
            newline()
        first = False
        type_line(line, base)
        typed_lines += 1
        idx += 1
        # pause between lines, longer after blank lines and block openers
        pause = random.uniform(0.12, 0.4)
        if line.strip() == "":
            pause += random.uniform(0.1, 0.3)
        if line.rstrip().endswith(":") or line.strip().startswith(("def ", "class ")):
            pause += random.uniform(0.1, 0.35)
        if random.random() < 0.04:
            pause += random.uniform(0.6, 1.6)  # occasional "thinking" pause
        time.sleep(pause)
    return typed_lines, time.time() - start


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def open_scratch(path):
    open(path, "w", encoding="utf-8").close()  # truncate to empty
    code = shutil.which("code") or shutil.which("code.cmd")
    if code:
        try:
            subprocess.run([code, "-r", path], check=False,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return True
        except Exception:  # noqa: BLE001
            pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=20.0)
    ap.add_argument("--countdown", type=int, default=8)
    ap.add_argument("--base-delay", type=float, default=0.07,
                    help="base per-character delay in seconds (~human speed)")
    ap.add_argument("--target", choices=["scratch", "current"], default="scratch",
                    help="scratch: open a fresh empty .py file (safe); "
                         "current: type into the already-focused editor")
    ap.add_argument("--scratch", default=os.path.join(REPO_ROOT, "scripts",
                                                      "_live_demo_scratch.py"))
    ap.add_argument("--no-patch", action="store_true",
                    help="do not touch settings.json (output may be messier)")
    args = ap.parse_args()

    duration = args.minutes * 60.0
    lines = gather_lines()
    print(f"[live-type] {len(lines)} source lines staged from GNN_PNCA "
          f"({duration/60:.0f} min budget, ~{1/args.base_delay:.0f} cps).")

    # F12 abort listener
    def on_press(key):
        if key == Key.f12:
            ABORT.set()
            print("\n[live-type] F12 -> aborting...")
            return False
    Listener(on_press=on_press).start()

    settings_state = None
    try:
        if not args.no_patch:
            settings_state = patch_settings()
            time.sleep(0.4)  # let VS Code hot-reload settings

        if args.target == "scratch":
            ok = open_scratch(args.scratch)
            print(f"  [target] {'opened' if ok else 'could NOT open via code CLI ->'} "
                  f"{args.scratch}")
            if not ok:
                print("  [target] will send Ctrl+N for a fresh buffer after countdown.")

        print(f"\n>>> Focus the VS Code editor now. Starting in {args.countdown}s "
              f"(F12 aborts)...")
        for i in range(args.countdown, 0, -1):
            if ABORT.is_set():
                break
            print(f"    {i}...", flush=True)
            time.sleep(1)

        if ABORT.is_set():
            print("[live-type] aborted before typing.")
            return

        if args.target == "scratch" and not shutil.which("code"):
            with kb.pressed(Key.ctrl):
                tap("n")
            time.sleep(0.5)

        typed, elapsed = run(lines, duration, args.base_delay)
        print(f"\n[live-type] done: {typed} lines over {elapsed/60:.1f} min "
              f"({'aborted' if ABORT.is_set() else 'time budget reached'}).")
    finally:
        restore_settings(settings_state)


if __name__ == "__main__":
    main()
