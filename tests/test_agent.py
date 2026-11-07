import asyncio
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from contextlib import asynccontextmanager

from hermes_personal_agent.agent_store import Store, now, parse_at
from hermes_personal_agent.telegram_agent import TelegramAgent
from hermes_personal_agent.voice_notes import speech_chunks


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "state.json"
        self.store = Store(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_schedule_survives_restart_and_cancel(self):
        when = (now() + timedelta(hours=1)).isoformat()
        job = self.store.schedule("call", when, "test")
        restored = Store(self.path)
        self.assertEqual(restored.data["jobs"][0]["id"], job["id"])
        restored.cancel(job["id"])
        self.assertEqual(Store(self.path).data["jobs"][0]["status"], "cancelled")
        self.assertEqual(parse_at(when).utcoffset(), timedelta(hours=5))

    def test_running_external_action_is_not_replayed(self):
        job = self.store.schedule("message", (now() + timedelta(hours=1)).isoformat(), "hello")
        job["status"] = "running"
        self.store.save()
        self.assertEqual(Store(self.path).data["jobs"][0]["status"], "interrupted")

    def test_repeat_advances_and_naive_time_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.schedule("call", "2028-01-01T09:00:00")
        job = self.store.schedule("call", (now() + timedelta(hours=1)).isoformat(), repeat="daily")
        previous = parse_at(job["at"])
        job["at"] = (previous - timedelta(days=2)).isoformat()
        self.store.finish(job, "done")
        self.assertEqual(job["status"], "scheduled")
        self.assertGreater(parse_at(job["at"]), now())

    def test_only_one_live_goal_per_chat(self):
        first = self.store.watch(-123, "first")
        second = self.store.watch(-123, "second")
        self.assertEqual(first["status"], "replaced")
        self.assertIs(self.store.mission_for(-123), second)
        self.store.unwatch(second["id"])
        self.assertIsNone(self.store.mission_for(-123))


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.directory.name) / "state.json")
        self.client = SimpleNamespace(send_message=AsyncMock(), get_input_entity=AsyncMock(return_value="peer"))
        self.service = SimpleNamespace(client=self.client, owner_id=111, status=lambda: {"call": "idle"})
        self.agent = TelegramAgent(self.service, store=self.store)
        self.agent.notify = AsyncMock()

    async def asyncTearDown(self):
        await self.agent.close()
        self.directory.cleanup()

    def event(self, sender=111, chat=111, message_id=10):
        message = SimpleNamespace(id=message_id, date=now(), raw_text="topshiriq", media=None)
        return SimpleNamespace(is_private=chat > 0, sender_id=sender, chat_id=chat,
                               id=message_id, raw_text=message.raw_text, message=message)

    async def test_other_people_cannot_create_owner_tasks(self):
        await self.agent.on_message(self.event(sender=222, chat=222))
        self.assertTrue(self.agent.queue.empty())
        self.agent.notify.assert_not_awaited()

    async def test_owner_message_queued_once(self):
        event = self.event()
        await self.agent.on_message(event)
        await self.agent.on_message(event)
        self.assertEqual(self.agent.queue.qsize(), 1)

    async def test_group_follow_up_requires_owner_mission(self):
        await self.agent.on_message(self.event(sender=222, chat=-333))
        self.assertFalse(self.agent.mission_tasks)
        mission = self.store.watch(-333, "Arrange Friday meeting")
        await self.agent.on_message(self.event(sender=222, chat=-333))
        self.assertIn(mission["id"], self.agent.mission_tasks)

    async def test_scheduled_message_runs_once_after_due(self):
        job = self.store.schedule("message", (now() + timedelta(hours=1)).isoformat(), "Reminder")
        job["at"] = (now() - timedelta(seconds=1)).isoformat()
        task = asyncio.create_task(self.agent.scheduler())
        await asyncio.sleep(.08)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        self.agent.notify.assert_awaited_once_with("Reminder")
        self.assertEqual(job["status"], "done")
        self.assertEqual(Store(self.store.path).data["jobs"][0]["status"], "done")

    async def test_very_late_call_does_not_ring(self):
        self.service.start_call = AsyncMock()
        job = self.store.schedule("call", (now() + timedelta(hours=1)).isoformat())
        job["at"] = (now() - timedelta(minutes=10)).isoformat()
        task = asyncio.create_task(self.agent.scheduler())
        await asyncio.sleep(.08)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        self.service.start_call.assert_not_awaited()
        self.assertEqual(job["status"], "missed")

    async def exercise_owner_voice(self, transcript="Salom", speech_error=None):
        @asynccontextmanager
        async def action(*args):
            yield
        self.client.action = action
        self.agent.download = AsyncMock(return_value={"path": "test.ogg"})
        self.agent.transcribe = AsyncMock(return_value=transcript)
        self.agent.send_voice = AsyncMock(side_effect=speech_error)
        message = SimpleNamespace(raw_text="", voice=True, audio=False, media=True, chat_id=111, id=25)
        worker = asyncio.create_task(self.agent.owner_worker())
        with patch("hermes_personal_agent.telegram_agent.run_task", new_callable=AsyncMock,
                   return_value={"ok": True, "text": "Va alaykum assalom."}) as task:
            await self.agent.queue.put(message)
            await asyncio.wait_for(self.agent.queue.join(), 2)
            called = task.await_count
        worker.cancel()
        await asyncio.gather(worker, return_exceptions=True)
        return called

    async def test_voice_input_gets_both_text_and_voice(self):
        self.assertEqual(await self.exercise_owner_voice(), 1)
        self.agent.notify.assert_awaited_once_with("Va alaykum assalom.", 25)
        self.agent.send_voice.assert_awaited_once_with(111, "Va alaykum assalom.", 25)

    async def test_unintelligible_voice_does_not_execute_a_task(self):
        self.assertEqual(await self.exercise_owner_voice(transcript=""), 0)
        self.agent.send_voice.assert_not_awaited()
        self.assertIn("tushunolmadim", self.agent.notify.call_args.args[0])

    async def test_speech_failure_keeps_text_and_does_not_repeat_task(self):
        self.assertEqual(await self.exercise_owner_voice(speech_error=RuntimeError()), 1)
        self.assertEqual(self.agent.notify.await_count, 2)
        self.assertEqual(self.agent.notify.await_args_list[0].args[0], "Va alaykum assalom.")

    async def test_long_speech_is_split_without_losing_text(self):
        text = "Bu birinchi gap. " * 400
        chunks = list(speech_chunks(text, maximum=200))
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 200 for chunk in chunks))
        self.assertEqual(" ".join(chunks).split(), text.split())


if __name__ == "__main__":
    unittest.main()
