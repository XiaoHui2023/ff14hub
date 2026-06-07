from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from config import hub_config_to_agent_settings, load_hub_config  # noqa: E402
from runtime import HuntAgentRuntime  # noqa: E402


def _ensure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main() -> int:
    _ensure_utf8_stdio()
    try:
        hub_config = load_hub_config()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    settings = hub_config_to_agent_settings(hub_config)
    runtime = HuntAgentRuntime(settings)
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
