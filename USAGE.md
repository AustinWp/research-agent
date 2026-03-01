# Research Agent 使用说明

## 环境信息

- 虚拟环境: `/Users/austin/Desktop/MyAgent/research_agent/.venv`
- 激活虚拟环境: `source /Users/austin/Desktop/MyAgent/research_agent/.venv/bin/activate`
- 激活后可直接使用 `research-agent` 命令，否则需用完整路径:
  `/Users/austin/Desktop/MyAgent/research_agent/.venv/bin/research-agent`

## 当前渠道状态 (8/9)

| 渠道 | 状态 | 说明 |
|------|------|------|
| GitHub | ✅ | 读取、搜索、Fork、Issue、PR |
| Twitter/X | ✅ | 搜索、时间线、发推 |
| YouTube | ✅ | 视频字幕 (yt-dlp) |
| B站 | ✅ | 视频信息和字幕 |
| RSS/Atom | ✅ | 订阅源读取 |
| 网页 (任意 URL) | ✅ | Jina Reader API |
| 全网搜索 | ✅ | Exa 语义搜索，同时支持 Reddit/Twitter |
| 小红书 | ✅ | 阅读、搜索、发帖、评论、点赞 |
| Reddit 帖子读取 | ⬜ | 搜索可用，读帖子需配代理 |

## 常用命令

### 1. 读取任意 URL

```bash
research-agent read <url>
research-agent read <url> --json    # JSON 格式输出
```

支持自动识别平台：推文、Reddit 帖子、文章、YouTube 视频、GitHub 仓库等。

**示例：**
```bash
research-agent read https://x.com/elonmusk/status/123456789
research-agent read https://github.com/anthropics/claude-code
research-agent read https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### 2. 全网搜索

```bash
research-agent search "关键词"
```

**示例：**
```bash
research-agent search "AI Agent 2026 趋势"
research-agent search "React Server Components" -n 20
```

### 3. 平台搜索

```bash
# Twitter/X 搜索
research-agent search-twitter "关键词"

# Reddit 搜索
research-agent search-reddit "关键词"
research-agent search-reddit "关键词" --sub MachineLearning   # 指定 subreddit

# GitHub 搜索
research-agent search-github "关键词"
research-agent search-github "关键词" --lang python            # 按语言过滤

# YouTube 搜索
research-agent search-youtube "关键词"

# B站搜索
research-agent search-bilibili "关键词"

# 小红书搜索
research-agent search-xhs "关键词"
```

所有搜索命令都支持 `-n <数量>` 指定返回结果数。

### 4. 小红书专属功能 (通过 mcporter)

```bash
# 搜索小红书
mcporter call xiaohongshu search_feeds keyword="AI绘画"

# 获取首页推荐
mcporter call xiaohongshu list_feeds

# 获取笔记详情
mcporter call xiaohongshu get_feed_detail feed_id="笔记ID" xsec_token="token"

# 发布图文
mcporter call xiaohongshu publish_content title="标题" content="正文" images='["图片路径"]'

# 点赞
mcporter call xiaohongshu like_feed feed_id="笔记ID" xsec_token="token"

# 收藏
mcporter call xiaohongshu favorite_feed feed_id="笔记ID" xsec_token="token"

# 评论
mcporter call xiaohongshu post_comment_to_feed feed_id="笔记ID" xsec_token="token" content="评论内容"

# 检查登录状态
mcporter call xiaohongshu check_login_status
```

### 5. 管理与维护

```bash
research-agent doctor          # 查看所有渠道状态
research-agent watch           # 快速健康检查 + 更新检查
research-agent check-update    # 检查新版本
```

### 6. 配置

```bash
# 配置代理 (解锁 Reddit 帖子读取)
research-agent configure proxy http://user:pass@ip:port

# 从浏览器自动提取 cookies
research-agent configure --from-browser chrome

# 配置 Twitter cookies
research-agent configure twitter-cookies "auth_token=xxx; ct0=yyy"
```

## AI Agent 中使用

Research Agent 安装时已自动注册为 Claude Code 的 skill。在 Claude Code 对话中，你可以直接说：

- "搜索 Twitter 上关于 xxx 的讨论"
- "读取这个链接的内容: https://..."
- "在小红书上搜索 xxx"
- "在 GitHub 上找 xxx 相关的项目"

Claude Code 会自动调用 research-agent 完成操作。

## 解锁 Reddit (可选)

Reddit 搜索已可用（通过 Exa），但读取帖子内容需要配置一个住宅代理：

```bash
research-agent configure proxy http://user:pass@ip:port
```

住宅代理服务推荐（约 $1/月起）：可搜索 "residential proxy" 选择合适的服务商。

## 小红书登录过期处理

如果小红书登录过期，重新获取二维码扫码即可：

```bash
mcporter call xiaohongshu get_login_qrcode
```

然后用小红书 App 扫码登录。

## Docker 容器管理 (小红书 MCP)

```bash
docker ps                                    # 查看运行中的容器
docker restart xiaohongshu-mcp              # 重启小红书服务
docker logs xiaohongshu-mcp                 # 查看日志
docker stop xiaohongshu-mcp                 # 停止
docker start xiaohongshu-mcp               # 启动
```
