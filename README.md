# Kaggle Benchmark Starter Template

This repository shows how to publish a dataset and benchmark on Kaggle using a
[Harbor](https://github.com/harbor-framework/harbor)-compatible spec. The starter task,
`tasks/hello-world`, asks an agent to create `/app/hello.txt` containing exactly
`Hello, world!`.

Use this repo to see the full loop: define a task, run it locally with Harbor,
connect it to the Kaggle model proxy, and commit named job outputs as evidence.

## Reference Implementations

| Pattern | Implementation | Successful run |
| --- | --- | --- |
| Built-in Harbor agent | `harbor run -a mini-swe-agent` | `jobs/mini-swe-agent` |
| Binary CLI agent | `agents/opencode_binary_agent.py` | `jobs/opencode-binary` |
| SDK-backed custom agent | `agents/antigravity_agent.py` and `agents/antigravity_runner.py` | `jobs/antigravity` |

The custom examples borrow Harbor's agent interfaces, but the pattern is
general: implement an adapter, run the task with Harbor, and commit the
resulting job output as a concrete reference.

## Quick Start

Install the Kaggle CLI with uv and create model proxy credentials:

```bash
uv tool install kaggle
kaggle auth login
kaggle benchmarks auth -y --env-file .env
```

Run the starter task locally:

```bash
harbor run \
  -p tasks/hello-world \
  -a mini-swe-agent \
  -m openai/gemini-3.5-flash
```

Run the OpenCode binary-agent example:

```bash
harbor run \
  -p tasks/hello-world \
  --agent-import-path agents.opencode_binary_agent:OpenCodeBinaryAgent \
  -m google/gemini-3.5-flash \
  --ae GEMINI_API_KEY="${GEMINI_API_KEY}"
```

## Reusable Skill

Install the agent skill with the Vercel [skills CLI](https://github.com/vercel-labs/skills) to get started building with Kaggle.

```bash
npx skills add https://github.com/ivanleomk/kaggle-benchmark-starter-template/tree/main/.agents/skills/kaggle-harbor-benchmark
```

The skill keeps `SKILL.md` brief and stores details in references:

- `references/harbor_spec.md`: what Kaggle runs, the Harbor task pieces, and
  the local-first workflow.
- `references/model_proxy.md`: Kaggle auth, proxy endpoints, model slugs, and
  `/chat/completions` vs `/responses`.
- `references/agent.md`: mini-swe, binary CLI, SDK-backed custom
  agents, ATIF, and links to sample implementations in this repo.
- `references/debug.md`: local Harbor runs, runner image smoke tests,
  Docker-in-Docker notes, model proxy debugging, and named job evidence.
