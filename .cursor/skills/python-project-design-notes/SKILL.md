---
name: python-project-design-notes
description: 本仓库：Agent 当前有效的设计意图与硬性要求；变更见 python-project-changelog。
---

# 设计笔记（当前有效）

> 变更记录见 `.cursor/skills/python-project-changelog/SKILL.md`；矛盾以 changelog 最新条目为准。

## 设计意图

- **ff14-agent**：面向《最终幻想 XIV》的本地自动化/辅助 Agent 工具仓库；具体玩法、感知与执行链路在后续迭代中补齐。
- **配置与密钥**：运行配置与私密参数不进远程；样例用 `*.example` 或文档占位，真值留在本机（`.env`、本地 yaml 等，见 `.gitignore`）。
- **依赖**：以 `pyproject.toml` 声明；Windows 下用仓库根 `update.bat` 维护 `.venv` 与可编辑安装。

## 硬性要求

- Python 本地工具约定见 `~/.cursor/skills/python-project-ai/SKILL.md`。
- 项目内 `.cursor/skills/` 仅保留三件套；领域规范放用户根 `~/.cursor/skills/`。
- 提交物不得含密钥、`.env` 真值，以及指向本仓库外的硬编码路径（见 `github-upload` 跨仓库路径审查）。

## 备忘与待定

- 首版仅脚手架与 Agent 三件套；业务模块与 CLI 子命令待需求明确后追加。
