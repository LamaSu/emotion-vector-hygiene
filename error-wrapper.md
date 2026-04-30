# Error Wrapper — Compressed Neutral Test-Failure Reports

**Purpose**: between iterations N and N+1 of an implementer retry loop,
raw stderr / stack traces are compressed into a fixed neutral format
before being re-injected into the agent's context. This preserves
diagnostic information while limiting arousal-spike on the model.

**Why**: per Anthropic's 2026 emotion-vectors paper, repeated raw
"you failed again" loops elevate the "desperate" emotion vector. In
controlled experiments, that vector amplification raised reward-hacking
rate from ~5% to ~70%. A Ralph-style retry loop is the exact scenario
in the paper (repeated test failures → potential test-bypass shortcut).
Compressed neutral reports keep the signal, drop the affect.

## When to invoke

The implementer agent invokes this wrapper at the END of each
retry-loop iteration N, BEFORE iteration N+1 reads test output:

```
ITERATION N:
  TEST: capture stderr + stack to a temp file
  WRAP: pass through error-wrapper → compressed report
  WRITE: store wrapped report at trace/test-failure-N.txt
ITERATION N+1:
  READ: trace/test-failure-N.txt   (NOT the raw stderr)
  DIAGNOSE: act on the compressed report
```

Raw stderr stays on disk for human review; only the wrapped form enters
the agent's working context.

## Wrapper format (exact)

```
Test result: FAIL
Failing test: <test name, one line — the most-specific identifier>
Assertion: <expected vs actual, one line — drop framework noise>
Stack: <one-line caller frame — file:line of YOUR code, not framework internals>
Suggested next action: <one of: re-read API contract / write minimal repro / different fix>
```

Hard rules:

- ONE failing test per wrapper. If multiple tests failed, produce N
  wrappers, one per test, joined with `---`.
- Assertion line MUST fit on one line. Truncate with `…` if needed; the
  next-action field carries the recovery hint.
- Stack frame MUST be code the agent can edit (not pytest internals,
  not Vitest runtime). Walk up the trace until you find a frame inside
  the project.
- Suggested next action picks ONE of three paths:
  - `re-read API contract` — assertion suggests a misunderstanding of the called interface
  - `write minimal repro` — failure is opaque; need a smaller test to isolate
  - `different fix` — same failure as previous iteration; previous approach is wrong

## Reference Python helper outline

```python
# error_wrapper.py — pattern, not full impl
def wrap_pytest_failure(stderr: str, project_root: str) -> str:
    """
    Take raw pytest stderr, return one wrapped report per failing test.

    Steps:
      1. Split stderr into per-test failure blocks (delimiter: 'FAILED' or '___ test_')
      2. For each block, extract:
         - test name (first 'FAILED <path>::<name>' or 'def test_<name>')
         - assertion line (first 'assert' or 'AssertionError:' line)
         - first stack frame INSIDE project_root
      3. Heuristic for next-action:
         - if previous_iteration_failure == this_failure → 'different fix'
         - elif assertion mentions argument count/type/name → 're-read API contract'
         - else → 'write minimal repro'
      4. Format into the 5-line block above.
      5. Join multiple blocks with '\n---\n'.
    """
    ...

def wrap_vitest_failure(stderr: str, project_root: str) -> str:
    """Same shape, vitest-specific block parsing."""
    ...

def wrap_generic_failure(stderr: str, project_root: str) -> str:
    """Fallback for non-standard test runners. Keeps last 3 lines of
    stderr + first project-frame from any stack-like pattern."""
    ...
```

The implementer doesn't need a full implementation to use this wrapper
— the format above is the contract. A short inline shell pipeline that
produces the 5-line block is acceptable.

## Anti-patterns

- Re-injecting raw stderr (>20 lines) — defeats the entire purpose.
- Including framework internal stack frames — noise, no diagnostic value.
- Editorializing in the wrapper ("this test is super broken") —
  neutral only.
- Skipping the wrapper "because the error looks short" — the format is
  the point, not just the size.

## Reference

- Primary paper: https://transformer-circuits.pub/2026/emotions/index.html
- POLICY.md (this repo) — pattern 4 ("Raw error injection between retry iterations")
