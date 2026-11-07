import asyncio
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import pytest
from hermes_personal_agent.voice_service import CallBridge, FRAME_BYTES, PLAYBACK_START_BYTES


@pytest.mark.asyncio
async def test_playback_buffers_jitter_and_finishes_short_tail():
    sent = []
    class Calls:
        async def send_frame(self, owner, device, chunk):
            sent.append(chunk)
            if len(sent) == 1:
                bridge.output.extend(b'\x01' * (PLAYBACK_START_BYTES - FRAME_BYTES))
            if len(sent) == 3:
                bridge.output.clear()
                bridge.output.extend(b'\x02' * 100)
                bridge.output_complete = True
            if len(sent) == 4:
                raise RuntimeError('done')
    bridge = CallBridge(Calls(), 1)
    bridge.output.extend(b'\x01' * FRAME_BYTES)
    with pytest.raises(RuntimeError, match='done'):
        await bridge.play_output()
    assert sent[0] == bytes(FRAME_BYTES)
    assert sent[1] == b'\x01' * FRAME_BYTES
    assert sent[3] == b'\x02' * 100 + bytes(FRAME_BYTES - 100)


@pytest.mark.asyncio
async def test_receive_flushes_short_audio_at_turn_end():
    samples = np.arange(80, dtype='<i2').tobytes()
    class Session:
        async def receive(self):
            yield SimpleNamespace(server_content=None, data=samples, tool_call=None, go_away=None)
            yield SimpleNamespace(server_content=SimpleNamespace(input_transcription=None, output_transcription=None,
                turn_complete=True, interrupted=False), data=None, tool_call=None, go_away=None)
            bridge.stopped.set()
    bridge = CallBridge(None, 1)
    bridge.session = Session()
    await bridge.receive()
    assert bridge.output_complete
    assert len(bridge.output) > 0
    assert not bridge.output_has_audio
