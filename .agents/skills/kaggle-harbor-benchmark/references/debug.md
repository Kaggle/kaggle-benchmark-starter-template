# Debugging

Debug benchmark failures by isolating one layer at a time.

## 1. Check Model Access

Before running Harbor, confirm the model endpoint works with a tiny request.

For Kaggle model proxy, source `.env` and call:

```bash
curl "${MODEL_PROXY_URL%/}/openapi/chat/completions" \
  -H "Authorization: Bearer ${MODEL_PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"Reply with exactly: ok"}]}'
```

If this fails, refresh credentials:

```bash
kaggle benchmarks auth -y --env-file .env
```

## 2. Check the Task With a Built-In Agent

Run the task without any custom agent first:

```bash
harbor run -p tasks/hello-world -a mini-swe-agent -m openai/gemini-3.5-flash
```

If this fails, inspect the task Dockerfile, instruction, verifier, and
artifacts before debugging custom agent code.

## 3. Check the Custom Agent

Look at the latest job directory:

```bash
find jobs -name result.json -print | sort
harbor view jobs
```

Inspect:

- `job.log`
- `<trial>/trial.log`
- `<trial>/agent/*`
- `<trial>/verifier/*`
- `<trial>/result.json`

If the agent created the right artifact but Harbor reports an exception, inspect
the agent log for post-success errors. For OpenCode against the model proxy,
this often means it used `/responses` instead of `/chat/completions`.

## 4. Check OpenCode Tool Calling

The proxy's `/openapi/chat/completions` path handles tool-result turns. The
`/openapi/responses` path has shown `function_response.name` translation errors
for tool-result turns.

Use `scripts/repro_model_proxy_tool_result.py` to reproduce the Responses API
failure with the OpenAI client.

For OpenCode, configure a custom provider with `@ai-sdk/openai-compatible` so
the agent uses Chat Completions.

## 5. Check Runner Image Smoke Tests

Use the packaged runner image only after local Harbor works. The runner image
adds repo cloning, ref checkout, and Docker-in-Docker.

On macOS Docker Desktop, pass:

```bash
-e DOCKERD_STORAGE_DRIVER=vfs
```

For private repos, pass:

```bash
-e KAGGLE_GIT_TOKEN="$(gh auth token)"
```

If the image clones and checks out the ref but fails while building/running
Docker, the task may be fine and the failure may be Docker-in-Docker storage or
architecture support.

## 6. Check Committed Job Outputs

Before committing sample jobs, confirm each named run has `n_errors: 0` and a
passing reward in `result.json`. Also scan for secrets:

```bash
rg --pcre2 -n "sk-[A-Za-z0-9]|AIza|Authorization: Bearer|Bearer [A-Za-z0-9_\\-.=]{20,}" jobs/<named-run>
```
