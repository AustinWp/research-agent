# Research Agent

全方位社媒调研工具 —— 一行命令搜索和阅读 10+ 平台，帮你系统性调研任何议题在各大社交媒体上的表现。

```
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

### 检查状态

```bash
research-agent doctor
```

装好即用的平台（Web、GitHub、YouTube、B站、RSS）不需要任何配置。其他平台按需开启：

```bash
research-agent setup    # 交互式引导
```

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

Research Agent 设计为 AI Agent 的「眼睛」，可以作为 Claude Code 或其他 Agent 平台的 Skill 使用。告诉 Agent：

> "帮我调研'AI Agent'这个话题在 Twitter 和小红书上的用户反馈"

Agent 会自动调用 research-agent 搜索和阅读，然后生成结构化的调研报告。

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
3. 注册到 Channel 列表

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
pip install research-agent[mcp]
python -m research_agent.integrations.mcp_server
```

提供 8 个工具：`read_url`、`read_batch`、`detect_platform`、`search`、`search_reddit`、`search_github`、`search_twitter`、`get_status`

## License

MIT
