# Harbor Spec

[Harbor](https://github.com/harbor-framework/harbor) is a framework for
evaluating agents in sandboxed environments. A Kaggle benchmark can use a
Harbor-compatible spec so the same task can run locally while you iterate and
inside Kaggle when published.

## What Kaggle Runs

Think of each benchmark item as one task:

1. Kaggle prepares the task environment from the Dockerfile or public Docker
   image declared by the spec.
2. Kaggle runs the selected agent inside that environment.
3. The agent attempts the instruction and writes files/artifacts.
4. Kaggle runs the verifier.
5. Kaggle records the reward, logs, artifacts, and model calls.

For this starter, the task is `tasks/hello-world`: the environment is defined
under `tasks/hello-world/environment`, the instruction asks for `/app/hello.txt`,
and the verifier lives under `tasks/hello-world/tests`.

When documenting a benchmark, assume users can provide a Dockerfile in the task
spec or point at a public Docker image. Keep private image and registry
requirements out of the quick-start path unless the benchmark genuinely needs
them.

## Core Pieces

A useful Harbor task usually has:

- **Environment**: Dockerfile or public image that defines the sandbox.
- **Instruction**: what the agent must accomplish.
- **Verifier**: code that checks the final state and returns a reward.
- **Oracle or solution**: optional reference implementation for sanity checks.
- **Artifacts**: files copied out after the run.

Keep the first task deterministic. A good smoke test asks the agent to create
one exact file and verifies that file with shell or pytest checks.

## Local-First Workflow

Build and debug with local `harbor run` first. This uses the host Docker daemon
and gives fast iteration on Dockerfiles, task instructions, and verifier logic.

Run the packaged runner image only after local Harbor passes. That smoke test
adds repo cloning, ref checkout, and Docker-in-Docker, so failures there are a
different layer from task correctness.
