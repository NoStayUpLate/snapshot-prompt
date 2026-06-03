<!--
Date: 2026-06-03
Creator: Claude Code (snapshot-prompt plugin)
Purpose: Single authoritative README (English) — marketplace intro + install + usage + troubleshooting + privacy + maintenance, for all readers (users / maintainers). The AI execution spec lives in SKILL.md.
-->

# xinguan-analysis · snapshot-prompt plugin

A **Claude Code plugin marketplace** (marketplace name `xinguan-analysis`) shipping a single plugin:

- **`snapshot-prompt`** — generates a "prompt provenance / summary" markdown for the current AI session, saved as a traceable, reproducible file. Inside a git repo it can be committed alongside the branch as a PR / MR review artifact and future reproduction guide; outside a git repo it still works standalone (keep it local, paste into a wiki / knowledge base, etc.).

> 📑 This file is the **only human-facing doc** (intro / install / usage / troubleshooting / maintenance). There is also a separate [`snapshot_prompt/skills/snapshot-prompt/SKILL.md`](snapshot_prompt/skills/snapshot-prompt/SKILL.md) which is the **AI execution spec** (Claude Code loads it to drive `/snapshot-prompt` behavior). It is not intended for human reading and you usually don't need to open it.

> 🌏 The default README is in Chinese. See [`README.md`](README.md) for the Chinese version.

## Table of Contents

- [What this plugin solves](#what-this-plugin-solves)
- [Installation (offline zip, zero auth)](#installation-offline-zip-zero-auth)
- [How to use](#how-to-use)
- [What the output looks like](#what-the-output-looks-like)
- [Typical scenarios](#typical-scenarios)
- [Troubleshooting](#troubleshooting)
- [Privacy boundary](#privacy-boundary)
- [Cross-platform notes (hook interpreter)](#cross-platform-notes-hook-interpreter)
- [Customizing the output directory](#customizing-the-output-directory)
- [Repository layout](#repository-layout)
- [Maintenance: packaging the distribution zip](#maintenance-packaging-the-distribution-zip)

---

## What this plugin solves

You just finished a multi-turn AI-assisted task in Claude Code (wrote some code, ran an analysis, drafted some docs) and want to keep a record. The problem is:

- A few weeks later you look back at the artifact and **can't remember what instructions you gave the AI** — the commit message / file itself only records "what was done", not "why it was done this way".
- A teammate doing review **can't see the AI collaboration process** — they only see the final artifact, not the key corrections / option analyses / proposals you rejected.
- Someone wants to **reproduce** your result — they don't know which prompts to feed the AI to get a similar output.

`/snapshot-prompt` solves all three at once. Core capabilities:

- **Four-section provenance file**: core prompt summary / spec snapshot / AI key decisions / raw user messages.
- **Cross-session history**: when a single task spans multiple Claude Code sessions, you can include historical sessions in the snapshot (powered by a SessionEnd hook registered with the plugin + auto-backfill on trigger to build the index, **including sessions that existed before installing the plugin**).
- **Sensitive info redaction**: scans for passwords / connection strings / phone numbers / emails before saving; code blocks are collapsed by default (opt-in restore).
- **Does not touch git**: only generates the file. How to archive it (commit to git / keep local / paste into wiki) is entirely up to you.

## Installation (offline zip, zero auth)

This plugin is distributed as an offline zip — **no GitLab account, SSH key, or access token required** — unzip and install.

**Step 1: Unzip**

Extract the `snapshot-prompt-plugin.zip` you received into any directory, e.g. `D:\tools\snapshot-prompt\` (you should see `.claude-plugin\marketplace.json` and a `snapshot_prompt\` subdirectory inside).

> No command line needed — on Windows, right-click the zip → "Extract All".

**Step 2: Register and install**

> 💭 **Why two commands after extracting — can't I just drop the folder into the skills directory?** Dropping the skill folder does make `/snapshot-prompt` available, but **you lose the "cross-session history" capability** — that feature relies on the SessionEnd hook bundled with the plugin, which only registers via `marketplace add` + `install`. For full functionality, follow the steps below.

> ⚠️ `/plugin` is an interactive command — **available only in the standalone `claude` REPL terminal**. Inside IDE-embedded chat (VSCode / Cursor / etc.) it reports `/plugin isn't available`. In IDEs, use the `claude plugin ...` CLI subcommands instead.

Replace the paths in the commands below with **your actual extracted directory** from Step 1:

```
# Standalone REPL:
/plugin marketplace add D:\tools\snapshot-prompt
/plugin install snapshot-prompt@xinguan-analysis

# IDE-embedded chat / integrated terminal:
claude plugin marketplace add D:\tools\snapshot-prompt
claude plugin install snapshot-prompt@xinguan-analysis
```

> 💡 **Don't want to memorize commands?** Just send this in the IDE chat and let Claude do it for you:
> > Please install the snapshot-prompt plugin. The extracted directory is `D:\tools\snapshot-prompt` (replace with your actual path). Run `claude plugin marketplace add <that directory>` and `claude plugin install snapshot-prompt@xinguan-analysis` in the terminal. After installing, run `claude plugin list` to confirm status is enabled, then tell me whether I need to restart.

**Step 3: Restart Claude Code**

So the SessionEnd hook registered by the plugin takes effect. After installing, type `/snapshot-prompt` to use it.

> ℹ️ **About updates**: the zip is an offline snapshot and **does not auto-update**. When a new version is released, re-acquire the zip, extract over the previous one, and run `claude plugin marketplace update xinguan-analysis` (or remove and re-add).
>
> ℹ️ **Don't delete the extracted directory**: `marketplace add` registers a reference to that directory — it does not copy files into Claude Code. Deleting the extracted directory disables the plugin. Put it somewhere stable (e.g. `D:\tools\snapshot-prompt\`) and keep it.

## How to use

**When to trigger**: when an AI collaboration round wraps up and you want to record the session. (If you work inside a git repo, just before `git commit` is a natural trigger point — but not required. Works outside git repos too.)

**When NOT to use**:

- Throwaway scripts / debug one-shot code → no need to record.
- Typo fixes / formatting tweaks / comment edits that don't need AI design input → no need.
- Work is still in progress → wait until it's wrapped up.

After installing, in Claude Code type:

```
/snapshot-prompt
```

The skill asks you 4 things in order:

| Step | Prompt | What you do |
| --- | --- | --- |
| **1. Historical session selection** | "Which historical sessions should be included in §4 of this snapshot? (multi-select, can leave all unchecked)" | Lists the 10 most recent **same-project** sessions (inside a git repo, further filtered by **same branch**) (with time + first-message summary + turn count); tick the ones to include. **Only your own machine's sessions** — you can't see teammates'. Tasks spanning 2–3 sessions are common; tick them. |
| **2. Theme confirmation** | "The theme field for this snapshot (5–15 Chinese characters), goes into the filename" | The skill suggests a candidate; accept if accurate, or click "Other" to write your own. |
| **3. Sensitive info redaction** | "The following sensitive fields were found, how do you want to handle them?" | Only pops up if matches are found (passwords / phone numbers / DSN / email, etc.); decide per-item whether to replace with a placeholder or keep as-is. |
| **4. Code block restoration** | "The following code blocks were collapsed to `<REDACTED:credential_block>` by default. Which should be restored?" | Opt-in restore by design — all code blocks are collapsed by default; you manually tick the ones you've "confirmed contain no sensitive fields" to restore them. |

Once done, the skill tells you the output path, like:

> Saved: `prompt-snapshots/重构ROI周报特征工程_analysis_wangli_2026-06-03.md`

How you **archive it next is up to you** — the skill does no git operations on your behalf:

- **Inside a git repo**: after reviewing the output, commit it yourself and ship with PR / MR review —
  ```bash
  git add prompt-snapshots/<new file> <your code changes>
  git commit -m "<your commit message>"
  ```
- **Outside a git repo**: the file is already in `prompt-snapshots/` — just keep it, archive it, or paste into a wiki / knowledge base. No extra steps needed.

## What the output looks like

Filename: `<theme>_<branch>_<date>.md`, e.g. `重构ROI周报特征工程_analysis_wangli_2026-06-03.md`. The `<branch>` segment **only appears inside a git repo**; outside a git repo, the filename degrades to `<theme>_<date>.md` (e.g. `重构ROI周报特征工程_2026-06-03.md`).

File structure (four sections):

```
Header / metadata
├── §1 Core prompt summary    ← 5-15 copy-pasteable key prompts + each one's output
├── §2 Spec snapshot           ← The system prompt / CLAUDE.md / etc. the AI saw at trigger time
├── §3 AI key decision recap   ← What decisions the AI made at which forks / why
└── §4 Raw user messages       ← All user messages preserved verbatim (incl. selected historical sessions)
```

**§1 is the most useful section**: hand someone the repo, they read §1, and they can replay these prompts in their own Claude Code in order to roughly reproduce the artifact.

## Typical scenarios

**Small feature done in a single session** (refactored a feature-engineering script for an ROI weekly report, started and finished today): trigger `/snapshot-prompt` → leave historical sessions **all unticked** → theme "重构ROI周报特征工程" → handle redaction / collapse per prompts → archive the output as needed (commit alongside code in a git repo; keep local otherwise).

**Complex task across 3 sessions** (designed Monday → implemented Wednesday → fixed bugs Friday): after the final Friday edit, trigger → **multi-select the two Monday and Wednesday sessions** in the historical list → summarize the overall objective in the theme → §1 picks the most substantive 5–15 prompts across all 3 sessions → the output captures the final-change context plus "Monday's design thinking" and "Wednesday's gotchas".

**While debugging**: don't use it. Debug code itself is temporary; snapshotting it has no value.

## Troubleshooting

**Q: After installing the plugin, `/snapshot-prompt`'s historical session list is empty?**

A: Normally it shouldn't be — the skill **auto-runs a backfill on trigger** that indexes all historical jsonls for the current project (including those that existed before installing the plugin), so on the **first** trigger after installing you should see all sessions for the current project. If it's still empty, check in order:

1. **Confirm `python` is available** — both auto-backfill and the SessionEnd hook invoke the script via `python "<script>" ...` (compatible with Python 3.7+). If the `python` command doesn't exist on your machine (Windows commonly has `py -3`, some Linux/macOS have `python3`), auto-backfill silently skips and the hook produces no meta. Edit the plugin's `snapshot_prompt/hooks/hooks.json` to replace `python` with the correct interpreter command, then restart. See [Cross-platform notes](#cross-platform-notes-hook-interpreter).
2. **Restart Claude Code** — sessions opened before the plugin was installed don't have an active SessionEnd hook; only new sessions after restart will trigger one on close (auto-backfill is not affected by this, but a restart rules out partial-load issues).
3. **Manual backfill fallback** — if auto-backfill didn't solve it, run the script manually to confirm it works:
   ```
   python <extracted dir>/snapshot_prompt/scripts/write_session_meta.py --backfill
   ```

**Q: Is it safe for the skill to modify my `~/.claude/`?**

A: This plugin **does not let the skill modify your `~/.claude/settings.json`** — hooks are registered uniformly by the plugin framework at install time, and the script ships with the plugin (~120 lines of pure stdlib, no network calls, no outbound data; source at [`snapshot_prompt/scripts/write_session_meta.py`](snapshot_prompt/scripts/write_session_meta.py)). Meta files only land in your local `~/.claude/projects/` — not committed, not uploaded.

**Q: I forgot to snapshot until after I committed. What now?**

A: You can still trigger — the skill builds the snapshot from the current session + historical sessions, and the file can reference the already-committed short hash.

**Q: Can I review a teammate's snapshot on my machine?**

A: Yes — provided they archived it via a shared channel. The most common one is committing it to git so it ships with the branch; just clone and open in your editor (same for wiki / knowledge base). **However** their jsonl / meta files aren't in the shared channel, so "reproducing" means running §1's prompts on your end — you can't pull their conversation logs directly.

## Privacy boundary

- The script only reads session jsonls under your local `~/.claude/projects/` and writes a sibling `<uuid>.meta.json` index. **No network access, no outbound data, never enters git.**
- The snapshot output (`prompt-snapshots/*.md`) is the only part that could ever be shared by you — redaction runs before saving; whether to commit / paste into wiki afterward is your call.
- Teammates can't see your local session contents; the only thing shared is the snapshot markdown you actively archive (e.g. by committing).

## Cross-platform notes (hook interpreter)

The hook command in [`snapshot_prompt/hooks/hooks.json`](snapshot_prompt/hooks/hooks.json) defaults to `python`:

```json
"command": "python \"${CLAUDE_PLUGIN_ROOT}/scripts/write_session_meta.py\""
```

The script is pure stdlib, no third-party dependencies, compatible with **Python 3.7+** (uses `from __future__ import annotations` to remove the higher-version annotation syntax requirement), so most environments work out of the box.

If `python` isn't available on your machine or doesn't point to Python 3.7+, change `python` in `hooks.json` to the right command and restart Claude Code:

- **Windows**: usually `py -3`
- **macOS / Linux**: usually `python3`

## Customizing the output directory

Defaults to `prompt-snapshots/`. If your team has a convention (e.g. `.gitlab/approvals/prompts/`, `.github/prompt-snapshots/`), edit the single line in the "Configurable" section at the top of [`SKILL.md`](snapshot_prompt/skills/snapshot-prompt/SKILL.md) — that section is the source of truth.

## Repository layout

```
.
├── .claude-plugin/
│   └── marketplace.json          # Marketplace manifest (name: xinguan-analysis), source → ./snapshot_prompt
├── snapshot_prompt/              # Plugin body
│   ├── .claude-plugin/
│   │   └── plugin.json           # Plugin manifest
│   ├── skills/
│   │   └── snapshot-prompt/
│   │       └── SKILL.md          # AI execution spec (naming convention / redaction / trigger flow, all inline)
│   ├── hooks/
│   │   └── hooks.json            # SessionEnd hook declaration (auto-registered on plugin install)
│   └── scripts/
│       └── write_session_meta.py # Script that writes sidecar meta.json for session jsonls
├── README.md                     # Chinese README (default human-facing doc)
└── README_EN.md                  # This file (English README)
```

> The marketplace manifest `marketplace.json` lives at the **repo root** under `.claude-plugin/`; `/plugin marketplace add` scans from the repo root by default. Its `source: "./snapshot_prompt"` points to the plugin body directory (which contains `.claude-plugin/plugin.json`).

## Maintenance: packaging the distribution zip

The distribution `snapshot-prompt-plugin.zip` is a build artifact (already ignored by `.gitignore`, not committed). To build a new package, run this in the repo root (`git archive` ships with git; PowerShell / git bash both work):

```
git archive --format=zip --prefix=snapshot-prompt/ HEAD -o snapshot-prompt-plugin.zip README.md README_EN.md .claude-plugin snapshot_prompt
```

- Packing from `HEAD` automatically includes only committed content (no `.git` / `__pycache__` / local config), so **commit your changes first**.
- After extracting, the top-level is `snapshot-prompt/`, containing the repo-root `marketplace.json` + `snapshot_prompt/` — exactly the directory structure required by the "Installation" section above.
- Send the resulting zip to teammates. For install steps, see "Installation (offline zip, zero auth)" above.
