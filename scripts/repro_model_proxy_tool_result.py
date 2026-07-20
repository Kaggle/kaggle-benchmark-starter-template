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

#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["openai", "python-dotenv"]
# ///
"""Minimal OpenAI client repro for model-proxy Chat Completions tool results."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI


MODEL = "google/gemini-3.5-flash"


load_dotenv()


client = OpenAI(
    api_key=os.environ["MODEL_PROXY_API_KEY"],
    base_url=f"{os.environ['MODEL_PROXY_URL'].rstrip('/')}/openapi",
)

tool = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write text content to a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
}

# 1. Ask the model to call write_file.
user_message = {
    "role": "user",
    "content": (
        "Call the write_file tool with path /tmp/hello.txt and content exactly: "
        "Hello, world!"
    ),
}

first_response = client.chat.completions.create(
    model=MODEL,
    messages=[user_message],
    tools=[tool],
    tool_choice={"type": "function", "function": {"name": "write_file"}},
)

assistant_message = first_response.choices[0].message
tool_call = assistant_message.tool_calls[0]
function_id = tool_call.id

print("call 1 tool call:")
print(json.dumps(tool_call.model_dump(), indent=2))

# 2. Send the tool result back using the function id. This currently throws.
print("\ncall 2 tool result:")
try:
    second_response = client.chat.completions.create(
        model=MODEL,
        tools=[tool],
        messages=[
            user_message,
            {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": function_id,
                "content": "Wrote file successfully.",
            },
        ],
    )
    print(json.dumps(second_response.model_dump(), indent=2))
except Exception as exc:
    print(type(exc).__name__)
    print(exc)
    raise
