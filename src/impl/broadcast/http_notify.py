from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request

from onebot_protocol import MessagePayload

_log = logging.getLogger(__name__)


class HttpSendNotifier:
    """向配置的 HTTP ``POST /send`` 地址推送 ``MessagePayload``。"""

    def __init__(self, send_url: str) -> None:
        self._send_url = send_url.rstrip("/")
        if not self._send_url.endswith("/send"):
            self._send_url = f"{self._send_url}/send"

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def broadcast(self, payload: MessagePayload) -> None:
        thread = threading.Thread(
            target=self._post_sync,
            args=(payload,),
            daemon=True,
            name="http-notify",
        )
        thread.start()

    def _post_sync(self, payload: MessagePayload) -> None:
        body = payload.model_dump_json().encode("utf-8")
        request = urllib.request.Request(
            self._send_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            _log.warning(
                "onebot HTTP 推送失败 url=%s message_id=%s status=%s body=%s",
                self._send_url,
                payload.message_id,
                exc.code,
                detail[:200],
            )
            return
        except urllib.error.URLError as exc:
            _log.warning(
                "onebot HTTP 推送失败 url=%s message_id=%s reason=%s",
                self._send_url,
                payload.message_id,
                exc.reason,
            )
            return
        except Exception:
            _log.warning(
                "onebot HTTP 推送失败 url=%s message_id=%s",
                self._send_url,
                payload.message_id,
                exc_info=True,
            )
            return

        status = "ok"
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                status = str(parsed.get("status", status))
        except json.JSONDecodeError:
            status = "unknown"
        _log.info(
            "onebot HTTP 已推送 url=%s message_id=%s http_status=%s",
            self._send_url,
            payload.message_id,
            status,
        )
