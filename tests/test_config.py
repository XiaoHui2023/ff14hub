from __future__ import annotations

import sys
from pathlib import Path

import pytest
from ff14_the_hunt import HuntRankKind

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config import HubConfig, hub_config_to_hunt_settings, load_hub_config


def test_load_hub_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "hunt:\n"
        "  data_centers: [猫小胖]\n"
        "  worlds: [静语庄园]\n"
        "  ranks: [s, a]\n"
        "  patches: [DT]\n"
        "  spawn_output: output/spawns\n"
        "  recent_grace_seconds: 600\n"
        "once: true\n",
        encoding="utf-8",
    )
    loaded = load_hub_config(config_path)
    assert loaded.hunt is not None
    assert loaded.hunt.data_centers == ["猫小胖"]
    assert loaded.hunt.worlds == ["静语庄园"]
    assert loaded.hunt.ranks == ["s", "a"]
    assert loaded.hunt.patches == ["DT"]
    assert loaded.hunt.spawn_output == "output/spawns"
    assert loaded.hunt.recent_grace_seconds == 600.0
    assert loaded.once is True


def test_hub_config_to_hunt_settings() -> None:
    config = HubConfig(
        hunt={
            "data_centers": ["猫小胖"],
            "ranks": ["s", "fate"],
            "broadcast_port": 8766,
        },
        once=True,
    )
    settings = hub_config_to_hunt_settings(config)
    assert settings.data_centers == ["猫小胖"]
    assert settings.rank_kinds == [HuntRankKind.S, HuntRankKind.FATE]
    assert settings.continuous_poll is False
    assert settings.spawn_output is None
    assert settings.broadcast_port == 8766


def test_hub_config_to_hunt_settings_requires_section() -> None:
    with pytest.raises(ValueError, match="未配置 hunt"):
        hub_config_to_hunt_settings(HubConfig())


def test_load_hub_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="缺少"):
        load_hub_config(tmp_path / "config.yaml")

