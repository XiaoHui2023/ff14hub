from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from log import setup_log  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_root_logging() -> None:
    yield
    root = logging.getLogger()
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)
    root.setLevel(logging.WARNING)


def test_setup_log_writes_normal_and_debug_files(tmp_path: Path) -> None:
    log_root = tmp_path / "logs"
    debug_root = tmp_path / "debug_logs"
    setup_log(str(log_root), "info", debug_log_dir=str(debug_root))

    logger = logging.getLogger("runtime.hunt_runtime")
    logger.info("测试摘要")
    logger.debug("测试细节 key=value")

    for handler in logging.getLogger().handlers:
        handler.flush()

    date_dir = next(log_root.iterdir())
    log_file = next(date_dir.iterdir())
    assert "测试摘要" in log_file.read_text(encoding="utf-8")

    debug_date_dir = next(debug_root.iterdir())
    debug_session_dir = next(debug_date_dir.iterdir())
    debug_file = debug_session_dir / "runtime.hunt_runtime.log"
    assert debug_file.is_file()
    assert "测试细节 key=value" in debug_file.read_text(encoding="utf-8")


def test_parse_args_log_flags() -> None:
    main_path = _SRC / "__main__.py"
    spec = importlib.util.spec_from_file_location("ff14hub_main", main_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    args = module.parse_args(["-l", "logs", "-d", "debug_logs", "-g", "debug"])
    assert args.log_dir == Path("logs")
    assert args.debug_log_dir == Path("debug_logs")
    assert args.log_level == "debug"
