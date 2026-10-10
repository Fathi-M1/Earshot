"""Microphone capture into a RAM ring buffer. Raw audio NEVER touches disk
(CLAUDE.md non-negotiable). Privacy mute = close the stream immediately.

16 kHz mono float32, 30 s ring (overwritten). ``snapshot(seconds)`` returns the
most recent N seconds as a contiguous float32 array for the ASR window.
"""

from __future__ import annotations

import threading

import numpy as np

from . import config

# AGC targets (far-field hearing): normalise quiet/distant speech toward -20 dBFS.
_TARGET_RMS = 0.10            # 10^(-20/20)
_MAX_GAIN = 15.85            # +24 dB
_MIN_GAIN = 1.0
_AGC_SMOOTH = 0.05           # per-30ms-block smoothing (gentle attack/release)
_SILENCE_RMS = 0.0008        # below this it's silence — don't amplify it


def apply_agc_static(samples: np.ndarray) -> np.ndarray:
    """One-shot AGC for offline/bench use: normalise toward -20 dBFS, +24 dB cap."""
    if len(samples) == 0:
        return samples
    rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)) + 1e-9)
    if rms <= _SILENCE_RMS:
        return samples
    gain = float(np.clip(_TARGET_RMS / rms, _MIN_GAIN, _MAX_GAIN))
    return np.clip(samples * gain, -1.0, 1.0).astype(np.float32)


def pick_input_device() -> tuple[int | None, str]:
    """Choose the best input device: prefer a microphone array, else the default."""
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        ins = [(i, d) for i, d in enumerate(devices) if d.get("max_input_channels", 0) > 0]
        for i, d in ins:
            name = d["name"].lower()
            if "array" in name or "microphone array" in name:
                return i, d["name"]
        default = sd.default.device[0] if isinstance(sd.default.device, (list, tuple)) else None
        if default is not None and default >= 0:
            return default, sd.query_devices(default)["name"]
        if ins:
            return ins[0][0], ins[0][1]["name"]
    except Exception:
        pass
    return None, "default"


class RingMic:
    def __init__(
        self,
        sample_rate: int = config.SAMPLE_RATE,
        ring_seconds: int = config.RING_SECONDS,
        device: int | None = None,
        blocksize: int = 480,  # 30 ms at 16 kHz
        agc: bool = False,     # measured WORSE on synthetic far-field — off by default
    ):
        self.sample_rate = sample_rate
        self.capacity = sample_rate * ring_seconds
        self.device = device
        self.blocksize = blocksize
        self.agc = agc
        self._buf = np.zeros(self.capacity, dtype=np.float32)
        self._write = 0
        self._filled = 0
        self._lock = threading.Lock()
        self._stream = None
        self._gain = 1.0          # smoothed AGC gain (applied in snapshot)
        self._rms = 0.0           # EMA of block RMS
        self._floor = 0.01        # tracked room-noise floor
        self.device_name = "default"

    def _callback(self, indata, frames, time_info, status):  # sounddevice thread
        mono = indata[:, 0] if indata.ndim > 1 else indata
        if self.agc and len(mono):
            r = float(np.sqrt(np.mean(mono.astype(np.float32) ** 2)) + 1e-9)
            self._rms = 0.9 * self._rms + 0.1 * r
            # slowly track the quiet floor (room noise)
            self._floor = min(self._floor * 1.001, 0.9 * self._floor + 0.1 * r) if r < self._floor * 1.5 else self._floor
            if self._rms > _SILENCE_RMS:  # don't amplify pure silence/hum
                desired = float(np.clip(_TARGET_RMS / self._rms, _MIN_GAIN, _MAX_GAIN))
            else:
                desired = _MIN_GAIN
            self._gain += (desired - self._gain) * _AGC_SMOOTH
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

        if self.device is None:
            self.device, self.device_name = pick_input_device()
        else:
            try:
                self.device_name = sd.query_devices(self.device)["name"]
            except Exception:
                self.device_name = str(self.device)
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
                out = self._buf[start:start + n].copy()
            else:
                first = self.capacity - start
                out = np.concatenate((self._buf[start:], self._buf[: n - first])).copy()
        if self.agc and self._gain > 1.01:  # apply smoothed far-field gain
            out = np.clip(out * self._gain, -1.0, 1.0).astype(np.float32)
        return out

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
