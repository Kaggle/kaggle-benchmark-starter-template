#!/usr/bin/env bash
set -euo pipefail

if [ -f /sys/fs/cgroup/cgroup.controllers ]; then
  mkdir -p /sys/fs/cgroup/init
  xargs -rn1 < /sys/fs/cgroup/cgroup.procs > /sys/fs/cgroup/init/cgroup.procs || true
  sed -e 's/ / +/g' -e 's/^/+/' < /sys/fs/cgroup/cgroup.controllers \
    > /sys/fs/cgroup/cgroup.subtree_control || true
fi

echo "Starting dockerd..."
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0
DOCKERD_STORAGE_DRIVER="${DOCKERD_STORAGE_DRIVER:-vfs}"
dockerd --storage-driver="$DOCKERD_STORAGE_DRIVER" > /var/log/dockerd.log 2>&1 &

for i in $(seq 1 90); do
  if docker info >/dev/null 2>&1; then
    echo "dockerd is ready after ${i}s"
    break
  fi
  sleep 1
done

if ! docker info >/dev/null 2>&1; then
  echo "dockerd failed to start" >&2
  tail -50 /var/log/dockerd.log >&2
  exit 1
fi

if [ -n "${KAGGLE_GIT_TOKEN:-}" ]; then
  cat > /usr/local/bin/git-askpass.sh <<'ASKPASS'
#!/bin/sh
case "$1" in
  Username*) echo "x-access-token" ;;
  Password*) echo "$KAGGLE_GIT_TOKEN" ;;
esac
ASKPASS
  chmod +x /usr/local/bin/git-askpass.sh
  export GIT_ASKPASS=/usr/local/bin/git-askpass.sh
  export GIT_TERMINAL_PROMPT=0
fi

if [ -z "${KAGGLE_TASK_REPO_URL:-}" ]; then
  echo "KAGGLE_TASK_REPO_URL is required" >&2
  exit 1
fi

echo "Cloning task repo: $KAGGLE_TASK_REPO_URL"
git clone "$KAGGLE_TASK_REPO_URL" /workspace/task-repo

if [ -n "${KAGGLE_TASK_REPO_REF:-}" ]; then
  echo "Checking out ref: $KAGGLE_TASK_REPO_REF"
  git -C /workspace/task-repo checkout "$KAGGLE_TASK_REPO_REF"
fi

task_path="/workspace/task-repo/${KAGGLE_TASK_PATH:-.}"
if [ ! -d "$task_path" ]; then
  echo "Task path does not exist: $task_path" >&2
  exit 1
fi

mkdir -p /kaggle/working
if [ -f "$task_path/task.toml" ]; then
  cp "$task_path/task.toml" /kaggle/working/task.toml
fi

agent="${KAGGLE_HARBOR_AGENT:-nop}"
cmd=(harbor run --yes -o /kaggle/working/jobs -p "$task_path" -e docker --agent "$agent")

if [ -n "${KAGGLE_HARBOR_MODEL:-}" ]; then
  cmd+=(--model "$KAGGLE_HARBOR_MODEL")
fi

echo "Running: ${cmd[*]}"
exec "${cmd[@]}"
