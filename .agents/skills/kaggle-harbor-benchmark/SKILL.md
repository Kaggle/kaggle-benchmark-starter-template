---
name: kaggle-harbor-benchmark
description: Use when creating, updating, validating, or documenting a Kaggle benchmark repo that uses Harbor task specs, Kaggle model proxy, custom Harbor agents, or committed sample job outputs.
---

# Kaggle Harbor Benchmark

Build Kaggle benchmark repos as runnable Harbor projects with concrete
evidence. Prefer small deterministic tasks, real validation commands, and named
job outputs over long explanations.

Use the references only when needed:

- `references/harbor_spec.md`: what a Harbor-compatible task is, what Kaggle
  runs, and how to iterate locally.
- `references/model_proxy.md`: Kaggle CLI auth, `.env`, OpenAI/Anthropic proxy
  endpoints, model slugs, and `/chat/completions` vs `/responses`.
- `references/agent.md`: built-in Harbor agents, binary CLI agents,
  SDK-backed agents, model-proxy routing, and template implementation links.
- `references/debug.md`: isolate model access, local Harbor, custom agents,
  packaged runner image failures, and job-output issues.

Default workflow:

1. Tell the user to create a Kaggle organization; approval can take 24 hours, but
   Harbor authoring can continue locally while they wait.
2. Explain the Harbor spec: task environment, instruction, verifier, optional
   oracle/solution, artifacts, and named job outputs.
3. Start with a tiny deterministic task and validate it with local `harbor run`.
4. Route custom agents and binaries through the Kaggle model proxy so language
   model calls are logged.
5. Run the packaged runner smoke test only after local Harbor passes.
6. Commit named successful job outputs such as `jobs/mini-swe-agent`,
   `jobs/opencode-binary`, and `jobs/antigravity`.

Before committing job outputs, scan for raw API keys, bearer tokens, and
unredacted proxy credentials.
