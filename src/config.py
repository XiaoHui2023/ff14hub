from __future__ import annotations

from pathlib import Path
from typing import Literal

from configlib import load_config
from ff14_the_hunt import HuntRankKind
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from runtime.hunt_runtime import AgentSettings

RankToken = Literal["s", "a", "fate"]

_RANK_MAP: dict[RankToken, HuntRankKind] = {
    "s": HuntRankKind.S,
    "a": HuntRankKind.A,
    "fate": HuntRankKind.FATE,
}


def _empty_to_none(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def _broadcast_endpoint_url(
    broadcast_url: str | None,
    broadcast_host: str,
    broadcast_port: int | None,
) -> str | None:
    if broadcast_url is not None:
        url = broadcast_url.rstrip("/")
        if not url.endswith("/send"):
            return f"{url}/send"
        return url
    if broadcast_port is None:
        return None
    host = broadcast_host.strip() or "127.0.0.1"
    return f"http://{host}:{broadcast_port}/send"


class HuntSourceConfig(BaseModel):
    """FF14 狩猎追踪源配置。"""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True, description="是否启用狩猎源")
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
    broadcast_url: str | None = Field(
        default=None,
        description="onebot HTTP 推送地址（POST /send）；未配置则不广播",
    )
    broadcast_host: str = Field(default="127.0.0.1", description="onebothub 起点 HTTP 地址")
    broadcast_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
        description="onebothub 起点 HTTP 端口；未配置则不广播",
    )
    print_every_crawl: bool = Field(
        default=False,
        description="为 true 时每轮爬取都打印终端摘要（调试用）；默认仅在状态变化或新检出时打印",
    )

    @field_validator("broadcast_url", mode="before")
    @classmethod
    def _empty_broadcast_url(cls, value: object) -> object:
        return _empty_to_none(value)

    @property
    def broadcast_endpoint_url(self) -> str | None:
        return _broadcast_endpoint_url(
            self.broadcast_url,
            self.broadcast_host,
            self.broadcast_port,
        )

    @field_validator("ranks", mode="after")
    @classmethod
    def _ensure_ranks(cls, value: list[RankToken]) -> list[RankToken]:
        if value:
            return value
        return ["s"]


class NewsSourceConfig(BaseModel):
    """FF14 新闻源配置。"""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(default=True, description="是否启用新闻源")
    poll_interval_minutes: float = Field(
        default=15.0,
        gt=0,
        description="两次爬取间隔（分钟）",
    )
    limit_per_channel: int = Field(
        default=5,
        ge=1,
        description="每个渠道每次抓取条数",
    )
    broadcast_url: str | None = Field(
        default=None,
        description="onebot HTTP 推送地址（POST /send）；未配置则不广播",
    )
    broadcast_host: str = Field(default="127.0.0.1", description="onebothub 起点 HTTP 地址")
    broadcast_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
        description="onebothub 起点 HTTP 端口；未配置则不广播",
    )

    @field_validator("broadcast_url", mode="before")
    @classmethod
    def _empty_news_broadcast_url(cls, value: object) -> object:
        return _empty_to_none(value)

    @property
    def broadcast_endpoint_url(self) -> str | None:
        return _broadcast_endpoint_url(
            self.broadcast_url,
            self.broadcast_host,
            self.broadcast_port,
        )

    enable_cn_official: bool = Field(default=True, description="启用国服官网渠道")
    enable_cn_weibo: bool = Field(default=True, description="启用官方微博渠道")
    enable_jp_official: bool = Field(default=True, description="启用日文 Lodestone 渠道")
    cn_weibo_cookie: str | None = Field(
        default=None,
        description="微博 Cookie 整串；空则尝试 Playwright 自动获取",
    )
    cn_weibo_cookie_storage_path: str | None = Field(
        default=None,
        description="Playwright 微博会话缓存路径",
    )


class HubConfig(BaseModel):
    """ff14hub 根配置，对应仓库根 ``config.yaml``。"""

    model_config = ConfigDict(extra="forbid")

    once: bool = Field(
        default=False,
        description="为 true 时各已启用源只爬取一次后退出",
    )
    hunt: HuntSourceConfig | None = Field(
        default=None,
        description="狩猎追踪源；省略表示不启用",
    )
    news: NewsSourceConfig | None = Field(
        default=None,
        description="FF14 新闻源；省略表示不启用",
    )


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


def hub_config_to_hunt_settings(config: HubConfig) -> AgentSettings:
    if config.hunt is None:
        raise ValueError("未配置 hunt 源")
    hunt = config.hunt
    spawn_output: Path | None = None
    if hunt.spawn_output:
        spawn_output = Path(hunt.spawn_output)
    return AgentSettings(
        data_centers=list(hunt.data_centers),
        worlds=list(hunt.worlds),
        rank_kinds=[_RANK_MAP[token] for token in hunt.ranks],
        patches=list(hunt.patches),
        spawn_output=spawn_output,
        recent_grace_seconds=hunt.recent_grace_seconds,
        continuous_poll=not config.once,
        broadcast_url=hunt.broadcast_endpoint_url,
        print_every_crawl=hunt.print_every_crawl,
    )


def hub_config_to_agent_settings(config: HubConfig) -> AgentSettings:
    """``hub_config_to_hunt_settings`` 的兼容别名。"""
    return hub_config_to_hunt_settings(config)


def hub_config_to_news_settings(config: HubConfig):
    from runtime.news_runtime import NewsAgentSettings

    if config.news is None:
        raise ValueError("未配置 news 源")
    news = config.news
    cookie_storage: Path | None = None
    if news.cn_weibo_cookie_storage_path:
        cookie_storage = Path(news.cn_weibo_cookie_storage_path)
    return NewsAgentSettings(
        poll_interval_seconds=news.poll_interval_minutes * 60.0,
        limit_per_channel=news.limit_per_channel,
        broadcast_url=news.broadcast_endpoint_url,
        continuous_poll=not config.once,
        enable_cn_official=news.enable_cn_official,
        enable_cn_weibo=news.enable_cn_weibo,
        enable_jp_official=news.enable_jp_official,
        cn_weibo_cookie=news.cn_weibo_cookie,
        cn_weibo_cookie_storage_path=cookie_storage,
    )
