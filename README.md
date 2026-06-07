# ff14hub

面向《最终幻想 XIV》的本地 Agent 工具仓库（Python）。仓库：[github.com/XiaoHui2023/ff14hub](https://github.com/XiaoHui2023/ff14hub)。

## 项目结构与目录布局

```
ff14hub/
├── .cursor/skills/          # Agent 预加载、设计笔记、changelog（进库）
├── src/                     # 入口 python src
├── tests/                   # 单元测试
├── pyproject.toml
├── update.bat               # 创建 .venv 并 pip install -e ".[dev]"
└── test.bat                 # 无 .venv 时先 update，再 pytest
```

## 命令行参数

从仓库根执行：

```
python src
```

当前无额外 CLI 选项；占位入口打印就绪提示。

## 开发与测试

| 操作 | 命令 |
| --- | --- |
| 安装依赖 | 双击或执行 `update.bat` |
| 运行测试 | `test.bat` 或 `.venv\Scripts\pytest` |
