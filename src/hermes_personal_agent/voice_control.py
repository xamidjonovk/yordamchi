"""Authenticated local controls usable by Hermes without accessing session credentials."""
import argparse
import json
import sys
from pathlib import Path
from .voice_common import control


def main(argv=None):
    parser = argparse.ArgumentParser(description="Hermes personal Telegram account controls.")
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("status", "hangup", "jobs", "missions", "pause", "resume", "shutdown"):
        commands.add_parser(name)
    call = commands.add_parser("call")
    call.add_argument("--chat", help="Telegram username or user ID; omit to call the owner")
    call.add_argument("--purpose", default="", help="Owner-authorized purpose for the call")
    commands.add_parser('voice-provider').add_argument('provider', choices=['gemini', 'openai'])
    chats = commands.add_parser("chats")
    chats.add_argument("--query", default="")
    chats.add_argument("--limit", type=int, default=200)
    for name in ("history", "search"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--chat", required=name == "history")
        cmd.add_argument("--limit", type=int, default=50)
        cmd.add_argument("--offset-id", type=int, default=0)
        if name == "search":
            cmd.add_argument("--query", required=True)
    for name in ("send", "send-file", "send-voice"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--chat", required=True)
        text = cmd.add_mutually_exclusive_group(required=name in {"send", "send-voice"})
        text.add_argument("--text")
        text.add_argument("--text-file", help="UTF-8 file, or - for stdin")
        cmd.add_argument("--reply-to", type=int)
        if name == "send-file":
            cmd.add_argument("--path", required=True)
    download = commands.add_parser("download")
    download.add_argument("--chat", required=True)
    download.add_argument("--message-id", type=int, required=True)
    schedule = commands.add_parser("schedule")
    schedule.add_argument("--kind", choices=["call", "task", "message"], required=True)
    schedule.add_argument("--at", required=True, help="ISO datetime, e.g. 2026-11-03T09:00:00+05:00")
    schedule.add_argument("--repeat", choices=["once", "daily", "weekly"], default="once")
    text = schedule.add_mutually_exclusive_group()
    text.add_argument("--text", default="")
    text.add_argument("--text-file")
    for name in ("cancel", "unwatch"):
        commands.add_parser(name).add_argument("--id", required=True)
    watch = commands.add_parser("watch")
    watch.add_argument("--chat", required=True)
    watch.add_argument("--goal", required=True)
    watch.add_argument("--hours", type=float, default=24)
    data = vars(parser.parse_args(argv))
    action = data.pop("action")
    path = data.pop("text_file", None)
    if path:
        data["text"] = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8-sig")
    if action == "call" and data.get("chat"):
        return control("agent", {"op": "call", **data})
    if action in {"status", "call", "hangup", "shutdown"}:
        return control(action)
    return control("agent", {"op": action, **data})


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = main()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("ok") is False:
            raise SystemExit(1)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": type(error).__name__,
                          "detail": "Local operation failed; check service, arguments and files."}))
        raise SystemExit(1)
