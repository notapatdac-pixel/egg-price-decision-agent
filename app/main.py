"""
Streamlit UI: chat + reasoning trace sidebar.
Run from repository root: streamlit run app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from agent.main import DecisionAgent


def _init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_trace" not in st.session_state:
        st.session_state.last_trace = []


def main() -> None:
    st.set_page_config(page_title="Egg Price Decision Agent", layout="wide")
    _init_session()

    st.title("Egg Price Decision Agent")
    st.caption("SME-focused guidance using egg history and oil/energy context.")

    with st.sidebar:
        st.header("Reasoning trace")
        if st.session_state.last_trace:
            for row in st.session_state.last_trace:
                with st.expander(str(row.get("step", "step")), expanded=False):
                    st.json(row)
        else:
            st.info("Send a message to see model steps, tool calls, and tool results.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Describe inventory, weekly egg usage, and what you want to decide."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                agent = DecisionAgent()
                result = agent.run(prompt)
                st.session_state.last_trace = result.get("trace", [])
                reply = result.get("reply", "")
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                err = f"**Error:** {e}"
                st.error(err)
                st.session_state.last_trace = [{"step": "error", "detail": str(e)}]
                st.session_state.messages.append({"role": "assistant", "content": err})


if __name__ == "__main__":
    main()
