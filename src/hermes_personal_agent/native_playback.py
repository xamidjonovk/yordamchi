"""Feed Linux native Telegram playback independently of the asyncio event loop."""
import os
import select
import shlex
import tempfile
import threading
import time


class NativePlayback:
    def __init__(self, next_frame, directory):
        self.next_frame = next_frame
        self.directory = tempfile.TemporaryDirectory(prefix='call-pcm-', dir=directory)
        self.path = os.path.join(self.directory.name, 'audio.pcm')
        os.mkfifo(self.path, 0o600)
        self.fd = os.open(self.path, os.O_RDWR | os.O_NONBLOCK)
        self.stop = threading.Event()
        self.error = None
        self.written = 0
        self.max_gap_ms = 0
        self.late_frames = 0
        self.thread = threading.Thread(target=self._write, name='telegram-pcm', daemon=True)

    @property
    def command(self):
        # Only an internally generated private path is passed to the shell.
        return 'cat -- ' + shlex.quote(self.path)

    def start(self):
        self.thread.start()

    def _write(self):
        deadline = time.monotonic()
        last_write = None
        try:
            while not self.stop.is_set():
                if not select.select([], [self.fd], [], 0.05)[1]:
                    continue
                frame = self.next_frame()
                view = memoryview(frame)
                while view and not self.stop.is_set():
                    try:
                        written = os.write(self.fd, view)
                        view = view[written:]
                    except BlockingIOError:
                        self.stop.wait(0.002)
                self.written += 1
                now = time.monotonic()
                if last_write is not None:
                    gap = (now - last_write) * 1000
                    self.max_gap_ms = max(self.max_gap_ms, round(gap))
                    if gap >= 20:
                        self.late_frames += 1
                last_write = now
                deadline += 0.01
                # Never send a burst of old frames after a scheduling pause.
                if deadline < now:
                    deadline = now
                self.stop.wait(max(0, deadline - now))
        except Exception as exc:
            self.error = exc

    def close(self):
        self.stop.set()
        if self.thread.ident:
            self.thread.join(timeout=1)
        os.close(self.fd)
        self.directory.cleanup()
