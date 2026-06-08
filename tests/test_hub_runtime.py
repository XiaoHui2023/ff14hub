from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config import HubConfig
from hub import HubRuntime


def test_hub_runtime_requires_source() -> None:
    with pytest.raises(ValueError, match="未启用任何信息源"):
        HubRuntime(HubConfig())

