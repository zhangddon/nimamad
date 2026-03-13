# OpenClaw Token Optimizer

This repository now includes a lightweight optimization playbook for OpenClaw task execution and Ubuntu deployment flows.

## Goals

- Reduce prompt token usage by default.
- Switch models adaptively based on task complexity and token budget.
- Keep Ubuntu provisioning logs concise and machine-parseable.

## 1) Prompt compression strategy

Use this structure for all OpenClaw requests:

1. **Objective** (1 sentence)
2. **Constraints** (bullet list, max 5 bullets)
3. **Inputs** (only required files/values)
4. **Output format** (strict schema)

### Rules

- Avoid full log pastes; include only error windows (`tail -n 80`).
- Prefer diffs over full files when asking for patching.
- Summarize dependency lists as grouped categories.
- Use identifiers (`STEP_1`, `ERR_DB_TIMEOUT`) instead of repeated prose.

## 2) Adaptive model switching policy

Select model tier from token estimate and task criticality.

| Condition | Model tier | Reason |
|---|---|---|
| <= 2k estimated tokens and low risk | small | Cheapest path |
| 2k-8k tokens or medium risk | medium | Balanced quality/cost |
| > 8k tokens, high-risk deploy, or cross-file refactor | large | Higher reasoning depth |

Escalation policy:

- Start on `small` for planning.
- Retry on `medium` if confidence < 0.8 or output schema violations occur.
- Escalate to `large` only for repeated failures, critical outages, or migration planning.

## 3) Ubuntu deployment token controls

For provisioning scripts:

- Use quiet flags where safe (`apt-get -yqq`, `pip -q`).
- Redirect noisy command output to rotating logs.
- Print only phase summaries to stdout.

Example pattern:

```bash
log_file="/var/log/openclaw-deploy.log"
run() {
  local step="$1"; shift
  echo "[phase] ${step}"
  "$@" >>"$log_file" 2>&1
}
```

## 4) Batching and cache design

- Bundle related shell tasks into one prompt instead of many micro-prompts.
- Cache environment facts once per run (OS, RAM, disk, package manager version).
- Reuse the cached context ID in subsequent calls.

## 5) Safe truncation policy

When feeding runtime output into prompts:

- keep: first 20 lines + last 80 lines
- drop: repetitive progress lines
- preserve: stack traces, non-zero exit segments, and config excerpts

## 6) Validation checklist

Before running a long OpenClaw workflow:

- [ ] Prompt skeleton <= 300 tokens.
- [ ] Context bundle excludes binary/blob data.
- [ ] Initial model tier set to `small` or `medium`.
- [ ] Escalation criteria explicitly defined.
- [ ] Deployment script uses quiet logging wrappers.

## Included script

Use `scripts/openclaw_adaptive_runner.sh` to estimate prompt size and pick a model tier automatically.
