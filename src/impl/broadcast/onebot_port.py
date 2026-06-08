from __future__ import annotations

import asyncio
import logging
import threading

from onebot_protocol import MessagePayload

_log = logging.getLogger(__name__)


class OnebotPortBroadcaster:
    """在配置端口上接受长连接，向所有已连接客户端各发一行 JSON。"""

    def __init__(self, port: int, *, host: str = "0.0.0.0") -> None:
        """绑定监听地址与端口。

        Args:
            port: 监听端口
            host: 绑定地址，默认全网卡
        """
        self._host = host
        self._port = port
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._server: asyncio.Server | None = None
        self._clients: set[asyncio.StreamWriter] = set()
        self._ready = threading.Event()

    def start(self) -> None:
        """在后台线程启动 TCP 监听。"""
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name=f"onebot-port-{self._port}",
        )
        self._thread.start()
        if not self._ready.wait(timeout=10.0):
            raise RuntimeError(f"onebot 广播端口 {self._port} 未能启动")

    def stop(self) -> None:
        """停止监听并关闭连接。"""
        if self._loop is None:
            return
        future = asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop)
        try:
            future.result(timeout=5.0)
        except Exception:
            _log.debug("onebot 广播停止时出现异常", exc_info=True)
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def broadcast(self, payload: MessagePayload) -> None:
        """向当前所有连接各发送一条 JSON 行；无连接时不发送。"""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(payload), self._loop)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        finally:
            self._loop.close()

    async def _serve(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
        )
        self._ready.set()
        _log.info("onebot 广播监听 %s:%s", self._host, self._port)
        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self._clients.add(writer)
        peer = writer.get_extra_info("peername")
        _log.debug("onebot 客户端已连接 %s", peer)
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
        except Exception:
            _log.debug("onebot 客户端读失败 %s", peer, exc_info=True)
        finally:
            self._clients.discard(writer)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            _log.debug("onebot 客户端已断开 %s", peer)

    async def _broadcast(self, payload: MessagePayload) -> None:
        if not self._clients:
            _log.debug("onebot 广播跳过 client_count=0")
            return
        _log.debug("onebot 广播 client_count=%s", len(self._clients))
        line = payload.model_dump_json() + "\n"
        data = line.encode("utf-8")
        dead: list[asyncio.StreamWriter] = []
        for writer in list(self._clients):
            try:
                writer.write(data)
                await writer.drain()
            except Exception:
                dead.append(writer)
        for writer in dead:
            self._clients.discard(writer)

    async def _shutdown(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        for writer in list(self._clients):
            writer.close()
        self._clients.clear()
        self._loop.stop()
