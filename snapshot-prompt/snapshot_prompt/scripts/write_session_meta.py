"""
Date: 2026-05-14
Creator: Claude Code (snapshot-prompt plugin)
Purpose: 给 Claude Code session jsonl 写侧车 meta.json，便于 /snapshot-prompt skill 跨会话识别历史 session。
         两种模式：(1) SessionEnd hook 模式 —— 从 stdin 读 hook context，处理单个 session；
         (2) --backfill 模式 —— 扫 ~/.claude/projects/* 下所有 jsonl，给没有 meta 的补一份。
"""

# 让 `X | None` 等注解惰性求值（PEP 563），从而兼容 Python 3.7+，不再要求 3.10+。
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
EXCERPT_LEN = 150


def extract_first_user_message(jsonl_path: Path) -> dict | None:
    """Read jsonl head, find first real user message (skip queue ops / attachments / sidechains)."""
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "user":
                    continue
                if rec.get("isSidechain"):
                    continue
                msg = rec.get("message", {})
                content = msg.get("content")
                text = None
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text = part.get("text")
                            break
                if not text:
                    continue
                return {
                    "session_id": rec.get("sessionId"),
                    "git_branch": rec.get("gitBranch"),
                    "cwd": rec.get("cwd"),
                    "timestamp": rec.get("timestamp"),
                    "first_message_excerpt": text.strip()[:EXCERPT_LEN],
                    "entrypoint": rec.get("entrypoint"),
                    "version": rec.get("version"),
                }
    except OSError:
        return None
    return None


def count_user_messages(jsonl_path: Path) -> int:
    """Rough activity signal: total user turns (skip sidechains)."""
    n = 0
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                if '"type":"user"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") == "user" and not rec.get("isSidechain"):
                    n += 1
    except OSError:
        return 0
    return n


def write_meta(jsonl_path: Path, force: bool = False) -> str:
    """Write <session-id>.meta.json sidecar next to the jsonl. Returns status string."""
    meta_path = jsonl_path.with_suffix(".meta.json")
    if meta_path.exists() and not force:
        return f"skip (exists): {meta_path.name}"
    first = extract_first_user_message(jsonl_path)
    if first is None:
        return f"skip (no user msg): {jsonl_path.name}"
    meta = {
        **first,
        "user_turns": count_user_messages(jsonl_path),
        "jsonl_mtime": jsonl_path.stat().st_mtime,
    }
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return f"wrote: {meta_path.name}"


def find_main_session_jsonls() -> list[Path]:
    """Top-level <session-id>.jsonl files only, skip subagents/ subdirs."""
    if not PROJECTS_DIR.exists():
        return []
    out = []
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl in project_dir.glob("*.jsonl"):
            out.append(jsonl)
    return out


def hook_mode() -> int:
    """Read hook JSON from stdin, locate the session's jsonl, write its meta."""
    try:
        ctx = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    session_id = ctx.get("session_id")
    if not session_id:
        return 0
    matches = list(PROJECTS_DIR.glob(f"*/{session_id}.jsonl"))
    if not matches:
        return 0
    for jsonl in matches:
        write_meta(jsonl, force=True)
    return 0


def backfill_mode() -> int:
    jsonls = find_main_session_jsonls()
    print(f"Found {len(jsonls)} main-session jsonl files under {PROJECTS_DIR}")
    written = skipped = 0
    for jsonl in jsonls:
        status = write_meta(jsonl, force=False)
        if status.startswith("wrote"):
            written += 1
        else:
            skipped += 1
        print(f"  {status}")
    print(f"\nDone: {written} written, {skipped} skipped")
    return 0


if __name__ == "__main__":
    if "--backfill" in sys.argv:
        sys.exit(backfill_mode())
    sys.exit(hook_mode())
