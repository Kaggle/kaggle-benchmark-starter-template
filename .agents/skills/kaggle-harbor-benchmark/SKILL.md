---
name: kaggle-harbor-benchmark
description: Build, run, and validate Kaggle benchmarks using Harbor.
---

# Kaggle Harbor Benchmark

Guide for authoring and validating Harbor benchmark tasks for Kaggle.

## Task Structure (`tasks/<task-name>/`)

- `environment/Dockerfile`: Container sandbox setup.
- `instruction.md`: Task prompt given to the agent.
- `solution/solve.sh`: Reference solution script (used by `--agent oracle`).
- `tests/`: Verifier test suite. Outputs result to `verifier/ctrf.json` or exit status.

## Quick Workflow

1. **Authenticate Kaggle Model Proxy**:
   ```bash
   kaggle benchmarks auth -y --env-file .env
   source .env
   ```
   *Model Proxy Base URL*: `${MODEL_PROXY_URL%/}/openapi/v1`  
   *Supported Models*: `google/gemini-3.5-flash`, `google/gemini-3-flash-preview`, `google/gemini-3.1-flash-lite`, `openai/gpt-oss-120b` (use `openai/` prefix with `--model`).

2. **Run Local Harbor Checks**:
   - **Baseline** (Reward 0.0): `harbor run --path tasks/<task> --agent nop`
   - **Oracle** (Reward 1.0): `harbor run --path tasks/<task> --agent oracle`
   - **LLM Agent**:
     ```bash
     OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
     OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi/v1" \
     harbor run --path tasks/<task> --agent mini-swe-agent --model openai/google/gemini-3.5-flash
     ```

3. **Test Against Kaggle Runner**:
   Execute `./run_mini_swe_agent.sh` or run the `harbor-git-v1` Docker container locally.

4. **Inspect & Verify**:
   - View jobs: `harbor view jobs` or inspect `jobs/<timestamp>/<task>/trial.log` & `verifier/ctrf.json`.
   - Scan for leaked credentials before committing: `rg -n "Bearer|sk-[A-Za-z0-9]|AIza" jobs/`.

## Agents

- **Built-In**: `nop` (baseline), `oracle` (solution), `mini-swe-agent` (coding agent).
- **Custom Adapters**: Read proxy credentials from `OPENAI_API_KEY` and `OPENAI_BASE_URL`. Extend `BaseInstalledAgent` (CLI binaries) or `BaseAgent` (SDK runners).
