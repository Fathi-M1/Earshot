"""Microphone capture into a RAM ring buffer. Raw audio NEVER touches disk
(CLAUDE.md non-negotiable). Privacy mute = close the stream immediately.

16 kHz mono float32, 30 s ring (overwritten). ``snapshot(seconds)`` returns the
most recent N seconds as a contiguous float32 array for the ASR window.
"""

from __future__ import annotations

import threading

import numpy as np

from . import config


class RingMic:
    def __init__(
        self,
        sample_rate: int = config.SAMPLE_RATE,
        ring_seconds: int = config.RING_SECONDS,
        device: int | None = None,
        blocksize: int = 480,  # 30 ms at 16 kHz
    ):
        self.sample_rate = sample_rate
        self.capacity = sample_rate * ring_seconds
        self.device = device
        self.blocksize = blocksize
        self._buf = np.zeros(self.capacity, dtype=np.float32)
        self._write = 0
        self._filled = 0
        self._lock = threading.Lock()
        self._stream = None

    def _callback(self, indata, frames, time_info, status):  # sounddevice thread
        mono = indata[:, 0] if indata.ndim > 1 else indata
        n = len(mono)
        with self._lock:
            end = self._write + n
            if end <= self.capacity:
                self._buf[self._write:end] = mono
            else:
                first = self.capacity - self._write
                self._buf[self._write:] = mono[:first]
                self._buf[: n - first] = mono[first:]
            self._write = end % self.capacity
            self._filled = min(self._filled + n, self.capacity)

    def start(self) -> None:
        import sounddevice as sd

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.blocksize,
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()

    def snapshot(self, seconds: float) -> np.ndarray:
        """Most-recent ``seconds`` of audio as a contiguous float32 array (RAM)."""
        want = min(int(seconds * self.sample_rate), self.capacity)
        with self._lock:
            filled = self._filled
            write = self._write
            n = min(want, filled)
            if n == 0:
                return np.zeros(0, dtype=np.float32)
            start = (write - n) % self.capacity
            if start + n <= self.capacity:
                return self._buf[start:start + n].copy()
            first = self.capacity - start
            return np.concatenate((self._buf[start:], self._buf[: n - first])).copy()

    def close(self) -> None:
        """Stop and release the mic immediately (privacy mute)."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None
        with self._lock:
            self._buf[:] = 0.0
            self._write = 0
            self._filled = 0

    @property
    def is_open(self) -> bool:
        return self._stream is not None
