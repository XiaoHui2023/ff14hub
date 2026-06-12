from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config import HubConfig, hub_config_to_news_settings, load_hub_config


def test_load_hub_config_with_news(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "hunt:\n"
        "  enabled: false\n"
        "news:\n"
        "  enabled: true\n"
        "  poll_interval_minutes: 10\n"
        "  limit_per_channel: 3\n"
        "  broadcast_url: http://127.0.0.1:9001/send\n"
        "once: true\n",
        encoding="utf-8",
    )
    loaded = load_hub_config(config_path)
    assert loaded.news is not None
    assert loaded.news.poll_interval_minutes == 10.0
    assert loaded.news.limit_per_channel == 3
    assert loaded.news.broadcast_url == "http://127.0.0.1:9001/send"


def test_hub_config_to_news_settings() -> None:
    config = HubConfig(
        news={
            "enabled": True,
            "poll_interval_minutes": 15,
            "limit_per_channel": 5,
            "broadcast_url": "http://127.0.0.1:8765/send",
        },
    )
    settings = hub_config_to_news_settings(config)
    assert settings.poll_interval_seconds == 900.0
    assert settings.limit_per_channel == 5
    assert settings.broadcast_url == "http://127.0.0.1:8765/send"
    assert settings.continuous_poll is True


def test_hub_config_to_news_settings_requires_section() -> None:
    with pytest.raises(ValueError, match="未配置 news"):
        hub_config_to_news_settings(HubConfig())
