"""Atomic durable jobs and scoped conversation missions; no Telegram session material."""
import json
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .voice_common import STATE, CONFIG
from .database import connect

TASHKENT = ZoneInfo(CONFIG['timezone'])


def now():
    return datetime.now(TASHKENT)


def parse_at(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Use an ISO datetime including timezone, e.g. +05:00")
    return result.astimezone(TASHKENT)


class Store:
    def __init__(self, path=None):
        self.path = path or STATE / "scheduler.sqlite3"
        with connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS runtime_state(id INTEGER PRIMARY KEY CHECK(id=1),revision INTEGER NOT NULL,payload TEXT NOT NULL)")
            row=db.execute("SELECT revision,payload FROM runtime_state WHERE id=1").fetchone()
        self.revision=row['revision'] if row else 0
        legacy=STATE/'agent-state.json'
        self.data = json.loads(row['payload']) if row else json.loads(legacy.read_text()) if legacy.exists() else {
            "jobs": [], "missions": [], "paused": False, "owner_seen_id": 0}
        # Do not replay an ambiguous external action after a crash.
        for job in self.data["jobs"]:
            if job["status"] == "running":
                job["status"] = "interrupted"
        self.save()

    def save(self):
        with connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT revision FROM runtime_state WHERE id=1").fetchone()
            if row and row['revision'] != self.revision:
                raise RuntimeError('Another writer changed scheduler state; refusing to overwrite it')
            db.execute("INSERT OR REPLACE INTO runtime_state VALUES(1,?,?)",(self.revision+1,json.dumps(self.data,ensure_ascii=False)))
        self.revision+=1

    def schedule(self, kind, at, text="", repeat="once"):
        when = parse_at(at)
        if when <= now():
            raise ValueError("Scheduled time must be in the future")
        if kind not in {"call", "task", "message"} or repeat not in {"once", "daily", "weekly"}:
            raise ValueError("Unsupported job kind or repeat")
        if kind in {"task", "message"} and not text.strip():
            raise ValueError("Task/message text is required")
        job = {"id": uuid.uuid4().hex[:12], "kind": kind, "at": when.isoformat(),
               "text": text[:24000], "repeat": repeat, "status": "scheduled"}
        self.data["jobs"].append(job)
        self.save()
        return job

    def cancel(self, job_id):
        job = next((j for j in self.data["jobs"] if j["id"] == job_id), None)
        if not job or job["status"] != "scheduled":
            raise ValueError("Scheduled job not found")
        job["status"] = "cancelled"
        self.save()
        return job

    def finish(self, job, status, error=""):
        job.update(status=status, finished_at=now().isoformat(), error=error)
        if job["repeat"] != "once" and status in {"done", "missed"}:
            step = timedelta(days=1 if job["repeat"] == "daily" else 7)
            when = parse_at(job["at"])
            while when <= now():
                when += step
            job.update(at=when.isoformat(), status="scheduled", last_status=status)
        self.save()

    def watch(self, chat_id, goal, hours=24):
        if not goal.strip() or not 0 < hours <= 720:
            raise ValueError("A goal and duration of 1..720 hours are required")
        mission = {"id": uuid.uuid4().hex[:12], "chat_id": int(chat_id), "goal": goal[:16000],
                   "until": (now() + timedelta(hours=hours)).isoformat(), "status": "active",
                   "created_at": now().isoformat(), "seen_id": 0}
        # One active instruction per chat prevents contradictory automatic replies.
        for previous in self.data["missions"]:
            if previous["chat_id"] == chat_id and previous["status"] == "active":
                previous["status"] = "replaced"
        self.data["missions"].append(mission)
        self.save()
        return mission

    def unwatch(self, mission_id):
        mission = next((m for m in self.data["missions"] if m["id"] == mission_id), None)
        if not mission:
            raise ValueError("Mission not found")
        mission["status"] = "stopped"
        self.save()
        return mission

    def mission_for(self, chat_id):
        return next((m for m in reversed(self.data["missions"]) if m["chat_id"] == chat_id
                     and m["status"] == "active" and parse_at(m["until"]) > now()), None)
