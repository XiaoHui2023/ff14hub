# ff14hub

面向《最终幻想 XIV》的本地 Agent 工具：轮询 Bear Tracker 狩猎计时，终端 Rich 日志，可选导出新检出刷点资料。仓库：[github.com/XiaoHui2023/ff14hub](https://github.com/XiaoHui2023/ff14hub)。

## 项目结构与目录布局

```
ff14hub/
├── .cursor/skills/          # Agent 预加载、设计笔记、changelog（进库）
├── config.example.yaml      # 配置样例（复制为 config.yaml）
├── src/                     # 入口 python src
├── tests/                   # 单元测试
├── pyproject.toml
├── update.bat               # 创建 .venv 并 pip install -e ".[dev]"
├── run.bat                  # 无 .venv 时先 update，再 python src
└── test.bat                 # 无 .venv 时先 update，再 pytest
```

## 配置

复制 `config.example.yaml` 为 `config.yaml` 后修改。键名与样例一致。

| 键 | 含义 | 默认 |
| --- | --- | --- |
| `data_centers` | 数据中心名列表；空表示不过滤 | `[]` |
| `worlds` | 世界名列表；空表示由数据中心展开 | `[]` |
| `ranks` | 狩猎等级：`s`、`a`、`fate` | `[s]` |
| `patches` | 资料片缩写或中文名 | `[]` |
| `spawn_output` | 新检出聚合输出根目录；`null` 表示不写盘 | `null` |
| `recent_grace_seconds` | 刚刷新宽限秒数 | `900` |
| `once` | 为 `true` 时只爬取一次后退出 | `false` |

## 日志

`run.bat` 默认写入仓库根 `logs/`（普通摘要）与 `debug_logs/`（按模块分文件的 DEBUG）。直接 `python src` 时不写文件，仅控制台。

| 短参 | 长参 | 含义 | 默认 |
| --- | --- | --- | --- |
| `-l` | `--log-dir` | 普通日志根目录 | 省略则不写文件 |
| `-d` | `--debug-log-dir` | debug 日志根目录 | 省略则不写 debug 文件 |
| `-g` | `--log-level` | 控制台与普通日志最低级别 | `info` |

`-g` 管控制台与普通 `.log`；`-d` 目录下各模块 `.log` 始终只收 DEBUG。

## 开发与测试

| 操作 | 命令 |
| --- | --- |
| 安装依赖 | 双击或执行 `update.bat` |
| 运行 Agent | `run.bat` 或 `python src -l logs -d debug_logs`（须已有 `config.yaml`） |
| 运行测试 | `test.bat` 或 `.venv\Scripts\pytest` |
