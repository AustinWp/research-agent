# -*- coding: utf-8 -*-
"""Environment health checker — powered by channels.

Each channel knows how to check itself. Doctor just collects the results.
"""

from typing import Dict
from research_agent.config import Config
from research_agent.channels import get_all_channels


def check_all(config: Config) -> Dict[str, dict]:
    """Check all channels and return status dict."""
    results = {}
    for ch in get_all_channels():
        status, message = ch.check(config)
        results[ch.name] = {
            "status": status,
            "name": ch.description,
            "message": message,
            "tier": ch.tier,
            "backends": ch.backends,
        }
    return results


def format_report(results: Dict[str, dict]) -> str:
    """Format results as a readable text report."""
    lines = []
    lines.append("👁️  Research Agent 状态")
    lines.append("=" * 40)

    ok_count = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)

    # Tier 0 — zero config
    lines.append("")
    lines.append("✅ 装好即用：")
    for key, r in results.items():
        if r["tier"] == 0:
            if r["status"] == "ok":
                lines.append(f"  ✅ {r['name']} — {r['message']}")
            elif r["status"] == "warn":
                lines.append(f"  ⚠️  {r['name']} — {r['message']}")
            elif r["status"] in ("off", "error"):
                lines.append(f"  ❌ {r['name']} — {r['message']}")

    # Tier 1 — needs free key
    tier1 = {k: r for k, r in results.items() if r["tier"] == 1}
    if tier1:
        lines.append("")
        lines.append("🔍 搜索（mcporter 即可解锁）：")
        for key, r in tier1.items():
            if r["status"] == "ok":
                lines.append(f"  ✅ {r['name']} — {r['message']}")
            else:
                lines.append(f"  ⬜ {r['name']} — {r['message']}")

    # Tier 2 — optional setup
    tier2 = {k: r for k, r in results.items() if r["tier"] == 2}
    if tier2:
        lines.append("")
        lines.append("🔧 配置后可用：")
        for key, r in tier2.items():
            if r["status"] == "ok":
                lines.append(f"  ✅ {r['name']} — {r['message']}")
            elif r["status"] == "warn":
                lines.append(f"  ⚠️  {r['name']} — {r['message']}")
            else:
                lines.append(f"  ⬜ {r['name']} — {r['message']}")

    lines.append("")
    lines.append(f"状态：{ok_count}/{total} 个渠道可用")
    if ok_count < total:
        lines.append("运行 `research-agent setup` 解锁更多渠道")

    return "\n".join(lines)
