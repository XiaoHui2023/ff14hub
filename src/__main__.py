from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ff14_the_hunt import HuntRankKind  # noqa: E402

from runtime import AgentSettings, HuntAgentRuntime  # noqa: E402

_RANK_CHOICES = {
    "s": HuntRankKind.S,
    "a": HuntRankKind.A,
    "fate": HuntRankKind.FATE,
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ff14-agent",
        description="FF14 狩猎追踪 Agent：轮询 Bear Tracker 并输出终端日志与新检出资料。",
    )
    parser.add_argument(
        "-d",
        "--data-center",
        action="append",
        dest="data_centers",
        metavar="NAME",
        help="数据中心名，可多次指定",
    )
    parser.add_argument(
        "-w",
        "--world",
        action="append",
        dest="worlds",
        metavar="NAME",
        help="世界名，可多次指定",
    )
    parser.add_argument(
        "-r",
        "--rank",
        action="append",
        dest="ranks",
        choices=sorted(_RANK_CHOICES),
        metavar="KIND",
        help="狩猎等级：s、a、fate；可多次指定，默认 s",
    )
    parser.add_argument(
        "-p",
        "--patch",
        action="append",
        dest="patches",
        metavar="CODE",
        help="资料片缩写或中文名，可多次指定",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        dest="spawn_output",
        metavar="DIR",
        help="新检出聚合输出根目录",
    )
    parser.add_argument(
        "--recent-grace",
        type=float,
        default=900.0,
        dest="recent_grace_seconds",
        metavar="SECONDS",
        help="刚刷新宽限秒数",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只爬取一次后退出，不进入轮询",
    )
    return parser.parse_args(argv)


def _ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    args = _parse_args(argv)
    rank_tokens = args.ranks or ["s"]
    rank_kinds = [_RANK_CHOICES[token] for token in rank_tokens]
    settings = AgentSettings(
        data_centers=list(args.data_centers or []),
        worlds=list(args.worlds or []),
        rank_kinds=rank_kinds,
        patches=list(args.patches or []),
        spawn_output=args.spawn_output,
        recent_grace_seconds=args.recent_grace_seconds,
    )
    runtime = HuntAgentRuntime(settings)
    if args.once:
        runtime.crawl_once()
        return 0
    runtime.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
