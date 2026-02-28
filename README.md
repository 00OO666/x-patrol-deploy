# 🔍 X Patrol Deploy

X (Twitter) 信息流巡检 + 智能部署 Skill for [OpenClaw](https://github.com/openclaw/openclaw)

自动抓取 X 推荐页和收藏夹，AI 筛选分级，三级评估复杂度，简单工具一键部署到你的 Agent 团队。

## ✨ 特性

- **自动抓取**：Chrome headless 抓取 X 推荐页 + 收藏夹
- **AI 筛选**：🔥建议行动 / 👀值得关注 / 💡仅供了解 三级分类
- **智能评估**：自动分析工具复杂度（🟢简单/🟡需配置/🔴复杂）
- **一键部署**：🟢简单工具自动安装，🟡🔴生成部署计划等确认
- **去重检查**：自动检测已安装的工具，避免重复部署
- **三级降级**：web_fetch GitHub README → Gemini CLI → 自行判断
- **Obsidian 归档**：巡检报告自动归档到 Obsidian vault
- **Telegram 交互**：部署计划带按钮，少主一键确认

## 📋 工作流程

```
阶段1（每日自动）
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 抓取 X  │ →  │ AI筛选  │ →  │ 评估    │ →  │ 🟢自动装│
│ 信息流  │    │ 分级    │    │ 复杂度  │    │ 发计划  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                  ↓
阶段2（少主确认后）                          ┌─────────┐
┌─────────┐    ┌─────────┐                  │ 按钮确认│
│ 部署🟡🔴│ ←  │ 问API   │ ←               │✅⏸️🔧  │
│ 工具    │    │ 要配置  │                  └─────────┘
└─────────┘    └─────────┘
```

## 🚀 安装

### 前置要求

- [OpenClaw](https://github.com/openclaw/openclaw) 已安装并运行
- Chrome/Chromium（用于 headless 抓取）
- Python 3.8+
- X (Twitter) 账号已登录（Cookie 有效）

### 一键安装

```bash
# 克隆到 OpenClaw skills 目录
git clone https://github.com/00OO666/x-patrol-deploy.git \
  ~/.openclaw/skills/x-patrol-deploy

# 复制抓取脚本（如果还没有）
cp ~/.openclaw/skills/x-patrol-deploy/scripts/run-patrol.sh \
  ~/.openclaw/skills/x-patrol-report/scripts/run-patrol.sh
```

### 配置 Cron

在 OpenClaw 中添加定时任务：

```json
{
  "name": "X巡检+智能部署",
  "schedule": { "kind": "cron", "expr": "0 9 * * *", "tz": "Asia/Shanghai" },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "执行 x-patrol-deploy Skill（~/.openclaw/skills/x-patrol-deploy/SKILL.md）",
    "timeoutSeconds": 3600
  }
}
```

## 🎯 智能分类

| 分类 | 条件 | 处理方式 |
|------|------|----------|
| 🟢 简单 | npm/pip 一键装，无需 API | 立刻自动部署 |
| 🟡 需配置 | 需要 API key 或注册 | 先装工具，问你要配置 |
| 🔴 复杂 | 需编译/多步骤/有风险 | 生成计划，等你确认 |
| ⏭️ 跳过 | 已安装 | 去重检测，自动跳过 |

## 🔄 三级降级评估

获取工具部署信息时，按优先级降级：

1. **web_fetch GitHub README**（最准确，不依赖 API）
2. **Gemini CLI 查询**（备选，需要 Gemini 配置）
3. **自行判断**（兜底，根据工具名和描述推断）

## 📁 文件结构

```
x-patrol-deploy/
├── SKILL.md          # OpenClaw Skill 定义
├── README.md         # 本文件
├── scripts/
│   ├── run-patrol.sh # Chrome headless 抓取脚本
│   └── scraper.py    # X 信息流抓取器
└── examples/
    └── cron.json     # Cron 配置示例
```

## 📊 输出示例

### 巡检报告

```
🔍 X信息流巡检报告（2026-02-28 09:00）

━━━ 🔥 建议行动 ━━━
1. 🔥 Agent Reach 开源脚手架 — @GitHub_Daily
🔗 https://github.com/example/agent-reach
📊 回复15 | 转发127 | 赞543
【建议】一键给 AI Agent 装上全能互联网接口

━━━ 👀 值得关注 ━━━
2. 👀 GitNexus 代码知识图谱 — @GitHub_Daily
🔗 https://github.com/example/gitnexus

📊 扫描统计：推荐页35条 + 收藏夹28条 = 共63条（精选16条）
```

### 部署报告

```
🔧 X巡检部署报告（2026-02-28 09:15）

━━━ ✅ 已自动部署 ━━━
🟢 agent-reach — npm install -g agent-reach ✅
⏭️ x-tweet-fetcher — 已存在，跳过

━━━ 🟡 需要配置 ━━━
🟡 6551-mcp — 已安装，需要 X API key

━━━ 🔴 待确认 ━━━
🔴 polymarket-cli — 需要 Rust 编译环境

[✅ 全部部署] [⏸️ 暂缓] [🔧 自定义]
```

## 🤝 贡献

欢迎 PR 和 Issue！

## 📄 License

MIT
