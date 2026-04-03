"""
Core agent: tool-aware reasoning loop for buy/wait style guidance.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from agent.tools import get_default_tools


def _prompts_dir() -> Path:
    return Path(__file__).resolve().parent / "prompts"


def load_system_prompt() -> str:
    path = _prompts_dir() / "system.md"
    return path.read_text(encoding="utf-8")


def _build_chat_model() -> BaseChatModel:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")

    if provider == "gemini" and google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = os.getenv("LLM_MODEL_GEMINI", "gemini-1.5-pro")
        return ChatGoogleGenerativeAI(model=model, temperature=0)

    if openai_key:
        from langchain_openai import ChatOpenAI

        model = os.getenv("LLM_MODEL_OPENAI", "gpt-4o")
        return ChatOpenAI(model=model, temperature=0)

    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = os.getenv("LLM_MODEL_GEMINI", "gemini-1.5-pro")
        return ChatGoogleGenerativeAI(model=model, temperature=0)

    raise ValueError(
        "Configure OPENAI_API_KEY and/or GOOGLE_API_KEY (and LLM_PROVIDER if using Gemini)."
    )


class DecisionAgent:
    """
    Runs a bounded tool-calling loop: the model decides whether to invoke
    egg_price_lookup or oil_price_indicator, then produces a final answer.
    """

    def __init__(self, max_iterations: int = 8) -> None:
        self.max_iterations = max_iterations
        self._tools = get_default_tools()
        self._tool_map = {t.name: t for t in self._tools}
        self._llm = _build_chat_model().bind_tools(self._tools)
        self._system = load_system_prompt()

    def run(self, user_text: str) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        messages: list[BaseMessage] = [
            SystemMessage(content=self._system),
            HumanMessage(content=user_text),
        ]

        for i in range(self.max_iterations):
            trace.append({"step": "model", "iteration": i, "note": "Invoking LLM with current context"})
            ai: AIMessage = self._llm.invoke(messages)
            messages.append(ai)

            if getattr(ai, "content", None):
                trace.append(
                    {
                        "step": "assistant_text",
                        "iteration": i,
                        "content": ai.content,
                    }
                )

            tool_calls = getattr(ai, "tool_calls", None) or []
            if not tool_calls:
                trace.append({"step": "done", "iteration": i, "note": "No tool calls; final reply"})
                return {"reply": ai.content or "", "trace": trace, "messages": messages}

            for call in tool_calls:
                name = call.get("name", "")
                args = call.get("args", {}) or {}
                tid = call.get("id") or name
                trace.append(
                    {
                        "step": "tool_call",
                        "iteration": i,
                        "name": name,
                        "args": args,
                    }
                )
                tool = self._tool_map.get(name)
                if not tool:
                    out = f"Unknown tool: {name}"
                else:
                    out = tool.invoke(args)
                trace.append(
                    {
                        "step": "tool_result",
                        "iteration": i,
                        "name": name,
                        "result": str(out)[:4000],
                    }
                )
                messages.append(ToolMessage(content=str(out), tool_call_id=str(tid)))

        trace.append({"step": "halt", "note": "max_iterations reached"})
        return {
            "reply": "Stopped after maximum reasoning steps; refine your question or raise max_iterations.",
            "trace": trace,
            "messages": messages,
        }


def main() -> None:
    load_dotenv()
    agent = DecisionAgent()
    q = input("Your situation (inventory / usage / question): ").strip()
    out = agent.run(q)
    print(out["reply"])
    for row in out["trace"]:
        print(row)


if __name__ == "__main__":
    main()
