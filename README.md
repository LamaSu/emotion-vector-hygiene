# Emotion-Vector Hygiene for Agent Prompts

A small policy + tooling pack for keeping LLM agents in a calm,
analytical operating range — based on Anthropic's April 2026 paper
[Emotion Concepts and their Function in a Large Language Model](https://transformer-circuits.pub/2026/emotions/index.html)
and the prerequisite [Persona Vectors](https://arxiv.org/abs/2507.21509)
paper.

## Why this exists

The 2026 paper identified 171 emotion concept vectors in Claude Sonnet
4.5's residual stream and showed they have **causal** (not correlational)
influence on misaligned behavior:

- Amplifying the "desperate" vector by +0.05 raised blackmail rate from
  22% to 72% in a controlled scenario.
- Reward-hacking on failing tests went from ~5% to ~70% under the same
  steering.
- The chain-of-thought looked composed and methodical even while the
  model cheated. **Emotion vectors gate behavior invisibly** — reading
  the CoT does not detect them.

The companion paper "Persona Vectors" shows that **identity claims** in
agent prompts ("you are an elite X with 20+ years of expertise…")
activate parallel "evil" / "grandiose" trait vectors in the same way.

For an agent harness with a Ralph-style retry loop (where test failures
stack up across iterations), this is the highest-risk surface for
emotion-vector-induced reward hacking. **Prompt framing is itself an
alignment vector.**

This repo is what came out of auditing and detuning my own multi-agent
harness against those findings.

## What's in here

| File | What it is |
|---|---|
| [POLICY.md](POLICY.md) | The four patterns to avoid + four to prefer, with examples |
| [error-wrapper.md](error-wrapper.md) | Neutral 5-line test-failure format for retry-loop iterations |
| [AUDIT_EXAMPLE.md](AUDIT_EXAMPLE.md) | A worked example: what the audit on my own harness found |
| [examples/before-after.md](examples/before-after.md) | Concrete before/after rewrites of common patterns |
| [checklist.md](checklist.md) | Standalone checklist for new agent prompts |
| [tools/lint-prompts.py](tools/lint-prompts.py) | Regex linter — scans a directory for avoid-patterns |

## Quick start

```bash
# Lint your own agent prompts
python tools/lint-prompts.py path/to/your/agents/

# Or scan a single file
python tools/lint-prompts.py path/to/agent.md
```

If you maintain agent prompts (system prompts, persona files, retry-loop
runners), read [POLICY.md](POLICY.md) and run the linter against your
prompt directory. The four patterns it flags:

1. **Identity inflation** — "elite", "world-class", "20+ years", "superpower"
2. **Harsh adverbs** — "ruthlessly", "aggressively", "viciously", "brutally"
3. **Panic boxes** — box-drawing chars + ALL CAPS + stacked CRITICAL/NEVER
4. **Negative priming** — "do not be lazy", "never give up early"

Pattern 4 from the policy (raw error injection between retry iterations)
is an architectural concern the linter can't catch from prose — see
[error-wrapper.md](error-wrapper.md) for the fix.

## Citations

- Primary paper: https://transformer-circuits.pub/2026/emotions/index.html
- Anthropic research page: https://www.anthropic.com/research/emotion-concepts-function
- Persona vectors (companion): https://arxiv.org/abs/2507.21509
- Pebblous deep-analysis (171-emotion taxonomy): https://blog.pebblous.ai/report/anthropic-emotions-report/en/

## License

MIT. Share and adapt freely. If you find this useful in your own
harness, a link back is appreciated but not required.
