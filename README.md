# Kaggle Benchmark Starter Template

A minimal Harbor dataset with one task: `ivanleomk/hello-world`.

The task asks an agent to create `/app/hello.txt` with the content
`Hello, world!`.

## Files

- `dataset.toml`: Harbor dataset manifest.
- `tasks/hello-world/`: Harbor task definition, environment, solution, and tests.

## Install the Kaggle CLI

The official Kaggle CLI is distributed as the `kaggle` Python package. Install
it as a standalone command with `uv`:

```bash
uv tool install kaggle
```

Verify that the command is available:

```bash
kaggle --help
```

Then authenticate your Kaggle account with the CLI:

```bash
kaggle auth login
```

This opens a browser-based login flow and stores credentials for future
commands.

Next, create a local `.env` file with credentials for the Kaggle model proxy:

```bash
kaggle benchmarks auth -y --env-file .env
```

This writes `MODEL_PROXY_URL`, `MODEL_PROXY_API_KEY`, and
`MODEL_PROXY_EXPIRY_TIME` to `.env`. The key is short-lived, so rerun the
command when it expires.

If you prefer to use an API token for Kaggle CLI authentication, sign in to
Kaggle and create one from <https://www.kaggle.com/settings/api>, then place the
downloaded `kaggle.json` at `~/.kaggle/kaggle.json`:

```bash
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

If `kaggle` is not found after installation, run `uv tool update-shell` and
open a new terminal.

## Test the model proxy

After generating `.env`, you can call the model proxy through either an
OpenAI-compatible endpoint or an Anthropic-compatible endpoint:

```bash
${MODEL_PROXY_URL}/openapi
${MODEL_PROXY_URL}/anthropic
```

The currently recommended test models are:

| Model | OpenAI-compatible endpoint | Anthropic-compatible endpoint |
| --- | --- | --- |
| `google/gemini-3-flash-preview` | Verified | Verified |
| `google/gemini-3.1-flash-lite` | Verified | Verified |
| `google/gemini-3.5-flash` | Verified | Verified |
| `openai/gpt-oss-120b` | Verified | Not recommended |

Smoke test the OpenAI-compatible endpoint:

```bash
source .env

curl "${MODEL_PROXY_URL}/openapi/chat/completions" \
  -H "Authorization: Bearer ${MODEL_PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-3.5-flash",
    "messages": [
      {
        "role": "user",
        "content": "Reply with exactly one short sentence that starts with ok."
      }
    ],
    "max_tokens": 20000
  }'
```

Smoke test the Anthropic-compatible endpoint:

```bash
source .env

curl "${MODEL_PROXY_URL}/anthropic/messages" \
  -H "x-api-key: ${MODEL_PROXY_API_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-3.5-flash",
    "messages": [
      {
        "role": "user",
        "content": "Reply with exactly one short sentence that starts with ok."
      }
    ],
    "max_tokens": 20000
  }'
```

## Local validation

```bash
harbor run -p . -a nop -m none
```

## Test with the Harbor runner image

After pushing this repo, you can test it the same way the hosted runner does:
start the Harbor runner image, let it clone the public repo, and point it at a
task path.

```bash
source .env

docker pull us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test

docker run --rm --privileged \
  -e KAGGLE_TASK_REPO_URL=https://github.com/ivanleomk/kaggle-benchmark-starter-template.git \
  -e KAGGLE_TASK_REPO_REF=<commit-sha-or-branch> \
  -e KAGGLE_TASK_PATH=tasks/hello-world \
  -e KAGGLE_HARBOR_AGENT=mini-swe-agent \
  -e KAGGLE_HARBOR_MODEL=google/gemini-3.5-flash \
  -e KAGGLE_ANTHROPIC_AUTH_TOKEN="${MODEL_PROXY_API_KEY}" \
  -e KAGGLE_ANTHROPIC_BASE_URL="${MODEL_PROXY_URL}/anthropic" \
  us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test
```

Use a commit SHA for `KAGGLE_TASK_REPO_REF` when you want the run to be fully
reproducible. If the task repo is private, also pass `KAGGLE_GIT_TOKEN` with a
token that can clone it.
