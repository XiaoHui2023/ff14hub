---
name: python-project-changelog
description: 本仓库：按时间记录要求与决议；最新在上；矛盾以最新为准。
---

# 变更记录

（规则见 `~/.cursor/skills/agent-project-changelog/SKILL.md`。）

## 2026-06-08

- **决议**：``run.bat`` / ``test.bat`` 缺 ``.venv`` 时仅报错并提示执行 ``update.bat``，不再自动调用 ``update.bat``；``ensure_playwright.py`` 缺 Chromium 时仅提示 ``python -m playwright install chromium``，不在脚本内安装。
- **决议**：轮询模式支持 Ctrl+C 退出：SIGINT 触发 ``FF14TheHunt.stop()``，终端打印「已停止」。
- **决议**：入口改为 ``config.yaml`` + ``python-library-configlib``；移除 argparse CLI。样例 ``config.example.yaml``，本地 ``config.yaml`` 不进库。
- **决议**：终端摘要显示下次爬取时间（``HuntCrawlPacket.next_fetch_at``）；``once: true`` 时不展示下次爬取。
- **决议**：``python-library-ff14-the-hunt`` 依赖下限升至 ``>=0.0.3``。
- **决议**：``python-library-ff14-the-hunt`` 依赖下限升至 ``>=0.0.2``（导出 ``HuntCrawlPacket``、locale、poll 等与 ff14hub 对齐）。

## 2026-06-07

- **决议**：新增 ``run.bat``（无 ``.venv`` 时先 ``update.bat``，再 ``python src`` 并转发 CLI 参数）；README 补充运行说明。
- **决议**：仓库自 ``ff14_agent`` 更名为 ``ff14hub``（远程 [XiaoHui2023/ff14hub](https://github.com/XiaoHui2023/ff14hub)）；``pyproject`` 包名、CLI ``prog``、README 与三件套中的项目名对齐。
- **决议**：实现狩猎追踪 Agent 首版：CLI 筛选数据中心/世界/等级/资料片，轮询 ``ff14_the_hunt`` 并 Rich 终端日志；可选 ``--output`` 导出新检出刷点 bundle（地图标点 PNG + JSON）。
- **决议**：依赖对齐 PyPI 最新：``rich>=15.0``、``python-library-ff14-the-hunt>=0.0.1``、``pytest>=9.0.3``；``update.bat`` 使用 ``pip install -U``。

## 2026-06-04

- **决议**：新建仓库；按 Agent 协作规范初始化三件套（`python-project-session-manifest`、`python-project-design-notes`、`python-project-changelog`）。
- **决议**：`.cursor/skills/` 纳入版本库；其它 Cursor 本地状态（如 `rules/`）若出现则不进远程。
- **决议**：提供最小 Python 脚手架（`pyproject.toml`、`src/__main__.py`、`update.bat` / `test.bat`），业务功能后续迭代。
