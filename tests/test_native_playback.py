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
    enough_frames = threading.Event()
    def read():
        while True:
            chunk = reader.stdout.read(960)
            if not chunk:
                break
            frames.append(chunk)
            if len(frames) >= 30:
                enough_frames.set()
    thread = threading.Thread(target=read, daemon=True)
    thread.start()
    try:
        playback.start()
        # Block the main thread until audio arrives. Bound the wait without
        # making OS process startup/scheduling speed the behavior under test.
        assert enough_frames.wait(timeout=2), "Audio stalled while the main thread waited"
        assert all(chunk == frame for chunk in frames)
        assert playback.error is None
    finally:
        playback.close()
        reader.wait(timeout=2)
        thread.join(timeout=2)
    assert not playback.thread.is_alive()
    assert not os.path.exists(playback.path)
