import sqlite3

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, PIIMiddleware
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

load_dotenv()

CHECKPOINT_DB = "checkpoints.sqlite"


@tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """Send an email to a recipient. Use when the user asks to email someone."""
    print("=" * 60)
    print("DUMMY EMAIL — not actually sent")
    print(f"To:      {recipient}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("=" * 60)
    return f"Email has been sent to {recipient} with subject '{subject}'."


def build_agent():
    conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
    checkpointer = SqliteSaver(conn=conn)
    checkpointer.setup()

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    tavily_tool = TavilySearch(
        max_results=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
        include_images=False,
    )

    return create_agent(
        model=model,
        tools=[tavily_tool, send_email],
        system_prompt=(
            "You are a helpful assistant with web search and a send_email tool. "
            "Use web search for current events. "
            "When the user asks to send an email, call send_email with recipient, subject, and body. "
            "Do not claim an email was sent until the send_email tool returns success."
        ),
        middleware=[
            PIIMiddleware(
                "credit_card",
                strategy="block",
                apply_to_input=True,
            ),
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "send_email": True,
                }
            ),
        ],
        checkpointer=checkpointer,
    )


def get_pending_email_tool_call(agent, config):
    """Return the send_email tool call dict if the agent is paused for HITL, else None."""
    snapshot = agent.get_state(config)
    if not snapshot.next:
        return None

    messages = snapshot.values.get("messages", [])
    if not messages:
        return None

    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None) or []
    for tc in tool_calls:
        if tc.get("name") == "send_email":
            return tc
    return None


def resume_with_decision(agent, config, decision: str):
    """Resume an interrupted thread. decision is 'approve' or 'reject'."""
    return agent.invoke(
        Command(resume={"decisions": [{"type": decision}]}),
        config,
    )