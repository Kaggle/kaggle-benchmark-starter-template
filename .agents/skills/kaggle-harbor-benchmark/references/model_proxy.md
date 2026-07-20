# Model Proxy

## Kaggle CLI Auth

Drop an email to Ivan at ileo@google.com for extra quota and to create a kaggle organisation, see docs [here](https://www.kaggle.com/docs/organizations).  

While waiting, continue authoring and debugging the benchmark locally with Harbor.

Install and authenticate the Kaggle CLI with uv:

```bash
uv tool install kaggle
kaggle auth login
kaggle benchmarks auth -y --env-file .env
```

The generated `.env` contains:

```text
MODEL_PROXY_URL
MODEL_PROXY_API_KEY
MODEL_PROXY_EXPIRY_TIME
```

The key is short-lived. Rerun `kaggle benchmarks auth -y --env-file .env` when
it expires.

## Endpoints

The proxy exposes two compatibility surfaces:

```text
${MODEL_PROXY_URL%/}/openapi
${MODEL_PROXY_URL%/}/anthropic
```

Use `/openapi/chat/completions` for OpenAI-compatible chat and tool-calling
flows. Use `/anthropic/messages` for Anthropic-compatible calls.

## OpenAI Chat Completions Smoke Test

```bash
source .env

curl "${MODEL_PROXY_URL%/}/openapi/chat/completions" \
  -H "Authorization: Bearer ${MODEL_PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-3.5-flash",
    "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
    "max_tokens": 20000
  }'
```

## Anthropic Smoke Test

```bash
source .env

curl "${MODEL_PROXY_URL%/}/anthropic/messages" \
  -H "x-api-key: ${MODEL_PROXY_API_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-3.5-flash",
    "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
    "max_tokens": 20000
  }'
```

## Supported Test Models

Use these first when checking a new task:

```text
google/gemini-3-flash-preview
google/gemini-3.1-flash-lite
google/gemini-3.5-flash
openai/gpt-oss-120b
```

## Chat Completions vs Responses

Prefer `/openapi/chat/completions` for coding agents that perform tool calls.
In local testing, Chat Completions accepted the tool result turn:

```text
assistant tool_call -> role: tool result -> final assistant response
```

The `/openapi/responses` path exposed a proxy translation issue for tool
results:

```text
function_response.name: [REQUIRED_FIELD_MISSING]
```

OpenCode's built-in `openai` provider uses `/responses`. To force
`/chat/completions`, register a custom OpenCode provider with
`@ai-sdk/openai-compatible` and point it at `${MODEL_PROXY_URL%/}/openapi`.

For a debugging walkthrough and the local repro script, see `debug.md`.
