import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
import numpy as np
import pytest
from hermes_personal_agent import voice_service as voice

@pytest.mark.asyncio
async def test_contact_recording_encoded_and_delivered(tmp_path, monkeypatch):
    monkeypatch.setattr(voice, 'STATE', tmp_path)
    recording = voice.CallRecording('sample')
    samples = (np.sin(np.arange(4800) * 0.1) * 10000).astype('<i2').tobytes()
    recording.add(0, samples)
    recording.add(1, samples)
    output = await asyncio.to_thread(recording.finish)
    assert output.stat().st_size > 100
    bridge = SimpleNamespace(recording_path=output, ever_connected=True, recording=recording, owner_id=55)
    client = SimpleNamespace(send_file=AsyncMock())
    agent = SimpleNamespace(send_lock=asyncio.Lock(), last_send=0, notify=AsyncMock())
    service = SimpleNamespace(client=client, agent=agent, owner_id=22)
    task = asyncio.create_task(asyncio.sleep(0))
    await task
    await voice.Service.report_contact_call(service, task, bridge)
    client.send_file.assert_awaited_once()
    agent.notify.assert_not_awaited()
    assert not output.exists()

@pytest.mark.asyncio
async def test_failed_delivery_retains_recording(tmp_path):
    output = tmp_path / 'suhbat.ogg'
    output.write_bytes(b'audio')
    recording = SimpleNamespace(dropped=0, cleanup=lambda: output.unlink())
    bridge = SimpleNamespace(recording_path=output, ever_connected=True, recording=recording, owner_id=55)
    client = SimpleNamespace(send_file=AsyncMock(side_effect=RuntimeError('offline')))
    agent = SimpleNamespace(send_lock=asyncio.Lock(), notify=AsyncMock())
    task = asyncio.create_task(asyncio.sleep(0))
    await task
    await voice.Service.report_contact_call(SimpleNamespace(client=client,agent=agent,owner_id=22), task, bridge)
    assert output.exists()
    agent.notify.assert_awaited_once()
