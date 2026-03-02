# Research Agent

> Give your AI Agent eyes to see the entire internet.

全方位社媒调研工具 —— 一行命令搜索和阅读 10+ 平台，帮你系统性调研任何议题在各大社交媒体上的表现。

```bash
research-agent search-twitter "AI Agent 2026"
research-agent search-xhs "AI绘画教程"
research-agent read https://github.com/anthropics/claude-code
```

## 为什么需要这个工具

当你想调研一个议题时，信息分散在 Twitter、Reddit、小红书、B站、YouTube 等各个平台。每个平台有不同的 API、反爬策略和数据格式。

Research Agent 把这些差异屏蔽掉，提供统一的 `search` + `read` 接口：

- 一条命令搜索任意平台
- 一条命令读取任意 URL（自动识别平台）
- 搜集的数据可以直接生成结构化调研报告
- 可作为 Claude Code Skill 或 MCP Server 接入 AI Agent

## 支持的平台

| 平台 | 搜索 | 阅读 | 后端 | 配置 |
|------|:----:|:----:|------|------|
| 任意网页 | - | ✅ | Jina Reader | 零配置 |
| GitHub | ✅ | ✅ | gh CLI | 零配置 |
| YouTube | ✅ | ✅ | yt-dlp | 零配置 |
| B站 | ✅ | ✅ | yt-dlp | 零配置 |
| RSS/Atom | - | ✅ | feedparser | 零配置 |
| Twitter/X | ✅ | ✅ | bird CLI | 需 Cookie |
| 全网搜索 | ✅ | - | Exa (MCP) | 免费 |
| Reddit | ✅ | ✅ | Exa + 代理 | 需代理 |
| 小红书 | ✅ | ✅ | mcporter + Docker | 需 Docker |

## 快速开始

### 安装

```bash
pip install git+https://github.com/AustinWp/research-agent.git
```

或开发模式安装：

```bash
git clone https://github.com/AustinWp/research-agent.git
cd research-agent
pip install -e ".[all]"
```

### 检查状态

```bash
research-agent doctor
```

装好即用的平台（Web、GitHub、YouTube、B站、RSS）不需要任何配置。其他平台按需开启：

```bash
research-agent setup    # 交互式引导
```

各平台详细配置指南见 `research_agent/guides/` 目录。

### 基本用法

```bash
# 读取任意 URL —— 自动识别平台
research-agent read <url>

# 全网搜索
research-agent search "你的关键词"

# 平台搜索
research-agent search-twitter "关键词"
research-agent search-reddit "关键词" --sub MachineLearning
research-agent search-github "关键词" --lang python
research-agent search-youtube "关键词"
research-agent search-bilibili "关键词"
research-agent search-xhs "关键词"
```

## 作为 Python 库使用

```python
from research_agent import ResearchAgent
import asyncio

agent = ResearchAgent()

# 读取
result = asyncio.run(agent.read("https://x.com/elonmusk/status/123"))

# 搜索
results = asyncio.run(agent.search("AI Agent 趋势"))

# 平台搜索
results = asyncio.run(agent.search_twitter("Claude Code"))
results = asyncio.run(agent.search_xhs("AI绘画"))
```

## 调研工作流

Research Agent 的核心场景是 **社媒调研**。典型流程：

```
1. 多平台搜索 ─── 在 Twitter、小红书、Reddit 等平台搜索关键词
                    ↓
2. 批量阅读 ─────── 读取搜索结果的详细内容
                    ↓
3. 生成报告 ─────── 按模板输出结构化调研报告
```

### 配合 AI Agent 使用

Research Agent 设计为 AI Agent 的「眼睛」，提供两种接入方式：

**Claude Code Skill**（推荐）：安装后自动注册为 Skill，告诉 Agent：

> "帮我调研'AI Agent'这个话题在 Twitter 和小红书上的用户反馈"

Agent 会自动调用 research-agent 搜索和阅读，然后生成结构化的调研报告。

**MCP Server**：适用于任何兼容 MCP 协议的 Agent 平台，详见下方 MCP Server 章节。

项目附带 3 个 Skill 定义（`skills/` 目录）：

| Skill | 用途 |
|-------|------|
| `research-agent` | 完整使用指南，含平台特定工作流 |
| `research-agent-mcp` | 轻量安装引导，面向 MCP 场景 |
| `user-research-report` | 调研报告输出模板 |

## 架构

```
CLI / Python API
  └── ResearchAgent
        └── Channel 注册表（URL 路由）
              ├── GitHubChannel    ← gh CLI
              ├── TwitterChannel   ← bird CLI / Jina
              ├── YouTubeChannel   ← yt-dlp
              ├── BilibiliChannel  ← yt-dlp
              ├── RedditChannel    ← Exa + 代理
              ├── XiaoHongShuChannel ← mcporter + Docker
              ├── RSSChannel       ← feedparser
              ├── ExaSearchChannel ← mcporter (MCP)
              └── WebChannel       ← Jina Reader（兜底）
```

每个 Channel 是独立的可插拔模块，封装一个外部工具的调用。添加新平台只需要：

1. 创建 `research_agent/channels/your_platform.py`
2. 实现 `can_handle()`、`read()`、可选 `search()`
3. 注册到 Channel 列表（`WebChannel` 之前）

## 项目结构

```
research_agent/
├── cli.py              # CLI 入口
├── core.py             # ResearchAgent 主类
├── config.py           # 配置加载
├── doctor.py           # 健康检查
├── channels/           # 平台 Channel 实现
│   ├── base.py         # Channel ABC + 数据类
│   ├── github.py
│   ├── twitter.py
│   ├── youtube.py
│   ├── bilibili.py
│   ├── reddit.py
│   ├── xiaohongshu.py
│   ├── rss.py
│   ├── exa_search.py
│   └── web.py          # 兜底
├── guides/             # 各平台配置指南
│   ├── setup-exa.md
│   ├── setup-twitter.md
│   ├── setup-reddit.md
│   ├── setup-xiaohongshu.md
│   ├── setup-wechat.md
│   └── setup-groq.md
└── integrations/
    └── mcp_server.py   # MCP 协议服务器
skills/                 # Claude Code Skill 定义
├── research-agent/
├── research-agent-mcp/
└── user-research-report/
```

## 配置

配置文件位于 `~/.research-agent/config.yaml`，支持环境变量覆盖。

```bash
# 常用配置命令
research-agent configure proxy http://user:pass@ip:port    # Reddit/B站代理
research-agent configure twitter-cookies "auth_token=xxx; ct0=yyy"
research-agent configure --from-browser chrome             # 自动提取浏览器 Cookie
```

## MCP Server

支持 MCP 协议，可接入任何兼容的 Agent 平台：

```bash
pip install "research-agent[mcp]"
python -m research_agent.integrations.mcp_server
```

提供 8 个工具：`read_url`、`read_batch`、`detect_platform`、`search`、`search_reddit`、`search_github`、`search_twitter`、`get_status`

## License

MIT
