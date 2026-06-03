<!--
Date: 2026-06-03
Creator: Claude Code (snapshot-prompt skill)
Purpose: Single authoritative README (English) — intro + install + usage + troubleshooting + privacy + maintenance, for all readers (users / maintainers). The AI execution spec lives in SKILL.md.
-->

# snapshot-prompt

A **Claude Code skill**: generates a "prompt provenance / summary" markdown for the current AI session, saved as a traceable, reproducible file. Inside a git repo it can be committed alongside the branch as a PR / MR review artifact and future reproduction guide; outside a git repo it still works standalone (keep it local, paste into a wiki / knowledge base, etc.).

> 📑 This file is the **only human-facing doc** (intro / install / usage / troubleshooting / maintenance). There is also a separate [`snapshot_prompt/skills/snapshot-prompt/SKILL.md`](snapshot_prompt/skills/snapshot-prompt/SKILL.md) which is the **AI execution spec** (Claude Code loads it to drive `/snapshot-prompt` behavior). It is not intended for human reading and you usually don't need to open it.

> 🌏 The default README is in Chinese. See [`README.md`](README.md) for the Chinese version.

## Table of Contents

- [What this skill solves](#what-this-skill-solves)
- [Installation](#installation)
- [How to use](#how-to-use)
- [What the output looks like](#what-the-output-looks-like)
- [Typical scenarios](#typical-scenarios)
- [Troubleshooting](#troubleshooting)
- [Privacy boundary](#privacy-boundary)
- [Optional: enable cross-session history (manually register the SessionEnd hook)](#optional-enable-cross-session-history-manually-register-the-sessionend-hook)
- [Customizing the output directory](#customizing-the-output-directory)
- [Repository layout](#repository-layout)

---

## What this skill solves

You just finished a multi-turn AI-assisted task in Claude Code (wrote some code, ran an analysis, drafted some docs) and want to keep a record. The problem is:

- A few weeks later you look back at the artifact and **can't remember what instructions you gave the AI** — the commit message / file itself only records "what was done", not "why it was done this way".
- A teammate doing review **can't see the AI collaboration process** — they only see the final artifact, not the key corrections / option analyses / proposals you rejected.
- Someone wants to **reproduce** your result — they don't know which prompts to feed the AI to get a similar output.

`/snapshot-prompt` solves all three at once. Core capabilities:

- **Four-section provenance file**: core prompt summary / spec snapshot / AI key decisions / raw user messages.
- **Cross-session history (optional)**: when a single task spans multiple Claude Code sessions, you can include historical sessions in the snapshot. Requires registering a SessionEnd hook (see "Optional: enable cross-session history" below). Without that hook, the picker list will be empty, but the main `/snapshot-prompt` flow still works — you just lose the cross-session input.
- **Sensitive info redaction**: scans for passwords / connection strings / phone numbers / emails before saving; code blocks are collapsed by default (opt-in restore).
- **Does not touch git**: only generates the file. How to archive it (commit to git / keep local / paste into wiki) is entirely up to you.

## Installation

This repo is a Claude Code skill. The minimum install is to drop `snapshot_prompt/skills/snapshot-prompt/` into a place Claude Code can discover.

**Two simplest paths:**

**A. Clone and let Claude Code load it from the repo (recommended)**

```bash
git clone git@github.com:NoStayUpLate/snapshot-prompt.git
```

Open Claude Code in that cloned directory; the skill is auto-discovered (`/snapshot-prompt` appears in your skill list). This is the cleanest setup — the skill stays with the repo and doesn't pollute `~/.claude/`.

**B. Install globally to `~/.claude/skills/`**

If you want `/snapshot-prompt` available from any project directory:

```bash
# Linux / macOS
mkdir -p ~/.claude/skills
cp -r snapshot_prompt/skills/snapshot-prompt ~/.claude/skills/

# Windows (PowerShell)
New-Item -ItemType Directory -Force ~\.claude\skills | Out-Null
Copy-Item -Recurse snapshot_prompt\skills\snapshot-prompt ~\.claude\skills\
```

**Step 2: restart Claude Code**

so the new skill is discovered. After restarting, type `/snapshot-prompt` to use it.

> ℹ️ **Optional: enable cross-session history** — the steps above are enough to make `/snapshot-prompt` work, but the "cross-session history" picker will be permanently empty (nobody is writing the meta index). To get that capability back, follow [Optional: enable cross-session history (manually register the SessionEnd hook)](#optional-enable-cross-session-history-manually-register-the-sessionend-hook) below — about 5 minutes.

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
| **1. Historical session selection** | "Which historical sessions should be included in §4 of this snapshot? (multi-select, can leave all unchecked)" | Lists the 10 most recent **same-project** sessions (inside a git repo, further filtered by **same branch**) (with time + first-message summary + turn count); tick the ones to include. **Only your own machine's sessions** — you can't see teammates'. Tasks spanning 2–3 sessions are common; tick them. **The list is empty if the cross-session history hook isn't enabled** — see the [optional section](#optional-enable-cross-session-history-manually-register-the-sessionend-hook) above. |
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

**Small feature done in a single session** (refactored a feature-engineering script for an ROI weekly report, started and finished today): trigger `/snapshot-prompt` → leave historical sessions **all unticked** (or just skip if the list is empty because no hook is enabled) → theme "重构ROI周报特征工程" → handle redaction / collapse per prompts → archive the output as needed (commit alongside code in a git repo; keep local otherwise).

**Complex task across 3 sessions** (designed Monday → implemented Wednesday → fixed bugs Friday): **requires the cross-session history hook to be enabled** — after the final Friday edit, trigger → **multi-select the two Monday and Wednesday sessions** in the historical list → summarize the overall objective in the theme → §1 picks the most substantive 5–15 prompts across all 3 sessions → the output captures the final-change context plus "Monday's design thinking" and "Wednesday's gotchas".

**While debugging**: don't use it. Debug code itself is temporary; snapshotting it has no value.

## Troubleshooting

**Q: `/snapshot-prompt`'s historical session list is empty?**

A: **Most likely the SessionEnd hook isn't enabled** — this repo doesn't auto-register a hook (deliberately, so it never touches your `~/.claude/settings.json`), so nothing is writing the meta index and the picker stays empty. To enable it, follow [Optional: enable cross-session history (manually register the SessionEnd hook)](#optional-enable-cross-session-history-manually-register-the-sessionend-hook).

If you've **already configured the hook** but the list is still empty:

1. **Check that `python` is available** — the hook defaults to `python "<script>"`. If `python` doesn't exist on your machine (Windows commonly has `py -3`, some Linux/macOS have `python3`), the hook silently fails. Edit your `~/.claude/settings.json` hook command to use the right interpreter and restart.
2. **Restart Claude Code** — settings.json changes take effect only after restart.
3. **Manual backfill fallback** — to add meta to already-existing historical sessions:
   ```
   python <repo path>/snapshot_prompt/scripts/write_session_meta.py --backfill
   ```

**Q: Is it safe for the skill to modify my `~/.claude/`?**

A: This skill **does not auto-modify your `~/.claude/settings.json`** — the SessionEnd hook only takes effect if you explicitly copy it into settings.json (see optional section below). The script itself ([`snapshot_prompt/scripts/write_session_meta.py`](snapshot_prompt/scripts/write_session_meta.py), ~120 lines pure stdlib, no network, no outbound data) only reads session jsonls under your local `~/.claude/projects/` and writes a sibling `<uuid>.meta.json` index — never enters git, never uploads. You can review the script and the [`snapshot_prompt/hooks/hooks.json`](snapshot_prompt/hooks/hooks.json) template before deciding to enable it.

**Q: I forgot to snapshot until after I committed. What now?**

A: You can still trigger — the skill builds the snapshot from the current session + historical sessions (if enabled), and the file can reference the already-committed short hash.

**Q: Can I review a teammate's snapshot on my machine?**

A: Yes — provided they archived it via a shared channel. The most common one is committing it to git so it ships with the branch; just clone and open in your editor (same for wiki / knowledge base). **However** their jsonl / meta files aren't in the shared channel, so "reproducing" means running §1's prompts on your end — you can't pull their conversation logs directly.

## Privacy boundary

- The script only reads session jsonls under your local `~/.claude/projects/` and writes a sibling `<uuid>.meta.json` index. **No network access, no outbound data, never enters git.**
- The snapshot output (`prompt-snapshots/*.md`) is the only part that could ever be shared by you — redaction runs before saving; whether to commit / paste into wiki afterward is your call.
- Teammates can't see your local session contents; the only thing shared is the snapshot markdown you actively archive (e.g. by committing).

## Optional: enable cross-session history (manually register the SessionEnd hook)

Cross-session history relies on a SessionEnd hook: every time a Claude Code session ends, run [`scripts/write_session_meta.py`](snapshot_prompt/scripts/write_session_meta.py) once to write a sidecar `<uuid>.meta.json` for that session (next to the jsonl, i.e. `~/.claude/projects/<proj>/`). Each meta carries session_id / git_branch / cwd / timestamp / first-message excerpt / user_turns — the index that powers `/snapshot-prompt`'s historical session picker.

**Setup steps:**

1. **Find the absolute path of the script** — e.g. if you cloned this repo to `D:\code\snapshot-prompt`, the script is at `D:\code\snapshot-prompt\snapshot_prompt\scripts\write_session_meta.py`. If you copied the skill to `~/.claude/skills/snapshot-prompt/`, copy the `scripts/` folder along with it.

2. **Edit `~/.claude/settings.json`** and merge in the snippet below (if a `hooks.SessionEnd` array already exists, append a new object — don't overwrite the whole section):

   ```json
   {
     "hooks": {
       "SessionEnd": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "python \"D:/code/snapshot-prompt/snapshot_prompt/scripts/write_session_meta.py\""
             }
           ]
         }
       ]
     }
   }
   ```

   - Replace `python` with your machine's Python interpreter command: **Windows** typically `py -3`, **macOS / Linux** typically `python3`.
   - Use absolute paths; on Windows, forward slashes `/` or escaped backslashes `\\` both work.
   - The script is pure stdlib, no third-party dependencies, compatible with **Python 3.7+**.

   Reference template: [`snapshot_prompt/hooks/hooks.json`](snapshot_prompt/hooks/hooks.json) (uses `${CLAUDE_PLUGIN_ROOT}` as a placeholder for a future plugin form; replace with an absolute path when registering manually).

3. **Restart Claude Code.**

4. **Run a one-time backfill** to write meta for sessions that existed before you added the hook (new sessions will be indexed automatically):

   ```
   python <script path> --backfill
   ```

After this, `/snapshot-prompt` will show all historical sessions for the current project in its picker.

## Customizing the output directory

Defaults to `prompt-snapshots/`. If your team has a convention (e.g. `.gitlab/approvals/prompts/`, `.github/prompt-snapshots/`), edit the single line in the "Configurable" section at the top of [`SKILL.md`](snapshot_prompt/skills/snapshot-prompt/SKILL.md) — that section is the source of truth.

## Repository layout

```
.
├── snapshot_prompt/
│   ├── skills/
│   │   └── snapshot-prompt/
│   │       └── SKILL.md          # AI execution spec (naming convention / redaction / trigger flow, all inline)
│   ├── hooks/
│   │   └── hooks.json            # SessionEnd hook template (optional; copy into ~/.claude/settings.json to enable)
│   └── scripts/
│       └── write_session_meta.py # Script that writes sidecar meta.json for session jsonls (~120 lines stdlib-only)
├── README.md                     # Chinese README (default human-facing doc)
└── README_EN.md                  # This file (English README)
```
