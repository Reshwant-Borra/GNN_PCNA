"""
Telegram Remote Research Gateway — frontend for ResearchOS.

Approved collaborators send prompts via Telegram; the gateway parses them,
submits intents to agents/orchestrator.py (NEVER to Claude Code), subscribes
for orchestrator events, and pushes progress + final artifacts back to chat.

Risky / long-running intents land in an approval queue. The owner is DM'd
when a request needs sign-off and can /approve or /deny by task id.

Two ways to drive it:
  1. Free-form text — "train for 50 epochs", "bundle the repo", "what's pending?"
     Routed through agents/intent_parser.py (Gemma 3:4b via Ollama) → orchestrator.
  2. Slash commands — explicit, no LLM call. Use these for power-user / scripting.

Commands:
    /start                          Greet and confirm role
    /help                           Show available commands + intents (role-filtered)
    /status                         Orchestrator snapshot
    /pending                        Tasks awaiting owner approval
    /run <intent> [k=v ...]         Submit an intent explicitly (no LLM)
    /approve <task_id>              Owner: approve a pending task
    /deny <task_id> [reason]        Owner: deny a pending task
    /cancel <task_id>               Cancel one of your tasks (owner can cancel any)
    /get <task_id>                  Show a task's current state + artifacts
    /whoami                         Show your role + Telegram user id

Long-polling only (no webhook). Requires python-telegram-bot>=20.
NL parsing requires Ollama at localhost:11434 with gemma3:4b pulled; falls back
to a clear error message if Ollama is down so /run still works.

Usage:
    set TELEGRAM_BOT_TOKEN=<token>
    python agents/telegram_gateway.py --config configs/telegram_gateway.yaml
"""
from __future__ import annotations

import argparse
import asyncio
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.orchestrator import (  # noqa: E402
    INTENTS, Event, Orchestrator, Role, Task, TaskState,
)
from agents.intent_parser import parse as parse_intent  # noqa: E402


# ── Config ───────────────────────────────────────────────────────────────────

@dataclass
class UserEntry:
    telegram_id:  int
    username:     str
    role:         Role
    auto_approve: bool = False    # if True, risky/long tasks skip the approval queue


@dataclass
class GatewayConfig:
    bot_token:   str
    users:       dict[int, UserEntry]
    owner_ids:   list[int]
    poll_interval: float = 1.0


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit(
            "[telegram_gateway] PyYAML is required to load the whitelist.\n"
            "  pip install pyyaml"
        ) from exc
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"[telegram_gateway] config {path} must be a YAML mapping")
    return data


def load_config(path: Path) -> GatewayConfig:
    data = _load_yaml(path)
    token_env = data.get("bot_token_env", "TELEGRAM_BOT_TOKEN")
    token     = os.environ.get(token_env, "").strip()
    if not token:
        raise SystemExit(
            f"[telegram_gateway] bot token not set: env var {token_env} is empty.\n"
            f"  set {token_env}=<token>"
        )

    users: dict[int, UserEntry] = {}
    owner_ids: list[int] = []
    for entry in data.get("users", []):
        try:
            tg_id   = int(entry["telegram_id"])
            uname   = str(entry.get("username", "")).lstrip("@")
            role    = Role(str(entry["role"]).lower())
            auto_ok = bool(entry.get("auto_approve", False))
        except (KeyError, ValueError) as exc:
            raise SystemExit(f"[telegram_gateway] bad user entry {entry!r}: {exc}")
        users[tg_id] = UserEntry(tg_id, uname, role, auto_ok)
        if role == Role.OWNER:
            owner_ids.append(tg_id)

    if not users:
        raise SystemExit("[telegram_gateway] no users defined in config")
    if not owner_ids:
        raise SystemExit("[telegram_gateway] at least one owner must be defined")

    return GatewayConfig(
        bot_token=token,
        users=users,
        owner_ids=owner_ids,
        poll_interval=float(data.get("poll_interval", 1.0)),
    )


# ── Arg parsing ──────────────────────────────────────────────────────────────

def _parse_run_args(tokens: list[str]) -> dict[str, Any]:
    """k=v tokens → dict; bare flags → True. Repeated keys → list."""
    out: dict[str, Any] = {}
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
            k = k.strip(); v = v.strip()
            # try to coerce simple types
            try:
                if v.lower() in ("true", "false"):
                    parsed: Any = v.lower() == "true"
                elif "." in v:
                    parsed = float(v)
                else:
                    parsed = int(v)
            except ValueError:
                parsed = v
            if k in out:
                if not isinstance(out[k], list):
                    out[k] = [out[k]]
                out[k].append(parsed)
            else:
                out[k] = parsed
        else:
            out[tok] = True
    return out


def _fmt_intent_table(role: Role) -> str:
    rank = {Role.VIEWER: 0, Role.COLLABORATOR: 1, Role.OWNER: 2}
    lines = ["Available intents (visible to your role):"]
    for name, spec in INTENTS.items():
        if rank[role] < rank[spec.min_role]:
            continue
        flags = []
        if spec.risky:        flags.append("RISKY")
        if spec.long_running: flags.append("LONG")
        tag = f" [{'/'.join(flags)}]" if flags else ""
        lines.append(f"  {name}{tag} — {spec.description}")
    return "\n".join(lines)


def _fmt_task_short(t: Task) -> str:
    line = (f"task {t.task_id}  intent={t.intent}  state={t.state.value}  "
            f"user={t.user}  role={t.role.value}")
    if t.exit_code is not None:
        line += f"  exit={t.exit_code}"
    return line


def _fmt_task_full(t: Task) -> str:
    parts = [
        f"task_id: {t.task_id}",
        f"intent:  {t.intent}",
        f"user:    {t.user} ({t.role.value})",
        f"state:   {t.state.value}",
        f"created: {t.created_at}",
    ]
    if t.started_at:   parts.append(f"started:  {t.started_at}")
    if t.finished_at:  parts.append(f"finished: {t.finished_at}")
    if t.exit_code is not None:
        parts.append(f"exit:    {t.exit_code}")
    if t.note:
        parts.append(f"note:    {t.note}")
    if t.artifact_dir:
        parts.append(f"artifacts_dir: {t.artifact_dir}")
    if t.artifacts:
        parts.append("artifacts:")
        for a in t.artifacts:
            parts.append(f"  - {a}")
    return "\n".join(parts)


# ── Gateway ──────────────────────────────────────────────────────────────────

class TelegramGateway:
    def __init__(self, config: GatewayConfig, orchestrator: Orchestrator) -> None:
        self.cfg          = config
        self.orch         = orchestrator
        # task_id -> chat_ids subscribed to it
        self._subscribers: dict[str, set[int]] = {}
        # bot application (set in run())
        self._app = None

    # -- auth ---------------------------------------------------------------

    def _user(self, telegram_id: int) -> UserEntry | None:
        return self.cfg.users.get(telegram_id)

    # -- subscriptions ------------------------------------------------------

    def _subscribe_chat(self, task_id: str, chat_id: int) -> None:
        self._subscribers.setdefault(task_id, set()).add(chat_id)

    async def _event_pump(self) -> None:
        """Forward orchestrator events to subscribed chats."""
        q = self.orch.subscribe()
        try:
            while True:
                try:
                    ev: Event = await asyncio.to_thread(q.get, True, 1.0)
                except Exception:
                    continue
                await self._dispatch_event(ev)
        finally:
            self.orch.unsubscribe(q)

    async def _dispatch_event(self, ev: Event) -> None:
        if self._app is None:
            return

        # Owner notification for new approval requests
        if ev.kind == "approval_required":
            txt = (f"Approval required for task {ev.task_id}\n"
                   f"intent: {ev.payload.get('intent')}\n"
                   f"user:   {ev.payload.get('user')}\n"
                   f"reason: {ev.payload.get('reason')}\n\n"
                   f"/approve {ev.task_id}  |  /deny {ev.task_id} <reason>")
            for owner_id in self.cfg.owner_ids:
                try:
                    await self._app.bot.send_message(owner_id, txt)
                except Exception:
                    pass

        chats = self._subscribers.get(ev.task_id)
        if not chats:
            return

        if ev.kind == "log":
            line = ev.payload.get("line", "")
            if not line.strip():
                return
            text = f"[{ev.task_id}] {line[:3500]}"
        elif ev.kind == "started":
            text = f"[{ev.task_id}] STARTED  cmd: {ev.payload.get('cmd','')}"
        elif ev.kind == "approved":
            text = f"[{ev.task_id}] APPROVED by {ev.payload.get('approver')}"
        elif ev.kind == "denied":
            text = f"[{ev.task_id}] DENIED by {ev.payload.get('approver')}: {ev.payload.get('reason','')}"
        elif ev.kind == "cancelled":
            text = f"[{ev.task_id}] CANCELLED by {ev.payload.get('by')}"
        elif ev.kind == "finished":
            t        = self.orch.get(ev.task_id)
            arts     = "\n".join(f"  - {a}" for a in t.artifacts) or "  (none)"
            text     = (f"[{ev.task_id}] FINISHED  state={t.state.value}  "
                        f"exit={t.exit_code}\nartifacts:\n{arts}\nartifact_dir: {t.artifact_dir}")
        else:
            return

        for chat_id in list(chats):
            try:
                await self._app.bot.send_message(chat_id, text)
            except Exception:
                pass

    # -- command handlers ---------------------------------------------------

    async def _cmd_start(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text(
                "Unauthorized. Your Telegram user id is not on the whitelist.\n"
                f"Tell the owner your id: {update.effective_user.id}"
            )
            return
        await update.message.reply_text(
            f"Hi {u.username or u.telegram_id}. Role: {u.role.value}.\n"
            f"Use /help for commands."
        )

    async def _cmd_whoami(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text(
                f"Unauthorized. Your Telegram user id: {update.effective_user.id}"
            )
            return
        await update.message.reply_text(
            f"telegram_id: {u.telegram_id}\nusername: {u.username}\nrole: {u.role.value}"
        )

    async def _cmd_help(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text("Unauthorized."); return
        cmds = (
            "Just message me in plain English ('train for 50 epochs', 'bundle the repo').\n"
            "Or use slash commands:\n"
            "  /status, /pending, /get <task_id>, /whoami\n"
            "  /run <intent> [k=v ...]\n"
            "  /cancel <task_id>"
        )
        if u.role == Role.OWNER:
            cmds += "\n/approve <task_id>\n/deny <task_id> [reason]"
        await update.message.reply_text(
            f"Commands:\n{cmds}\n\n{_fmt_intent_table(u.role)}"
        )

    async def _cmd_status(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text("Unauthorized."); return
        snap = self.orch.status_snapshot()
        await update.message.reply_text(
            f"total={snap['total_tasks']}  pending={snap['pending_count']}  "
            f"running={snap['running_count']}\nby_state={snap['by_state']}\n"
            f"artifacts: {snap['artifact_root']}"
        )

    async def _cmd_pending(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text("Unauthorized."); return
        tasks = self.orch.pending()
        if not tasks:
            await update.message.reply_text("No tasks awaiting approval."); return
        await update.message.reply_text("\n".join(_fmt_task_short(t) for t in tasks))

    async def _cmd_get(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text("Unauthorized."); return
        args = ctx.args or []
        if not args:
            await update.message.reply_text("Usage: /get <task_id>"); return
        try:
            t = self.orch.get(args[0])
        except KeyError as exc:
            await update.message.reply_text(str(exc)); return
        await update.message.reply_text(_fmt_task_full(t))

    async def _cmd_run(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text("Unauthorized."); return
        raw = " ".join(ctx.args or [])
        if not raw:
            await update.message.reply_text("Usage: /run <intent> [k=v ...]"); return
        try:
            tokens = shlex.split(raw)
        except ValueError as exc:
            await update.message.reply_text(f"parse error: {exc}"); return
        intent = tokens[0]
        kwargs = _parse_run_args(tokens[1:])

        if intent not in INTENTS:
            await update.message.reply_text(
                f"unknown intent: {intent}\n\n{_fmt_intent_table(u.role)}"
            )
            return

        try:
            t = self.orch.submit(
                u.username or str(u.telegram_id),
                u.role, intent, kwargs,
                auto_approve=u.auto_approve,
            )
        except PermissionError as exc:
            await update.message.reply_text(f"denied: {exc}"); return
        except ValueError as exc:
            await update.message.reply_text(f"bad request: {exc}"); return

        self._subscribe_chat(t.task_id, update.effective_chat.id)

        if t.state == TaskState.AWAITING_APPROVAL:
            await update.message.reply_text(
                f"Submitted task {t.task_id} — awaiting owner approval (intent={intent})."
            )
        else:
            await update.message.reply_text(
                f"Submitted task {t.task_id} — running (intent={intent})."
            )

    async def _cmd_approve(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u or u.role != Role.OWNER:
            await update.message.reply_text("Owner only."); return
        if not ctx.args:
            await update.message.reply_text("Usage: /approve <task_id>"); return
        try:
            t = self.orch.approve(ctx.args[0], u.username or str(u.telegram_id), u.role)
        except (KeyError, RuntimeError, PermissionError) as exc:
            await update.message.reply_text(str(exc)); return
        self._subscribe_chat(t.task_id, update.effective_chat.id)
        await update.message.reply_text(f"Approved {t.task_id}; starting now.")

    async def _cmd_deny(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u or u.role != Role.OWNER:
            await update.message.reply_text("Owner only."); return
        if not ctx.args:
            await update.message.reply_text("Usage: /deny <task_id> [reason]"); return
        task_id = ctx.args[0]
        reason  = " ".join(ctx.args[1:]) if len(ctx.args) > 1 else ""
        try:
            t = self.orch.deny(task_id, u.username or str(u.telegram_id), u.role, reason)
        except (KeyError, RuntimeError, PermissionError) as exc:
            await update.message.reply_text(str(exc)); return
        await update.message.reply_text(f"Denied {t.task_id}.")

    async def _on_text(self, update, ctx):  # type: ignore[no-untyped-def]
        """Non-slash messages: route through the NL intent parser."""
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text("Unauthorized."); return
        text = (update.message.text or "").strip()
        if not text:
            return

        await update.message.reply_text("Thinking...")
        result = await asyncio.to_thread(parse_intent, text)

        if "error" in result:
            await update.message.reply_text(
                f"Couldn't parse that: {result['error']}\n"
                f"Try /run <intent> [k=v ...] or /help."
            )
            return
        if "clarify" in result:
            await update.message.reply_text(f"Clarify: {result['clarify']}")
            return

        intent = result["intent"]
        args   = result.get("args", {})
        arg_str = " ".join(f"{k}={v}" for k, v in args.items()) or "(no args)"
        await update.message.reply_text(
            f"Interpreted as: {intent} {arg_str}"
        )

        try:
            t = self.orch.submit(
                u.username or str(u.telegram_id),
                u.role, intent, args,
                auto_approve=u.auto_approve,
            )
        except PermissionError as exc:
            await update.message.reply_text(f"denied: {exc}"); return
        except ValueError as exc:
            await update.message.reply_text(f"bad request: {exc}"); return

        self._subscribe_chat(t.task_id, update.effective_chat.id)
        if t.state == TaskState.AWAITING_APPROVAL:
            await update.message.reply_text(
                f"task {t.task_id} — awaiting owner approval. "
                f"/approve {t.task_id} or /deny {t.task_id} <reason>"
            )
        else:
            await update.message.reply_text(
                f"task {t.task_id} — running."
            )

    async def _cmd_cancel(self, update, ctx):  # type: ignore[no-untyped-def]
        u = self._user(update.effective_user.id)
        if not u:
            await update.message.reply_text("Unauthorized."); return
        if not ctx.args:
            await update.message.reply_text("Usage: /cancel <task_id>"); return
        try:
            t = self.orch.cancel(ctx.args[0], u.username or str(u.telegram_id), u.role)
        except (KeyError, PermissionError) as exc:
            await update.message.reply_text(str(exc)); return
        await update.message.reply_text(f"Cancelled {t.task_id}.")

    # -- runtime ------------------------------------------------------------

    def run(self) -> None:
        try:
            from telegram.ext import (
                Application, CommandHandler, MessageHandler, filters,
            )
        except ImportError as exc:
            raise SystemExit(
                "[telegram_gateway] python-telegram-bot>=20 is required.\n"
                "  pip install 'python-telegram-bot>=20'"
            ) from exc

        app = Application.builder().token(self.cfg.bot_token).build()
        self._app = app

        app.add_handler(CommandHandler("start",    self._cmd_start))
        app.add_handler(CommandHandler("help",     self._cmd_help))
        app.add_handler(CommandHandler("whoami",   self._cmd_whoami))
        app.add_handler(CommandHandler("status",   self._cmd_status))
        app.add_handler(CommandHandler("pending",  self._cmd_pending))
        app.add_handler(CommandHandler("get",      self._cmd_get))
        app.add_handler(CommandHandler("run",      self._cmd_run))
        app.add_handler(CommandHandler("approve",  self._cmd_approve))
        app.add_handler(CommandHandler("deny",     self._cmd_deny))
        app.add_handler(CommandHandler("cancel",   self._cmd_cancel))
        # Any non-slash text → LLM intent parser → orchestrator
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_text))

        async def _post_init(_app):  # type: ignore[no-untyped-def]
            _app.create_task(self._event_pump())

        app.post_init = _post_init

        print(f"[telegram_gateway] running long-polling, "
              f"{len(self.cfg.users)} whitelisted users, "
              f"{len(self.cfg.owner_ids)} owner(s)")
        app.run_polling(poll_interval=self.cfg.poll_interval, drop_pending_updates=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Telegram Remote Research Gateway")
    p.add_argument("--config", type=Path,
                   default=REPO_ROOT / "configs" / "telegram_gateway.yaml",
                   help="Path to YAML whitelist + settings")
    args = p.parse_args()

    if not args.config.exists():
        raise SystemExit(f"[telegram_gateway] config not found: {args.config}")

    cfg  = load_config(args.config)
    orch = Orchestrator()
    gw   = TelegramGateway(cfg, orch)
    gw.run()


if __name__ == "__main__":
    main()
