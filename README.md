# ileo/sample-dataset

This is a starter repository for building Agentic Benchmarks using the [Harbor Benchmark Framework](https://github.com/kaggle/harbor) to be ran on Kaggle.

## Initialising your Harbor Dataset

You can initialise the repository using the following command

```bash
uv venv .venv
source .venv/bin/activate
uv pip install harbor
echo ".venv/" > .gitignore
harbor init --dataset ileo/sample-dataset
harbor init --task ileo/example-task -o tasks
```

## Generating your Kaggle Credentials

Before running your first task locally.

Install the Kaggle CLI and mint authentication credentials using the commands below:

```bash
pip install kaggle
kaggle auth login
kaggle benchmarks auth -y --env-file .env
```

This will in turn mint a .env file with the credentials needed to connect to the model proxy server.

```toml
MODEL_PROXY_URL=
MODEL_PROXY_API_KEY=
MODEL_PROXY_EXPIRY_TIME=2026-07-20T22:18:38.291000Z
```

Once you've minted your first set of credentials, you should then verify that they work by testing it as seen below.

```bash
source .env
curl "${MODEL_PROXY_URL%/}/openapi/v1/chat/completions" \
  -H "Authorization: Bearer ${MODEL_PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"Reply with exactly: ok"}]}'
```

If you'd like to test it with an Anthropic compatible endpoint, you can use the following

```bash
source .env
curl "${MODEL_PROXY_URL%/}/anthropic/v1/messages" \
  -H "x-api-key: ${MODEL_PROXY_API_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.5-flash","messages":[{"role":"user","content":"Reply with exactly: ok"}],"max_tokens":100}'
```

We also support the responses API as seen below if you're using the new OpenAI models.

```bash
source .env
curl "${MODEL_PROXY_URL%/}/openapi/v1/responses" \
  -H "Authorization: Bearer ${MODEL_PROXY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemini-3.5-flash","input":"Reply with exactly: ok"}'
```

## Your First Run

After initialising your dataset and generating your Kaggle credentials, perform your first local run to verify that your Docker environment and task verifier work end-to-end.

To test the baseline environment, you can run the NOP agent. This builds the Docker image and runs the test suite without modifications (expecting Reward: 0.0).

```bash
harbor run --path tasks/example-task --agent nop
```

To test the task reference solution, you can run the Oracle agent. The `oracle` agent executes `solution/solve.sh` inside the container to solve the task and verify that your test suite passes (expecting Reward: 1.0).

```bash
harbor run --path tasks/example-task --agent oracle
```

To run an LLM agent (e.g. `mini-swe-agent`) locally using your Kaggle Model Proxy credentials:

```bash
source .env
OPENAI_API_KEY="${MODEL_PROXY_API_KEY}" \
OPENAI_BASE_URL="${MODEL_PROXY_URL%/}/openapi/v1" \
harbor run --path tasks/example-task --agent mini-swe-agent --model openai/google/gemini-3.5-flash
```

After the run finishes, you can inspect the run results in `jobs/`. You can view a summary using `harbor view jobs`, or check detailed logs in `jobs/<timestamp>/<task-name>/trial.log` and `jobs/<timestamp>/<task-name>/verifier/ctrf.json`.

## Testing against Kaggle

You can verify and run a task using `mini-swe-agent` on the Kaggle Harbor executor Docker image locally:

```bash
source .env
docker run --rm -it \
  --privileged \
  -v "$PWD/kaggle/working:/kaggle/working" \
  -v "harbor-dind-data:/var/lib/docker" \
  -e KAGGLE_TASK_REPO_URL="git@github.com:Kaggle/kaggle-benchmark-starter-template.git" \
  -e KAGGLE_TASK_PATH="tasks/hello-world" \
  -e KAGGLE_HARBOR_AGENT="mini-swe-agent" \
  -e LLM_DEFAULT="openai/google/gemini-3.5-flash" \
  -e KAGGLE_HARBOR_MODEL="openai/google/gemini-3.5-flash" \
  -e MODEL_PROXY_BASE_URL="${MODEL_PROXY_URL%/}/openapi/v1" \
  -e MODEL_PROXY_API_KEY="${MODEL_PROXY_API_KEY}" \
  us-west1-docker.pkg.dev/kaggle-playground-170215/kaggle-benchmarks/harbor-git-v1:latest
```

> **Note:**
>
> - The executor container automatically sets `ANTHROPIC_API_KEY` if it detects a Claude model, and sets `OPENAI_API_KEY` otherwise.
> - Additional environment variables can be passed into the container using extra `-e VAR_NAME="value"` flags.

Alternatively, run `./run_mini_swe_agent.sh` to execute the task using the pre-configured script.
