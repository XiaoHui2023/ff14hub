from __future__ import annotations

import datetime
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Literal

import colorlog
from colorama import init as colorama_init

LEVEL_MAP = {
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

_NORMAL_FMT = "%(asctime)s - %(levelname)s - %(message)s"
_DEBUG_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"
_FILE_ROTATE_KW = {
    "encoding": "utf-8",
    "maxBytes": 10 * 1024 * 1024,
    "backupCount": 5,
}


class _DebugOnlyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == logging.DEBUG


class PerModuleDebugHandler(logging.Handler):
    """按 logger 名将 DEBUG 记录写入各自文件。"""

    def __init__(self, session_dir: str, formatter: logging.Formatter) -> None:
        super().__init__(logging.DEBUG)
        self._session_dir = session_dir
        self._formatter = formatter
        self._handlers: dict[str, RotatingFileHandler] = {}
        self.addFilter(_DebugOnlyFilter())

    def emit(self, record: logging.LogRecord) -> None:
        name = record.name or "root"
        safe_name = name.replace(os.sep, "_").replace(":", "_")
        handler = self._handlers.get(safe_name)
        if handler is None:
            path = os.path.join(self._session_dir, f"{safe_name}.log")
            handler = RotatingFileHandler(path, **_FILE_ROTATE_KW)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(self._formatter)
            self._handlers[safe_name] = handler
        handler.emit(record)

    def close(self) -> None:
        for handler in self._handlers.values():
            handler.close()
        self._handlers.clear()
        super().close()


def setup_log(
    log_dir: str,
    level: Literal["info", "debug", "warning", "error", "critical"],
    *,
    debug_log_dir: str = "",
) -> None:
    """配置双轨日志：控制台与普通文件按 level 过滤，debug 按模块分文件。

    Args:
        log_dir: 普通日志根目录；空字符串则跳过普通日志文件
        level: 控制台与普通日志文件的最低级别
        debug_log_dir: debug 日志根目录；空字符串则跳过分模块 debug 文件
    """
    log_level = LEVEL_MAP.get(level.lower(), logging.INFO)

    colorama_init()

    color_formatter = colorlog.ColoredFormatter(
        f"%(log_color)s{_DEBUG_FMT}",
        datefmt=_DATE_FMT,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(color_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M-%S")

    if log_dir:
        normal_formatter = logging.Formatter(_NORMAL_FMT, datefmt=_DATE_FMT)
        normal_log_dir = os.path.join(log_dir, date)
        os.makedirs(normal_log_dir, exist_ok=True)

        normal_file_handler = RotatingFileHandler(
            os.path.join(normal_log_dir, f"{time}.log"),
            **_FILE_ROTATE_KW,
        )
        normal_file_handler.setLevel(logging.INFO)
        normal_file_handler.setFormatter(normal_formatter)
        root_logger.addHandler(normal_file_handler)

    if debug_log_dir:
        debug_formatter = logging.Formatter(_DEBUG_FMT, datefmt=_DATE_FMT)
        debug_session_dir = os.path.join(debug_log_dir, date, time)
        os.makedirs(debug_session_dir, exist_ok=True)

        module_debug_handler = PerModuleDebugHandler(debug_session_dir, debug_formatter)
        root_logger.addHandler(module_debug_handler)
