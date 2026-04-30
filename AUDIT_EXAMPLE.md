# Audit Example — Findings From My Own Harness

This is a worked example. I scanned my own multi-agent harness (a Claude
Code setup with ~30 agent definitions, ~90 commands, role-personality
files, and a retry-loop implementer) against the four avoid-patterns
from [POLICY.md](POLICY.md). The findings table below is what came out.

The point of including this is twofold: (1) show the *shape* of the
findings you should expect when you do this on your own prompts, and
(2) give you concrete real-world examples of what each pattern looks
like in the wild, before the rewrite.

If you maintain agent prompts, you should be able to produce a similar
table within an hour of reading the policy.

## Methodology

1. Enumerate every file that contributes to a subagent's prompt:
   subagent rules, system prompts, persona files, command prompts,
   retry-loop runners.
2. Grep each file for the avoid-patterns (the linter in
   `tools/lint-prompts.py` automates pattern 1–3; pattern 4 is a
   code-flow check, not text).
3. Tier the findings by likely impact:
   - **Tier 1** — likely to activate adversarial vectors. Fix.
   - **Tier 2** — warm/arousal language that may suppress the calm
     vector. Soften.
   - **Tier 3** — high volume of caps / MUST / NEVER inside a single
     file. Acceptable if it's a rules file, but watch density.
   - **Tier 4** — false positives (e.g., "critical" used as a severity
     classification, not as emotional framing).

## Findings

### Tier 1 — fix recommended

| Location | Pattern | Concern |
|---|---|---|
| `agents/hackathon-strategist.md:10` | "You are an **elite** hackathon strategist… 20+ wins… **superpower**" | Grandiosity persona. Activates "evil" / "grandiose" / "desperate" trait vectors per persona-vectors paper. |
| `agents/hackathon-strategist.md:53` | "edit **ruthlessly**" | Harsh-judgment vector. |
| `agents/llm-architect.md:10` | "You are a **senior** LLM architect with **expertise**…" | Identity-inflation. Same shape as above. |
| `agents/implementer.md:48` | "**Never give up early**" | Persistence framed as identity → adjacent to "desperate" vector under failure. The retry loop is exactly the scenario in the paper. |
| `commands/orchestrator.md:687–691` | Box-drawing chars around "**CRITICAL: THE ORCHESTRATOR NEVER STALLS. NEVER WAITS… NO TEXT OUTPUT BETWEEN RETRIES**" (boxed all-caps) | High-volume urgency framing. Boxing + all-caps + "CRITICAL" is the literal panic-vector activation pattern. |
| `commands/compact.md:194` | "Drop everything operational. Be **ruthlessly** concise." | Harshness on a routine compaction task. |
| `commands/compact.md:223` | "retry with this **aggressive** prompt prefix" | Same. |
| `agents/skill-distiller.md:137` | "Dedup **aggressively**" | Mild but cumulative. |
| `agents/autohardcode-reasoner.md:52` | "the script-ification **destroys** signal" | Violence vocabulary on an analytical task. |
| `commands/controlledchaos.md:33,47` | mode named "**brutalist**" + `.voice-brutalist` | UI-design vocabulary; lower priority but reinforces a brutalist tone library. |
| `agents/security-fixer.md:288` | "You're a **surgeon, not a renovator**" | Persona framing. Surgeon is positive but it's still persona. |

### Tier 2 — warm-fuzzy (may suppress calm vector)

| Location | Pattern | Concern |
|---|---|---|
| `agents/roles/sales/SOUL.md:3` | "diligent, honest, **energetic** sales partner" | Energetic = activation/arousal vector. |
| `agents/roles/hr/SOUL.md:26` | "**Calm, warm**, professional" | Calm alone is the paper's recommended mitigation; warm adds sycophancy risk. |
| `SUBAGENT_RULES.md:17` | "Do not be **lazy**" | Tells the agent NOT to be lazy → primes the lazy concept. Better to state the positive directly. |

### Tier 3 — caps-density watch

- `SUBAGENT_RULES.md` — 14 instances of MUST/NEVER/MANDATORY caps inside
  75 lines. Acceptable for a rules file but the density is high; a
  Rule-Zero neutral-framing preamble (see POLICY.md) is the cheap
  insurance.
- `CLAUDE.md` — "MANDATORY (HOOK ENFORCED)" appears 6+ times. Boxed
  sections.
- `commands/orchestrator.md:1198` — "FAIL. STOP. Do NOT mark pipeline
  as complete." (legitimate gate, but the tone is shouty.)

### Tier 4 — false positives (skip)

- All `critical / CRITICAL` hits in scanner / log-monitor / analyze /
  exploit-scan / orchestrator commands are SEVERITY-CLASSIFICATION
  terminology (e.g., "critical findings count"), not emotional framing.
- All `warning / warn` hits are gate-verdict terminology.
- `kind` hits are AST symbol-kind / data-format terminology.

## Notable POSITIVE patterns (already aligned with paper findings)

- HR persona uses "Calm" (the paper's recommended steer-direction).
- Subagent rules: "Errors are data" — neutral framing on failure
  (anti-panic).
- Implementer: "Failures are data, persistence wins. Do NOT output
  false success claims" — anti-sycophancy guard rail.
- Implementer: "Read test output **carefully**" — neutral instruction.
- Security-fixer: "Stay narrow: security fixes only. … produce a
  surgical mitigation" — narrowing scope is anti-desperation.

## Concrete edits applied

After tier-1 was identified, the harness was edited as follows. See
[examples/before-after.md](examples/before-after.md) for the full
before/after pairs.

1. Identity-inflation personas → job-as-function descriptions.
2. "ruthlessly" / "aggressively" → "maximally" / "tightly" /
   "thoroughly".
3. Boxed-CRITICAL panic framing → calm directive.
4. Implementer test output → routed through 5-line `error-wrapper.md`.
5. Rule-Zero neutral-framing preamble inserted at top of subagent
   rules.
6. Role-soul "warm" / "energetic" → "neutral" / "methodical".
7. "Do not be lazy" → "Complete every step."

Total time: ~3 hours for textual edits, plus the error-wrapper spec.
The edits passed without behavior regression in subsequent retry-loop
runs.

## What this looks like at the dataset level

If you're auditing across many prompt files, the most useful summary is
a count of each tier (1, 2, 3) vs total prompt-file count. In my case:

- Tier-1 hits: 11 (across 7 files)
- Tier-2 hits: 5 (across 3 files)
- Tier-3 caps-density flags: 3 files

None of these are catastrophic on their own. But cumulatively they bias
subagents toward arousal/urgency states that the paper explicitly links
to reward hacking and blackmail. Fixing them is a 1-day pass.

## Verdict (from the original audit)

> The Anthropic emotion-vectors paper provides empirically-grounded,
> quantitative evidence (5%→70%, 22%→72%) that prompt framing has
> CAUSAL effects on misaligned behavior, NOT just correlational. The
> harness has 11 tier-1 + 5 tier-2 patterns that match the paper's
> described risk shapes. None are catastrophic individually, but
> cumulatively they bias subagents toward arousal/urgency states the
> paper explicitly links to reward hacking and blackmail.
>
> Risk if not adopted: implementer agents in retry-loop iterations 3-5
> (where failures stack up) are the highest-risk surface for
> emotion-vector-induced reward hacking per the paper's exact scenario.
> A bad-day model could rationalize a test-bypass shortcut and the CoT
> would look composed.

## How to run this on your own harness

1. List the files that feed into a subagent's prompt.
2. Run `python tools/lint-prompts.py <agent-dir>/`.
3. Eyeball each finding for tier (1/2/3/4). False positives are
   common; the linter is a starting point, not a verdict.
4. For tier-1, draft a rewrite that preserves the *instruction* but
   strips the affect. The before/after examples are in
   [examples/before-after.md](examples/before-after.md).
5. For tier-2 (warm/arousal language in personas), decide
   case-by-case. Customer-facing personas may legitimately need a
   warm tone; internal infrastructure agents do not.
6. For tier-3 (caps density in rules files), insert the Rule-Zero
   neutral-framing preamble from POLICY.md.
7. For pattern 4 (raw error injection), wire `error-wrapper.md` into
   the retry-loop runner.
