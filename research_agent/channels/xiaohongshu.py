# -*- coding: utf-8 -*-
"""XiaoHongShu (小红书) — via mcporter + xiaohongshu MCP server.

Backend: xiaohongshu-mcp server (internal API, reliable)
Requires: mcporter CLI + xiaohongshu MCP server running
"""

import json
import random
import shutil
import subprocess
import time
from urllib.parse import urlparse
from .base import Channel, ReadResult, SearchResult
from typing import List, Optional


class XiaoHongShuChannel(Channel):
    name = "xiaohongshu"
    description = "小红书笔记"
    backends = ["xiaohongshu-mcp"]
    tier = 2

    def _mcporter_ok(self) -> bool:
        """Check if mcporter + xiaohongshu MCP is available."""
        if not shutil.which("mcporter"):
            return False
        try:
            r = subprocess.run(
                ["mcporter", "list"], capture_output=True, text=True, timeout=10
            )
            return "xiaohongshu" in r.stdout
        except Exception:
            return False

    def _call(self, expr: str, timeout: int = 30) -> str:
        r = subprocess.run(
            ["mcporter", "call", expr],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr or r.stdout)
        return r.stdout

    def _call_tool(self, server: str, tool: str, args: dict, timeout: int = 30) -> str:
        """Call mcporter with positional server/tool/args syntax."""
        r = subprocess.run(
            ["mcporter", "call", server, tool, json.dumps(args)],
            capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode != 0:
            raise RuntimeError(r.stderr or r.stdout)
        return r.stdout

    # ── Channel interface ──

    def can_handle(self, url: str) -> bool:
        d = urlparse(url).netloc.lower()
        return "xiaohongshu.com" in d or "xhslink.com" in d

    def check(self, config=None):
        if not shutil.which("mcporter"):
            return "off", (
                "需要 mcporter + xiaohongshu-mcp。安装步骤：\n"
                "  1. npm install -g mcporter\n"
                "  2. docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp\n"
                "  3. mcporter config add xiaohongshu http://localhost:18060/mcp\n"
                "  详见 https://github.com/xpzouying/xiaohongshu-mcp"
            )
        if not self._mcporter_ok():
            return "off", (
                "mcporter 已装但小红书 MCP 未配置。运行：\n"
                "  docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp\n"
                "  mcporter config add xiaohongshu http://localhost:18060/mcp"
            )
        try:
            out = self._call("xiaohongshu.check_login_status()", timeout=10)
            if "已登录" in out or "logged" in out.lower():
                return "ok", "完整可用（阅读、搜索、发帖、评论、点赞）"
            return "warn", "MCP 已连接但未登录，需扫码登录"
        except Exception:
            return "warn", "MCP 连接异常，检查 xiaohongshu-mcp 服务是否在运行"

    async def read(self, url: str, config=None) -> ReadResult:
        if not self._mcporter_ok():
            return ReadResult(
                title="XiaoHongShu",
                content=(
                    "⚠️ 小红书需要 mcporter + xiaohongshu-mcp 才能使用。\n\n"
                    "安装步骤：\n"
                    "1. npm install -g mcporter\n"
                    "2. docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp\n"
                    "3. mcporter config add xiaohongshu http://localhost:18060/mcp\n"
                    "4. 运行 research-agent doctor 检查状态\n\n"
                    "详见 https://github.com/xpzouying/xiaohongshu-mcp"
                ),
                url=url, platform="xiaohongshu",
            )

        note_id = self._extract_note_id(url)
        if not note_id:
            return ReadResult(
                title="XiaoHongShu",
                content=f"⚠️ 无法从 URL 提取笔记 ID: {url}",
                url=url, platform="xiaohongshu",
            )

        # Step 1: get xsec_token from feeds
        xsec_token = self._find_token(note_id)

        if not xsec_token:
            return ReadResult(
                title="XiaoHongShu",
                content=(
                    f"⚠️ 无法获取笔记 {note_id} 的访问令牌。\n"
                    "小红书需要 xsec_token 才能读取笔记详情。\n"
                    "请先通过搜索找到这篇笔记，或直接使用搜索功能。"
                ),
                url=url, platform="xiaohongshu",
            )

        # Step 2: get detail
        out = self._call(
            f'xiaohongshu.get_feed_detail(feed_id: "{note_id}", xsec_token: "{xsec_token}")',
            timeout=15,
        )

        return ReadResult(
            title=self._extract_title(out) or f"XHS {note_id}",
            content=out.strip(),
            url=url, platform="xiaohongshu",
        )

    async def search(self, query: str, config=None, **kwargs) -> List[SearchResult]:
        if not self._mcporter_ok():
            raise ValueError(
                "小红书搜索需要 mcporter + xiaohongshu-mcp。\n"
                "安装: npm install -g mcporter && mcporter config add xiaohongshu http://localhost:18060/mcp"
            )
        limit = kwargs.get("limit", 20)
        max_pages = 10  # safety cap to prevent infinite loop

        results = []
        seen_ids = set()
        cursor = ""

        for page in range(max_pages):
            if len(results) >= limit:
                break

            # Build search args
            search_args = {"keyword": query}
            if cursor:
                search_args["cursor"] = cursor

            try:
                out = self._call_tool(
                    "xiaohongshu", "search_feeds", search_args, timeout=30
                )
            except Exception:
                # If positional syntax fails, fall back to expression syntax
                safe_q = query.replace('"', '\\"')
                expr = f'xiaohongshu.search_feeds(keyword: "{safe_q}")'
                if cursor:
                    safe_cursor = cursor.replace('"', '\\"')
                    expr = f'xiaohongshu.search_feeds(keyword: "{safe_q}", cursor: "{safe_cursor}")'
                try:
                    out = self._call(expr, timeout=30)
                except Exception:
                    break

            try:
                data = json.loads(out)
            except (json.JSONDecodeError, ValueError):
                break

            feeds = data.get("feeds", [])
            if not feeds:
                break

            for item in feeds:
                note_id = item.get("id", "")
                if not note_id or note_id in seen_ids:
                    continue
                seen_ids.add(note_id)

                card = item.get("noteCard", {})
                user = card.get("user", {})
                interact = card.get("interactInfo", {})
                results.append(SearchResult(
                    title=card.get("displayTitle", ""),
                    url=f"https://www.xiaohongshu.com/explore/{note_id}",
                    snippet=f"👤 {user.get('nickname', '')} · ❤ {interact.get('likedCount', '0')}",
                    score=0,
                ))

            # Check for next page cursor
            new_cursor = data.get("cursor", "") or data.get("searchCursor", "")
            has_more = data.get("hasMore", False) or data.get("has_more", False)

            if not new_cursor or not has_more:
                break  # no more pages available
            if new_cursor == cursor:
                break  # cursor didn't advance — avoid infinite loop

            cursor = new_cursor

            # Rate limit: 2-3 second delay between pages (per SKILL.md guidelines)
            if len(results) < limit:
                time.sleep(random.uniform(2.0, 3.0))

        return results[:limit]

    # ── Helpers ──

    def _extract_note_id(self, url: str) -> str:
        parts = urlparse(url).path.strip("/").split("/")
        return parts[-1] if parts else ""

    def _find_token(self, note_id: str) -> Optional[str]:
        """Try to find xsec_token for a note from feeds."""
        try:
            out = self._call("xiaohongshu.list_feeds()", timeout=15)
            data = json.loads(out)
            for feed in data.get("feeds", []):
                if feed.get("id") == note_id:
                    return feed.get("xsecToken", "")
        except Exception:
            pass
        return None

    def _extract_title(self, text: str) -> str:
        for line in text.split("\n"):
            line = line.strip()
            if line and not line.startswith(("{", "[", "#", "http")):
                return line[:80]
        return ""
