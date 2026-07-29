from agent.loop import run_agent_loop

def handle_tool(query, history=None):
    return run_agent_loop(query, history=history)