# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "cryptography<47",
#   "fastapi",
#   "google-antigravity==0.1.1",
# ]
# ///
"""Container-side uv script for the custom Antigravity Harbor agent."""

import argparse
import asyncio
import json
import logging
import os
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any


async def run_agent(args: argparse.Namespace) -> None:
    from google.antigravity import Agent, LocalAgentConfig
    from google.antigravity.hooks import policy
    from google.antigravity.types import (
        GeminiConfig,
        GenerationConfig,
        McpSseServer,
        McpStdioServer,
        McpStreamableHttpServer,
        ModelConfig,
        ModelEntry,
        StepSource,
        StepStatus,
        ThinkingLevel,
    )

    logging.getLogger().setLevel(logging.ERROR)

    model = os.environ.get("MODEL_NAME")
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    if not model:
        print("Error: MODEL_NAME environment variable not set", file=sys.stderr)
        sys.exit(1)

    normalized_model = model.split("/")[-1]

    mcp_servers_list = []
    mcp_servers_raw = os.environ.get("MCP_SERVERS_JSON")
    if mcp_servers_raw:
        mcp_data = json.loads(mcp_servers_raw)
        for mcp in mcp_data:
            transport = mcp.get("transport", "stdio")
            name = mcp.get("name")
            if transport == "stdio":
                mcp_servers_list.append(
                    McpStdioServer(
                        name=name,
                        command=mcp.get("command"),
                        args=mcp.get("args", []),
                    )
                )
            elif transport == "sse":
                mcp_servers_list.append(
                    McpSseServer(
                        name=name,
                        url=mcp.get("url"),
                    )
                )
            elif transport == "streamable-http":
                mcp_servers_list.append(
                    McpStreamableHttpServer(
                        name=name,
                        url=mcp.get("url"),
                    )
                )

    reasoning_effort_str = os.environ.get("REASONING_EFFORT", "medium").lower()
    thinking_level_map = {
        "minimal": ThinkingLevel.MINIMAL,
        "low": ThinkingLevel.LOW,
        "medium": ThinkingLevel.MEDIUM,
        "high": ThinkingLevel.HIGH,
    }
    thinking_level = thinking_level_map.get(reasoning_effort_str)

    default_model_entry = ModelEntry(
        name=normalized_model,
        generation=GenerationConfig(thinking_level=thinking_level),
    )
    gemini_config = GeminiConfig(
        api_key=api_key,
        models=ModelConfig(default=default_model_entry),
    )

    skills_paths_list = None
    skills_paths_raw = os.environ.get("SKILLS_PATHS_JSON")
    if skills_paths_raw:
        try:
            skills_paths_list = json.loads(skills_paths_raw)
        except Exception:
            pass

    config = LocalAgentConfig(
        gemini_config=gemini_config,
        mcp_servers=mcp_servers_list,
        policies=[policy.allow_all()],
        skills_paths=skills_paths_list,
    )

    steps = [
        {
            "step_id": 1,
            "timestamp": None,
            "source": "user",
            "message": args.instruction,
        }
    ]
    step_id = 2

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cached_tokens = 0

    print(f"Starting Antigravity SDK Agent with instruction: {args.instruction[:200]}...")
    print(f"Using model: {normalized_model}")
    if mcp_servers_list:
        print(f"MCP servers: {[server.name for server in mcp_servers_list]}")

    async with Agent(config) as agent:
        await agent.conversation.send(args.instruction)

        async for step in agent.conversation.receive_steps():
            if step.status != StepStatus.DONE:
                continue
            if step.source == StepSource.USER:
                continue

            usage = getattr(step, "usage_metadata", None)
            if usage is not None:
                total_prompt_tokens += usage.prompt_token_count or 0
                total_completion_tokens += usage.candidates_token_count or 0
                total_cached_tokens += usage.cached_content_token_count or 0

            step_dict = {
                "step_id": step_id,
                "timestamp": None,
                "source": "agent" if step.source == StepSource.MODEL else "system",
                "message": step.content or "",
                "model_name": normalized_model,
            }

            if step.source == StepSource.MODEL and usage is not None:
                step_dict["metrics"] = {
                    "prompt_tokens": usage.prompt_token_count,
                    "completion_tokens": usage.candidates_token_count,
                    "cached_tokens": usage.cached_content_token_count,
                }

            if step.thinking:
                step_dict["reasoning_content"] = step.thinking

            if step.tool_calls:
                tool_calls_list = []
                observation_results = []
                for tool_call in step.tool_calls:
                    tool_calls_list.append(
                        {
                            "tool_call_id": tool_call.id,
                            "function_name": tool_call.name,
                            "arguments": tool_call.args or {},
                        }
                    )
                    tool_output = getattr(tool_call, "output", None)
                    if tool_output is not None:
                        observation_results.append(
                            {
                                "source_call_id": tool_call.id,
                                "content": tool_output,
                            }
                        )
                step_dict["tool_calls"] = tool_calls_list
                if observation_results:
                    step_dict["observation"] = {"results": observation_results}

            steps.append(step_dict)
            step_id += 1

    trajectory = build_atif_trajectory(
        steps=steps,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        total_cached_tokens=total_cached_tokens,
    )

    trajectory_path = Path(args.trajectory_path)
    trajectory_path.parent.mkdir(parents=True, exist_ok=True)
    trajectory_path.write_text(json.dumps(trajectory, indent=2))

    print(f"Agent completed. Trajectory saved to {trajectory_path}")


def build_atif_trajectory(
    steps: list[dict[str, Any]],
    total_prompt_tokens: int,
    total_completion_tokens: int,
    total_cached_tokens: int,
    agent_version: str = "0.1.1",
) -> dict[str, Any]:
    for i, step in enumerate(steps):
        step["step_id"] = i + 1

    return {
        "schema_version": "ATIF-v1.7",
        "session_id": os.environ.get("SESSION_ID", "harbor-session"),
        "agent": {
            "name": "custom-antigravity",
            "version": agent_version,
        },
        "steps": steps,
        "final_metrics": {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_cached_tokens": total_cached_tokens,
            "total_cost_usd": 0.0,
        },
    }


def main() -> None:
    if "--version" in sys.argv:
        print(version("google-antigravity"))
        return

    parser = argparse.ArgumentParser(description="Run Google Antigravity SDK agent")
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--logs-dir", required=True)
    parser.add_argument("--trajectory-path", required=True)
    args = parser.parse_args()

    asyncio.run(run_agent(args))


if __name__ == "__main__":
    main()
