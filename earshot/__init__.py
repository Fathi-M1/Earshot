"""Earshot — a private, fully offline listening companion.

The product name is a variable: read it from ``earshot.brand`` (which reads
``design/tokens.json``). Never hard-code the name in UI strings.
"""

import os as _os

# Force offline model libraries BEFORE faster-whisper / huggingface_hub import,
# so loading a cached whisper model never phones home to the HF hub (privacy).
_os.environ.setdefault("HF_HUB_OFFLINE", "1")
_os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
_os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

__version__ = "0.1.0"
