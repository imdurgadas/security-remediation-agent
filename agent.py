import os, requests
import logging
import time
from typing import Annotated, Sequence, TypedDict, Literal
from dotenv import load_dotenv

# Configure logging to show INFO level messages with function names
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s'
)

# Configuration for audit scheduling
AUDIT_INTERVAL_SECONDS = 300  # Run audit every 5 minutes (300 seconds)

# LangGraph Imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv()

# --- 1. THE TOOLS (Security Operations) ---
@tool
def list_vulnerable_instances():
    """Returns instances with security vulnerabilities."""
    logging.info("Starting security audit.")
    
    # Mock data for testing
    logging.info("Returning Mock data from list_vulnerable_instances .....")
    mock_instances = [
        {"id": "mock-instance-001", "name": "test-vulnerable-instance-1"},
        {"id": "mock-instance-002", "name": "test-vulnerable-instance-2"}
    ]
    return mock_instances
    # TODO: Replace with actual implementation

    

@tool
def stop_instance(instance_id: str):
    """Issues a STOP command to remediate a vulnerable instance."""
    # Mock implementation
    return f"REMEDIATED: Instance {instance_id} stopped."
    
    # TODO: Replace with actual implementation

tools = [list_vulnerable_instances, stop_instance]

# --- 3. THE NOTIFICATION SYSTEM ---
def slack_notifier(state: dict):
    """Sends the agent's final report to Slack."""
    report = state["messages"][-1].content
    payload = {"text": f"🚨 *AI Security Audit Complete*\n\n*Actions:* {report}"}
    requests.post(os.getenv("SLACK_WEBHOOK_URL"), json=payload)
    return state

# --- 4. THE AGENTIC BRAIN ---
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Connecting to local LM Studio
llm = ChatOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio", temperature=0, model="google/gemma-4-e4b")
llm_with_tools = llm.bind_tools(tools)

def agent(state: State):
    sys_msg = SystemMessage(content="""You are an autonomous security auditor. Your task:
1. Use the list_vulnerable_instances tool to find instances with Port 22 open to 0.0.0.0/0
2. For each vulnerable instance found, use the stop_instance tool to remediate it
3. After all remediations, provide a summary of actions taken

You MUST use the available tools to complete this task.""")
    
    message_to_invoke = [sys_msg] + list(state["messages"])
    response = llm_with_tools.invoke(message_to_invoke)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_names = [tc.get('name', 'unknown') for tc in response.tool_calls]
        logging.info(f"→ AGENT: Requesting tools: {', '.join(tool_names)}")
    else:
        logging.info("→ AGENT: No tools requested, generating final response")
    
    return {"messages": [response]}

def route(state: State):
    last_message = state["messages"][-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logging.info(f"→ ROUTE: Executing {len(last_message.tool_calls)} tool(s)")
        return "tools"
    else:
        logging.info("→ ROUTE: Sending notification and ending workflow")
        return "notify"

# --- 5. THE WORKFLOW GRAPH ---
workflow = StateGraph(State)
workflow.add_node("agent", agent)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("notify", slack_notifier)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", route)
workflow.add_edge("tools", "agent")
workflow.add_edge("notify", END)

# COMPILE & RUN
app = workflow.compile()

def run_scheduled_audit():
    """Run security audits on a schedule with time gaps between runs."""
    logging.info(f"Starting scheduled security audits (interval: {AUDIT_INTERVAL_SECONDS} seconds)")
    
    audit_count = 0
    while True:
        audit_count += 1
        logging.info(f"=== Starting Audit #{audit_count} ===")
        
        try:
            app.invoke({"messages": [HumanMessage(content="Start the audit.")]})
            logging.info(f"=== Audit #{audit_count} Complete ===")
        except Exception as e:
            logging.error(f"Audit #{audit_count} failed: {e}")
        
        logging.info(f"Waiting {AUDIT_INTERVAL_SECONDS} seconds before next audit...")
        time.sleep(AUDIT_INTERVAL_SECONDS)

# Start the scheduled audit loop
run_scheduled_audit()