from __future__ import annotations

import sys
from pathlib import Path

import pytest
from ff14_the_hunt import HuntRankKind

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config import HubConfig, hub_config_to_agent_settings, load_hub_config


def test_load_hub_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "data_centers: [猫小胖]\n"
        "worlds: [静语庄园]\n"
        "ranks: [s, a]\n"
        "patches: [DT]\n"
        "spawn_output: output/spawns\n"
        "recent_grace_seconds: 600\n"
        "once: true\n",
        encoding="utf-8",
    )
    loaded = load_hub_config(config_path)
    assert loaded.data_centers == ["猫小胖"]
    assert loaded.worlds == ["静语庄园"]
    assert loaded.ranks == ["s", "a"]
    assert loaded.patches == ["DT"]
    assert loaded.spawn_output == "output/spawns"
    assert loaded.recent_grace_seconds == 600.0
    assert loaded.once is True


def test_hub_config_to_agent_settings() -> None:
    config = HubConfig(
        data_centers=["猫小胖"],
        ranks=["s", "fate"],
        once=True,
    )
    settings = hub_config_to_agent_settings(config)
    assert settings.data_centers == ["猫小胖"]
    assert settings.rank_kinds == [HuntRankKind.S, HuntRankKind.FATE]
    assert settings.continuous_poll is False
    assert settings.spawn_output is None


def test_load_hub_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="缺少"):
        load_hub_config(tmp_path / "config.yaml")
