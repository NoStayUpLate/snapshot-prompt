---
name: snapshot-prompt
description: 为本次 AI 会话生成提示词存证/总结文件（核心汇总 / 规范快照 / AI 决策 / 用户原文 四段式），落盘到 prompt-snapshots/<主题>_<YYYY-MM-DD>.md（在 git 仓时文件名会带分支段）。支持跨会话历史选择 + 主题归纳确认 + 敏感信息脱敏；只生成文件、不做任何 git 操作。可在 git 仓使用（文件名带分支、§2 用 hash 引用），也可在任意目录独立使用。用法：一段 AI 协作告一段落、想留存提示词/决策时显式调用本 skill。关键词：snapshot-prompt、提示词存证、prompt snapshot、AI 协作存证、prompt log、prompt audit。
---

<!--
Date: 2026-05-14
Creator: Claude Code (snapshot-prompt plugin)
Purpose: Claude Code skill —— 团队 AI 协作"提示词存证"流程的执行规范（plugin 版，命名规范已内联，无外部仓库依赖）
-->

# Snapshot Prompt — 提示词存证 Skill

> 👋 **新成员入门见仓库根 [README.md](../../../README.md)**——介绍 skill 的目的 / 使用流程 / 产物结构 / 数据边界，比本文件（行为规范）更易上手。本文件是 AI 执行规范，README 是给人看的使用说明。

## 可配置：存证落盘目录

本 skill 默认把存证文件落到**仓库根下的 `prompt-snapshots/` 目录**。这是面向通用团队的中性默认值。

> 🔧 **改成你团队的约定**：若你们有既定的存证目录（例如用 GitLab 的团队习惯放 `.gitlab/approvals/prompts/`、用 GitHub 的可能放 `.github/prompt-snapshots/`），把本节这一行的路径改掉即可——全文凡提到「存证目录」处都以本节为准。下文示例统一用 `prompt-snapshots/`。

## 何时调用

| 类型 | 说明 |
| --- | --- |
| **显式触发** | 用户在 Claude Code 中调用 `/snapshot-prompt`，或在对话中说"运行 snapshot-prompt skill"、"做一次提示词存证" |
| **典型场景** | 一次 AI 协作告一段落（产生了代码 / SQL / 文档 / 分析结论），想把本次会话的提示词背景固化成一份可追溯 / 可复现的文件。若在 git 仓，可随分支进 PR / MR 评审；也可只留本地、贴 wiki 或归档到别处 |
| **不触发** | 用户只是讨论本 skill、查询用法、引用关键词——必须是命令式显式调用 |

> ⚠️ **只生成文件、不做任何 git 操作**。本 skill 仅生成存证文件 + 跑脱敏审查；落盘后如何归档由用户自行决定（`git add` + `git commit` 随 PR / MR 进仓、留本地、或贴到 wiki / 知识库均可）。设计上避免 skill 拥有任何写仓 / 提交权，保留用户最后审查环节。

## 任务

把本次 AI 会话所依赖的**用户提示词、规范上下文、AI 关键决策**落盘为一份独立 markdown 文件，供后续追溯与复现（在 git 仓时可随分支进 PR / MR 评审）。

文件命名规范见下方 §文件命名规范。

## 输入

1. 当前会话**所有用户消息原文**，外加用户在触发时**选中的历史会话**的用户消息（写入 §1）。历史会话来源见下方"跨会话历史选择"段
2. 当前会话触发时刻 AI 看到的规范文件：system prompt、根目录 `CLAUDE.md`（若存在）、本 skill 文件、其他主动加载的 skill 文件（写入 §2）
3. 当前会话 AI 的关键决策走向（写入 §3，基于上下文复述）

### 跨会话历史选择

> ⚠️ 一个完整任务常跨多次 Claude Code 会话才完成（设计 → 实现 → 测试 → 修复）。仅取当前会话会丢前几轮的决策语境。

机制：本 plugin 注册的 SessionEnd hook（脚本 `${CLAUDE_PLUGIN_ROOT}/scripts/write_session_meta.py`）会在每次 session 结束时写一份侧车 `<uuid>.meta.json`（与 jsonl 同目录，即 `~/.claude/projects/<proj>/` 下），包含 `session_id` / `git_branch` / `cwd` / `timestamp` / `first_message_excerpt` / `user_turns` 等字段——这是历史会话候选的索引。**此外，skill 触发时会先自动跑一次 `--backfill`（见下方步骤 1）补齐插件安装前 / 异常退出漏写的会话**，因此装好后**首次**取历史即可看到当前项目的全部历史会话，无需等新会话逐个结束。

> ℹ️ **hook 由 plugin 安装时自动注册**，无需用户手动配置 `~/.claude/settings.json`。脚本随 plugin 分发，源真值见同仓 [`scripts/write_session_meta.py`](../../scripts/write_session_meta.py)。若装好 plugin 后 meta 文件不生成，见仓库根 [README.md](../../../README.md) 的"故障排查"段（多半是 hook 命令里的 `python` 不存在或不指向 3.7+）。

skill 触发时按以下步骤选择历史会话：

1. **自动补齐索引（backfill）**：先用 `Glob` 找已安装脚本 `~/.claude/plugins/cache/*/snapshot-prompt/*/scripts/write_session_meta.py`（`*` 兼容 marketplace 名与版本号，多个匹配取最新一个）。找到则用 Bash 跑 `python "<脚本路径>" --backfill`（若 `python` 不在，依次试 `py -3` / `python3`，见仓库根 README「跨平台说明」），给所有**缺 meta 的历史 jsonl**（含插件安装前就存在、或异常退出没触发 SessionEnd hook 的会话）补侧车索引。这一步让「装好后首次取历史」就能看到当前项目的全部历史会话，而不只是装后新结束的。
   - **幂等**：已有 meta 的会话只做一次 `exists()` 判断即 skip、不读 jsonl，稳态开销可忽略，所以每次触发都跑无妨。
   - **降级**：Glob 找不到脚本（非插件方式安装本 skill）或无可用 python → **跳过本步**，用现有 meta 继续，**不报错中断**。
   - backfill 可能给「当前仍在进行的会话」也写一份**部分** meta，无妨：它在第 4 步按 session_id 被排除出 picker，且会在本会话 SessionEnd 时被 `force=True` 覆盖刷新。
2. 用 `Glob` 扫 `~/.claude/projects/*/[0-9a-f]*.meta.json`（顶级文件，非 `subagents/`）；当前会话 cwd 通过 `git status` 或 system context 拿到
3. 过滤：**始终**保留 `cwd` 与当前一致的 meta。**若当前在 git 仓**（拿得到当前分支），再优先按 `git_branch` 与当前分支一致过滤（跨分支也是常态——若你要纳入异分支会话需用户在 picker 里显式勾选）；**若不在 git 仓 / 拿不到分支**，跳过分支过滤，仅按 `cwd`
4. 按 `timestamp` 倒序取最近 **10** 个候选，**排除当前会话本身**
5. 用 `AskUserQuestion`（`multiSelect: true`）列出候选，每项 label 用 `<HH:MM 月-日> · <首条消息前 30 字> · <user_turns 轮>`，让用户多选要纳入的历史会话
6. 选中的 session 对应 jsonl 全文读出，按时间顺序提取所有 user 消息（跳过 `isSidechain:true` 与 `attachment` / `queue-operation` 类型）合并到 §1，每个 session 用 `## Session <短 id 前 8 位> · <YYYY-MM-DD HH:MM> · 分支 <branch>` 头分隔，session 内仍用 `### Turn N (HH:MM)` 子标题

> 注：（若在 git 仓）`git diff main...HEAD` 与未提交改动仅用于辅助 AI 写 §3 决策复文，**不写入本文件**——diff 可以从 git 直接获取，无需在存证里重复。不在 git 仓时跳过这步，§3 仅凭会话 context 复述。

## 输出：`prompt-snapshots/<主题>_<branch>_<YYYY-MM-DD>.md`（不在 git 仓时省略 `_<branch>`）

文件名按下方 §文件命名规范确定（5-15 字中文主题打头 + 分支名清洗 + 日期级精度，同名自动 `_v2`/`_v3` 防撞）。落盘目录见顶部 §可配置 小节。

### 文件命名规范

适用范围：**所有由本 skill 生成、落到存证目录下的存证文件**。

- **格式**：**git 仓内** `<主题>_<branch>_<YYYY-MM-DD>.md`；**不在 git 仓 / 拿不到分支** `<主题>_<YYYY-MM-DD>.md`（连同 `<branch>` 段及其前导下划线一并省略）
- **字段顺序设计**：主题打头便于 `ls` 一眼扫描业务用途；branch 居中（仅 git 仓出现）；日期殿后（日期级精度，时间序用 `ls -t`）
- **时区**：本地时间（默认团队统一 UTC+8 China Standard Time；跨时区团队按需调整）
- **精度**：日期级——同日同分支同主题二次触发自动追加 `_v2` / `_v3` / `_vN` 后缀防撞，无需用户介入
- **主题字段**：5-15 字中文短语，**描述本次 AI 协作的核心任务**（如"新建随机数测试脚本"、"重构审批流为 skill"），禁止写"提示词存证"、"AI 协作"等空话。由 AI 助手从会话内容归纳一个候选 → 通过 AskUserQuestion 让用户**总是确认一次**后再落盘。文件名安全处理：剔除文件系统保留字符（`< > : " / \ | ? *`）与控制字符，把空白替换为 `_`，超 15 字截断
- **branch 字段（仅 git 仓）**：实际 git 分支名（`git rev-parse --abbrev-ref HEAD`），把所有非 `[a-zA-Z0-9._-]` 字符（包括 `/`、空格、Unicode 等）替换为 `_`。**不在 git 仓 / 命令失败拿不到分支时，整段（含前导下划线）省略**
- **示例**：
  - git 仓内：`新建随机数测试脚本_analysis_zhangzihan_2026-05-14.md` 表示分支 `analysis_zhangzihan` 于 2026-05-14 为"新建随机数测试脚本"任务触发存证；当日二次触发同主题则落 `_v2` 后缀
  - 非 git 仓：`新建随机数测试脚本_2026-05-14.md`（无分支段）

### 元信息块（文件头之后第一段）

- **触发时间**：YYYY-MM-DD HH:MM:SS（本地）
- **分支**：实际 git 分支名（**仅 git 仓**，否则省略此行）
- **HEAD git short hash**：触发时刻的 `git rev-parse --short HEAD`（**仅 git 仓**，否则省略此行）
- **AI 助手标识**：模型 ID 与版本（如 `claude-opus-4-7[1m]`），便于后续比对不同模型在同一规范下的表现差异
- **脱敏标记**（如有）：列出本次替换为占位符的敏感字段类型

### 四段式正文

> 排序意图：可执行/可复现的内容靠前（§1 核心提示词），上下文与决策中部（§2 §3），最厚的原始证据垫底（§4）。reviewer 一展开文件就能拿到"能复现的提示词列表"，不必先翻完几十 KB 原文。

#### §1 提示词核心汇总

**意图**：给一个能复制粘贴复现的提示词序列。reviewer 拿了这一节就能在自己机器上重跑、得到差不多的产物。

**结构**：

```markdown
> 复现指南：把以下提示词按顺序投给同等级 Claude Code 实例（同 system prompt 体系 / 同项目目录），应能复现本次成果或非常接近的版本。
> AskUserQuestion 答案以 `(答: <选项>)` 行内注释表示。

### 1. <一句话标题，描述这条提示词的作用>

\```
<verbatim 用户提示词原文>
\```

→ 产生：<简述这条提示词驱动的具体改动 / 决策走向>

### 2. <下一条标题>
...
```

**挑选标准**（AI 在归纳时遵循）：

- ✅ 任务首条 / 主要起点提示词
- ✅ 改变方向 / 推翻早先决策的纠偏提示词
- ✅ 架构选择性 / 范式性提示词（"用 A 不用 B"、"放到 X 不放 Y"）
- ✅ AskUserQuestion 的关键回答（影响走向的二选一）
- ❌ "继续" / "好的" / "OK" 等机械响应
- ❌ 复述前文已说过的内容
- ❌ 工具调用接续语

**篇幅控制**：5-15 条最实质性的提示词；超 15 条说明全文都很核心，回去想想哪些其实是过渡，能合并或丢

#### §2 规范快照（触发时刻的"Prompt 环境"）

列出触发时刻 AI 看到的所有规范文件，**采用混合策略**避免重复存储：

- **不在 git 仓 / 拿不到 hash 时**：所有规范文件一律走下面的「嵌入完整内容」分支（没有 hash 可引用，git 回放指针也无意义）。
- **Git 追踪且工作树干净的文件**（典型：本 SKILL.md、项目根 `CLAUDE.md`）：
  写一行 `<path> @ <git short hash>`，可选附 SHA-256 内容摘要。读者凭 hash 可以 `git show` 还原完整内容。
- **工作树有未提交修改 / 处于 untracked / 被 `.gitignore` 排除的文件**（典型：本地 `CLAUDE.md`、本次会话新建尚未 commit 的文件）：
  **嵌入完整内容**到 ` ```markdown ... ``` ` 代码块，确保未来 working tree 改变后仍能复现当时环境。
- **§1 已纳入会话 ≥ 3 段或总 §4 篇幅 ≥ 30KB 时**：允许 §2 嵌入策略降级为"骨架结构 + git 跨版本回放指针"，避免单份存证 100KB+ 失控（此降级仅在 git 仓内可用——无 hash 时仍须嵌入完整内容）

#### §3 AI 关键决策复文

按时间顺序列出本会话中影响代码 / 文档产物的关键决策点。每点结构：

- **用户提示**：触发该决策的用户消息要点（一两句）
- **Claude 决策**：AI 当时的判断 / 选项分析 / 最终走向
- **结果**：落到代码 / 文档 / 配置的具体改动（带文件路径与行号）

> ⚠️ 本段为**基于当前会话 context 的复述**，**非逐字日志**。Claude 没有"导出自身全部历史输出"的能力，复文中可能存在小幅措辞偏差，但关键决策走向与结果必须真实。

#### §4 用户消息原文

按 turn 顺序列出本会话**所有用户消息**，每条加 `### Turn N (HH:MM)` 子标题；**保留中文原貌、代码块、链接和换行**，不重写、不重组、不缩略——这是 §1 / §3 的原始证据，审计追溯最终凭据。

若用户在触发时选择了历史会话（见上方"跨会话历史选择"），按 session 时间倒序排布：每个 session 以 `## Session <短 id 前 8 位> · <YYYY-MM-DD HH:MM> · 分支 <branch>` 二级标题开头，session 内再按 `### Turn N (HH:MM)` 排列；当前会话**永远放在最后**作为"最新一节"。

## 敏感信息脱敏（CRITICAL）

写入前**必须**对用户原文做敏感信息扫描。发现以下任意一类，**停下询问用户**是否替换为占位符 `<REDACTED:<类型>>`，禁止未经确认直接落盘：

| 类型 | 检测启发 | 占位符 |
| --- | --- | --- |
| 密码 / API Key / Token | 形如 `pwd=...`、`api_key=...`、`Bearer xxx`、20+ 字符随机串 | `<REDACTED:password>` / `<REDACTED:apikey>` |
| 生产数据库连接串 | `mysql://...`、`clickhouse://...` 含 user:pass@host | `<REDACTED:dsn>` |
| 手机号 | 11 位数字以 13/14/15/16/17/18/19 开头 | `<REDACTED:phone>` |
| 邮箱 | 标准邮箱格式（**仅豁免** RFC 2606 保留域：`@example.com` / `@example.org` / `@example.net`） | `<REDACTED:email>` |
| 隐私转发邮箱 | DuckDuckGo (`@dr.com` / `@duck.com`)、Apple (`@privaterelay.appleid.com`)、SimpleLogin (`@simplelogin.*`)、Firefox Relay (`@mozmail.com`) 等——**视为高敏感**，每个别名背后都是真人，泄露无法通过换地址挽回 | `<REDACTED:relay_email>` |
| 身份证号 | 18 位（含 X） | `<REDACTED:idcard>` |
| 客户姓名 / 内部代号 | 上下文中明显为真实人员 / 客户标识 | `<REDACTED:name>` |
| 机器绝对路径 | `C:/Users/<具体用户名>/...` 中的用户名 | `<REDACTED:username>`（路径其余部分保留） |

确认完成后才允许写文件。如果用户授权"原样保留"，需要在元信息块的**脱敏标记**字段中明确标注 `脱敏：已征得用户同意保留原值`。

### ⚠️ 脱敏标记本身禁止泄露原值

元信息块中记录脱敏行为时**只写"类型 + 位置 + 占位符"**，绝不写被脱敏的原值。原值若出现在脱敏标记里，会随文件进入 git 仓库——等同于没脱敏，且常常比正文里的脱敏更显眼（reviewer 第一眼就看到）。

**反例（禁止——示例本身使用 RFC 2606 保留域，绝不要拿真实用户值当反例）**：

```
- ✅ `alice@example.com` → `<REDACTED:email>`            ← 把原值写出来等于没脱敏
```

**正例（推荐）**：

```
- ✅ user email（§2 system context 中 1 处）→ `<REDACTED:email>`
- ✅ Windows 路径中的用户名（§2 多处）→ `<REDACTED:username>`
```

> ⚠️ 写规范文件 / 示例时本身也要遵守脱敏规则。AI 助手会从会话 system context（如 `userEmail` 字段）"凑示例"——任何示例值都必须用 RFC 2606 保留域 / 占位符，绝不要复用会话里看到的真实账号、路径、IP。

唯一例外：**用户明确授权"原样保留"** 的字段，因为它本来就出现在正文里，脱敏标记中写出来不增加泄露面（如：`⚪ 内部 GitLab IP 192.168.x.y，用户授权保留`）。

### §1 高敏感片段处理（默认折叠 / 反向授权）

§1 要求**逐字保留**用户消息——但**代码块 / shell 命令 / 配置片段 / 多行日志**是凭证最常溜进 git 的渠道。自然语言里的 "我之前用 admin/123456 登过" 上面的脱敏表能命中；但贴在 ` ``` ` 围栏里的 `DB_PASSWORD=...` 或 `mysql://user:pass@host` 经常在审脱敏弹窗时被一键 Yes 放行。

**默认折叠策略——反过来的安全态**：

任何包含以下结构的片段，**默认整段替换为 `<REDACTED:credential_block>`**，由用户在脱敏确认环节**主动指认"这段是无敏感字段，请保留原文"** 才恢复；不再要求用户从一大段代码里"挑出哪段要脱敏"：

- 三引号 / 反引号围栏代码块（` ``` ` 或 `~~~`）
- 行首像 `export KEY=`、`<KEY>=<VALUE>`、`Bearer xxx`、`mysql://` / `clickhouse://` / `postgres://` 等连接串前缀的命令式片段
- 形如 `[A-Za-z0-9+/=]{20,}` 的长随机串（疑似 token / hash / base64 凭证）
- 多行日志输出（含时间戳、log level、stack trace 等结构）

**为什么反过来**：用户在 AskUserQuestion 上"匆忙点 Yes"是一种已知行为偏差。

- 正向（默认保留、要求用户挑出敏感段）—— 漏检 = 凭证入 git，**事故**
- 反向（默认折叠、要求用户主动指认无害段）—— 漏检 = 一段无害代码被打码，**只是 reviewer 看不到代码**

漏检方向反过来之后，最坏后果从"安全事故"降级为"可读性下降"，安全是稳赢方向。

**用户授权恢复时的记录**：在元信息块的**脱敏标记**字段标注：

```
- ⚪ §1 Turn N 代码块（30 行 SQL）已恢复原文，用户确认无敏感字段
```

注意按上文"§脱敏标记本身禁止泄露原值"的规则——只记位置 + 行数，不复述代码内容。

## 触发流程

1. Claude Code 通过 Skill tool 调用本 skill（用户输入 `/snapshot-prompt` 或要求"运行 snapshot-prompt skill"）
2. 读取本文件 → 准备元信息块与四段式正文内容草案
3. **跨会话历史选择**：按 §输入"跨会话历史选择"段流程扫 meta 文件、过滤同 cwd（git 仓内再叠加同分支过滤），取最近 10 个候选，AskUserQuestion (multiSelect) 让用户多选要纳入的历史会话。可全不选 → 仅当前会话
4. **主题归纳与确认**：从**所有已纳入会话**的内容归纳 1 个 5-15 字中文主题候选（描述核心任务，禁止"提示词存证"等空话），用 AskUserQuestion **总是问一次**让用户确认或改写。文件名安全处理：剔除 `< > : " / \ | ? *` 与控制字符，空白替换为 `_`，超 15 字截断
5. **提示词核心汇总归纳**：从已纳入会话所有 user 消息中按 §1 挑选标准筛 5-15 条最实质性提示词，写入 §1；不再问用户确认（如果错，用户在审稿时改文件即可）
6. **敏感信息扫描**：对 §4 用户原文（含所有纳入会话）跑一遍脱敏检测；命中即询问用户
7. **§4 代码块默认折叠**：把代码块 / 连接串 / 长 token / 日志默认替换为 `<REDACTED:credential_block>`，询问用户哪些需要恢复原文
8. **同名冲突检测**：若目标文件名（git 仓内 `<主题>_<branch>_<日期>.md`，否则 `<主题>_<日期>.md`）已存在，追加 `_v2` / `_v3` / `_vN` 直到唯一，不弹窗
9. 按命名规范确定最终文件名 → 落盘到存证目录（默认 `prompt-snapshots/`，见顶部 §可配置）
10. 用 markdown 相对链接把产出路径回报给用户；如何归档由用户自行决定（git 仓可 `git add` + `git commit` 随 PR / MR 进仓，也可留本地或贴 wiki）——**本 skill 不做任何 git 操作**

---

## 附录 A：write_session_meta.py 脚本

跨会话历史能力依赖一个 SessionEnd hook + 一个 Python 脚本。本 plugin 已把二者打包：

- **脚本**：[`scripts/write_session_meta.py`](../../scripts/write_session_meta.py)（同仓，~120 行 stdlib-only Python 3.7+，源真值；**不再内嵌于本文件**，避免双份维护）
- **hook 声明**：[`hooks/hooks.json`](../../hooks/hooks.json)（plugin 安装时由框架自动注册 SessionEnd hook，命令通过 `${CLAUDE_PLUGIN_ROOT}` 引用上面脚本）

脚本两种模式：

- **SessionEnd hook 模式**（默认，无参数）：从 stdin 读 hook context，定位本 session 的 jsonl，写侧车 `<uuid>.meta.json`
- **`--backfill` 模式**：扫 `~/.claude/projects/*` 下所有 jsonl，给没有 meta 的补一份（已有 meta 的 skip，幂等）。**skill 现在每次触发会自动跑一次 backfill（见 §跨会话历史选择 步骤 1），所以手动跑通常已无必要**；仅在排障、或想脱离 skill 立即建索引时手动执行：
  ```
  python <plugin安装路径>/scripts/write_session_meta.py --backfill
  ```

故障排查见仓库根 [README.md](../../../README.md) 的"故障排查"段。
