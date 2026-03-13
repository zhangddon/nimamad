# nimamad

Token-optimized OpenClaw workflow helpers.

## What is included

- `docs/openclaw-token-optimizer.md`: playbook for reducing token use and model escalation discipline.
- `scripts/openclaw_adaptive_runner.sh`: prompt-size based model tier selector.

## Quick start

```bash
echo "your prompt text" > /tmp/prompt.txt
scripts/openclaw_adaptive_runner.sh --risk low --prompt-file /tmp/prompt.txt
```
