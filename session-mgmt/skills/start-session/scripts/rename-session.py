#!/usr/bin/env python3
"""Give a Claude Code session a durable title — the effect of the user typing `/rename`.

Usage:
    rename-session.py <session-id> <name>

There is no callable tool for `/rename`, so this writes the underlying record.
`/resume`'s picker builds its title list by scanning each session's own transcript
for `{"type":"custom-title","customTitle":...}` lines (falling back to `ai-title`
if none exist). It does NOT read ~/.claude/sessions/<pid>.json — that file only
drives the live "concurrent sessions" indicator while the process runs and is
deleted the instant it exits, so writing only there renames nothing durable.

Exit status is always 0: a missing name is not worth failing a session over. The
outcome is reported on stdout.
"""
import glob
import json
import os
import sys
import tempfile


def rename_transcript(sid, name):
    """Append the title records to this session's own transcript.

    Match by filename (<session-id>.jsonl) rather than reconstructing the
    project-dir slug — that encoding is not a stable contract.
    """
    matches = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))
    if not matches:
        return False
    # Append, never read-modify-write: this file is being actively written by the
    # session for the rest of its life. One open(..., "a") write is a single
    # write(2) under O_APPEND, which cannot race with the process's own appends.
    with open(matches[0], "a") as f:
        f.write(json.dumps({"type": "custom-title", "customTitle": name, "sessionId": sid}) + "\n")
        f.write(json.dumps({"type": "agent-name", "agentName": name, "sessionId": sid}) + "\n")
    return True


def mirror_pid_file(sid, name):
    """Best-effort cosmetic mirror so a live concurrent-sessions view reflects the name."""
    d = os.path.expanduser("~/.claude/sessions")
    for p in glob.glob(os.path.join(d, "*.json")):
        try:
            with open(p) as f:
                j = json.load(f)
        except Exception:
            continue
        if j.get("sessionId") != sid:
            continue
        j["name"] = name
        try:
            fd, tmp = tempfile.mkstemp(dir=d)
            with os.fdopen(fd, "w") as f:
                json.dump(j, f)
            os.replace(tmp, p)
        except Exception:
            return False
        return True
    return False


def main():
    if len(sys.argv) != 3 or not sys.argv[1] or not sys.argv[2]:
        print("skipping rename: need <session-id> and <name>")
        return
    sid, name = sys.argv[1], sys.argv[2]
    if rename_transcript(sid, name):
        print(f"renamed session -> {name}")
    else:
        print("no transcript file matched; skipping rename")
    if mirror_pid_file(sid, name):
        print("mirrored into the live pid file")


if __name__ == "__main__":
    main()
