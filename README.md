<!--
Date: 2026-06-02
Creator: Claude Code (snapshot-prompt plugin)
Purpose: 单一权威 README —— 市场介绍 + 安装 + 用法 + 故障排查 + 隐私 + 维护，面向所有读者（使用者 / 维护者）。AI 执行规范另见 SKILL.md。
-->

# xinguan-analysis · snapshot-prompt 插件

一个 **Claude Code plugin marketplace**（市场名 `xinguan-analysis`），收录一个 plugin：

- **`snapshot-prompt`** —— 为本次 AI 会话生成一份"提示词存证/总结"markdown，留存为可追溯、可复现的文件。在 git 仓里可随分支进 git、作为 PR / MR 评审凭据与未来复现指南；不在 git 仓也能独立使用（留本地、贴 wiki / 知识库均可）。

> 📑 本文件是**唯一面向人的说明**（介绍 / 安装 / 用法 / 故障排查 / 维护）。另有一份 [`snapshot_prompt/skills/snapshot-prompt/SKILL.md`](snapshot_prompt/skills/snapshot-prompt/SKILL.md) 是 **AI 执行规范**（Claude Code 加载它来驱动 `/snapshot-prompt` 的行为），不是给人读的，一般无需打开。

## 目录

- [这个插件解决什么问题](#这个插件解决什么问题)
- [安装（离线 zip，零认证）](#安装离线-zip零认证)
- [怎么用](#怎么用)
- [产物长什么样](#产物长什么样)
- [典型场景](#典型场景)
- [故障排查](#故障排查)
- [隐私边界](#隐私边界)
- [跨平台说明（hook 解释器）](#跨平台说明hook-解释器)
- [自定义落盘目录](#自定义落盘目录)
- [仓库结构](#仓库结构)
- [维护：打包分发 zip](#维护打包分发-zip)

---

## 这个插件解决什么问题

你在 Claude Code 里完成一段 AI 协助的多轮工作（写了代码、跑了分析、整理了文档），想留个底。问题是：

- 几周后回看产物，**记不清当时给 AI 的指令是什么**——commit message / 文件本身只记录了"做了什么"，不是"为什么这么做"。
- 同事 review 时**看不到 AI 协作的思考过程**——只看到最终产物，不知道哪些是关键的纠偏 / 选项分析 / 你拒掉的方案。
- 别人想**复现**你的成果——不知道把哪几句提示词喂给 AI 能得到相似结果。

`/snapshot-prompt` 一次性解决这三件事，核心能力：

- **四段式存证**：核心提示词汇总 / 规范快照 / AI 关键决策复文 / 用户消息原文。
- **跨会话历史**：一个任务跨多次 Claude Code 会话时，可把历史会话一并纳入（靠随 plugin 注册的 SessionEnd hook + 触发时自动 backfill 建索引，**含安装插件前就存在的历史会话**）。
- **敏感信息脱敏**：落盘前扫描密码 / 连接串 / 手机号 / 邮箱等，代码块默认折叠（反向授权）。
- **不碰 git**：只生成文件，如何归档（进 git / 留本地 / 贴 wiki）由你自己决定。

## 安装（离线 zip，零认证）

本 plugin 以离线 zip 分发，**不需要 GitLab 账号、SSH key 或访问令牌**——拿到 zip 解压即可装。

**第 1 步：解压**

把发给你的 `snapshot-prompt-plugin.zip` 解压到任意目录，例如解压后得到 `D:\tools\snapshot-prompt\`（里面应能看到 `.claude-plugin\marketplace.json` 和 `snapshot_prompt\` 子目录）。

> 解压不需要命令行——Windows 右键 zip →「全部解压」即可。

**第 2 步：注册并安装**

> 💭 **为什么解压后还要这两条命令、不能直接把文件夹丢进 skills 目录?** 直接丢 skill 文件夹确实能让 `/snapshot-prompt` 可用，但**会丢掉"跨会话历史"能力**——那个功能靠插件里的 SessionEnd hook，只有走 `marketplace add` + `install` 才会注册 hook。所以要完整功能，就走下面这步。

> ⚠️ `/plugin` 是交互式命令，**只在独立终端的 `claude` REPL 里可用**；在 VSCode / Cursor 等 IDE 内嵌对话里会报 `/plugin isn't available`。IDE 里改用下面的 `claude plugin ...` 命令行子命令。

把下面命令里的路径换成你第 1 步的**实际解压目录**：

```
# 独立终端 REPL：
/plugin marketplace add D:\tools\snapshot-prompt
/plugin install snapshot-prompt@xinguan-analysis

# IDE 内嵌对话 / 集成终端：
claude plugin marketplace add D:\tools\snapshot-prompt
claude plugin install snapshot-prompt@xinguan-analysis
```

> 💡 **不想记命令?** 在 IDE 对话里直接发这段话，让 Claude 替你执行：
> > 请帮我安装 snapshot-prompt 插件，解压目录是 `D:\tools\snapshot-prompt`（换成你的实际路径）。在终端执行 `claude plugin marketplace add <该目录>` 和 `claude plugin install snapshot-prompt@xinguan-analysis`，装完用 `claude plugin list` 确认状态是 enabled，再告诉我是否需要重启。

**第 3 步：重启 Claude Code**

让随 plugin 注册的 SessionEnd hook 生效。装好后输入 `/snapshot-prompt` 即可使用。

> ℹ️ **关于更新**：zip 是离线快照，**不会自动更新**。插件有新版本时，需重新获取 zip、解压覆盖，再 `claude plugin marketplace update xinguan-analysis`（或移除后重新 add）。
>
> ℹ️ **解压目录别删**：`marketplace add` 注册的是该目录的引用，不是把文件拷进 Claude Code。删掉解压目录会导致插件失效——建议放一个固定位置（如 `D:\tools\snapshot-prompt\`）长期保留。

## 怎么用

**触发时机**：一段 AI 协作告一段落、想把本次会话留存下来时。（在 git 仓里工作的话，`git commit` 前是个自然的触发点，但不是必须——不在 git 仓也能用。）

**不要用的场景**：

- 临时验证脚本 / debug 一次性代码 → 不需要存证。
- 改 typo / 调格式 / 改注释这类不需要 AI 设计的小动作 → 不需要。
- 工作还没告一段落 → 等做完再触发。

安装好后，直接在 Claude Code 中输入：

```
/snapshot-prompt
```

skill 会按顺序问你 4 件事：

| 步骤 | 提示 | 你需要做什么 |
| --- | --- | --- |
| **1. 历史会话选择** | "纳入哪些历史会话到本次存证的 §4？（多选，可全不选）" | 列出最近 10 个**同项目**的会话（在 git 仓里再叠加"同分支"过滤）（带时间 + 首条消息摘要 + 轮数），勾选要纳入的。**只本机自己的会话**，看不到同事的。一次任务跨 2-3 个 session 是常态，要勾上 |
| **2. 主题确认** | "本次存证的主题字段（5-15 字中文），会进文件名" | skill 给一个候选；你觉得准就选，不准点 Other 自己写 |
| **3. 敏感信息脱敏** | "发现以下敏感字段，怎么处理？" | 只有命中（密码 / 手机号 / DSN / 邮箱等）时才弹；逐项决定占位符替换还是原样保留 |
| **4. 代码块恢复** | "以下代码块已默认折叠为 `<REDACTED:credential_block>`，哪些恢复原文？" | 反向授权设计 —— 默认折叠所有代码块，你手动勾"确认无敏感字段"的才恢复 |

完成后 skill 会告诉你产物路径，类似：

> 已落盘：`prompt-snapshots/重构ROI周报特征工程_analysis_wangli_2026-06-03.md`

接下来**怎么归档自便**，skill 不会代你做任何 git 操作：

- **在 git 仓里**：审过产物后自行 commit，随 PR / MR 进仓评审——
  ```bash
  git add prompt-snapshots/<新文件> <你的代码改动>
  git commit -m "<你的 commit message>"
  ```
- **不在 git 仓**：文件已经落在 `prompt-snapshots/` 下，直接留着、归档或贴到 wiki / 知识库即可，无需任何额外步骤。

## 产物长什么样

文件命名：`<主题>_<分支>_<日期>.md`，示例 `重构ROI周报特征工程_analysis_wangli_2026-06-03.md`。其中 `<分支>` 段**仅在 git 仓里出现**；不在 git 仓时文件名退化为 `<主题>_<日期>.md`（如 `重构ROI周报特征工程_2026-06-03.md`）。

文件结构（四段）：

```
Header / 元信息
├── §1 提示词核心汇总       ← 5-15 条可复制粘贴的关键提示词 + 各自产出
├── §2 规范快照            ← 触发时刻 AI 看到的 system prompt / CLAUDE.md / 等
├── §3 AI 关键决策复文      ← AI 在哪几个分叉做了什么决定 / 为什么
└── §4 用户消息原文         ← 所有 user 消息逐字保留（含选中的历史会话）
```

**§1 是最有用的一节**：把对方拉了仓库，看 §1 就能在自己 Claude Code 里按顺序投这些提示词，复现差不多的产物。

## 典型场景

**单 session 完成的小 feature**（改了一个 ROI 报表的特征工程脚本，今天起意今天完工）：触发 `/snapshot-prompt` → 历史会话**全不选** → 主题"重构ROI周报特征工程" → 脱敏 / 折叠按提示走 → 产物按需归档（在 git 仓就和代码一起 commit，不在就留本地）。

**跨 3 个 session 的复杂任务**（周一设计 → 周三实现 → 周五修 bug）：周五最后改完后触发 → 历史会话**多选周一和周三的两个 session** → 主题归纳整体目标 → §1 会跨 3 个 session 挑出最实质的 5-15 条提示词 → 产物里既有最终改动语境，也保留"周一的设计思路"和"周三遇到的坑"。

**Debug 时**：不要用。debug 代码本身就是临时的，存证没意义。

## 故障排查

**Q：装好 plugin 后，`/snapshot-prompt` 的历史会话列表是空的？**

A：正常情况下不该为空——skill 触发时会**自动跑一次 backfill**，给当前项目下所有历史 jsonl（含装插件前就存在的）补索引，所以装好后**首次**取历史就应看到当前项目的全部会话。若仍为空，按顺序排查：

1. **确认 `python` 可用** —— 自动 backfill 与 SessionEnd hook 都靠 `python "<脚本>" ...` 调脚本（兼容 Python 3.7+）。若你机器上 `python` 这个命令不存在（Windows 常见是 `py -3`、部分 Linux/mac 是 `python3`），自动 backfill 会静默跳过、hook 也不生成 meta。编辑 plugin 的 `snapshot_prompt/hooks/hooks.json` 把 `python` 换成正确的解释器命令，再重启。详见[跨平台说明](#跨平台说明hook-解释器)。
2. **重启 Claude Code** —— 装 plugin 之前打开的 session，其 SessionEnd hook 不生效；重启后新 session 才会在结束时触发（自动 backfill 不受此影响，但重启能排除 plugin 未完全加载的情况）。
3. **手动兜底 backfill** —— 自动 backfill 没解决时，可手动跑一次确认脚本本身工作：
   ```
   python <解压目录>/snapshot_prompt/scripts/write_session_meta.py --backfill
   ```

**Q：skill 改我 `~/.claude/` 安全吗？**

A：本 plugin **不让 skill 自己改你的 `~/.claude/settings.json`**——hook 由 plugin 框架在安装时统一注册，脚本随 plugin 分发（约 120 行纯 stdlib、无网络调用、无外发数据，源码见 [`snapshot_prompt/scripts/write_session_meta.py`](snapshot_prompt/scripts/write_session_meta.py)）。meta 文件只写到 `~/.claude/projects/` 你本机，不进 git、不上传。

**Q：我已经 commit 了才想起来存证，怎么办？**

A：仍可触发 —— skill 会基于当前会话 + 历史 session 生成存证，文件指向已 commit 的 short hash 即可。

**Q：同事的产物文件能在我机器上 review 吗？**

A：能——前提是你把产物归档到了共享渠道。最常见是 git 跟踪、随分支分发，clone 下来用编辑器打开即可（贴 wiki / 知识库同理）。**但**他的 jsonl / meta 不在共享渠道里，所以你"复现"只能照他存证里 §1 的提示词来跑，不能直接拉他的对话记录。

## 隐私边界

- 脚本只读 `~/.claude/projects/` 下你本机的 session jsonl，写一份同目录的 `<uuid>.meta.json` 索引。**不联网、不外发、不进 git**。
- 存证产物（`prompt-snapshots/*.md`）是唯一可能被你分享出去的部分——落盘前会跑脱敏审查；之后进不进 git、贴不贴 wiki 由你决定。
- 同事看不到你本地的会话内容；共享的只有你主动归档（如 commit）的存证 markdown。

## 跨平台说明（hook 解释器）

[`snapshot_prompt/hooks/hooks.json`](snapshot_prompt/hooks/hooks.json) 里的 hook 命令默认用 `python`：

```json
"command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/write_session_meta.py\""
```

脚本是纯 stdlib、无第三方依赖，兼容 **Python 3.7+**（已用 `from __future__ import annotations` 消除高版本注解语法的门槛），常见环境基本开箱即用。

若你机器上 `python` 这个命令不存在或不指向 Python 3.7+，把 `hooks.json` 里的 `python` 改成对应命令再重启 Claude Code：

- **Windows**：通常用 `py -3`
- **macOS / Linux**：通常用 `python3`

## 自定义落盘目录

默认落 `prompt-snapshots/`。若你团队有既定约定（如 `.gitlab/approvals/prompts/`、`.github/prompt-snapshots/`），改 [`SKILL.md`](snapshot_prompt/skills/snapshot-prompt/SKILL.md) 顶部「可配置」小节那一行即可，全文以该小节为准。

## 仓库结构

```
.
├── .claude-plugin/
│   └── marketplace.json          # 市场清单（市场名 xinguan-analysis），source → ./snapshot_prompt
├── snapshot_prompt/              # plugin 本体
│   ├── .claude-plugin/
│   │   └── plugin.json           # plugin manifest
│   ├── skills/
│   │   └── snapshot-prompt/
│   │       └── SKILL.md          # AI 执行规范（命名规范 / 脱敏 / 触发流程，全内联）
│   ├── hooks/
│   │   └── hooks.json            # SessionEnd hook 声明（plugin 安装时自动注册）
│   └── scripts/
│       └── write_session_meta.py # 给 session jsonl 写侧车 meta.json 的脚本
└── README.md                     # 本文件（唯一面向人的说明）
```

> 市场清单 `marketplace.json` 在**仓库根** `.claude-plugin/` 下，`/plugin marketplace add` 默认从仓库根扫描；其 `source: "./snapshot_prompt"` 指向 plugin 本体目录（内含 `.claude-plugin/plugin.json`）。

## 维护：打包分发 zip

分发用的 `snapshot-prompt-plugin.zip` 是构建产物（已被 `.gitignore` 忽略，不进仓）。需要出新包时，在仓库根执行（git 自带 `git archive`，PowerShell / git bash 均可）：

```
git archive --format=zip --prefix=snapshot-prompt/ HEAD -o snapshot-prompt-plugin.zip README.md .claude-plugin snapshot_prompt
```

- 从 `HEAD` 打包，自动只含已提交内容（不含 `.git` / `__pycache__` / 本地配置），所以**打包前先把改动 commit**。
- 解压后顶层是 `snapshot-prompt/`，内含仓库根 `marketplace.json` + `snapshot_prompt/`，即上文「安装」所需的目录结构。
- 把生成的 zip 发给同事即可，安装步骤见上文「安装（离线 zip，零认证）」。
