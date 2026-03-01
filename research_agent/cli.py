# -*- coding: utf-8 -*-
"""
Research Agent CLI — command-line interface.

Usage:
    research-agent read <url>
    research-agent search <query>
    research-agent search-reddit <query> [--sub <subreddit>]
    research-agent search-github <query> [--lang <language>]
    research-agent search-twitter <query>
    research-agent setup
    research-agent doctor
    research-agent version
"""

import sys
import asyncio
import argparse
import json
import os

# Fix Windows console encoding — emoji/CJK characters crash on cp936/cp1252
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from research_agent import __version__


def _configure_logging(verbose: bool = False):
    """Suppress loguru output unless --verbose is set."""
    from loguru import logger
    logger.remove()  # Remove default stderr handler
    if verbose:
        logger.add(sys.stderr, level="INFO")


def main():
    parser = argparse.ArgumentParser(
        prog="research-agent",
        description="👁️ Give your AI Agent eyes to see the entire internet",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug logs")
    parser.add_argument("--version", action="version", version=f"Research Agent v{__version__}")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # ── read ──
    p_read = sub.add_parser("read", help="Read content from a URL")
    p_read.add_argument("url", help="URL to read")
    p_read.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")

    # ── search ──
    p_search = sub.add_parser("search", help="Search the web (Exa)")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("-n", "--num", type=int, default=5, help="Number of results")

    # ── search-reddit ──
    p_sr = sub.add_parser("search-reddit", help="Search Reddit")
    p_sr.add_argument("query", nargs="+", help="Search query")
    p_sr.add_argument("--sub", help="Subreddit filter")
    p_sr.add_argument("-n", "--num", type=int, default=10, help="Number of results")

    # ── search-github ──
    p_sg = sub.add_parser("search-github", help="Search GitHub")
    p_sg.add_argument("query", nargs="+", help="Search query")
    p_sg.add_argument("--lang", help="Language filter")
    p_sg.add_argument("-n", "--num", type=int, default=5, help="Number of results")

    # ── search-twitter ──
    p_st = sub.add_parser("search-twitter", help="Search Twitter")
    p_st.add_argument("query", nargs="+", help="Search query")
    p_st.add_argument("-n", "--num", type=int, default=10, help="Number of results")

    # ── search-youtube ──
    p_sy = sub.add_parser("search-youtube", help="Search YouTube")
    p_sy.add_argument("query", nargs="+", help="Search query")
    p_sy.add_argument("-n", "--num", type=int, default=5, help="Number of results")

    # ── search-bilibili ──
    p_sb = sub.add_parser("search-bilibili", help="Search Bilibili")
    p_sb.add_argument("query", nargs="+", help="Search query")
    p_sb.add_argument("-n", "--num", type=int, default=5, help="Number of results")

    # ── search-xhs ──
    p_sx = sub.add_parser("search-xhs", help="Search XiaoHongShu")
    p_sx.add_argument("query", nargs="+", help="Search query")
    p_sx.add_argument("-n", "--num", type=int, default=20, help="Number of results")

    # ── setup ──
    sub.add_parser("setup", help="Interactive configuration wizard")

    # ── install ──
    p_install = sub.add_parser("install", help="One-shot installer with flags")
    p_install.add_argument("--env", choices=["local", "server", "auto"], default="auto",
                           help="Environment: local, server, or auto-detect")
    p_install.add_argument("--proxy", default="",
                           help="Residential proxy for Reddit/Bilibili (http://user:pass@ip:port)")

    # ── configure ──
    p_conf = sub.add_parser("configure", help="Set a config value or auto-extract from browser")
    p_conf.add_argument("key", nargs="?", default=None,
                        choices=["proxy", "github-token", "groq-key",
                                 "twitter-cookies", "youtube-cookies"],
                        help="What to configure (omit if using --from-browser)")
    p_conf.add_argument("value", nargs="*", help="The value(s) to set")
    p_conf.add_argument("--from-browser", metavar="BROWSER",
                        choices=["chrome", "firefox", "edge", "brave", "opera"],
                        help="Auto-extract ALL platform cookies from browser (chrome/firefox/edge/brave/opera)")

    # ── doctor ──
    sub.add_parser("doctor", help="Check platform availability")

    # ── check-update ──
    sub.add_parser("check-update", help="Check for new versions and changes")

    # ── watch ──
    sub.add_parser("watch", help="Quick health check + update check (for scheduled tasks)")

    # ── version ──
    sub.add_parser("version", help="Show version")

    args = parser.parse_args()

    # Suppress loguru noise unless --verbose
    _configure_logging(getattr(args, "verbose", False))

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "version":
        print(f"Research Agent v{__version__}")
        sys.exit(0)

    if args.command == "doctor":
        _cmd_doctor()
    elif args.command == "check-update":
        _cmd_check_update()
    elif args.command == "watch":
        _cmd_watch()
    elif args.command == "setup":
        _cmd_setup()
    elif args.command == "install":
        _cmd_install(args)
    elif args.command == "configure":
        _cmd_configure(args)
    elif args.command == "read":
        asyncio.run(_cmd_read(args))
    elif args.command.startswith("search"):
        asyncio.run(_cmd_search(args))


# ── Command handlers ────────────────────────────────


def _cmd_install(args):
    """One-shot deterministic installer."""
    import os
    from research_agent.config import Config
    from research_agent.doctor import check_all, format_report

    config = Config()
    print()
    print("👁️  Research Agent Installer")
    print("=" * 40)

    # Auto-detect environment
    env = args.env
    if env == "auto":
        env = _detect_environment()
    
    if env == "server":
        print(f"📡 Environment: Server/VPS (auto-detected)")
    else:
        print(f"💻 Environment: Local computer (auto-detected)")

    # Apply explicit flags
    if args.proxy:
        config.set("reddit_proxy", args.proxy)
        config.set("bilibili_proxy", args.proxy)
        print(f"✅ Proxy configured for Reddit + Bilibili")

    # ── Install system dependencies ──
    print()
    _install_system_deps()

    # ── mcporter (for Exa search + XiaoHongShu) ──
    print()
    _install_mcporter()

    # Auto-import cookies on local computers
    if env == "local":
        print()
        print("🍪 Trying to import cookies from browser...")
        try:
            from research_agent.cookie_extract import configure_from_browser
            results = configure_from_browser("chrome", config)
            found = False
            for platform, success, message in results:
                if success:
                    print(f"  ✅ {platform}: {message}")
                    found = True
            if not found:
                # Try firefox
                results = configure_from_browser("firefox", config)
                for platform, success, message in results:
                    if success:
                        print(f"  ✅ {platform}: {message}")
                        found = True
            if not found:
                print("  ⬜ No cookies found (normal if you haven't logged into these sites)")
        except Exception:
            print("  ⬜ Could not read browser cookies (browser might be open)")

    # Environment-specific advice
    if env == "server":
        print()
        print("💡 Tip: Reddit and Bilibili block server IPs.")
        print("   Reddit search still works via Exa (free).")
        print("   For full access: research-agent configure proxy http://user:pass@ip:port")
        print("   Cheap option: https://www.webshare.io ($1/month)")

    # Test channels
    print()
    print("Testing channels...")
    results = check_all(config)
    ok = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)

    # Final status
    print()
    print(format_report(results))
    print()

    # ── Install agent skill ──
    _install_skill()

    print(f"✅ Installation complete! {ok}/{total} channels active.")

    if ok < total:
        print()
        print("🤖 Some channels are not active yet. If you're an AI Agent, try to fix them yourself — then run `research-agent doctor` again.")


def _install_skill():
    """Install Research Agent as an agent skill (OpenClaw / Claude Code)."""
    import os
    import importlib.resources

    # Determine skill install path
    skill_dirs = [
        os.path.expanduser("~/.openclaw/skills"),   # OpenClaw
        os.path.expanduser("~/.claude/skills"),      # Claude Code (if exists)
        os.path.expanduser("~/.agents/skills"),      # Generic agents
    ]

    installed = False
    for skill_dir in skill_dirs:
        if os.path.isdir(skill_dir):
            target = os.path.join(skill_dir, "research-agent")
            try:
                os.makedirs(target, exist_ok=True)
                # Read SKILL.md from package data
                skill_md = importlib.resources.files("research_agent").joinpath("skill", "SKILL.md").read_text()
                with open(os.path.join(target, "SKILL.md"), "w") as f:
                    f.write(skill_md)
                platform_name = "OpenClaw" if "openclaw" in skill_dir else "Claude Code" if "claude" in skill_dir else "Agent"
                print(f"🧩 Skill installed for {platform_name}: {target}")
                installed = True
            except Exception:
                pass

    if not installed:
        # No known skill directory found — create for OpenClaw by default
        target = os.path.expanduser("~/.openclaw/skills/research-agent")
        try:
            os.makedirs(target, exist_ok=True)
            skill_md = importlib.resources.files("research_agent").joinpath("skill", "SKILL.md").read_text()
            with open(os.path.join(target, "SKILL.md"), "w") as f:
                f.write(skill_md)
            print(f"🧩 Skill installed: {target}")
        except Exception:
            print("  ⬜ Could not install agent skill (optional)")


def _install_system_deps():
    """Install system-level dependencies: gh CLI, Node.js (for mcporter)."""
    import shutil
    import subprocess
    import platform

    print("🔧 Checking system dependencies...")

    # ── gh CLI ──
    if shutil.which("gh"):
        print("  ✅ gh CLI already installed")
    else:
        print("  📥 Installing gh CLI...")
        os_type = platform.system().lower()
        if os_type == "linux":
            try:
                # Official GitHub method for Linux
                cmds = [
                    "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg 2>/dev/null",
                    'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null',
                    "apt-get update -qq 2>/dev/null",
                    "apt-get install -y -qq gh 2>/dev/null",
                ]
                for cmd in cmds:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=60)
                if shutil.which("gh"):
                    print("  ✅ gh CLI installed")
                else:
                    print("  ⚠️  gh CLI install failed. You can try: snap install gh, or download from https://github.com/cli/cli/releases")
            except Exception:
                print("  ⚠️  gh CLI install failed. You can try: snap install gh, or download from https://github.com/cli/cli/releases")
        elif os_type == "darwin":
            if shutil.which("brew"):
                try:
                    subprocess.run(["brew", "install", "gh"], capture_output=True, timeout=120)
                    if shutil.which("gh"):
                        print("  ✅ gh CLI installed")
                    else:
                        print("  ⚠️  gh CLI install failed. Try: brew install gh")
                except Exception:
                    print("  ⚠️  gh CLI install failed. Try: brew install gh")
            else:
                print("  ⚠️  gh CLI not found. Install: https://cli.github.com")
        else:
            print("  ⚠️  gh CLI not found. Install: https://cli.github.com")

    # ── Node.js (needed for mcporter) ──
    if shutil.which("node") and shutil.which("npm"):
        print("  ✅ Node.js already installed")
    else:
        print("  📥 Installing Node.js...")
        try:
            # Use NodeSource for quick install
            subprocess.run(
                "curl -fsSL https://deb.nodesource.com/setup_22.x | bash - 2>/dev/null && apt-get install -y -qq nodejs 2>/dev/null",
                shell=True, capture_output=True, timeout=120,
            )
            if shutil.which("node"):
                print("  ✅ Node.js installed")
            else:
                print("  ⚠️  Node.js install failed. Try: apt install nodejs npm, or nvm install 22, or download from https://nodejs.org")
        except Exception:
            print("  ⚠️  Node.js install failed. Try: apt install nodejs npm, or nvm install 22, or download from https://nodejs.org")

    # ── bird CLI (for Twitter search) ──
    if shutil.which("bird") or shutil.which("birdx"):
        print("  ✅ bird CLI already installed")
    else:
        if shutil.which("npm"):
            try:
                subprocess.run(
                    ["npm", "install", "-g", "@steipete/bird"],
                    capture_output=True, text=True, timeout=120,
                )
                if shutil.which("bird"):
                    print("  ✅ bird CLI installed (Twitter search + timeline)")
                else:
                    print("  ⬜ bird CLI install failed (optional — Twitter reading still works via Jina)")
            except Exception:
                print("  ⬜ bird CLI install failed (optional — Twitter reading still works via Jina)")
        else:
            print("  ⬜ bird CLI requires Node.js (optional — Twitter reading still works via Jina)")


def _install_mcporter():
    """Install mcporter and configure Exa + XiaoHongShu MCP servers."""
    import shutil
    import subprocess

    print("📦 Setting up mcporter (search + XiaoHongShu backend)...")

    if shutil.which("mcporter"):
        print("  ✅ mcporter already installed")
    else:
        # Check for npm/npx
        if not shutil.which("npm") and not shutil.which("npx"):
            print("  ⚠️  mcporter requires Node.js. Install Node.js first:")
            print("     https://nodejs.org/ or: curl -fsSL https://fnm.vercel.app/install | bash")
            return
        try:
            subprocess.run(
                ["npm", "install", "-g", "mcporter"],
                capture_output=True, text=True, timeout=120,
            )
            if shutil.which("mcporter"):
                print("  ✅ mcporter installed")
            else:
                print("  ❌ mcporter install failed. Retry: npm install -g mcporter (check network/timeout), or try: npx mcporter@latest list")
                return
        except Exception as e:
            print(f"  ❌ mcporter install failed: {e}")
            return

    # Configure Exa MCP (free, no key needed)
    try:
        r = subprocess.run(
            ["mcporter", "list"], capture_output=True, text=True, timeout=10
        )
        if "exa" not in r.stdout:
            subprocess.run(
                ["mcporter", "config", "add", "exa", "https://mcp.exa.ai/mcp"],
                capture_output=True, text=True, timeout=10,
            )
            print("  ✅ Exa search configured (free, no API key needed)")
        else:
            print("  ✅ Exa search already configured")
    except Exception:
        print("  ⚠️  Could not configure Exa. Run manually: mcporter config add exa https://mcp.exa.ai/mcp")

    # Check XiaoHongShu MCP (only if server is running)
    try:
        r = subprocess.run(
            ["mcporter", "list"], capture_output=True, text=True, timeout=10
        )
        if "xiaohongshu" in r.stdout:
            print("  ✅ XiaoHongShu MCP already configured")
        else:
            # Check if XHS MCP server is running on localhost:18060
            import requests
            try:
                requests.get("http://localhost:18060/", timeout=3)
                subprocess.run(
                    ["mcporter", "config", "add", "xiaohongshu", "http://localhost:18060/mcp"],
                    capture_output=True, text=True, timeout=10,
                )
                print("  ✅ XiaoHongShu MCP auto-detected and configured")
            except Exception:
                print("  ⬜ XiaoHongShu MCP not detected (optional)")
                print("     Install: docker run -d --name xiaohongshu-mcp -p 18060:18060 xpzouying/xiaohongshu-mcp")
                print("     Then:    mcporter config add xiaohongshu http://localhost:18060/mcp")
                print("     Repo:    https://github.com/xpzouying/xiaohongshu-mcp")
    except Exception:
        pass


def _detect_environment():
    """Auto-detect if running on local computer or server."""
    import os

    # Check common server indicators
    indicators = 0

    # SSH session
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"):
        indicators += 2

    # Docker / container
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        indicators += 2

    # No display (headless)
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        indicators += 1

    # Cloud VM identifiers
    for cloud_file in ["/sys/hypervisor/uuid", "/sys/class/dmi/id/product_name"]:
        if os.path.exists(cloud_file):
            try:
                content = open(cloud_file).read().lower()
                if any(x in content for x in ["amazon", "google", "microsoft", "digitalocean", "linode", "vultr", "hetzner"]):
                    indicators += 2
            except:
                pass

    # systemd-detect-virt
    try:
        import subprocess
        result = subprocess.run(["systemd-detect-virt"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0 and result.stdout.strip() != "none":
            indicators += 1
    except:
        pass

    return "server" if indicators >= 2 else "local"


def _cmd_configure(args):
    """Set a config value and test it, or auto-extract from browser."""
    import shutil
    from research_agent.config import Config

    config = Config()

    # ── Auto-extract from browser ──
    if args.from_browser:
        from research_agent.cookie_extract import configure_from_browser

        browser = args.from_browser
        print(f"🔍 Extracting cookies from {browser}...")
        print()

        results = configure_from_browser(browser, config)

        found_any = False
        for platform, success, message in results:
            if success:
                print(f"  ✅ {platform}: {message}")
                found_any = True
            else:
                print(f"  ⬜ {platform}: {message}")

        print()
        if found_any:
            print("✅ Cookies configured! Run `research-agent doctor` to see updated status.")
        else:
            print(f"No cookies found. Make sure you're logged into the platforms in {browser}.")
        return

    # ── Manual configure ──
    if not args.key:
        print("Usage: research-agent configure <key> <value>")
        print("   or: research-agent configure --from-browser chrome")
        return

    value = " ".join(args.value) if args.value else ""
    if not value:
        print(f"Missing value for {args.key}")
        return

    if args.key == "proxy":
        config.set("reddit_proxy", value)
        config.set("bilibili_proxy", value)
        print(f"✅ Proxy configured for Reddit + Bilibili!")

        # Auto-test
        print("Testing Reddit access...", end=" ")
        try:
            import requests
            resp = requests.get(
                "https://www.reddit.com/r/test.json?limit=1",
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
                proxies={"http": value, "https": value},
                timeout=10,
            )
            if resp.status_code == 200:
                print("✅ Reddit works!")
            else:
                print(f"⚠️ Reddit returned {resp.status_code}")
        except Exception as e:
            print(f"❌ Failed: {e}")

    elif args.key == "twitter-cookies":
        # Accept two formats:
        # 1. auth_token ct0 (two separate values)
        # 2. Full cookie header string: "auth_token=xxx; ct0=yyy; ..."
        auth_token = None
        ct0 = None

        if "auth_token=" in value and "ct0=" in value:
            # Full cookie string — parse it
            for part in value.replace(";", " ").split():
                if part.startswith("auth_token="):
                    auth_token = part.split("=", 1)[1]
                elif part.startswith("ct0="):
                    ct0 = part.split("=", 1)[1]
        elif len(value.split()) == 2 and "=" not in value:
            # Two separate values: AUTH_TOKEN CT0
            parts = value.split()
            auth_token = parts[0]
            ct0 = parts[1]

        if auth_token and ct0:
            config.set("twitter_auth_token", auth_token)
            config.set("twitter_ct0", ct0)
            print(f"✅ Twitter cookies configured!")

            print("Testing Twitter access...", end=" ")
            try:
                import subprocess
                bird = shutil.which("bird") or shutil.which("birdx")
                if not bird:
                    print("⚠️ bird CLI not installed. Run: npm install -g @steipete/bird")
                else:
                    import os
                    env = os.environ.copy()
                    env["AUTH_TOKEN"] = auth_token
                    env["CT0"] = ct0
                    result = subprocess.run(
                        [bird, "search", "test", "-n", "1"],
                        capture_output=True, text=True, timeout=15,
                        env=env,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        print("✅ Twitter Advanced works!")
                    else:
                        print(f"⚠️ Test returned no results (cookies might be wrong)")
            except Exception as e:
                print(f"❌ Failed: {e}")
        else:
            print("❌ Could not find auth_token and ct0 in your input.")
            print("   Accepted formats:")
            print("   1. research-agent configure twitter-cookies AUTH_TOKEN CT0")
            print('   2. research-agent configure twitter-cookies "auth_token=xxx; ct0=yyy; ..."')

    elif args.key == "youtube-cookies":
        config.set("youtube_cookies_from", value)
        print(f"✅ YouTube cookie source configured: {value}")
        print("   yt-dlp will use cookies from this browser for age-restricted/member videos.")

    elif args.key == "github-token":
        config.set("github_token", value)
        print(f"✅ GitHub token configured!")

    elif args.key == "groq-key":
        config.set("groq_api_key", value)
        print(f"✅ Groq key configured!")


def _cmd_doctor():
    from research_agent.config import Config
    from research_agent.doctor import check_all, format_report
    config = Config()
    results = check_all(config)
    print(format_report(results))


def _cmd_setup():
    from research_agent.config import Config

    config = Config()
    print()
    print("👁️  Research Agent Setup")
    print("=" * 40)
    print()

    # Step 1: Exa
    print("【推荐】全网搜索 — Exa Search API")
    print("  免费 1000 次/月，注册地址: https://exa.ai")
    current = config.get("exa_api_key")
    if current:
        print(f"  当前状态: ✅ 已配置 ({current[:8]}...)")
        change = input("  要更换吗？[y/N]: ").strip().lower()
        if change != "y":
            print()
        else:
            key = input("  EXA_API_KEY: ").strip()
            if key:
                config.set("exa_api_key", key)
                print("  ✅ 已更新！")
            print()
    else:
        print("  当前状态: ⬜ 未配置")
        key = input("  EXA_API_KEY (回车跳过): ").strip()
        if key:
            config.set("exa_api_key", key)
            print("  ✅ 全网搜索 + Reddit搜索 + Twitter搜索 已开启！")
        else:
            print("  ℹ️  跳过。稍后可运行 research-agent setup 配置")
        print()

    # Step 2: GitHub token
    print("【可选】GitHub Token — 提高 API 限额")
    print("  无 token: 60 次/小时 | 有 token: 5000 次/小时")
    print("  获取: https://github.com/settings/tokens (无需任何权限)")
    current = config.get("github_token")
    if current:
        print(f"  当前状态: ✅ 已配置")
    else:
        key = input("  GITHUB_TOKEN (回车跳过): ").strip()
        if key:
            config.set("github_token", key)
            print("  ✅ GitHub API 已提升至 5000 次/小时！")
        else:
            print("  ℹ️  跳过。公开 API 也能用")
    print()

    # Step 3: Reddit proxy
    print("【可选】Reddit 代理 — 完整阅读 Reddit 帖子+评论")
    print("  Reddit 封锁很多 IP，需要 ISP 代理才能直接访问")
    print("  格式: http://用户名:密码@IP:端口")
    current = config.get("reddit_proxy")
    if current:
        print(f"  当前状态: ✅ 已配置")
    else:
        proxy = input("  REDDIT_PROXY (回车跳过): ").strip()
        if proxy:
            config.set("reddit_proxy", proxy)
            print("  ✅ Reddit 完整阅读已开启！")
        else:
            print("  ℹ️  跳过。仍可通过搜索获取 Reddit 内容")
    print()

    # Step 4: Groq (Whisper)
    print("【可选】Groq API — 视频无字幕时的语音转文字")
    print("  免费额度，注册: https://console.groq.com")
    current = config.get("groq_api_key")
    if current:
        print(f"  当前状态: ✅ 已配置")
    else:
        key = input("  GROQ_API_KEY (回车跳过): ").strip()
        if key:
            config.set("groq_api_key", key)
            print("  ✅ 语音转文字已开启！")
        else:
            print("  ℹ️  跳过")
    print()

    # Summary
    print("=" * 40)
    print(f"✅ 配置已保存到 {config.config_path}")
    print("运行 research-agent doctor 查看完整状态")
    print()


async def _cmd_read(args):
    from research_agent.core import ResearchAgent
    eyes = ResearchAgent()
    try:
        result = await eyes.read(args.url)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"\n📖 {result.get('title', 'Untitled')}")
            print(f"🔗 {result.get('url', '')}")
            if result.get("author"):
                print(f"👤 {result['author']}")
            print(f"\n{result.get('content', '')}")
    except Exception as e:
        error_str = str(e)
        if "400" in error_str and "Bad Request" in error_str:
            print(f"❌ Invalid URL: {args.url}", file=sys.stderr)
            print("   Please provide a valid URL (e.g., https://example.com)", file=sys.stderr)
        elif "ConnectionError" in type(e).__name__ or "Timeout" in type(e).__name__:
            print(f"❌ Could not connect to: {args.url}", file=sys.stderr)
            print("   Check your internet connection or the URL.", file=sys.stderr)
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


async def _cmd_search(args):
    from research_agent.core import ResearchAgent
    eyes = ResearchAgent()
    query = " ".join(args.query).strip()
    num = args.num

    if not query:
        print("Please provide a search query.", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "search":
            results = await eyes.search(query, num_results=num)
        elif args.command == "search-reddit":
            results = await eyes.search_reddit(query, subreddit=getattr(args, "sub", None), limit=num)
        elif args.command == "search-github":
            results = await eyes.search_github(query, language=getattr(args, "lang", None), limit=num)
        elif args.command == "search-twitter":
            results = await eyes.search_twitter(query, limit=num)
        elif args.command == "search-youtube":
            results = await eyes.search_youtube(query, limit=num)
        elif args.command == "search-bilibili":
            results = await eyes.search_bilibili(query, limit=num)
        elif args.command == "search-xhs":
            results = await eyes.search_xhs(query, limit=num)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str:
            print("⚠️  Exa API key not configured or invalid.")
            print("Get a free key at https://exa.ai (1000 searches/month free)")
            print("Then run: research-agent configure exa-key YOUR_KEY")
            sys.exit(1)
        elif "exa" in error_str.lower() or "api_key" in error_str.lower():
            print("⚠️  Exa API key not configured.")
            print("Get a free key at https://exa.ai")
            print("Then run: research-agent configure exa-key YOUR_KEY")
            sys.exit(1)
        else:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    if not results:
        print("No results found.")
        return

    for i, r in enumerate(results, 1):
        title = r.get("title") or r.get("name") or r.get("text", "")[:60]
        url = r.get("url", "")
        snippet = r.get("snippet") or r.get("description") or r.get("text", "")
        print(f"\n{i}. {title}")
        print(f"   🔗 {url}")
        if snippet:
            print(f"   {snippet[:200]}")
        # Extra info for GitHub
        extra = r.get("extra", {})
        if extra.get("stars"):
            print(f"   ⭐ {extra['stars']}  🍴 {extra.get('forks', 0)}  📝 {extra.get('language', '')}")


def _cmd_check_update():
    """Check for newer versions on GitHub."""
    import requests
    from research_agent import __version__

    print(f"📦 当前版本: v{__version__}")

    try:
        # Fetch latest version from GitHub
        resp = requests.get(
            "https://api.github.com/repos/AustinWp/research-agent/releases/latest",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v")
            body = data.get("body", "")

            if latest and latest != __version__:
                print(f"🆕 最新版本: v{latest} ← 有更新！")
                if body:
                    print()
                    print("更新内容：")
                    # Show first 20 lines of release notes
                    for line in body.strip().split("\n")[:20]:
                        print(f"  {line}")
                print()
                print("更新命令:")
                print("  pip install --upgrade https://github.com/AustinWp/research-agent/archive/main.zip")
                return "update_available"
            else:
                print(f"✅ 已是最新版本")
                return "up_to_date"
        else:
            # No releases yet, fall back to comparing commit
            resp2 = requests.get(
                "https://api.github.com/repos/AustinWp/research-agent/commits/main",
                timeout=10,
            )
            if resp2.status_code == 200:
                commit = resp2.json()
                sha = commit.get("sha", "")[:7]
                msg = commit.get("commit", {}).get("message", "").split("\n")[0]
                date = commit.get("commit", {}).get("committer", {}).get("date", "")[:10]
                print(f"🔍 最新提交: {sha} ({date}) {msg}")
                print()
                print("更新命令:")
                print("  pip install --upgrade https://github.com/AustinWp/research-agent/archive/main.zip")
                return "unknown"
            else:
                print("⚠️ 无法检查更新（网络问题）")
                return "error"
    except Exception as e:
        print(f"⚠️ 无法检查更新: {e}")
        return "error"


def _cmd_watch():
    """Quick health check + update check, designed for scheduled tasks.

    Only outputs problems. If everything is fine, outputs a single line.
    """
    from research_agent.config import Config
    from research_agent.doctor import check_all
    import requests
    from research_agent import __version__

    config = Config()
    issues = []

    # Check channels
    results = check_all(config)
    ok = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)

    # Find broken channels (were working, now broken)
    for key, r in results.items():
        if r["status"] in ("off", "error"):
            issues.append(f"❌ {r['name']}：{r['message']}")
        elif r["status"] == "warn":
            issues.append(f"⚠️ {r['name']}：{r['message']}")

    # Check for updates
    update_available = False
    new_version = ""
    release_body = ""
    try:
        resp = requests.get(
            "https://api.github.com/repos/AustinWp/research-agent/releases/latest",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v")
            if latest and latest != __version__:
                update_available = True
                new_version = latest
                release_body = data.get("body", "")
    except Exception:
        pass

    # Output
    if not issues and not update_available:
        print(f"👁️ Research Agent: 全部正常 ({ok}/{total} 渠道可用，v{__version__} 已是最新)")
        return

    print(f"👁️ Research Agent 监控报告")
    print(f"=" * 40)
    print(f"📦 版本: v{__version__}  |  渠道: {ok}/{total}")

    if issues:
        print()
        for issue in issues:
            print(f"  {issue}")

    if update_available:
        print()
        print(f"🆕 新版本可用: v{new_version}")
        if release_body:
            for line in release_body.strip().split("\n")[:10]:
                print(f"    {line}")
        print(f"  更新: pip install --upgrade https://github.com/AustinWp/research-agent/archive/main.zip")


if __name__ == "__main__":
    main()
