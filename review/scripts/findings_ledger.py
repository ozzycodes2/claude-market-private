#!/usr/bin/env python3
"""Durable findings ledger shared by `review`, `fix`, and `monitor-pr`.

`review` writes its findings to a session dir under /tmp that the next session
cannot find. This module normalizes every review pass's output into one schema
and persists it outside any repository, so `review:fix` can work the list to
completion days later and `monitor-pr` can append live CI and review-thread
findings to the same ledger.

Four producers emit four incompatible finding shapes. The differences that
matter are the location key (`path` vs `file`) and the remedy key (`suggestion`
vs `fix`); normalizing them here means `fix` consumes exactly one schema. The
fields that normalization would drop -- `cwe`, `drift_class`, `code_says`,
`fix_type` -- are precisely the ones that select a fix strategy, so they are
preserved under `extra`, and each source's payload is kept under `raw_sources`.

`raw_sources` is lossless with one deliberate exception: credential material is
replaced by a digest, because `security-scan` reports a hardcoded secret by
echoing it and this file is durable. See `sanitize_raw_source`.

Ledger path: ~/.claude/review-findings/<owner>__<repo>/pr-<N>.json

Usage:

    findings_ledger.py build --pr-url URL --out LEDGER \
        [--analysis pr-analysis.json] [--payload review-payload.json] \
        --source bug-finder=f.json --source docs-drift=g.json ...
    findings_ledger.py append --ledger L --source ci --from -
    findings_ledger.py show   --ledger L [--status open] [--json]
    findings_ledger.py claim  --ledger L --id F003 --run RUN
    findings_ledger.py resolve --ledger L --id F003 --sha SHA --strategy S1
    findings_ledger.py defer  --ledger L --id F003 --reason … --decision …
    findings_ledger.py lock|unlock --ledger L --run RUN [--force]

Run the tests with:

    python3 -m unittest discover review/tests
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SCHEMA_VERSION = 1

# Severities the ledger stores. `docs-drift` emits `low` and the bug-finder does
# not; the formatter's rubric has a `low` row, so `low` is kept rather than
# coerced upward.
SEVERITIES = ("critical", "high", "medium", "low")
_DEFAULT_SEVERITY = "medium"

# Severities that block by default, matching review_formatter's
# _SEVERITY_CONVENTIONAL (critical/high -> issue (blocking)).
_BLOCKING_SEVERITIES = frozenset(("critical", "high"))

CONVENTIONAL_LABELS = frozenset(
    ("praise", "nitpick", "suggestion", "issue", "thought", "question")
)
CONVENTIONAL_DECORATIONS = frozenset(("blocking", "non-blocking", "if-minor"))

KINDS = (
    "code-smell",
    "correctness",
    "security",
    "docs-prose",
    "code-comment",
    "generated-artifact",
    "lint",
    "dependency",
    "design-decision",
)

STATUSES = ("open", "claimed", "applied", "committed", "deferred", "failed")
TERMINAL_STATUSES = frozenset(("committed", "deferred"))

# The passes that emit the bug-finder finding shape: `path`/`line` plus
# `suggestion`, and optional `label`/`decoration`.
BUGFINDER_SHAPED = (
    "bug-finder",
    "domain-architecture",
    "data-contracts",
    "ops-reliability",
    "change-evolution",
)

# Named refactorings the review passes prescribe. Matched against a finding's
# suggestion/title/body to populate `refactoring`, which routes the finding to
# the refactor strategy and tells the fixing agent which move to apply. Longer
# names first so "Extract Class" is not shadowed by "Extract".
REFACTORING_CATALOG = (
    # Fowler, Refactoring (2nd ed.)
    "Replace Nested Conditional with Guard Clauses",
    "Replace Constructor with Factory Function",
    "Replace Primitive with Object",
    "Replace Type Code with Subclasses",
    "Replace Conditional with Polymorphism",
    "Replace Error Code with Exception",
    "Replace Magic Literal",
    "Combine Functions into Transform",
    "Combine Functions into Class",
    "Introduce Parameter Object",
    "Introduce Special Case",
    "Encapsulate Collection",
    "Encapsulate Variable",
    "Encapsulate Record",
    "Change Function Declaration",
    "Preserve Whole Object",
    "Substitute Algorithm",
    "Collapse Hierarchy",
    "Remove Flag Argument",
    "Remove Dead Code",
    "Decompose Conditional",
    "Extract Interface",
    "Extract Function",
    "Extract Class",
    "Inline Singleton",
    "Inline Function",
    "Inline Class",
    "Hide Delegate",
    "Move Function",
    "Move Field",
    "Rename Field",
    # Kerievsky, Refactoring to Patterns
    "Replace State-Altering Conditionals with State",
    "Replace Conditional Dispatcher with Command",
    "Replace Type Code with Class",
    "Move Creation Knowledge to Factory",
    "Encapsulate Classes with Factory",
    "Unify Interfaces with Adapter",
    "Introduce Null Object",
    "Form Template Method",
)

# Smell vocabulary -> kind. Applied to a bug-finder-shaped finding's text when no
# catalog refactoring is named, so a craft finding still routes to the refactor
# strategy rather than falling through to repair.
_SMELL_HINTS = (
    "feature envy",
    "inappropriate intimacy",
    "primitive obsession",
    "speculative generality",
    "god class",
    "god service",
    "divergent change",
    "shotgun surgery",
    "temporal coupling",
    "deep nesting",
    "long function",
    "long parameter list",
    "dead code",
    "duplication",
    "boolean blindness",
    "flag argument",
    "magic literal",
    "magic number",
    "leaked internals",
    "layering violation",
    "code smell",
    "complexity budget",
    "information hiding",
    "misuse-prone",
    "abstraction level",
    "shallow class",
)

_SECURITY_HINTS = (
    "sql injection",
    "xss",
    "ssrf",
    "idor",
    "hardcoded secret",
    "credential",
    "auth bypass",
    "cwe-",
    "owasp",
    "path traversal",
    "command injection",
    "pii in logs",
)

# docs-drift `drift_class` -> kind. `rendered-lag` must be regenerated rather
# than hand-edited, so it is kept distinct from ordinary prose drift.
_DRIFT_CLASS_KIND = {
    "stale-comment": "code-comment",
    "rendered-lag": "generated-artifact",
    "superseded-model": "docs-prose",
    "adr-index": "docs-prose",
    "env-mismatch": "docs-prose",
    "retired-rule": "docs-prose",
    "duplicated-claim": "docs-prose",
    "missing-doc": "docs-prose",
}

# CI `fix_type` -> kind. `sync_derived` and `version_bump` are both derived-file
# drift: the fix is to re-run the generator, not to hand-edit.
_CI_FIX_TYPE_KIND = {
    "lint": "lint",
    "formatting": "lint",
    "sync_derived": "generated-artifact",
    "version_bump": "generated-artifact",
}

# Longest source excerpt retained on a finding. A security finding's `code` is
# the offending line verbatim, and the ledger is durable -- bound it.
_MAX_CODE_EXCERPT = 240

# Subset of the analysis JSON that `fix` needs. The session dir it came from is
# gone by the time `fix` runs, so these are copied, never referenced.
_CONTEXT_KEYS = (
    "languages",
    "test_setup",
    "build_system",
    "change_categories",
    "impact_analysis",
    "risk_class",
    "security_sensitive",
    "uses_mac_ui",
)

_PR_URL_RE = re.compile(
    r"^https?://[^/]+/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
)


# --------------------------------------------------------------------------
# helpers


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")


def parse_pr_url(url: str) -> dict:
    """Split a PR URL into owner, repo, and number.

    Derived from the URL rather than `git remote` because the reviewed PR may
    belong to a repository that is not the current checkout.
    """
    m = _PR_URL_RE.match(str(url or "").strip())
    if not m:
        raise ValueError(f"not a PR URL: {url!r}")
    return {
        "owner": m.group("owner"),
        "name": m.group("repo"),
        "name_with_owner": f"{m.group('owner')}/{m.group('repo')}",
        "number": int(m.group("number")),
    }


def repo_slug(owner: str, name: str) -> str:
    """Build the one-segment directory name for a repository.

    A double underscore separates owner from repo so that ``a/b-c`` and
    ``a-b/c`` cannot collide on the same directory.
    """
    return f"{owner}__{name}"


def ledger_path(owner: str, name: str, number: int, home: str | None = None) -> Path:
    root = Path(home or os.path.expanduser("~")) / ".claude" / "review-findings"
    return root / repo_slug(owner, name) / f"pr-{number}.json"


def fingerprint(value: str) -> str:
    """Fingerprint a secret so the ledger can dedupe it without storing it.

    `security-scan` reports a hardcoded secret by echoing the offending line, so
    for that finding class the payload *is* the credential. The ledger is
    durable and lives in the home directory, so the value is replaced by a
    truncated digest -- enough to recognise the same secret across runs, not
    enough to use it.
    """
    digest = hashlib.sha256(str(value).encode("utf-8", "replace")).hexdigest()
    return f"sha256:{digest[:16]}"


def _truncate(text, limit: int = _MAX_CODE_EXCERPT):
    if text is None:
        return None
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "…"


def _norm_severity(value) -> str:
    sev = str(value or "").strip().lower()
    return sev if sev in SEVERITIES else _DEFAULT_SEVERITY


def _norm_label(value):
    label = str(value or "").strip().lower()
    return label if label in CONVENTIONAL_LABELS else None


def _norm_decoration(value):
    dec = str(value or "").strip().lower()
    return dec if dec in CONVENTIONAL_DECORATIONS else None


def _blocking(severity: str, decoration=None) -> bool:
    """Resolve whether a finding blocks.

    An explicit decoration wins; otherwise severity decides, matching the
    formatter's defaults where critical and high become blocking issues.
    """
    if decoration == "blocking":
        return True
    if decoration in ("non-blocking", "if-minor"):
        return False
    return severity in _BLOCKING_SEVERITIES


def dedupe_key(path, line, title) -> str:
    raw = f"{path or ''}|{line if line is not None else ''}|{_slug(title)}"
    return hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:16]


def match_refactoring(*texts):
    """Find the named refactoring a finding prescribes, if any.

    The review passes are instructed to name the resolving refactoring in
    `suggestion`, and the per-pass checklists append it after a `·`. Matching is
    on the catalog's own names so review and fix share one vocabulary.
    """
    haystack = " ".join(str(t) for t in texts if t).lower()
    for name in REFACTORING_CATALOG:
        if name.lower() in haystack:
            return name
    return None


def _has_hint(hints, *texts) -> bool:
    haystack = " ".join(str(t) for t in texts if t).lower()
    return any(h in haystack for h in hints)


def _clean_none(mapping: dict) -> dict:
    return {k: v for k, v in mapping.items() if v is not None and v != ""}


# Keys under `secrets_found` that hold the credential itself.
_SECRET_VALUE_KEYS = ("secret", "value", "match", "password", "token", "api_key")


def sanitize_raw_source(source: str, payload):
    """Strip credential material from a payload before it is persisted.

    `raw_sources` exists so that normalization stays lossless for the fields
    that select a fix strategy. Secrets are the one exception: `security-scan`
    reports a hardcoded credential by echoing it, and preserving the raw payload
    verbatim would re-introduce into a durable file exactly what fingerprinting
    the finding removed. Secrecy wins -- the value is replaced by its digest and
    source excerpts are bounded.
    """
    def walk(node, in_secret_entry=False):
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                key = str(k)
                if in_secret_entry and key in _SECRET_VALUE_KEYS and isinstance(v, str):
                    out[key] = fingerprint(v)
                elif key == "code" and isinstance(v, str):
                    out[key] = _truncate(v)
                else:
                    out[key] = walk(v, in_secret_entry=in_secret_entry or key == "secrets_found")
            return out
        if isinstance(node, list):
            return [walk(v, in_secret_entry=in_secret_entry) for v in node]
        return node

    return walk(payload)


# --------------------------------------------------------------------------
# finding construction


def _finding(
    *,
    source,
    source_ref,
    severity,
    title,
    body="",
    remedy="",
    path=None,
    line=None,
    start_line=None,
    label=None,
    decoration=None,
    kind="correctness",
    refactoring=None,
    confidence=None,
    extra=None,
    external_ref=None,
) -> dict:
    severity = _norm_severity(severity)
    label = _norm_label(label)
    decoration = _norm_decoration(decoration)
    return {
        "id": None,  # assigned by _assign_ids once the full list is known
        "source": source,
        "source_ref": source_ref,
        "severity": severity,
        "label": label,
        "decoration": decoration,
        "blocking": _blocking(severity, decoration),
        "path": path or None,
        "line": line,
        "start_line": start_line,
        "title": str(title or "").strip() or "(untitled finding)",
        "body": str(body or "").strip(),
        "remedy": str(remedy or "").strip(),
        "refactoring": refactoring,
        "kind": kind if kind in KINDS else "correctness",
        "confidence": confidence,
        "extra": _clean_none(extra or {}),
        "external_ref": external_ref,
        "dedupe_key": dedupe_key(path, line, title),
        "status": "open",
        "history": [{"at": _now(), "to": "open", "note": f"normalized from {source}"}],
    }


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# per-source normalizers


def normalize_bugfinder(payload: dict, source: str) -> list:
    """Normalize the bug-finder / quality-review finding shape.

    These already carry `path`/`line` and `suggestion`, and may declare their own
    Conventional Comments `label`/`decoration`.
    """
    out = []
    for i, f in enumerate(payload.get("findings") or []):
        if not isinstance(f, dict):
            continue
        suggestion = f.get("suggestion") or ""
        title = f.get("title") or ""
        body = f.get("body") or ""
        refactoring = match_refactoring(suggestion, title, body)
        if _has_hint(_SECURITY_HINTS, title, body, suggestion):
            kind = "security"
        elif refactoring or _has_hint(_SMELL_HINTS, title, body, suggestion):
            kind = "code-smell"
        else:
            kind = "correctness"
        if _norm_label(f.get("label")) == "question":
            kind = "design-decision"
        out.append(
            _finding(
                source=source,
                source_ref=f"raw_sources.{source}.findings[{i}]",
                severity=f.get("severity"),
                label=f.get("label"),
                decoration=f.get("decoration"),
                path=f.get("path"),
                line=_as_int(f.get("line")),
                start_line=_as_int(f.get("start_line")),
                title=title,
                body=body,
                remedy=suggestion,
                refactoring=refactoring,
                kind=kind,
                confidence=f.get("confidence"),
            )
        )
    return out


def normalize_docs_drift(payload: dict, source: str = "docs-drift") -> list:
    """Normalize docs-drift findings.

    Two shape differences from the bug-finder: the remedy lives in `fix`, not
    `suggestion`, and there is no `label`/`decoration`. `drift_class` selects the
    strategy -- notably `rendered-lag`, which must be regenerated rather than
    edited -- so it is preserved under `extra`.
    """
    out = []
    for i, f in enumerate(payload.get("findings") or []):
        if not isinstance(f, dict):
            continue
        drift_class = f.get("drift_class")
        doc_says = f.get("doc_says")
        code_says = f.get("code_says")
        body = f.get("body") or ""
        if doc_says or code_says:
            body = "\n".join(
                p
                for p in (
                    body,
                    f"doc says: {doc_says}" if doc_says else "",
                    f"code says: {code_says}" if code_says else "",
                )
                if p
            )
        out.append(
            _finding(
                source=source,
                source_ref=f"raw_sources.{source}.findings[{i}]",
                severity=f.get("severity"),
                path=f.get("path"),
                line=_as_int(f.get("line")),
                title=f.get("title"),
                body=body,
                remedy=f.get("fix"),
                kind=_DRIFT_CLASS_KIND.get(drift_class, "docs-prose"),
                extra=_clean_none(
                    {
                        "facet": f.get("facet"),
                        "drift_class": drift_class,
                        "doc_says": doc_says,
                        "code_says": code_says,
                    }
                ),
            )
        )
    return out


def normalize_security_scan(payload: dict, source: str = "security-scan") -> list:
    """Normalize security-scan findings.

    The documented output template and the builder in that skill disagree on
    which buckets exist, so every ``*_findings`` key is globbed rather than
    naming two. Location is `file`, not `path`. `secrets_found` values are
    fingerprinted, never stored.
    """
    out = []
    buckets = sorted(
        k
        for k, v in payload.items()
        if k.endswith("_findings") and isinstance(v, list)
    )
    for bucket in buckets:
        default_sev = bucket[: -len("_findings")].lower()
        for i, f in enumerate(payload.get(bucket) or []):
            if not isinstance(f, dict):
                continue
            message = f.get("message") or f.get("title") or ""
            title = re.split(r"[.;]\s", str(message), maxsplit=1)[0] or "(untitled)"
            out.append(
                _finding(
                    source=source,
                    source_ref=f"raw_sources.{source}.{bucket}[{i}]",
                    severity=f.get("severity") or default_sev,
                    path=f.get("file") or f.get("path"),
                    line=_as_int(f.get("line")),
                    title=title,
                    body=message,
                    remedy=f.get("fix"),
                    kind="security",
                    extra=_clean_none(
                        {
                            "category": f.get("category"),
                            "cwe": f.get("cwe"),
                            "rule": f.get("rule"),
                            "code": _truncate(f.get("code")),
                        }
                    ),
                )
            )

    for i, dep in enumerate(payload.get("dependency_vulnerabilities") or []):
        if not isinstance(dep, dict):
            continue
        name = dep.get("package") or dep.get("name") or "dependency"
        out.append(
            _finding(
                source=source,
                source_ref=f"raw_sources.{source}.dependency_vulnerabilities[{i}]",
                severity=dep.get("severity"),
                path=dep.get("manifest") or dep.get("file"),
                title=f"vulnerable dependency {name}",
                body=dep.get("description") or dep.get("message") or "",
                remedy=dep.get("fix") or dep.get("fixed_version") or "",
                kind="dependency",
                extra=_clean_none(
                    {
                        "package": name,
                        "cve": dep.get("cve") or dep.get("id"),
                        "installed_version": dep.get("installed_version"),
                        "fixed_version": dep.get("fixed_version"),
                    }
                ),
            )
        )

    for i, sec in enumerate(payload.get("secrets_found") or []):
        if not isinstance(sec, dict):
            continue
        raw_value = sec.get("secret") or sec.get("value") or sec.get("match") or ""
        out.append(
            _finding(
                source=source,
                source_ref=f"raw_sources.{source}.secrets_found[{i}]",
                severity=sec.get("severity") or "critical",
                path=sec.get("file") or sec.get("path"),
                line=_as_int(sec.get("line")),
                title=f"hardcoded secret ({sec.get('type') or 'unknown type'})",
                body="A credential is committed in the source. Rotate it; removing "
                "the line does not revoke it.",
                remedy=sec.get("fix")
                or "Move to a secret store or environment variable, then rotate "
                "the exposed credential.",
                kind="security",
                extra=_clean_none(
                    {
                        "secret_type": sec.get("type"),
                        "secret_fingerprint": fingerprint(raw_value) if raw_value else None,
                    }
                ),
            )
        )
    return out


def normalize_ci(payload: dict, source: str = "ci") -> list:
    """Normalize a `classify_ci_failure` result into a finding.

    Returns an empty list for a transient infrastructure failure (severity
    `info`): the remedy there is to re-run the check, which is not a code change
    and must not become a finding `fix` would try to resolve.

    CI findings usually carry no path -- the failure is reported against a check,
    not a line -- which is why `path` is nullable throughout the schema.
    """
    if not isinstance(payload, dict):
        return []
    if str(payload.get("severity") or "").lower() == "info":
        return []

    fix_type = payload.get("fix_type")
    details = payload.get("details") or {}
    check_name = payload.get("check_name") or details.get("check_name")
    summary = payload.get("summary") or "CI check failed"

    # `classify_ci_failure` has a dedicated security branch that reports no
    # fix_type and says only "Security check failure", so match its wording
    # here rather than widening the shared hint list -- a bare "security" there
    # would misroute any code finding that mentions the word in passing.
    if _has_hint(
        _SECURITY_HINTS + ("security", "vulnerability", "cve"),
        summary,
        payload.get("suggestion"),
    ):
        kind = "security"
    else:
        kind = _CI_FIX_TYPE_KIND.get(fix_type, "correctness")

    return [
        _finding(
            source=source,
            source_ref=f"raw_sources.{source}",
            severity=payload.get("severity"),
            path=payload.get("path") or details.get("path"),
            line=_as_int(payload.get("line") or details.get("line")),
            title=summary,
            body="\n".join(
                p
                for p in (
                    summary,
                    f"check: {check_name}" if check_name else "",
                    json.dumps(details, sort_keys=True) if details else "",
                )
                if p
            ),
            remedy=payload.get("suggestion"),
            kind=kind,
            extra=_clean_none(
                {
                    "fix_type": fix_type,
                    "auto_fixable": payload.get("auto_fixable"),
                    "details": details or None,
                }
            ),
            external_ref=_clean_none(
                {
                    "kind": "ci_check",
                    "check_name": check_name,
                    "run_url": payload.get("run_url") or details.get("run_url"),
                }
            )
            or None,
        )
    ]


def normalize_review_thread(payload: dict, source: str = "review-thread") -> list:
    """Normalize a PR review thread into a finding.

    `external_ref.thread_id` is the return path: once `fix` commits, `monitor-pr`
    maps the committed finding back to its thread and resolves it.
    """
    if not isinstance(payload, dict):
        return []
    threads = payload.get("threads") if "threads" in payload else [payload]
    out = []
    for i, th in enumerate(threads or []):
        if not isinstance(th, dict):
            continue
        body = th.get("body") or th.get("comment") or ""
        first_line = str(body).strip().splitlines()[0] if str(body).strip() else ""
        out.append(
            _finding(
                source=source,
                source_ref=f"raw_sources.{source}.threads[{i}]",
                severity=th.get("severity") or "medium",
                path=th.get("path"),
                line=_as_int(th.get("line")),
                title=th.get("title") or first_line or "review comment",
                body=body,
                remedy=th.get("suggestion") or th.get("fix") or body,
                kind="correctness",
                external_ref=_clean_none(
                    {
                        "kind": "review_thread",
                        "thread_id": th.get("thread_id") or th.get("threadId") or th.get("id"),
                        "comment_id": th.get("comment_id") or th.get("databaseId"),
                        "author": th.get("author"),
                        "is_outdated": th.get("is_outdated"),
                    }
                )
                or None,
            )
        )
    return out


NORMALIZERS = {
    "docs-drift": normalize_docs_drift,
    "security-scan": normalize_security_scan,
    "ci": normalize_ci,
    "review-thread": normalize_review_thread,
}


def normalize(source: str, payload) -> list:
    """Dispatch to the normalizer for `source`."""
    if source in NORMALIZERS:
        return NORMALIZERS[source](payload, source)
    if source in BUGFINDER_SHAPED:
        return normalize_bugfinder(payload, source)
    # Unknown pass: assume the bug-finder shape, which every quality-review pass
    # is contracted to emit.
    return normalize_bugfinder(payload, source)


# --------------------------------------------------------------------------
# ledger I/O


def _assign_ids(findings: list, start: int = 1) -> list:
    for n, f in enumerate(findings, start=start):
        f["id"] = f"F{n:03d}"
    return findings


def read_ledger(path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_ledger(path, ledger: dict) -> None:
    """Write the ledger atomically, owner-readable only.

    Mode 0600 because a security finding's `extra.code` is a verbatim source
    excerpt; the ephemeral session dir this replaces was 0700 for the same
    reason.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
        os.chmod(path.parent.parent, 0o700)
    except OSError:
        pass  # a pre-existing dir with other modes is not worth failing over
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".ledger-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(ledger, fh, indent=2, sort_keys=False, ensure_ascii=False)
            fh.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _find(ledger: dict, finding_id: str) -> dict:
    for f in ledger.get("findings") or []:
        if f.get("id") == finding_id:
            return f
    raise KeyError(f"no finding {finding_id!r} in ledger")


def _transition(finding: dict, status: str, note: str = "") -> None:
    finding["history"].append(
        {"at": _now(), "from": finding.get("status"), "to": status, "note": note}
    )
    finding["status"] = status


def build_ledger(
    *, pr_url: str, sources: dict, analysis=None, payload=None, run_id=None
) -> dict:
    """Normalize every pass's output into one ledger document.

    `analysis` is copied in, not referenced: it is written to a /tmp session dir
    that is gone by the time `fix` runs, and `fix` needs `test_setup.test_command`
    and `can_run_safely` to decide whether it has a local signal at all.
    """
    repo = parse_pr_url(pr_url)
    analysis = analysis or {}
    payload = payload or {}

    findings = []
    for source in sorted(sources):
        findings.extend(normalize(source, sources[source]))
    _assign_ids(findings)

    by_dedupe = {}
    for f in findings:
        by_dedupe.setdefault(f["dedupe_key"], []).append(f["id"])

    return {
        "schema_version": SCHEMA_VERSION,
        "repo": {
            "owner": repo["owner"],
            "name": repo["name"],
            "name_with_owner": repo["name_with_owner"],
        },
        "pr": {
            "number": repo["number"],
            "url": pr_url,
            "base_branch": analysis.get("base_branch"),
            "head_branch": analysis.get("head_branch"),
            "head_sha": analysis.get("head_sha"),
        },
        "review": {
            "run_id": run_id,
            "reviewed_at": _now(),
            "tool_version": (payload.get("review_metadata") or {}).get("tool_version"),
            "recommendation": payload.get("recommendation"),
            "review_url": payload.get("pr_url") or pr_url,
        },
        "context": {k: analysis[k] for k in _CONTEXT_KEYS if k in analysis},
        "findings": findings,
        "action_order": [f["id"] for f in findings],
        "duplicates": {k: v for k, v in by_dedupe.items() if len(v) > 1},
        "lock": None,
        "runs": [],
        "raw_sources": {k: sanitize_raw_source(k, v) for k, v in sources.items()},
    }


def append_findings(ledger: dict, source: str, payload) -> list:
    """Append newly discovered findings, skipping ones already in the ledger.

    `monitor-pr` calls this each tick. Dedupe on `dedupe_key` so a review thread
    that is still unresolved across several ticks does not accumulate duplicate
    findings.
    """
    existing = {f.get("dedupe_key") for f in ledger.get("findings") or []}
    incoming = [f for f in normalize(source, payload) if f["dedupe_key"] not in existing]
    next_n = len(ledger.get("findings") or []) + 1
    _assign_ids(incoming, start=next_n)
    ledger.setdefault("findings", []).extend(incoming)
    ledger.setdefault("action_order", []).extend(f["id"] for f in incoming)
    raw = ledger.setdefault("raw_sources", {})
    clean = sanitize_raw_source(source, payload)
    if source in raw and isinstance(raw[source], list):
        raw[source].append(clean)
    elif source in raw:
        raw[source] = [raw[source], clean]
    else:
        raw[source] = clean
    return incoming


# --------------------------------------------------------------------------
# CLI


def _load_json(spec):
    if spec in ("-", None):
        return json.load(sys.stdin)
    with open(spec, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _cmd_build(args):
    sources = {}
    for item in args.source or []:
        if "=" not in item:
            raise SystemExit(f"--source expects NAME=PATH, got {item!r}")
        name, _, spec = item.partition("=")
        sources[name.strip()] = _load_json(spec.strip())

    ledger = build_ledger(
        pr_url=args.pr_url,
        sources=sources,
        analysis=_load_json(args.analysis) if args.analysis else None,
        payload=_load_json(args.payload) if args.payload else None,
        run_id=args.run,
    )
    out = args.out or ledger_path(
        ledger["repo"]["owner"], ledger["repo"]["name"], ledger["pr"]["number"]
    )
    write_ledger(out, ledger)
    print(f"{out}\t{len(ledger['findings'])} findings")
    return 0


def _cmd_path(args):
    """Print the ledger path for a PR, so callers need no shell slug logic."""
    if args.pr_url:
        repo = parse_pr_url(args.pr_url)
        owner, name, number = repo["owner"], repo["name"], repo["number"]
    else:
        if not args.repo or args.pr is None:
            raise SystemExit("pass --pr-url, or both --repo owner/name and --pr N")
        if "/" not in args.repo:
            raise SystemExit(f"--repo expects owner/name, got {args.repo!r}")
        owner, _, name = args.repo.partition("/")
        number = args.pr
    print(ledger_path(owner, name, number))
    return 0


def _cmd_append(args):
    created = False
    if os.path.exists(args.ledger):
        ledger = read_ledger(args.ledger)
    elif args.create:
        if not args.pr_url:
            raise SystemExit("--create needs --pr-url to identify the PR")
        ledger = build_ledger(pr_url=args.pr_url, sources={}, run_id=args.run)
        created = True
    else:
        raise SystemExit(
            f"no ledger at {args.ledger}; run /review:review first, or pass "
            "--create --pr-url <url> to start one from live findings"
        )

    added = append_findings(ledger, args.source, _load_json(getattr(args, "from")))
    write_ledger(args.ledger, ledger)
    if created:
        # An empty `context` means no test_command, so a consumer has no local
        # signal and must lean on CI. Say it here rather than let fix discover it.
        print(f"created {args.ledger} with no analysis context")
    print(f"appended {len(added)} finding(s): {', '.join(f['id'] for f in added) or '-'}")
    return 0


def _cmd_show(args):
    ledger = read_ledger(args.ledger)
    wanted = set(s.strip() for s in args.status.split(",")) if args.status else None
    findings = [
        f for f in ledger.get("findings") or [] if not wanted or f.get("status") in wanted
    ]
    order = {fid: i for i, fid in enumerate(ledger.get("action_order") or [])}
    findings.sort(key=lambda f: order.get(f.get("id"), 10**6))

    if args.json:
        json.dump({**ledger, "findings": findings}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not findings:
        print("no matching findings")
        return 0
    for f in findings:
        loc = f.get("path") or "(no path)"
        if f.get("line"):
            loc = f"{loc}:{f['line']}"
        flag = "blocking" if f.get("blocking") else "non-blocking"
        print(f"{f['id']}\t{f['status']}\t{f['severity']}\t{flag}\t{f['kind']}\t{loc}\t{f['title']}")
        if f.get("refactoring"):
            print(f"\t\trefactoring: {f['refactoring']}")
    return 0


def _cmd_claim(args):
    ledger = read_ledger(args.ledger)
    f = _find(ledger, args.id)
    if f["status"] in TERMINAL_STATUSES:
        raise SystemExit(f"{args.id} is already {f['status']}")
    _transition(f, "claimed", f"run {args.run}")
    f["claimed_by"] = args.run
    write_ledger(args.ledger, ledger)
    print(f"{args.id} claimed by {args.run}")
    return 0


def _cmd_resolve(args):
    ledger = read_ledger(args.ledger)
    f = _find(ledger, args.id)
    _transition(f, "committed", f"{args.strategy or '?'} -> {args.sha}")
    f["resolved_by_sha"] = args.sha
    f["strategy"] = args.strategy
    write_ledger(args.ledger, ledger)
    print(f"{args.id} committed as {args.sha}")
    return 0


def _cmd_defer(args):
    ledger = read_ledger(args.ledger)
    f = _find(ledger, args.id)
    _transition(f, "deferred", args.reason)
    f["deferral"] = _clean_none(
        {
            "reason": args.reason,
            "decision_needed": args.decision,
            "blocked_on": args.blocked_on,
            "evidence": _load_json(args.evidence)
            if args.evidence and args.evidence.endswith(".json")
            else args.evidence,
            "deferred_at": _now(),
            "deferred_by": args.run,
        }
    )
    write_ledger(args.ledger, ledger)
    print(f"{args.id} deferred: {args.reason}")
    return 0


def _cmd_ack(args):
    """Record that a finding's originating review thread has been answered.

    Idempotent on `(id, thread)`: a second call for the same thread is a no-op
    rather than an error, because the thing it guards against is replying twice
    to one reviewer on a re-run.
    """
    ledger = read_ledger(args.ledger)
    f = _find(ledger, args.id)
    acks = f.setdefault("acknowledged", [])
    if any(a.get("thread_id") == args.thread for a in acks):
        print(f"{args.id} already acknowledged on {args.thread}")
        return 0
    acks.append(
        _clean_none(
            {
                "thread_id": args.thread,
                "action": args.action,
                "url": args.url,
                "at": _now(),
                "by": args.run,
            }
        )
    )
    # Status is unchanged -- acknowledging is not a state transition, so the
    # history entry records it without moving the finding.
    f["history"].append(
        {
            "at": _now(),
            "from": f.get("status"),
            "to": f.get("status"),
            "note": f"acknowledged ({args.action}) on {args.thread}",
        }
    )
    write_ledger(args.ledger, ledger)
    print(f"{args.id} acknowledged ({args.action}) on {args.thread}")
    return 0


def _cmd_lock(args):
    ledger = read_ledger(args.ledger)
    lock = ledger.get("lock")
    if lock and not args.force:
        raise SystemExit(
            f"ledger locked by run {lock.get('run_id')} since {lock.get('started_at')}; "
            "pass --force to break it"
        )
    ledger["lock"] = {"run_id": args.run, "pid": os.getpid(), "started_at": _now()}
    write_ledger(args.ledger, ledger)
    print(f"locked by {args.run}")
    return 0


def _cmd_unlock(args):
    ledger = read_ledger(args.ledger)
    ledger["lock"] = None
    write_ledger(args.ledger, ledger)
    print("unlocked")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="findings_ledger.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="normalize review pass outputs into a ledger")
    b.add_argument("--pr-url", required=True)
    b.add_argument("--source", action="append", metavar="NAME=PATH")
    b.add_argument("--analysis")
    b.add_argument("--payload")
    b.add_argument("--out")
    b.add_argument("--run")
    b.set_defaults(fn=_cmd_build)

    pa = sub.add_parser("path", help="print the ledger path for a PR")
    pa.add_argument("--pr-url")
    pa.add_argument("--repo", metavar="owner/name")
    pa.add_argument("--pr", type=int)
    pa.set_defaults(fn=_cmd_path)

    a = sub.add_parser("append", help="append live findings to a ledger")
    a.add_argument("--ledger", required=True)
    a.add_argument("--source", required=True, choices=sorted(NORMALIZERS) + list(BUGFINDER_SHAPED))
    a.add_argument("--from", default="-", dest="from")
    a.add_argument(
        "--create",
        action="store_true",
        help="start a ledger if none exists; needs --pr-url. The result has no "
        "analysis context, so a consumer gets no local test command.",
    )
    a.add_argument("--pr-url", help="only with --create")
    a.add_argument("--run")
    a.set_defaults(fn=_cmd_append)

    s = sub.add_parser("show", help="list findings, optionally filtered by status")
    s.add_argument("--ledger", required=True)
    s.add_argument("--status")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=_cmd_show)

    ak = sub.add_parser("ack", help="record that a finding's review thread was answered")
    ak.add_argument("--ledger", required=True)
    ak.add_argument("--id", required=True)
    ak.add_argument("--thread", required=True)
    ak.add_argument("--action", required=True, choices=("reply", "reply+resolve", "resolve"))
    ak.add_argument("--url")
    ak.add_argument("--run")
    ak.set_defaults(fn=_cmd_ack)

    c = sub.add_parser("claim", help="mark a finding as being worked")
    c.add_argument("--ledger", required=True)
    c.add_argument("--id", required=True)
    c.add_argument("--run", required=True)
    c.set_defaults(fn=_cmd_claim)

    r = sub.add_parser("resolve", help="record the commit that resolved a finding")
    r.add_argument("--ledger", required=True)
    r.add_argument("--id", required=True)
    r.add_argument("--sha", required=True)
    r.add_argument("--strategy")
    r.set_defaults(fn=_cmd_resolve)

    d = sub.add_parser("defer", help="record a finding as needing a human decision")
    d.add_argument("--ledger", required=True)
    d.add_argument("--id", required=True)
    d.add_argument("--reason", required=True)
    d.add_argument("--decision")
    d.add_argument("--blocked-on", dest="blocked_on")
    d.add_argument("--evidence")
    d.add_argument("--run")
    d.set_defaults(fn=_cmd_defer)

    lk = sub.add_parser("lock", help="take the per-ledger run lock")
    lk.add_argument("--ledger", required=True)
    lk.add_argument("--run", required=True)
    lk.add_argument("--force", action="store_true")
    lk.set_defaults(fn=_cmd_lock)

    ul = sub.add_parser("unlock", help="release the run lock")
    ul.add_argument("--ledger", required=True)
    ul.set_defaults(fn=_cmd_unlock)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
