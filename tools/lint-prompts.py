#!/usr/bin/env python3
"""
lint-prompts.py — emotion-vector hygiene linter for agent prompts.

Scans .md files for the four patterns from POLICY.md (patterns 1-3 are
text-detectable; pattern 4 is architectural and out of scope here).

Usage:
    python lint-prompts.py path/to/file.md
    python lint-prompts.py path/to/agents-dir/
    python lint-prompts.py path/to/agents-dir/ --json

Exit code:
    0 if no findings
    1 if any findings (suitable for CI gates)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Pattern 1 — Identity inflation. Adjective claims of expertise/rank applied
# to the agent itself ("you are an X..."). We match the adjective near a
# second-person identity claim or a clear persona claim.
IDENTITY_ADJECTIVES = [
    r"elite",
    r"world-?class",
    r"senior",
    r"master(?:ful)?",
    r"legendary",
    r"seasoned",
    r"veteran",
    r"top-?tier",
    r"expert",
    r"genius",
    r"superstar",
    r"rockstar",
    r"ninja",
    r"guru",
    r"wizard",
]

IDENTITY_PATTERNS = [
    # "You are an elite X" / "You are a senior X"
    (
        "identity-inflation: 'you are a/an <adjective>'",
        re.compile(
            r"\byou\s+are\s+(?:an?|the)\s+(?:" + "|".join(IDENTITY_ADJECTIVES) + r")\b",
            re.IGNORECASE,
        ),
    ),
    # "20+ years" / "10+ years of experience"
    (
        "identity-inflation: 'N+ years of experience'",
        re.compile(r"\b\d{1,2}\+?\s*years?\s+of\s+(?:experience|expertise)\b", re.IGNORECASE),
    ),
    # "your superpower"
    (
        "identity-inflation: 'your superpower'",
        re.compile(r"\byour\s+superpower\b", re.IGNORECASE),
    ),
    # "you've won 20+ hackathons" / "won N+ <thing>"
    (
        "identity-inflation: 'you've won N+ <thing>'",
        re.compile(r"\byou(?:'ve|\s+have)\s+won\s+\d{1,2}\+", re.IGNORECASE),
    ),
    # "deep expertise" / "deep knowledge" applied to persona
    (
        "identity-inflation: 'deep expertise/knowledge'",
        re.compile(r"\bdeep\s+(?:expertise|knowledge|understanding)\b", re.IGNORECASE),
    ),
]

# Pattern 2 — Harsh adverbs / violence vocabulary.
HARSH_ADVERBS = [
    "ruthlessly",
    "aggressively",
    "viciously",
    "brutally",
    "savagely",
    "mercilessly",
    "relentlessly",
    "fiercely",
]

VIOLENCE_VERBS = [
    "destroys?",
    "destroying",
    "kills?",
    "killing",
    "annihilates?",
    "annihilating",
    "obliterates?",
    "obliterating",
    "crushes?",
    "crushing",
]

HARSH_PATTERNS = [
    (
        "harsh-adverb",
        re.compile(r"\b(?:" + "|".join(HARSH_ADVERBS) + r")\b", re.IGNORECASE),
    ),
    (
        "violence-verb",
        re.compile(r"\b(?:" + "|".join(VIOLENCE_VERBS) + r")\b", re.IGNORECASE),
    ),
]

# Pattern 3 — Panic boxes. Box-drawing chars OR a line that's both
# heavily-capitalized and contains CRITICAL/NEVER/MUST stacking.
BOX_DRAWING_CHARS = re.compile(r"[╔╗╚╝═║╠╣┌┐└┘─│]{3,}")

# Heuristic: line is >= 30 chars, has at least 70% uppercase letters among
# its alpha chars, AND contains at least 2 of: CRITICAL / NEVER / MUST / STOP
# / FAIL / DO NOT.
SHOUT_TOKENS = ["CRITICAL", "NEVER", "MUST", "STOP", "FAIL", "DO NOT", "ALWAYS"]


def is_shouty_panic_line(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 30:
        return False
    alpha = [c for c in stripped if c.isalpha()]
    if not alpha:
        return False
    upper_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
    if upper_ratio < 0.70:
        return False
    shout_hits = sum(1 for tok in SHOUT_TOKENS if tok in stripped)
    return shout_hits >= 2


# Pattern 4-text-form — Negative priming on trait words.
NEGATION_TRAITS = [
    "lazy",
    "sloppy",
    "careless",
    "dumb",
    "stupid",
]

NEGATION_PATTERNS = [
    (
        "negative-priming: 'do not be <trait>'",
        re.compile(
            r"\b(?:do\s+not|don't|never)\s+be\s+(?:" + "|".join(NEGATION_TRAITS) + r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "negative-priming: 'never give up'",
        re.compile(r"\bnever\s+give\s+up\b", re.IGNORECASE),
    ),
]


# ---------------------------------------------------------------------------
# Linter
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    text: str

    def format_human(self) -> str:
        return f"{self.file}:{self.line}: [{self.rule}] {self.text}"


def lint_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()

    for lineno, line in enumerate(lines, start=1):
        # Pattern 1: identity inflation
        for rule, pat in IDENTITY_PATTERNS:
            m = pat.search(line)
            if m:
                findings.append(Finding(str(path), lineno, rule, line.strip()[:200]))

        # Pattern 2: harsh adverbs / violence verbs
        for rule, pat in HARSH_PATTERNS:
            m = pat.search(line)
            if m:
                findings.append(Finding(str(path), lineno, rule, line.strip()[:200]))

        # Pattern 3a: box-drawing chars
        if BOX_DRAWING_CHARS.search(line):
            findings.append(
                Finding(str(path), lineno, "panic-box: box-drawing chars", line.strip()[:200])
            )

        # Pattern 3b: shouty stacked CRITICAL/NEVER lines
        if is_shouty_panic_line(line):
            findings.append(
                Finding(
                    str(path),
                    lineno,
                    "panic-box: shouty stacked CRITICAL/NEVER",
                    line.strip()[:200],
                )
            )

        # Pattern 4-text: negative priming
        for rule, pat in NEGATION_PATTERNS:
            m = pat.search(line)
            if m:
                findings.append(Finding(str(path), lineno, rule, line.strip()[:200]))

    return findings


def iter_md_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return
    for p in sorted(target.rglob("*.md")):
        # Skip the policy / example docs in this repo when run on itself,
        # so the linter doesn't flag its own pattern dictionary.
        if p.name in {"POLICY.md", "AUDIT_EXAMPLE.md", "checklist.md", "before-after.md", "README.md"}:
            continue
        yield p


def main() -> int:
    parser = argparse.ArgumentParser(description="Emotion-vector hygiene linter.")
    parser.add_argument("path", help="Path to a .md file or a directory of prompts.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human format.")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"error: path not found: {target}", file=sys.stderr)
        return 2

    all_findings: list[Finding] = []
    for f in iter_md_files(target):
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = f.read_text(encoding="utf-8", errors="replace")
        all_findings.extend(lint_text(f, text))

    if args.json:
        print(json.dumps([asdict(x) for x in all_findings], indent=2))
    else:
        for x in all_findings:
            print(x.format_human())
        if all_findings:
            print(f"\n{len(all_findings)} finding(s) across {len(set(x.file for x in all_findings))} file(s).")
        else:
            print("clean - no findings.")

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
