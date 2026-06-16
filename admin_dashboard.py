import streamlit as st
from dotenv import load_dotenv

from approvals_db import get_pending_rows, init_db, update_status
from agent_setup import build_agent, resume_with_decision

load_dotenv()
init_db()


@st.cache_resource
def get_agent():
    return build_agent()


def approve(thread_id: str) -> tuple[bool, str]:
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = resume_with_decision(agent, config, "approve")
        update_status(thread_id, "APPROVED")
        last = result["messages"][-1].content if result.get("messages") else ""
        return True, last or "Approved — email tool executed."
    except Exception as e:
        return False, str(e)


def reject(thread_id: str) -> tuple[bool, str]:
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = resume_with_decision(agent, config, "reject")
        update_status(thread_id, "REJECTED")
        last = result["messages"][-1].content if result.get("messages") else ""
        return True, last or "Rejected — email was not sent."
    except Exception as e:
        return False, str(e)


st.set_page_config(page_title="Admin — Pending Email Approvals", layout="wide")
st.title("Admin Dashboard — Pending Email Approvals")
st.caption("No login in this lab — assume only admins open this page.")

agent = get_agent()

pending = get_pending_rows()

if not pending:
    st.success("No pending approvals.")
else:
    st.subheader(f"{len(pending)} pending request(s)")

    for row in pending:
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(f"**To:** {row['recipient']}")
                st.markdown(f"**Subject:** {row['subject']}")
                st.markdown(f"**Body:** {row['body']}")
                st.caption(f"Thread: `{row['thread_id'][:8]}…` · User asked: {row['user_message']}")
            with cols[1]:
                if st.button("Approve", key=f"approve_{row['id']}", type="primary"):
                    ok, msg = approve(row["thread_id"])
                    if ok:
                        st.success("Approved")
                        st.info(msg)
                    else:
                        st.error(msg)
                    st.rerun()
            with cols[2]:
                if st.button("Reject", key=f"reject_{row['id']}"):
                    ok, msg = reject(row["thread_id"])
                    if ok:
                        st.warning("Rejected")
                        st.info(msg)
                    else:
                        st.error(msg)
                    st.rerun()

st.divider()
st.markdown("**Table view**")
st.dataframe(
    pending,
    use_container_width=True,
    hide_index=True,
)