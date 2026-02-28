---
name: x-patrol-research
description: "X 信息流巡检 + 智能部署。两阶段：先评估生成部署计划，用户确认后再部署。简单工具自动装。"
---

# X Patrol Research — X 信息流巡检 + 智能部署

两阶段流程：
- 阶段1（cron 自动）：抓取 → 筛选 → 评估 → 简单工具立刻装 → 发部署计划带按钮
- 阶段2（用户确认后）：部署🟡🔴工具

## 阶段1：巡检 + 评估 + 简单部署

### 1. 抓取 X 信息流

```bash
bash ~/.openclaw/skills/x-patrol-report/scripts/run-patrol.sh
```

### 2. 筛选分级

读取 `/tmp/x-patrol-raw.json`，分级：
- **🔥 建议行动**：可直接部署的工具/Skill
- **👀 值得关注**：有价值但暂不行动
- **💡 仅供了解**：信息性内容

每条必须包含：标题、@handle、链接、【建议】

### 3. 发群聊（巡检报告）

用 message 发到群聊（channel=telegram, target=your-chat-id），格式同之前。

末尾加：`⏳ 正在评估🔥条目...`

### 4. 评估🔥条目

**去重检查**（每个条目必须先执行）：
```bash
ls ~/.openclaw/skills/ | grep -i "关键词"
which 工具名 2>/dev/null
pip list 2>/dev/null | grep -i "关键词"
npm list -g 2>/dev/null | grep -i "关键词"
```
已存在 → ⏭️ 跳过。

**获取部署信息（三级降级）**：

1. **优先：web_fetch 抓 GitHub README**
   - 从推文提取 GitHub 链接
   - `web_fetch` 抓 README.md
   - 分析安装方式、依赖、是否需要 API

2. **备选：Gemini CLI 查询**
   ```bash
   timeout 60s gemini -y -p "查询 [工具名]：安装方式、是否需要API、主要依赖。简洁回答"
   ```

3. **兜底：自行判断**
   - 根据工具名和描述推断复杂度
   - 不确定的归入🔴

**按复杂度分类**：

🟢 **简单工具**（立刻部署，不用问）：
- npm install -g 一键装
- pip install 一键装
- git clone + 无需配置
- 不需要 API key 或注册

🟡 **需要配置**（先装，后续问用户要配置）：
- 需要 API key
- 需要注册账号
- 需要配置文件

🔴 **复杂工具**（只生成计划，等用户确认）：
- 需要编译
- 多步骤安装
- 有安全风险
- 依赖复杂

### 5. 立刻部署🟢简单工具

对每个🟢工具：
1. 执行安装命令
2. 验证安装成功
3. 如果是 Skill，创建 SKILL.md
4. 记录结果

超时：每个工具 5 分钟，失败跳过。

### 6. 发群聊（部署结果 + 部署计划 + 按钮）

用 message 发到群聊，带 inline buttons：

```
🔧 X巡检部署报告（YYYY-MM-DD HH:MM）

━━━ ✅ 已自动部署 ━━━
🟢 工具1 — npm install -g xxx ✅
🟢 工具2 — pip install xxx ✅
⏭️ 工具3 — 已存在，跳过

━━━ 🟡 需要用户配置 ━━━
🟡 工具4 — 已安装，需要 API key
   → 请提供 [服务名] 的 API key
🟡 工具5 — 需要注册 [平台名]
   → 注册链接：https://...

━━━ 🔴 待确认部署 ━━━
🔴 工具6 — 需要编译，预计 10 分钟
   → 依赖：gcc, cmake
🔴 工具7 — 多步骤安装
   → 步骤：clone → build → configure

⏱️ 总用时：X分Y秒
📁 已归档 Obsidian
```

**按钮**（用 message 工具的 buttons 参数）：
- [✅ 全部部署] callback_data: deploy_all
- [⏸️ 暂缓] callback_data: deploy_skip
- [🔧 自定义] callback_data: deploy_custom

### 7. 归档 Obsidian

**巡检报告必须归档**：
```bash
python3 ~/.openclaw/skills/obsidian-archive/scripts/archive.py \
  --content /tmp/x-patrol-report.md \
  --dest "X巡检日报/X巡检-$(date +%Y-%m-%d).md"
```

### 8. 更新可行动建议

把🔥条目追加到 your-workspace/memory/x-insights-actionable.md。

### 9. 汇报总用时

```
✅ X巡检+部署完成
⏱️ 总用时：X分Y秒
🟢 自动部署 N 个 | 🟡 待配置 N 个 | 🔴 待确认 N 个
📁 已归档 Obsidian
```

## 阶段2：用户确认后部署（回调触发）

当用户点击按钮时：

**[✅ 全部部署]**：
- 部署所有🟡和🔴工具
- 🟡工具先装，配置用占位符，后续问用户要 API
- 🔴工具按计划执行

**[⏸️ 暂缓]**：
- 不部署，记录到待办
- 下次巡检时如果再次出现，提醒用户

**[🔧 自定义]**：
- 发消息问用户要部署哪些
- 等用户回复后执行

## 注意事项

- 抓取失败时直接报错，不继续
- **去重最重要**：已有工具绝对不要重复安装
- 🟢 简单工具立刻装，不用问
- 🟡 需要 API 的先装工具，发消息问用户要 API
- 🔴 复杂工具只生成计划，等用户确认
- **信息获取三级降级**：web_fetch GitHub > Gemini CLI > 自行判断
- 单工具部署超时 5 分钟
- 总超时 30 分钟
- 巡检报告每次必须归档 Obsidian
- 部署完成后必须汇报总用时

## 阶段2：用户确认后部署（回调触发）

当用户点击按钮后：

**[✅ 全部部署]**：
- 部署所有🟡和🔴工具
- 🟡工具如果缺 API，发消息问用户要

**[⏸️ 暂缓]**：
- 不部署，记录到待办

**[🔧 自定义]**：
- 发消息问用户要部署哪些
- 按用户指示执行

## 注意事项

- 抓取失败时直接报错，不继续
- 去重最重要：已有工具绝对不重复安装
- 🟢 简单工具立刻装，不用问
- 获取部署信息优先用 web_fetch 抓 GitHub README
- Gemini CLI 是备选，超时 60 秒自动跳过
- 实在查不到就自行判断，不确定的归🔴
- 单工具部署超时 5 分钟
- 总超时 30 分钟
- 巡检报告每次必须归档 Obsidian
