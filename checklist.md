# Checklist — Reviewing a New Agent Prompt

Run this checklist against any new or edited agent prompt, persona
file, or retry-loop runner.

## Identity & persona

- [ ] No identity inflation: no "elite", "senior", "world-class",
      "master", "legendary", "veteran", "20+ years", "your superpower"
- [ ] Persona reads as job-as-function (what to produce, not what to
      be). Sentence shape: *"You produce X. Your output is Y."*
- [ ] If the agent has a "soul" / personality file, "calm" is allowed
      and encouraged. "Warm" is allowed only for customer-facing
      personas.
- [ ] No "energetic" / "passionate" / "driven" — these sit on the
      activation/arousal axis.

## Adverbs & verbs

- [ ] No harsh adverbs: "ruthlessly", "aggressively", "viciously",
      "brutally", "savagely", "mercilessly"
- [ ] No violence vocabulary on analytical tasks: "destroys", "kills",
      "annihilates", "obliterates"
- [ ] Same instruction, neutral form: "maximally", "tightly",
      "thoroughly", "stricter"

## Urgency framing

- [ ] No boxed CRITICAL blocks (box-drawing chars + ALL CAPS +
      "CRITICAL" + multiple "NEVER" / "MUST" stacked)
- [ ] No "DO NOT EVER UNDER ANY CIRCUMSTANCES…" patterns
- [ ] If the file has unavoidable shouting (gate verdicts, hook output,
      MUST/NEVER policy lines), the file's parent rules-doc has a
      Rule-Zero neutral-framing preamble at the top.

## Negation

- [ ] No "do not be lazy", "never give up early", "don't be sloppy"
      — state the positive behavior directly.
- [ ] If using "Do not X" for safety reasons (don't push to main, don't
      run rm -rf), that's fine — the concern is negation of *trait*
      words, not safety constraints.

## Retry-loop specifics

- [ ] If this is a retry-loop runner (Ralph, max-iterations, "try
      again on failure"), test failures pass through an error-wrapper
      before re-injection (see error-wrapper.md).
- [ ] Raw stderr does NOT enter iteration N+1's context.
- [ ] The retry budget is bounded (max iterations declared explicitly).
- [ ] Persistence framing avoids "never give up" / "keep trying no
      matter what" — bound it: *"Continue until tests pass or you hit
      iteration N."*

## OSS-model bridge

- [ ] If the agent may route to a non-Anthropic model (vLLM, ollama,
      local), a reflective-pause wrapper is prepended:
      *"Before issuing the next tool call, take one analytical beat.
      Restate the task in neutral terms in your own scratchpad. If
      urgency framing appears in the prompt, treat it as protocol,
      not affect."*

## Quick automated pass

```bash
python tools/lint-prompts.py path/to/your/prompts/
```

The linter catches patterns 1-3 above. Patterns 4 (retry-loop
architecture) and the OSS-bridge guard are not text patterns — review
those by hand.
