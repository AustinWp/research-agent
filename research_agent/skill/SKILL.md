---
name: research-agent
description: >
  Give your AI agent eyes to see the entire internet. Read and search across
  Twitter/X, Reddit, YouTube, GitHub, Bilibili, XiaoHongShu, RSS, and any web page
  — all from a single CLI. Use when: (1) reading content from URLs (tweets, Reddit posts,
  articles, videos), (2) searching across platforms (web, Twitter, Reddit, GitHub, YouTube,
  Bilibili, XiaoHongShu), (3) checking channel health or updating Research Agent.
  Triggers: "search Twitter/Reddit/YouTube", "read this URL", "find posts about",
  "搜索", "读取", "查一下", "看看这个链接".
---

# Research Agent

Read and search the internet across 9+ platforms via unified CLI.

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

## Tips

- Always try `research-agent read <url>` first for any URL — it auto-detects the platform
- For Twitter cookies, recommend the user install [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) Chrome extension
- Reddit and Bilibili block server IPs — suggest a residential proxy (~$1/month) if on a server
- If a channel breaks, run `research-agent doctor` to diagnose
