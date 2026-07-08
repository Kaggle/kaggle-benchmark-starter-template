# Creating Custom Agents

Harbor can run built-in agents or custom adapters. Pick the simplest adapter
that matches how the target agent is packaged.

## Model Proxy Contract

Custom agents and binaries should send language model calls through the Kaggle
model proxy during benchmark validation. This keeps model calls visible to the
benchmark infrastructure and avoids hidden provider credentials in agent code.

Pass credentials through environment variables such as `OPENAI_API_KEY`,
`OPENAI_BASE_URL`, or `GEMINI_API_KEY`. Do not hardcode keys in adapters,
runner scripts, job logs, or committed sample outputs.

## Built-In Agent

Use a built-in Harbor agent first to prove the task, Docker environment,
verifier, artifacts, and model access are working.

```bash
harbor run -p tasks/hello-world -a mini-swe-agent -m openai/gemini-3.5-flash
```

Template example:

- command pattern: `harbor run -a mini-swe-agent`
- sample output: `jobs/mini-swe-agent`

## Binary CLI Agent

Use `BaseInstalledAgent` when the agent is a command-line binary.

Implementation shape:

1. Install system packages with `exec_as_root`.
2. Install user-level tools with `exec_as_agent`.
3. Run the binary against the rendered Harbor instruction.
4. Save raw stdout/stderr under `/logs/agent`.
5. Convert binary logs into ATIF at `/logs/agent/trajectory.json`.
6. Populate `AgentContext` metrics from the trajectory.

Template example:

- adapter: `agents/opencode_binary_agent.py`
- sample output: `jobs/opencode-binary`

OpenCode note: with the Kaggle model proxy, accept Harbor model names like
`openai/google/gemini-3.5-flash`, but run OpenCode through an internal custom
provider such as `kaggleproxy/google/gemini-3.5-flash`. Configure that provider
with `@ai-sdk/openai-compatible` so OpenCode uses `/chat/completions`, not the
built-in OpenAI `/responses` path.

## SDK-Backed Agent

Use `BaseAgent` when the agent has a Python SDK, richer runtime, or dedicated
runner script.

Implementation shape:

1. Keep the Harbor adapter small.
2. Install `uv` in the task container if needed.
3. Upload a runner script into the container.
4. Declare runner dependencies with PEP 723 metadata.
5. Pass model name, credentials, skill paths, and MCP config through env vars.
6. Write the SDK transcript as ATIF.

Template example:

- adapter: `agents/antigravity_agent.py`
- runner: `agents/antigravity_runner.py`
- sample output: `jobs/antigravity`
