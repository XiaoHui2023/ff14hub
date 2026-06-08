from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config import load_hub_config  # noqa: E402
from hub import HubRuntime  # noqa: E402
from log import setup_log  # noqa: E402

LogLevel = Literal["info", "debug", "warning", "error", "critical"]


def _ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ff14hub FF14 本地信息聚合")
    parser.add_argument(
        "-l",
        "--log-dir",
        type=Path,
        default=None,
        help="普通日志目录；省略则仅控制台",
    )
    parser.add_argument(
        "-d",
        "--debug-log-dir",
        type=Path,
        default=None,
        help="debug 日志目录；按模块分文件，省略则不写 debug 文件",
    )
    parser.add_argument(
        "-g",
        "--log-level",
        choices=["info", "debug", "warning", "error", "critical"],
        default="info",
        help="控制台与普通日志文件的最低级别；分模块 debug 文件始终只记 DEBUG",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    args = parse_args(argv)

    log_dir = str(args.log_dir) if args.log_dir is not None else ""
    debug_log_dir = str(args.debug_log_dir) if args.debug_log_dir is not None else ""
    setup_log(log_dir, args.log_level, debug_log_dir=debug_log_dir)

    try:
        hub_config = load_hub_config()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    runtime = HubRuntime(hub_config)
    try:
        if hub_config.once:
            runtime.crawl_once()
        else:
            runtime.run()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
