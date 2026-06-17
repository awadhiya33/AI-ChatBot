import json
import os
import sqlite3
import uuid

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite import SqliteSaver
import streamlit as st
from approvals_db import init_db, save_pending
from agent_setup import build_agent, get_pending_email_tool_call

init_db()

@st.cache_resource
def get_agent():
    return build_agent()

load_dotenv()

CHECKPOINT_DB = "checkpoints.sqlite"
THREADS_FILE = "chat_threads.json"


# @st.cache_resource
# def get_agent():
#     conn = sqlite3.connect(CHECKPOINT_DB, check_same_thread=False)
#     checkpointer = SqliteSaver(conn=conn)
#     checkpointer.setup()

#     model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

#     tavily_tool = TavilySearch(
#         max_results=3,
#         search_depth="advanced",
#         include_answer=True,
#         include_raw_content=False,
#         include_images=False,
#     )

#     return create_agent(
#         model=model,
#         tools=[tavily_tool],
#         system_prompt=(
#             "You are a helpful assistant with access to web search. "
#             "Use web search when the user asks about current events, recent news, "
#             "live data, or anything that needs up-to-date information from the internet. "
#             "For personal facts the user told you earlier in the same chat, use memory — do not search the web."
#         ),
#         checkpointer=checkpointer,
#     )


def load_threads():
    if os.path.exists(THREADS_FILE):
        with open(THREADS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_threads(threads):
    with open(THREADS_FILE, "w", encoding="utf-8") as f:
        json.dump(threads, f)


def add_thread(thread_id):
    threads = load_threads()
    if any(t["id"] == thread_id for t in threads):
        return
    threads.insert(0, {"id": thread_id, "label": f"Chat {thread_id[:8]}"})
    save_threads(threads)


# --- Page setup ---
st.set_page_config(page_title="Memory Chatbot", layout="wide")
st.title("Chatbot with Memory")

agent = get_agent()

# --- Pick active thread ---
if "thread_id" not in st.session_state:
    threads = load_threads()
    if threads:
        st.session_state.thread_id = threads[0]["id"]
    else:
        st.session_state.thread_id = str(uuid.uuid4())
        add_thread(st.session_state.thread_id)

# --- Sidebar: new chat + thread picker ---
with st.sidebar:
    st.header("Chats")

    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        add_thread(new_id)
        st.session_state.thread_id = new_id
        st.rerun()

    threads = load_threads()
    if threads:
        labels = [t["label"] for t in threads]
        ids = [t["id"] for t in threads]
        current_index = ids.index(st.session_state.thread_id)
        picked_label = st.selectbox("Previous chats", labels, index=current_index)
        picked_id = ids[labels.index(picked_label)]
        if picked_id != st.session_state.thread_id:
            st.session_state.thread_id = picked_id
            st.rerun()

    st.caption(f"Active thread:\n`{st.session_state.thread_id}`")

# --- Main chat area (right side) ---
config = {"configurable": {"thread_id": st.session_state.thread_id}}

if st.session_state.get("pending_notice"):
    st.warning(st.session_state.pending_notice)

# Also show banner if thread is still interrupted (e.g. after page refresh)
pending_now = get_pending_email_tool_call(agent, config)
if pending_now and not st.session_state.get("pending_notice"):
    st.warning(
        "Your email request is **pending admin approval**. "
        "An administrator must approve or reject it before the email can be sent."
    )
    
config = {"configurable": {"thread_id": st.session_state.thread_id}}
snapshot = agent.get_state(config)

for msg in snapshot.values.get("messages", []):
    if msg.type == "human":
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif msg.type == "ai" and msg.content:
        with st.chat_message("assistant"):
            st.markdown(msg.content)

# if prompt := st.chat_input("Say something..."):
#     agent.invoke(
#         {"messages": [{"role": "user", "content": prompt}]},
#         config,
#     )
#     st.rerun()


if prompt := st.chat_input("Say something..."):
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    try:
        agent.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config,
        )
    except Exception as e:
        err = str(e).lower()
        if "credit" in err or "pii" in err or "blocked" in err:
            st.error(
                "Your message was blocked because it appears to contain a credit card number. "
                "Please remove sensitive payment data and try again."
            )
        else:
            st.error(f"Something went wrong: {e}")
        st.stop()

    pending = get_pending_email_tool_call(agent, config)
    if pending:
        args = pending.get("args", {})
        save_pending(
            thread_id=st.session_state.thread_id,
            recipient=args.get("recipient", ""),
            subject=args.get("subject", ""),
            body=args.get("body", ""),
            user_message=prompt,
        )
        st.session_state.pending_notice = (
            "Your email request is **pending admin approval**. "
            "An administrator must approve or reject it before the email can be sent."
        )

    st.rerun()