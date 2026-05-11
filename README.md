# Security Remediation Agent

An autonomous AI agent that continuously monitors cloud infrastructure for security vulnerabilities and automatically remediates them using LangGraph and LLM-powered decision making.

## Overview

This agent uses a LangGraph workflow to:
1. Scan cloud instances for security vulnerabilities (e.g., Port 22 open to 0.0.0.0/0)
2. Automatically remediate vulnerable instances
3. Send notifications to Slack with audit results
4. Run continuously on a scheduled interval

## Features

- **Autonomous Operation**: Runs continuously with configurable audit intervals
- **LLM-Powered**: Uses local LM Studio for intelligent decision making
- **Tool-Based Architecture**: Modular tools for vulnerability scanning and remediation
- **Slack Integration**: Automatic notifications of audit results
- **Mock Mode**: Test the workflow without cloud provider credentials

## Prerequisites

- Python 3.8+
- LM Studio running locally on `http://localhost:1234/v1`
- LM Studio model that supports function/tool calling
- Slack webhook URL (for notifications)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd security-remediation-agent
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install langchain-openai langchain-core langgraph python-dotenv requests
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your SLACK_WEBHOOK_URL
```

## Configuration

### Environment Variables

Create a `.env` file with:
```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/here
```

### Audit Interval

Modify `AUDIT_INTERVAL_SECONDS` in `agent.py` (default: 300 seconds / 5 minutes):
```python
AUDIT_INTERVAL_SECONDS = 300  # Run audit every 5 minutes
```

### LM Studio Setup

1. Install and run [LM Studio](https://lmstudio.ai/)
2. Load a model that supports function calling (e.g., models with "function" or "tools" in their name)
3. Start the local server on `http://localhost:1234/v1`

## Usage

### Running the Agent

```bash
python agent.py
```

The agent will:
- Start scheduled audits every 5 minutes (configurable)
- Log execution flow with function names for easy debugging
- Continue running until manually stopped (Ctrl+C)

### Log Output

Logs show clear execution flow with function names:
```
2026-05-11 09:34:15,123 - INFO - [list_vulnerable_instances] Starting security audit.
2026-05-11 09:34:15,456 - INFO - [agent] → AGENT: Requesting tools: list_vulnerable_instances
2026-05-11 09:34:15,457 - INFO - [route] → ROUTE: Executing 1 tool(s)
```

## Architecture

### Workflow

```
START → Agent → Route Decision
         ↑         ↓
         └─ Tools ←┘
              ↓
           Notify → END
```

### Components

- **Agent**: LLM-powered decision maker that determines which tools to use
- **Tools**: 
  - `list_vulnerable_instances`: Scans for security vulnerabilities
  - `stop_ibm_instance`: Remediates vulnerable instances
- **Router**: Decides whether to execute tools or send notifications
- **Notifier**: Sends audit results to Slack

## Customization

### Adding Cloud Provider Support

The agent currently uses mock data. To add actual cloud provider integration:

1. Uncomment the example implementation in `list_vulnerable_instances` (lines 28-62)
2. Install cloud provider SDK (e.g., `pip install ibm-vpc ibm-cloud-sdk-core`)
3. Add required environment variables to `.env`
4. Modify the tool logic for your specific cloud provider

Example for IBM VPC is provided in comments.

### Adding New Tools

1. Define a new tool using the `@tool` decorator:
```python
@tool
def your_new_tool(param: str):
    """Tool description for the LLM."""
    # Your implementation
    return result
```

2. Add the tool to the tools list:
```python
tools = [list_vulnerable_instances, stop_ibm_instance, your_new_tool]
```

3. Update the system prompt in the `agent` function to instruct the LLM to use the new tool

## Troubleshooting

### Tools Not Being Called

- Ensure your LM Studio model supports function calling
- Check that LM Studio is running on `http://localhost:1234/v1`
- Review logs for "NO TOOL CALLS GENERATED" warning

### Infinite Loop

- The agent may repeatedly call the same tool if it doesn't understand empty results
- The scheduler ensures time gaps between audits to prevent system overload
- Each audit has a maximum of 10 iterations before moving to the next audit

### Slack Notifications Not Working

- Verify `SLACK_WEBHOOK_URL` is correctly set in `.env`
- Test the webhook URL manually with curl
- Check logs for notification errors

## Development

### Project Structure

```
security-remediation-agent/
├── agent.py           # Main agent implementation
├── .env              # Environment variables (not in git)
├── .env.example      # Example environment file
├── AGENTS.md         # AI assistant guidance
├── README.md         # This file
└── .venv/            # Virtual environment
```
