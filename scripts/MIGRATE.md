# 迁移指南

将 Research Agent 代码 + Skills 同步到新设备/云主机。

## 前提条件

- 目标机器已安装 Git、Python 3.10+
- 已 clone 过 reach-agent 仓库（任意分支均可，脚本会自动切换）

## 一键迁移

```bash
cd ~/Desktop/MyAgent/reach-agent
git fetch --all && git checkout refactor-v1.1 && git pull
bash scripts/migrate-skills.sh
```

## 脚本做了什么

| 步骤 | 内容 | 目标路径 |
|------|------|----------|
| 0 | 拉取最新代码 + `pip install -e .` 重装 Python 包 | 当前仓库目录 |
| 1 | 覆盖写入 `research-agent` skill | `~/.claude/skills/research-agent/SKILL.md` + `~/.openclaw/skills/research-agent/SKILL.md` |
| 2 | 覆盖写入 `user-research-report` skill | `~/.claude/skills/user-research-report/SKILL.md` + `~/.openclaw/skills/user-research-report/SKILL.md` |
| 3 | 清理旧名 `agent-reach` skill 目录 | `~/.claude/skills/agent-reach/` + `~/.openclaw/skills/agent-reach/` |
| 4 | 确保报告输出目录存在 | `~/Desktop/我的知识库/用户调研/` |

## 本次迁移涉及的改动 (2026-02-28)

### Python 源码 (refactor-v1.1)

`ffe6d15` 对所有 channel 进行了重构：

- 所有 9 个 channel 实现重写（bilibili/twitter/xhs/youtube/reddit/github/web/rss/exa）
- `cli.py` 重构（命令结构简化）
- `core.py`、`base.py` 接口优化
- 删除 douyin/linkedin/bosszhipin 三个未完成 channel
- 删除 tests/、docs/、CI（精简仓库）
- `pyproject.toml` 依赖简化

### research-agent skill

相比仓库内置的 `research_agent/skill/SKILL.md`（基础版），迁移脚本安装的是**增强版**，额外包含：

- **5 步强制工作流**：调用 skill → 采集数据 → 下载图片 → 加载报告模板 → 生成报告
- **XHS 详细用法**：API 字段映射、xsec_token 过期处理、rate limiting
- **登录降级方案**：QR 码失败时通过 Docker cookie 注入
- **图片下载流程**：curl + Referer 头，批量下载 Python 脚本

### user-research-report skill

- 报告格式从**单个 .md 文件** → **文件夹**（`README.md` + `images/`）
- 图片从引用 CDN 链接 → **下载到本地** `images/` 目录
- 新增 GitLab 自动上传流程（`~/.cache/product_user_research`）

## 验证

```bash
# 检查 Python 包
research-agent version
research-agent doctor

# 检查 skill 文件
cat ~/.claude/skills/research-agent/SKILL.md | head -5
cat ~/.claude/skills/user-research-report/SKILL.md | head -5
```

## 后续更新

以后本地改了 skill 或代码，只需：

1. 本地提交推送到 `refactor-v1.1`
2. 如果改了 skill 内容，同步更新 `scripts/migrate-skills.sh` 中的 heredoc
3. 云主机上重跑 `bash scripts/migrate-skills.sh`
