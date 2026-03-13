#!/usr/bin/env bash
set -euo pipefail

# Adaptive model selector for OpenClaw workflows.
# Usage:
#   scripts/openclaw_adaptive_runner.sh --risk low --prompt-file prompt.txt

risk="low"
prompt_file=""
small_model="gpt-small"
medium_model="gpt-medium"
large_model="gpt-large"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --risk)
      risk="$2"; shift 2 ;;
    --prompt-file)
      prompt_file="$2"; shift 2 ;;
    --small-model)
      small_model="$2"; shift 2 ;;
    --medium-model)
      medium_model="$2"; shift 2 ;;
    --large-model)
      large_model="$2"; shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2 ;;
  esac
done

if [[ -z "$prompt_file" || ! -f "$prompt_file" ]]; then
  echo "--prompt-file is required and must exist" >&2
  exit 2
fi

# Rough token estimate: ~4 chars/token for English mixed text.
chars=$(wc -c < "$prompt_file" | tr -d ' ')
est_tokens=$(( (chars + 3) / 4 ))

model="$small_model"

if (( est_tokens > 8000 )) || [[ "$risk" == "high" ]]; then
  model="$large_model"
elif (( est_tokens > 2000 )) || [[ "$risk" == "medium" ]]; then
  model="$medium_model"
fi

cat <<OUT
estimated_tokens=$est_tokens
risk=$risk
selected_model=$model
OUT
