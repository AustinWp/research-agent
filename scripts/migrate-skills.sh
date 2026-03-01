#!/usr/bin/env bash
# ============================================================
# Research Agent — 一键迁移 (代码 + Skills)
# 日期: 2026-02-28
# 用途: 在新设备/云主机上运行，同步最新代码并覆盖安装 skill
# 使用: bash migrate-skills.sh
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# pip 兼容：优先用项目 venv，其次 python3 -m pip
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -f "$PROJECT_DIR/.venv/bin/pip" ]; then
  PIP="$PROJECT_DIR/.venv/bin/pip"
elif command -v pip3 &>/dev/null; then
  PIP="pip3"
else
  PIP="python3 -m pip"
fi

# --------------------------------------------------
# 0. 更新 research-agent 代码仓库 + 重装 Python 包
# --------------------------------------------------
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -d "$REPO_DIR/.git" ]; then
  echo ""
  echo ">>> 更新代码仓库: $REPO_DIR"
  git -C "$REPO_DIR" fetch --all 2>/dev/null

  CURRENT=$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ "$CURRENT" = "refactor-v1.1" ]; then
    git -C "$REPO_DIR" pull --rebase 2>/dev/null && log "代码已更新 (refactor-v1.1)"
  else
    warn "当前分支: $CURRENT — 切换到 refactor-v1.1"
    git -C "$REPO_DIR" checkout refactor-v1.1 2>/dev/null
    git -C "$REPO_DIR" pull --rebase 2>/dev/null && log "已切换并更新到 refactor-v1.1"
  fi

  echo ""
  echo ">>> 重新安装 Python 包 (editable mode)"
  if $PIP install -e "$REPO_DIR" 2>&1 | tail -5; then
    log "research-agent Python 包已更新 ($(research-agent version 2>/dev/null || echo 'unknown'))"
  else
    warn "pip install 失败，请手动执行: $PIP install -e $REPO_DIR"
  fi
else
  warn "未找到 git 仓库: $REPO_DIR — 跳过代码更新"
  warn "请先 git clone 仓库，或手动安装: pip install -e /path/to/research_agent"
fi

echo ""

# --------------------------------------------------
# 1. 安装 research-agent skill（Claude Code + OpenClaw）
# --------------------------------------------------
SKILL_SRC="$PROJECT_DIR/skills/research-agent/SKILL.md"
if [ ! -f "$SKILL_SRC" ]; then
  warn "找不到 $SKILL_SRC — 跳过 research-agent skill 安装"
else
  for SKILL_DIR in \
    "$HOME/.claude/skills/research-agent" \
    "$HOME/.openclaw/skills/research-agent"; do
    mkdir -p "$SKILL_DIR"
    cp "$SKILL_SRC" "$SKILL_DIR/SKILL.md"
    log "research-agent skill → $SKILL_DIR/SKILL.md"
  done
fi

# --------------------------------------------------
# 2. 安装 user-research-report skill
# --------------------------------------------------
REPORT_SRC="$PROJECT_DIR/skills/user-research-report/SKILL.md"
if [ ! -f "$REPORT_SRC" ]; then
  warn "找不到 $REPORT_SRC — 跳过 user-research-report skill 安装"
else
  for SKILL_DIR in \
    "$HOME/.claude/skills/user-research-report" \
    "$HOME/.openclaw/skills/user-research-report"; do
    mkdir -p "$SKILL_DIR"
    cp "$REPORT_SRC" "$SKILL_DIR/SKILL.md"
    log "user-research-report skill → $SKILL_DIR/SKILL.md"
  done
fi

# --------------------------------------------------
# 3. 清理旧名 skill 目录（agent-reach → research-agent 改名残留）
# --------------------------------------------------
for OLD_DIR in \
  "$HOME/.claude/skills/agent-reach" \
  "$HOME/.openclaw/skills/agent-reach"; do
  if [ -d "$OLD_DIR" ]; then
    rm -rf "$OLD_DIR"
    log "已清理旧名目录: $OLD_DIR"
  fi
done

# --------------------------------------------------
# 4. 创建用户调研报告目录
# --------------------------------------------------
mkdir -p "$HOME/Desktop/我的知识库/用户调研"
log "报告目录 → ~/Desktop/我的知识库/用户调研/"

# --------------------------------------------------
# 5. 完成
# --------------------------------------------------
echo ""
echo "========================================="
echo "  迁移完成！已覆盖安装:"
echo "  [0] research-agent 代码 + Python 包"
echo "  [1] research-agent skill (含 XHS/图片下载)"
echo "  [2] user-research-report skill (文件夹格式)"
echo "  [3] 清理旧名 agent-reach skill 目录"
echo "  [4] 用户调研报告目录"
echo "========================================="
echo ""
echo "验证:"
echo "  research-agent doctor"
echo "  research-agent version"
