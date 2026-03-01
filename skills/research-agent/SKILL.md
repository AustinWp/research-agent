---
name: research-agent
description: >
  Give your AI agent eyes to see the entire internet. Read and search across
  Twitter/X, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu, RSS, and any web page
  — all from a single CLI. Use when: (1) reading content from URLs (tweets, Reddit posts,
  articles, videos), (2) searching across platforms (web, Twitter, Reddit, GitHub, YouTube,
  Bilibili, XiaoHongShu), (3) analyzing user feedback or sentiment from any platform,
  (4) checking channel health or updating Research Agent.
  Triggers: "search Twitter/Reddit/YouTube", "read this URL", "find posts about",
  "搜索", "读取", "查一下", "看看这个链接", "分析", "调研", "舆情",
  "通过小红书分析", "通过XX平台分析".
---

# Research Agent

Read and search the internet across 9+ platforms via unified CLI.

## IMPORTANT: Platform Research Workflow

When the user asks to **analyze/research/调研** user feedback via any platform, follow this mandatory workflow:

1. **Invoke this skill (`research-agent`) FIRST** — get the correct platform usage guide before any search/read. NEVER run CLI commands blindly.
2. **Collect data** — follow the platform-specific instructions below (search → read details).
3. **Download images locally** — during data collection, extract all image URLs from posts and download to `images/` folder. See "Image Download" section below.
4. **Invoke `user-research-report` skill BEFORE writing the report** — load the output template. NEVER output a free-form analysis.
5. **Write and save the report** — strictly follow the `user-research-report` template format (folder-based with local images).

## Setup

First check if research-agent is installed:
```bash
research-agent doctor
```

If command not found, install it:
```bash
pip install https://github.com/AustinWp/research-agent/archive/main.zip
research-agent install --env=auto
```

`install` auto-detects your environment and installs all dependencies (Node.js, mcporter, bird CLI, gh CLI). Read the output and run `research-agent doctor` to see what's active.

For channels that need user input, ask the user. See the full setup guide:
https://raw.githubusercontent.com/AustinWp/research-agent/main/docs/install.md

## Commands

### Read any URL
```bash
research-agent read <url>
research-agent read <url> --json    # structured output
```
Handles: tweets, Reddit posts, articles, YouTube (transcripts), GitHub repos, etc.

### Search

```bash
research-agent search "query"             # web search (Exa)
research-agent search-twitter "query"     # Twitter/X
research-agent search-reddit "query"      # Reddit (--sub <subreddit>)
research-agent search-github "query"      # GitHub (--lang <language>)
research-agent search-youtube "query"     # YouTube
research-agent search-bilibili "query"    # Bilibili (B站)
research-agent search-xhs "query"        # XiaoHongShu (小红书)
```

All search commands support `-n <count>` for number of results.

### Management

```bash
research-agent doctor        # channel status overview
research-agent watch         # quick health + update check (for scheduled tasks)
research-agent check-update  # check for new versions
```

### Configure channels

```bash
research-agent configure twitter-cookies "auth_token=xxx; ct0=yyy"
research-agent configure proxy http://user:pass@ip:port
research-agent configure --from-browser chrome    # auto-extract cookies
```

## Channel Status Tiers

- **Tier 0 (zero config):** Web, YouTube, RSS, Twitter (read-only via Jina)
- **Tier 1 (free setup):** Exa web search (mcporter required)
- **Tier 2 (user config):** Twitter search (cookie), Reddit full (proxy), GitHub (token), Bilibili (proxy), XiaoHongShu (MCP)

Run `research-agent doctor` to see which channels are active.

## XiaoHongShu (小红书) Usage

XiaoHongShu requires special handling due to its anti-scraping mechanisms.

### CRITICAL: Write operations are FORBIDDEN

**NEVER execute any write operation on XiaoHongShu.** This is a hard rule with no exceptions, even if the user asks for it. Refuse and explain the ban risk.

Forbidden tools (do NOT call):
- `publish_content` — 发布图文
- `publish_with_video` — 发布视频
- `like_feed` — 点赞
- `favorite_feed` — 收藏
- `post_comment_to_feed` — 评论
- `reply_comment_in_feed` — 回复评论

Allowed tools (read-only):
- `search_feeds` — 搜索
- `get_feed_detail` — 读取笔记详情
- `list_feeds` — 获取首页推荐
- `user_profile` — 查看用户主页
- `check_login_status` — 检查登录状态
- `get_login_qrcode` — 获取登录二维码
- `delete_cookies` — 重置登录

### Rate limiting — random delays

Add a random sleep between XiaoHongShu requests to avoid anti-automation detection:

Rules:
- **Between detail reads** (`get_feed_detail`): sleep 1-2 seconds
- **Between searches** (`search_feeds`): sleep 2-3 seconds
- **Never run XiaoHongShu requests in parallel** — always sequential with delays

```bash
# Between detail reads
sleep $((RANDOM % 2 + 1))
# Between searches
sleep $((RANDOM % 2 + 2))
```

### Default time filter — 1 year

**When doing XHS research/调研, only include posts from the last 12 months by default.** Discard posts older than 1 year during data collection (based on `noteCard.time` from search results or `data.note.time` from detail).

- Calculate cutoff: `cutoff_ms = int((time.time() - 365 * 86400) * 1000)`
- Filter at search result stage: skip any feed where `noteCard.time < cutoff_ms`
- If the user explicitly asks for a longer time range (e.g., "近两年", "all time", "不限时间"), respect their request
- In the report's "数据概览" section, note the time filter applied (e.g., "时间范围：近 1 年")

### Optimal workflow — batch read after each search

Search once, then read ALL results from that search before the next search. xsec_token lasts ~5-10 minutes — enough to read 15-20 posts sequentially with 1-2s delays.

```
search → filter by time (default 1 year) → sleep 1s → read detail 1 → sleep 1s → read detail 2 → ... → read detail N → sleep 2s → next search
```

For bulk collection (10+ posts), use a Python batch script instead of individual CLI calls:

```python
import subprocess, json, time, random

# Default: only posts from the last 12 months
CUTOFF_MS = int((time.time() - 365 * 86400) * 1000)

def is_recent(feed):
    """Check if a post is within the time filter."""
    t = feed.get("noteCard", {}).get("time", 0)
    return t >= CUTOFF_MS

def read_post(feed_id, token):
    time.sleep(random.uniform(1, 2))
    r = subprocess.run(
        ["mcporter", "call", "xiaohongshu", "get_feed_detail",
         f"feed_id={feed_id}", f"xsec_token={token}"],
        capture_output=True, text=True, timeout=15)
    return json.loads(r.stdout) if r.stdout.strip() else None
```

### Must-collect fields for reports

When collecting post data, **always extract and store** these fields for report generation:
- `id` — used to construct the original post link: `https://www.xiaohongshu.com/explore/{id}`
- `time` — millisecond timestamp, convert to `YYYY-MM-DD` for the report
- Both fields are available in `search_feeds` response (`feeds[].id`, `feeds[].noteCard.time`) and `get_feed_detail` response (`data.note.time`)

### xsec_token handling

- Tokens expire in ~5-10 minutes. Read all results from a search before doing the next search.
- If `get_feed_detail` returns empty/error, the token expired. Re-search to get a fresh token.
- Do NOT collect tokens from multiple searches before reading — tokens from the first search may expire while you search again.

### Reading post details requires search first

`research-agent read <xhs-url>` cannot resolve xsec_token on its own. Use `mcporter call xiaohongshu search_feeds` to get tokens, then `mcporter call xiaohongshu get_feed_detail` with the token.

### mcporter call examples (read-only operations only)

```bash
# Search (returns feed_id + xsec_token for each result)
mcporter call xiaohongshu search_feeds keyword="关键词"

# Read detail (1-2s delay after previous request)
sleep $((RANDOM % 2 + 1))
mcporter call xiaohongshu get_feed_detail feed_id="ID" xsec_token="TOKEN"

# Load all comments
sleep $((RANDOM % 2 + 1))
mcporter call xiaohongshu get_feed_detail feed_id="ID" xsec_token="TOKEN" load_all_comments=true limit=30

# Browse
sleep $((RANDOM % 2 + 2))
mcporter call xiaohongshu list_feeds

# Check status (no delay needed)
mcporter call xiaohongshu check_login_status
```

### CRITICAL: XiaoHongShu API response field names

The two main APIs return **completely different JSON structures**. Using wrong field names silently returns empty results — the most common XHS debugging pitfall.

**`search_feeds` response** — top-level key is `feeds` (NOT `data.items`), fields are **camelCase**:
```json
{
  "feeds": [
    {
      "id": "68d8d944000000000e0201cc",
      "xsecToken": "ABcDe...",
      "noteCard": {
        "displayTitle": "标题",
        "user": {"nickname": "用户名", "userId": "..."},
        "interactInfo": {
          "likedCount": "128",
          "commentCount": "32"
        },
        "time": 1727510400000
      }
    }
  ]
}
```

**`get_feed_detail` response** — nested under `data.note`, field names differ:
```json
{
  "data": {
    "note": {
      "title": "标题",
      "desc": "正文内容",
      "time": 1727510400000,
      "user": {"nickname": "用户名"},
      "interactInfo": {
        "likedCount": "128",
        "commentCount": "32",
        "collectedCount": "45",
        "shareCount": "12"
      },
      "imageList": [{"urlDefault": "https://..."}]
    },
    "comments": {
      "list": [{"content": "评论内容", "likeCount": "5"}]
    }
  }
}
```

**Common mistakes to avoid:**
| Wrong (will silently fail) | Correct |
|---|---|
| `d["data"]["items"]` | `d["feeds"]` |
| `item["xsec_token"]` | `item["xsecToken"]` |
| `item["note_card"]` | `item["noteCard"]` |
| `nc["display_title"]` | `nc["displayTitle"]` |
| `nc["interact_info"]` | `nc["interactInfo"]` |
| `info["liked_count"]` | `info["likedCount"]` |
| `info["comment_count"]` | `info["commentCount"]` |

**Note:** `check_login_status` returns **plain text** (not JSON). Do not pipe through `json.loads()`.

### Login expiration

If `check_login_status` shows not logged in, re-authenticate:
```bash
mcporter call xiaohongshu get_login_qrcode
# Save the base64 image, open it, ask user to scan with XHS app
```

### Login fallback — manual cookie injection

If QR code login fails repeatedly ("fail to login"), the user can provide `web_session` from their browser (via Cookie-Editor extension on xiaohongshu.com). Inject it directly into the Docker container:

```bash
docker exec xiaohongshu-mcp sh -c 'cat > /app/cookies.json << EOF
[
  {
    "name": "web_session",
    "value": "USER_WEB_SESSION_VALUE",
    "domain": ".xiaohongshu.com",
    "path": "/",
    "httpOnly": true,
    "secure": true
  }
]
EOF'
```

Then verify with `mcporter call xiaohongshu check_login_status`.

## Image Download

When collecting data for research reports, **always download images locally** to prevent CDN link expiration.

### Workflow

1. Create the report folder and `images/` subfolder first:
   ```bash
   REPORT_DIR="$HOME/Desktop/我的知识库/用户调研/{报告文件夹名}"
   mkdir -p "$REPORT_DIR/images"
   ```

2. After reading each post detail (`get_feed_detail`), extract image URLs from `data.note.imageList[].urlDefault` and download:
   ```bash
   curl -sL -o "$REPORT_DIR/images/img-001.jpg" \
     -H "Referer: https://www.xiaohongshu.com/" \
     "https://sns-webpic-qc.xhscdn.com/..."
   ```

3. For batch downloading, use inline Python:
   ```python
   import subprocess, json, os, time, random, urllib.request

   report_dir = os.path.expanduser("~/Desktop/我的知识库/用户调研/{报告文件夹名}")
   img_dir = os.path.join(report_dir, "images")
   os.makedirs(img_dir, exist_ok=True)

   img_counter = 1

   def download_images(image_list):
       global img_counter
       for img in image_list:
           url = img.get("urlDefault", "")
           if not url:
               continue
           ext = "jpg"
           out_path = os.path.join(img_dir, f"img-{img_counter:03d}.{ext}")
           req = urllib.request.Request(url, headers={"Referer": "https://www.xiaohongshu.com/"})
           try:
               with urllib.request.urlopen(req, timeout=10) as resp:
                   with open(out_path, "wb") as f:
                       f.write(resp.read())
               img_counter += 1
           except Exception as e:
               print(f"Failed to download {url}: {e}")
   ```

4. In the report markdown, reference images with relative paths:
   ```markdown
   <img src="./images/img-001.jpg" width="150" />
   ```

### Important notes

- Download images **during data collection**, not after — CDN URLs expire in hours
- Use `Referer: https://www.xiaohongshu.com/` header to avoid 403 errors
- Keep sequential numbering (`img-001`, `img-002`, ...) across all posts in the report
- Each post's images should be noted with their `img-XXX` numbers for mapping to the report

## Tips

- Always try `research-agent read <url>` first for any URL — it auto-detects the platform
- For Twitter cookies, recommend the user install [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) Chrome extension
- Reddit and Bilibili block server IPs — suggest a residential proxy (~$1/month) if on a server
- If a channel breaks, run `research-agent doctor` to diagnose

