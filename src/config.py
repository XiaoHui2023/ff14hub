from __future__ import annotations

from pathlib import Path
from typing import Literal

from configlib import load_config
from ff14_the_hunt import HuntRankKind
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from runtime import AgentSettings

RankToken = Literal["s", "a", "fate"]

_RANK_MAP: dict[RankToken, HuntRankKind] = {
    "s": HuntRankKind.S,
    "a": HuntRankKind.A,
    "fate": HuntRankKind.FATE,
}


class HubConfig(BaseModel):
    """ff14hub 根配置，对应仓库根 ``config.yaml``。"""

    model_config = ConfigDict(extra="forbid")

    data_centers: list[str] = Field(
        default_factory=list,
        description="数据中心名；空表示不过滤",
    )
    worlds: list[str] = Field(
        default_factory=list,
        description="世界名；空表示由数据中心展开",
    )
    ranks: list[RankToken] = Field(
        default_factory=lambda: ["s"],
        description="狩猎等级：s、a、fate",
    )
    patches: list[str] = Field(
        default_factory=list,
        description="资料片缩写或中文名；空表示不过滤",
    )
    spawn_output: str | None = Field(
        default=None,
        description="新检出聚合输出根目录；空表示不写盘",
    )
    recent_grace_seconds: float = Field(
        default=900.0,
        description="刚刷新宽限秒数",
    )
    once: bool = Field(
        default=False,
        description="为 true 时只爬取一次后退出",
    )

    @field_validator("ranks", mode="after")
    @classmethod
    def _ensure_ranks(cls, value: list[RankToken]) -> list[RankToken]:
        if value:
            return value
        return ["s"]


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_hub_config(path: Path | None = None) -> HubConfig:
    """从 YAML 加载并校验根配置。

    Raises:
        ValueError: 文件缺失、根节点不是对象或校验失败
    """
    config_path = path if path is not None else project_root() / "config.yaml"
    if not config_path.is_file():
        raise ValueError(
            f"缺少 {config_path}，请复制 config.example.yaml 为 config.yaml",
        )
    raw = load_config(config_path)
    if not isinstance(raw, dict):
        raise ValueError(f"{config_path} 根节点须为对象")
    try:
        return HubConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"config.yaml 校验失败：{exc}") from exc


def hub_config_to_agent_settings(config: HubConfig) -> AgentSettings:
    spawn_output: Path | None = None
    if config.spawn_output:
        spawn_output = Path(config.spawn_output)
    return AgentSettings(
        data_centers=list(config.data_centers),
        worlds=list(config.worlds),
        rank_kinds=[_RANK_MAP[token] for token in config.ranks],
        patches=list(config.patches),
        spawn_output=spawn_output,
        recent_grace_seconds=config.recent_grace_seconds,
        continuous_poll=not config.once,
    )
