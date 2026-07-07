# Kaggle Benchmark Starter Template

This repository is a starter template that shows how to publish a dataset and
benchmark on Kaggle using the Harbor-compatible benchmark spec. The examples in
this starter show how to structure benchmark tasks, validate them locally with
Harbor, and run the same payload through the packaged runner flow that Kaggle
can evaluate.

This starter includes one example task, `ivanleomk/hello-world`, which asks an
agent to create `/app/hello.txt` with the content
`Hello, world!`.

## Contents

Follow these steps when creating a benchmark from this template:

1. Create a Kaggle organization and wait for approval.
2. Install and authenticate the Kaggle CLI.
3. Generate local model proxy credentials.
4. Test the model proxy.
5. Run the benchmark locally with Harbor.
6. Push the repo and smoke test the packaged runner payload.
7. Publish multi-architecture runner images, if you maintain your own runner.

You can complete the local Harbor and model proxy steps while waiting for Kaggle
organization approval.

## Kaggle Organization Approval

Create a Kaggle organization for the benchmark publisher account and make sure
it is approved before publishing the final dataset and benchmark. Approval is
only required for publishing; you can still install the CLI, generate model
proxy credentials, and validate this repo locally while waiting.

## Repository Layout

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
${MODEL_PROXY_URL%/}/openapi
${MODEL_PROXY_URL%/}/anthropic
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

curl "${MODEL_PROXY_URL%/}/openapi/chat/completions" \
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

curl "${MODEL_PROXY_URL%/}/anthropic/messages" \
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

## Run the benchmark locally

While authoring a benchmark, run Harbor directly on your own machine. This uses
your normal local Docker daemon, so there is no Docker-in-Docker setup involved.

```bash
source .env
MODEL_PROXY_HOST="$(python3 -c 'from urllib.parse import urlparse; import os; print(urlparse(os.environ["MODEL_PROXY_URL"]).hostname)')"

harbor run \
  -p tasks/hello-world \
  -a mini-swe-agent \
  -m openai/google/gemini-3.5-flash \
  --ae OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
  --ae OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi" \
  --ae OPENAI_API_BASE="${MODEL_PROXY_URL%/}/openapi" \
  --allow-agent-host "${MODEL_PROXY_HOST}"
```

Use this loop to validate the task definition, Docker environment, verifier,
artifacts, agent loop, and model proxy credentials.

## Test the runner payload end to end

After the benchmark works locally and has been pushed, you can smoke test the
packaged runner flow. This is closer to how hosted evaluation runs: the runner
image clones the repo, checks out a ref, and runs Harbor against the requested
task path.

On macOS, the runner image uses Docker-in-Docker, so set
`DOCKERD_STORAGE_DRIVER=vfs` to avoid nested overlay filesystem failures in
Docker Desktop. The Kaggle team is working on a native arm64 runner image; use
that for Mac smoke tests once it is published.

```bash
source .env
mkdir -p .harbor-runner-test

docker pull us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test

docker run --rm --privileged \
  -v "$PWD/.harbor-runner-test:/kaggle/working" \
  -e DOCKERD_STORAGE_DRIVER=vfs \
  -e KAGGLE_TASK_REPO_URL=https://github.com/ivanleomk/kaggle-benchmark-starter-template.git \
  -e KAGGLE_TASK_REPO_REF=2c661dc \
  -e KAGGLE_TASK_PATH=tasks/hello-world \
  -e KAGGLE_HARBOR_AGENT=mini-swe-agent \
  -e KAGGLE_HARBOR_MODEL=openai/google/gemini-3.5-flash \
  -e OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
  -e OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi" \
  -e OPENAI_API_BASE="${MODEL_PROXY_URL%/}/openapi" \
  us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test
```

The mounted directory is where the runner writes outputs. Inside the container,
Harbor writes to `/kaggle/working/jobs`; on your machine, those files appear
under `.harbor-runner-test/jobs`:

```bash
find .harbor-runner-test/jobs -name result.json -print
```

Use a commit SHA for `KAGGLE_TASK_REPO_REF` when you want the run to be fully
reproducible.

If the task repo is private, also pass `KAGGLE_GIT_TOKEN` with a token that can
clone it. If you are already authenticated with the GitHub CLI, you can generate
one with `gh auth token`:

```bash
source .env
mkdir -p .harbor-runner-test

docker run --rm --privileged \
  -v "$PWD/.harbor-runner-test:/kaggle/working" \
  -e DOCKERD_STORAGE_DRIVER=vfs \
  -e KAGGLE_GIT_TOKEN="$(gh auth token)" \
  -e KAGGLE_TASK_REPO_URL=https://github.com/ivanleomk/kaggle-benchmark-starter-template.git \
  -e KAGGLE_TASK_REPO_REF=2c661dc \
  -e KAGGLE_TASK_PATH=tasks/hello-world \
  -e KAGGLE_HARBOR_AGENT=mini-swe-agent \
  -e KAGGLE_HARBOR_MODEL=openai/google/gemini-3.5-flash \
  -e OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
  -e OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi" \
  -e OPENAI_API_BASE="${MODEL_PROXY_URL%/}/openapi" \
  us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test
```

## Build a runner image

This repo also includes a minimal Harbor runner image in `runner/`. To publish
both amd64 and arm64 variants under one tag:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-test:latest \
  --push \
  runner
```
