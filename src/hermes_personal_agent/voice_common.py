"""Portable instance paths and configuration, kept outside the source tree."""
import json
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_data_path

_default_home=(Path(os.environ['LOCALAPPDATA'])/'HermesPersonalAgent' if os.name=='nt' and os.environ.get('LOCALAPPDATA')
               else user_data_path("HermesPersonalAgent", appauthor=False))
APP_HOME = Path(os.environ.get("HPA_HOME") or _default_home).expanduser().resolve()
STATE = APP_HOME / "data"
ROOT = APP_HOME / "workspace"
for directory in (APP_HOME, STATE, ROOT):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
load_dotenv(APP_HOME / ".env")
DEFAULTS = {
    "owner_name": "Owner", "owner_username": "", "owner_id": None, "owner_style": "",
    "agent_username": "", "agent_id": None, "timezone": "Asia/Tashkent", "language": "uz",
    "introduction": "", "personal_context": "",
    "model": "gemini-3.8-live", "voice": "Rasalgethi", "transcription_model": "gemini-3.8-flash",
    "voice_provider": "gemini", "openai_live_model": "gpt-live-1", "openai_live_voice": "marin", "openai_env_file": "",
    "openai_live_max_minutes": 3,
    "tts_model": "gemini-3.8-flash-tts", "voice_note_replies": True,
    "control_port": 18796, "max_call_minutes": 30, "hermes_timeout_seconds": 300,
    "hermes_model": "gpt-6.1-terra", "hermes_provider": "openai-codex", "hermes_bin": "", "hermes_home": "",
    "inbox_enabled": False, "important_keywords": "muhim,shoshilinch,urgent,tezkor",
    "live_voice_enabled": True,
    "semantic_enabled": True,
    "embedding_model": "intfloat/multilingual-e5-small",
    "memory_context_chars": 10000, "session_max_turns": 20, "session_max_hours": 12,
    "learning_enabled": True, "learning_interval_seconds": 30, "learning_max_attempts": 3,
    "max_document_mb": 100, "max_document_chars": 2000000, "missed_call_grace_seconds": 300,
}
CONFIG_PATH = APP_HOME / "config.json"
CONFIG = {**DEFAULTS, **(json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {})}
_legacy_hermes = Path(os.environ.get("LOCALAPPDATA",Path.home()))/'hermes' if os.name=='nt' else Path.home()/'.hermes'
HERMES_HOME = Path(CONFIG['hermes_home'] or os.environ.get('HERMES_HOME') or
    (_legacy_hermes if CONFIG_PATH.exists() and 'setup_completed' not in json.loads(CONFIG_PATH.read_text(encoding='utf-8')) else APP_HOME/'hermes-profile')).expanduser().resolve()


def find_hermes():
    configured = os.environ.get("HERMES_BIN") or CONFIG["hermes_bin"]
    if configured:
        return Path(configured).expanduser().resolve()
    candidates = [str(HERMES_HOME / "bin" / ("hermes.exe" if os.name == "nt" else "hermes")), shutil.which("hermes"), str(_legacy_hermes / 'bin' / ('hermes.exe' if os.name=='nt' else 'hermes')),
                  str(Path.home() / ".local/bin/hermes")]
    return Path(next((c for c in candidates if c and Path(c).is_file()), configured or "hermes"))


HERMES = find_hermes()


def save_config(values):
    from filelock import FileLock
    import tempfile
    # A browser and Telegram service may save unrelated settings concurrently.
    with FileLock(str(CONFIG_PATH) + '.lock', timeout=10):
        disk = json.loads(CONFIG_PATH.read_text(encoding='utf-8')) if CONFIG_PATH.exists() else {'hermes_home':str(HERMES_HOME),'setup_completed':False}
        merged = {**DEFAULTS, **disk, **values}
        fd, name = tempfile.mkstemp(prefix='.config-', dir=CONFIG_PATH.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(merged, stream, ensure_ascii=False, indent=2)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(name, CONFIG_PATH)
        finally:
            if os.path.exists(name): os.unlink(name)
        CONFIG.update(merged)


def credentials():
    path = STATE / "telegram.json"
    if not path.exists():
        raise RuntimeError("Run hpa setup to connect your Telegram account.")
    return json.loads(path.read_text(encoding="utf-8"))


def telegram_client():
    from telethon import TelegramClient
    c = credentials()
    return TelegramClient(str(STATE / "telegram"), int(c["api_id"]), c["api_hash"],
        device_model="Hermes Personal Agent", system_version=os.name, app_version="0.5.1",
        flood_sleep_threshold=0)


def control(action="status", data=None):
    import urllib.request
    token = (STATE / "control-token").read_text(encoding="utf-8").strip()
    req = urllib.request.Request(f"http://127.0.0.1:{CONFIG['control_port']}/{action}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data is not None else None,
        method="GET" if action == "status" else "POST")
    timeout = 240 if action == "agent" and data and data.get("op") == "send-voice" else 45
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)
