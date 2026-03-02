# CLAUDE.md

本文件为 Claude Code 提供项目上下文和开发指引。

## 项目概述

Research Agent（v1.1.0）是一个统一的 CLI 工具和 Python 库，提供跨 10+ 互联网平台（Twitter/X、Reddit、YouTube、GitHub、Bilibili、小红书、RSS、Exa、通用网页）的标准化读取和搜索能力。通过可插拔的 Channel 架构封装外部工具（gh、yt-dlp、bird、mcporter），采用 async-first API 设计。

项目同时提供 Claude Code Skill 定义（`skills/` 目录）和 MCP Server（`research_agent/integrations/mcp_server.py`），可作为 AI Agent 的感知层接入。

## 开发命令

```bash
# 开发模式安装
pip install -e .

# 安装所有可选功能
pip install -e ".[all]"

# CLI 命令
research-agent doctor          # 健康检查
research-agent read <url>      # 读取 URL
research-agent search "query"  # 搜索

# 以 Python 模块运行
python -m research_agent.cli doctor
```

本项目未配置测试框架或 linter。

## 架构

### Channel 系统（核心抽象）

每个平台对应一个 **Channel** —— 继承自 `research_agent/channels/base.py:Channel`（ABC）。Channel 需实现：

- `can_handle(url) -> bool` —— URL 路由（首个匹配生效）
- `read(url, config) -> ReadResult` —— 读取内容
- `search(query, ...) -> List[SearchResult]` —— 搜索（可选）
- `check(config) -> Tuple[str, str]` —— 健康状态

Channel 注册顺序在 `research_agent/channels/__init__.py:ALL_CHANNELS` 中。**顺序重要** —— `WebChannel` 在最后作为兜底。

### 数据流

```
CLI (cli.py) 或 Library (core.py)
  → ResearchAgent.read(url) / .search(query)
    → channels/__init__.py:get_channel_for_url(url)  # URL 路由
      → 具体 Channel.read() / .search()
        → subprocess 调用外部工具 (gh, yt-dlp, bird, mcporter)
          → 解析输出为 ReadResult / SearchResult
```

### 关键文件

| 文件 | 用途 |
|------|------|
| `research_agent/core.py` | `ResearchAgent` 类 —— 主要编程 API |
| `research_agent/cli.py` | CLI 入口（~900 行，所有命令） |
| `research_agent/channels/base.py` | `Channel` ABC、`ReadResult`、`SearchResult` 数据类 |
| `research_agent/channels/__init__.py` | Channel 注册表和 URL 路由 |
| `research_agent/config.py` | 配置加载，路径 `~/.research-agent/config.yaml` + 环境变量 |
| `research_agent/doctor.py` | 健康检查，聚合各 Channel 状态 |
| `research_agent/integrations/mcp_server.py` | MCP 协议服务器（8 个工具） |
| `research_agent/guides/` | 各平台配置指南（setup-exa/twitter/reddit/xiaohongshu/wechat/groq） |
| `config/mcporter.json` | Exa 和小红书的 MCP 端点配置 |

### Skills（Claude Code 集成）

`skills/` 目录包含 3 个独立 Skill 定义：

| Skill | 用途 |
|-------|------|
| `skills/research-agent/SKILL.md` | 完整使用指南，含小红书工作流、图片下载等 |
| `skills/research-agent-mcp/SKILL.md` | 轻量安装引导，面向 MCP 集成 |
| `skills/user-research-report/SKILL.md` | 调研报告输出模板，定义命名规则和 Markdown 格式 |

### Channel 后端

每个 Channel 通过 subprocess 调用外部 CLI 工具，部分有降级链：

- **Twitter**: bird CLI → Jina Reader 降级
- **GitHub**: gh CLI → Jina Reader 降级
- **YouTube/Bilibili**: yt-dlp
- **小红书/Exa**: mcporter（MCP 桥接 Docker 容器）
- **Web**: Jina Reader API（通用兜底）
- **RSS**: feedparser（纯 Python）

### Tier 分级

Channel 声明 `tier`（0/1/2）表示配置复杂度：
- **Tier 0**: 零配置 —— 装好即用（Web、YouTube、RSS、Twitter 阅读、GitHub 公开）
- **Tier 1**: 免费配置 —— 需要 mcporter（Exa 搜索）
- **Tier 2**: 需用户配置 —— 需要 token/代理/Docker（Twitter 搜索、Reddit、小红书）

### 添加新 Channel

1. 创建 `research_agent/channels/{platform}.py`
2. 继承 `Channel`，实现 `can_handle()`、`read()`，可选实现 `search()`
3. 在 `research_agent/channels/__init__.py:ALL_CHANNELS` 中注册（放在 `WebChannel` 之前）

### 配置

配置从 `~/.research-agent/config.yaml` 加载，支持环境变量覆盖。`config.py` 中的 `Config` 类通过 `FEATURE_REQUIREMENTS` 字典映射功能名到所需配置键。

## 外部依赖

本项目依赖系统安装的外部 CLI 工具：
- `gh`（GitHub CLI）
- `yt-dlp`（视频平台）
- `bird`（Twitter，可选）
- `mcporter`（Exa/小红书 MCP 桥接）
- Docker（小红书 MCP 容器，端口 18060）

## 注意事项

- `WebChannel` 必须在 `ALL_CHANNELS` 最后，作为兜底
- 小红书写操作（发帖/点赞/评论）在 Skill 中被禁止，仅允许读取
- CLI 入口 `cli.py` 体量较大（~900 行），所有命令集中在一个文件中
- 本项目未配置测试框架或 linter
