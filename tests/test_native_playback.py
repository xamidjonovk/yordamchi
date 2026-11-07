import os
import subprocess
import threading
import time
import pytest

from hermes_personal_agent.native_playback import NativePlayback


@pytest.mark.skipif(os.name != 'posix', reason='Linux FIFO transport')
def test_native_audio_continues_when_main_thread_waits(tmp_path):
    frame = b'\x01\x02' * 480
    playback = NativePlayback(lambda: frame, tmp_path)
    reader = subprocess.Popen(playback.command, shell=True, stdout=subprocess.PIPE)
    frames = []
    def read():
        while True:
            chunk = reader.stdout.read(960)
            if not chunk:
                break
            frames.append(chunk)
    thread = threading.Thread(target=read, daemon=True)
    thread.start()
    try:
        playback.start()
        # Simulate a main-loop pause longer than the previous observed stalls.
        time.sleep(.5)
        assert len(frames) >= 30
        assert all(chunk == frame for chunk in frames)
        assert playback.error is None
    finally:
        playback.close()
        reader.wait(timeout=2)
        thread.join(timeout=2)
    assert not playback.thread.is_alive()
    assert not os.path.exists(playback.path)
