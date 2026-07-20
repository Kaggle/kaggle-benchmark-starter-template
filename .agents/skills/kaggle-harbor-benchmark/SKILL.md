---
name: kaggle-harbor-benchmark
description: Build, run, and validate Kaggle benchmarks using Harbor.
---

# Kaggle Harbor Benchmark

Guide for authoring, testing, and validating Harbor benchmark tasks for Kaggle.

## Task Structure (`tasks/<task-name>/`)

- `environment/Dockerfile`: Container sandbox setup.
- `instruction.md`: Task prompt given to the agent.
- `solution/solve.sh`: Reference solution script (used by `--agent oracle`).
- `tests/`: Verifier test suite. Outputs result to `verifier/ctrf.json` or exit status.
- `task.toml`: Task metadata and evaluation settings.

## Model Proxy Auth & Endpoints

Install and authenticate the Kaggle CLI:

```bash
uv tool install kaggle
kaggle auth login
kaggle benchmarks auth -y --env-file .env
source .env
```

- **Endpoints**:
  - OpenAI Chat Completions: `${MODEL_PROXY_URL%/}/openapi/v1`
  - Anthropic Messages: `${MODEL_PROXY_URL%/}/anthropic/v1/messages`
- **Supported Test Models**: `google/gemini-3.5-flash`, `google/gemini-3-flash-preview`, `google/gemini-3.1-flash-lite`, `openai/gpt-oss-120b` (use `openai/` prefix with `--model` in Harbor).
- **Tool Calling Note**: Prefer Chat Completions (`/openapi/v1`) for coding agents performing tool calls. For OpenCode, use `@ai-sdk/openai-compatible` to force `/chat/completions`.

## Quick Workflow

1. **Baseline Check** (Reward 0.0):
   ```bash
   harbor run --path tasks/<task> --agent nop
   ```
2. **Oracle Check** (Reward 1.0):
   ```bash
   harbor run --path tasks/<task> --agent oracle
   ```
3. **LLM Agent Run**:
   ```bash
   source .env
   OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
   OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi/v1" \
   harbor run --path tasks/<task> --agent mini-swe-agent --model openai/google/gemini-3.5-flash
   ```
4. **Test Against Kaggle Runner**:
   Execute `./run_mini_swe_agent.sh` or run the `harbor-git-v1` Docker container locally.

## Custom Agents

- **Built-In**: `nop` (baseline), `oracle` (solution), `mini-swe-agent` (coding agent).
- **Binary CLI Agent**: Extend `BaseInstalledAgent` (e.g. `agents/opencode_binary_agent.py`). Save raw logs to `/logs/agent` and convert to ATIF at `/logs/agent/trajectory.json`.
- **SDK Agent**: Extend `BaseAgent` (e.g. `agents/antigravity_agent.py` & `agents/antigravity_runner.py`). Write SDK transcript as ATIF.

## Debugging & Secrets Check

- **Verify Proxy**: Test endpoint with `curl "${MODEL_PROXY_URL%/}/openapi/v1/chat/completions" -H "Authorization: Bearer ${MODEL_PROXY_API_KEY}" -H "Content-Type: application/json" -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"Reply with exactly: ok"}]}'`.
- **Inspect Jobs**: View summary with `harbor view jobs` or inspect `jobs/<timestamp>/<task>/trial.log` & `verifier/ctrf.json`.
- **Secrets Check**: Confirm `n_errors: 0` in `result.json` and scan for secrets before committing: `rg -n "Bearer|sk-[A-Za-z0-9]|AIza" jobs/`.
