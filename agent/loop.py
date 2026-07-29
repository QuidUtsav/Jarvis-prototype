import os
import json
from dotenv import load_dotenv
from groq import Groq

from agent.tools import AVAILABLE_TOOLS, TOOLS_SCHEMA

load_dotenv()
_client = Groq(api_key=os.getenv("api_key"))
MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an assistant with access to external tools. On each turn, decide ONE of two things:
1. Call a tool to gather more information, OR
2. Give a final answer to the user, if you already have enough information.

Available tools (JSON schema):
{TOOL_SCHEMA}

Respond in EXACTLY this format, nothing else:

thought: <your reasoning for this step>
action: <"call_tool" or "final_answer">
action_input: <if action is call_tool: {{"tool_name": "<name>", "tool_args": {{...}}}}. if action is final_answer: {{"response": "<your answer to the user>"}}>

Rules:
- Only ever pick ONE action per turn.
- Only call a tool if you genuinely need it to answer. If you already have what you need (e.g. from a previous tool result), use final_answer.
- action_input must be valid JSON on a single line. No extra text before or after the three fields.
""".format(TOOL_SCHEMA=json.dumps(TOOLS_SCHEMA))


def parse_agent_response(response):
    content = response.choices[0].message.content
    lines = content.split("\n")

    action = None
    action_input_raw = None

    for line in lines:
        line = line.strip()
        if line.startswith("action:"):
            action = line.split(":", 1)[1].strip()
        elif line.startswith("action_input:"):
            action_input_raw = line.split(":", 1)[1].strip()

    if action is None or action_input_raw is None:
        raise ValueError(f"Could not find action/action_input in response: {content}")

    action_input = json.loads(action_input_raw)

    if action == "call_tool":
        return "call_tool", action_input["tool_name"], action_input["tool_args"]
    elif action == "final_answer":
        return "final_answer", action_input["response"], None
    else:
        raise ValueError(f"Unknown action: {action}")


def run_agent_loop(query, history=None, max_turns=8):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    turn = 0
    while turn < max_turns:
        try:
            response = _client.chat.completions.create(model=MODEL_NAME, messages=messages)
            status, value, args = parse_agent_response(response)
        except Exception as e:
            return f"I hit an error trying to process that step: {e}"

        if status == "final_answer":
            return value

        tool_name = value
        tool_args = args

        if tool_name not in AVAILABLE_TOOLS:
            result = json.dumps({"error": f"Unknown tool: {tool_name}"})
        else:
            try:
                result = AVAILABLE_TOOLS[tool_name](**tool_args)
            except Exception as e:
                result = json.dumps({"error": str(e)})

        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        messages.append({"role": "user", "content": f"Tool result: {result}"})
        turn += 1

    return "I wasn't able to complete this within the allowed steps."