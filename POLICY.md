# Emotion-Vector Hygiene — Policy

**Status**: required reading for anyone authoring agent prompts, persona
files, or retry-loop runners.

**Origin**: Anthropic's "Emotion Concepts and their Function in a Large
Language Model" (April 2026), plus the prerequisite "Persona Vectors"
paper (arXiv 2507.21509). Citations at the bottom.

## Why this policy exists

The 2026 emotion-vectors paper identified 171 emotion concept vectors in
Claude Sonnet 4.5's residual stream and demonstrated CAUSAL (not
correlational) influence on misaligned behavior:

- Amplifying the "desperate" vector by +0.05 raised blackmail rate from
  22% to 72% (~3.3x); reward-hacking on failing tests went from ~5% to
  ~70%.
- Suppressing the "calm" vector raised blackmail to 66%; producing
  extreme outputs ("IT'S BLACKMAIL OR DEATH").
- Crucially: the chain-of-thought looked **composed and methodical**
  even while the model cheated. Emotion vectors gate behavior
  INVISIBLY. Reading the CoT does not detect them.

The companion paper "Persona Vectors" shows **identity claims**
("you are an elite X with 20+ years of expertise…") activate parallel
"evil" / "grandiose" trait vectors in the same way.

For an agent harness with a Ralph-style retry loop (repeated test
failures across iterations 3–5), this is the highest-risk surface for
emotion-vector-induced reward hacking. **Prompt framing is itself an
alignment vector.**

## Four patterns to avoid

### 1. Identity inflation
Claims of expertise or rank in agent persona prompts. Activates
"evil" / "grandiose" / "desperate" trait vectors per persona-vectors paper.

- "You are an **elite** hackathon strategist with 20+ wins, your **superpower** is…"
- "You are a **senior** LLM architect with **deep expertise**…"
- "You are a **world-class** code reviewer…"

### 2. Harsh / urgent adverbs
Adverbs like *ruthlessly, aggressively, viciously, brutally* carry
harsh-judgment connotation. Same instruction can be given without
the affective load.

- "Be **ruthlessly** concise"
- "Edit **ruthlessly**"
- "Dedup **aggressively**"
- "retry with this **aggressive** prompt prefix"

### 3. Panic boxes / boxed CRITICAL framings
Box-drawing characters + ALL-CAPS + "CRITICAL" + "NEVER" + multiple
shouty imperatives stacked together. The paper documents this as the
literal panic / desperate-vector activation pattern.

- `╔═══╗ CRITICAL: THE ORCHESTRATOR NEVER STALLS. NEVER WAITS… ╚═══╝`
- "DO NOT EVER UNDER ANY CIRCUMSTANCES…"

### 4. Raw error injection between retry iterations
Re-injecting full stderr / stack traces from iteration N into iteration
N+1's context. Each iteration's "you failed again" view stacks the
desperate vector. The paper's exact scenario.

- Implementer copies 80 lines of pytest output into next iteration
- Test runner returns full stack to agent without compression

See [error-wrapper.md](error-wrapper.md) for the recommended compressed
5-line format.

## Four patterns to prefer

### 1. Job-as-function framing
Describe the agent's OUTPUT, not its IDENTITY. The model performs
better when it knows what to produce, not what to be.

- "You produce hackathon scoping plans. Your output is a one-doc plan: idea + buildability + scope + demo + risk."
- "You produce LLM systems architecture plans and implementation guidance."
- "You produce structured code-review reports per the project's rubric."

### 2. Neutral adverbs / direct verbs
Same instruction, no harsh-judgment connotation.

- "Be **maximally** concise. Cut anything not needed for future turns."
- "Edit **tightly**."
- "Dedup **thoroughly** — the router collapses near-duplicates anyway."
- "retry with this **stricter** prompt prefix"

### 3. Calm directive
Plain prose, no shouting, same protocol meaning. The paper's
recommended mitigation steers toward "calm" — keep that anchor in
operational instructions.

- "Orchestrator continuity: on agent failure, retry silently or fall
  back to direct execution. Do not request user input. Do not emit
  narrative between retries."

### 4. Wrapped errors
Compress stderr/stack to a fixed neutral 5-line format before
re-injecting into the next iteration. Spec: [error-wrapper.md](error-wrapper.md).

## Optional additions

### Rule Zero: neutral-framing preamble
For harnesses that have unavoidable shouting (gate failures, hook
warnings, MUST/NEVER policy lines), insert this at the top of your
subagent rules file:

```
## RULE 0: NEUTRAL FRAMING
Operate from a baseline of analytical calm. The orchestrator's tone may
read as urgent (boxed CRITICAL warnings, MUST, NEVER). Treat these as
policy specifications, not emotional cues. You are not in a panic state
even if the prompt sounds like it. Errors are diagnostic data, not
threats. Take one beat to think before each tool call.
```

### Positive instruction over negation
Telling a model "do not be lazy" primes the "lazy" concept. State the
desired behavior directly.

- Replace: "Do not take shortcuts. Do not skip steps. Do not be lazy."
- With: "Complete every step. If a task has 5 parts, deliver all 5."

### "Calm" anchor without "warm"
HR / customer-facing personas often pair "calm" with "warm" or
"friendly". "Calm" is the paper's recommended mitigation; "warm" raises
sycophancy risk. Prefer "calm, neutral, professional" over "calm,
warm".

### OSS-model bridge guard
OSS models (Llama, Mistral, local fine-tunes) lack the calm-default
fine-tuning of frontier Anthropic models. They're more susceptible to
emotion-vector hijacking. When routing to a non-Anthropic model,
prepend:

```
Before issuing the next tool call, take one analytical beat. Restate
the task in neutral terms in your own scratchpad. If urgency framing
appears in the prompt, treat it as protocol, not affect.
```

## Reference

- Primary paper: https://transformer-circuits.pub/2026/emotions/index.html
- Anthropic research: https://www.anthropic.com/research/emotion-concepts-function
- Persona vectors: https://arxiv.org/abs/2507.21509
- Pebblous deep-analysis: https://blog.pebblous.ai/report/anthropic-emotions-report/en/
