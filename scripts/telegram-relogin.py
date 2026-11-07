"""Renew Telegram authorization on the destination, without exporting credentials."""
import asyncio
import getpass
import os
import time
from pathlib import Path

from filelock import FileLock
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from hermes_personal_agent.voice_common import CONFIG, STATE, credentials


async def main():
    creds = credentials()
    candidate = STATE / ("telegram-relogin-" + str(time.time_ns()))
    client = TelegramClient(str(candidate), int(creds["api_id"]), creds["api_hash"],
                            device_model="Hermes Coolify", flood_sleep_threshold=0)
    verified = False
    await client.connect()
    try:
        phone = creds.get("phone") or getpass.getpass("Agent account phone: ")
        sent = await client.send_code_request(phone)
        print("AGENT TELEGRAM ACCOUNT: @" + CONFIG["agent_username"], flush=True)
        try:
            await client.sign_in(phone, code=getpass.getpass("Telegram code (hidden; do not send to chat): "),
                                 phone_code_hash=sent.phone_code_hash)
        except SessionPasswordNeededError:
            await client.sign_in(password=getpass.getpass("Telegram 2FA password (hidden): "))
        me = await client.get_me()
        if me.bot or me.id != CONFIG["agent_id"]:
            await client.log_out()
            raise RuntimeError("Wrong account; existing session was not replaced")
        verified = True
    finally:
        await client.disconnect()
    if verified:
        archive = STATE / ("revoked-session-" + str(time.time_ns()))
        archive.mkdir(mode=0o700)
        for suffix in (".session", ".session-journal", ".session-wal", ".session-shm"):
            old = STATE / ("telegram" + suffix)
            if old.exists():
                old.replace(archive / old.name)
        fresh = Path(str(candidate) + ".session")
        fresh.chmod(0o600)
        fresh.replace(STATE / "telegram.session")
        print("TELEGRAM_RELOGIN_OK", flush=True)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        with FileLock(str(STATE / "runtime.lock"), timeout=0):
            asyncio.run(main())
    except Exception as exc:
        print("RELOGIN_FAILED: " + type(exc).__name__, flush=True)
        raise SystemExit(1)
