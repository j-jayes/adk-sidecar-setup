"""
Lease Reviewer – Streamlit Frontend
====================================
A clean chat interface that lets users:
  1. Upload a PDF lease agreement.
  2. Chat with an AI agent that reviews the document and reports missing items.

The app communicates with the FastAPI gateway (api service), which in turn
routes requests to the Google ADK agent backend.
"""

import json
import os
import re
import uuid
from pathlib import Path

import httpx
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_URL = os.getenv("API_URL", "http://api:8001")

# ---------------------------------------------------------------------------
# Page config & custom styles
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lease Reviewer",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded",
)

_css_path = Path(__file__).parent / "assets" / "custom.css"
if _css_path.exists():
    with _css_path.open() as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 Welcome to **Lease Reviewer**!\n\n"
                "I can help you check whether your residential lease agreement "
                "contains all the important clauses and details.\n\n"
                "**To get started**, upload your lease PDF using the panel on the "
                "left, or just type a question below."
            ),
        }
    ]

if "uploaded_file_path" not in st.session_state:
    st.session_state.uploaded_file_path = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _send_chat(message: str) -> str:
    """Post a message to the API gateway and return the agent reply."""
    with httpx.Client(timeout=180) as client:
        resp = client.post(
            f"{API_URL}/chat",
            json={
                "session_id": st.session_state.session_id,
                "message": message,
            },
        )
        resp.raise_for_status()
    return resp.json()["reply"]


def _upload_pdf(file_bytes: bytes, filename: str) -> str:
    """Upload a PDF to the API gateway and return the server-side file path."""
    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{API_URL}/upload",
            files={"file": (filename, file_bytes, "application/pdf")},
        )
        resp.raise_for_status()
    return resp.json()["file_path"]


_JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _render_assistant_message(content: str) -> None:
    """Render an assistant message, pulling any fenced JSON block into a
    collapsed expander so the prose and structured data are displayed
    separately."""
    match = _JSON_BLOCK_RE.search(content)
    if match:
        prose = (content[: match.start()] + content[match.end() :]).strip()
        st.markdown(prose)
        with st.expander("📋 Structured lease data", expanded=False):
            try:
                st.json(json.loads(match.group(1)))
            except json.JSONDecodeError:
                st.code(match.group(1), language="json")
    else:
        st.markdown(content)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📄 Lease Reviewer")
    st.caption("Powered by Google ADK · Gemini 2.5 Flash · Docling")

    st.divider()

    st.subheader("Upload your lease")
    uploaded = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Your file is processed locally inside Docker and never sent to third parties.",
        key="pdf_uploader",
    )

    if uploaded is not None and uploaded.name not in (
        st.session_state.get("_last_uploaded"),
    ):
        with st.spinner("Uploading and queuing for conversion…"):
            try:
                file_path = _upload_pdf(uploaded.read(), uploaded.name)
                st.session_state.uploaded_file_path = file_path
                st.session_state["_last_uploaded"] = uploaded.name
                st.success(f"✅ Uploaded: **{uploaded.name}**")

                # Automatically send a chat message to trigger the review
                trigger_msg = (
                    f"I have uploaded my lease agreement. "
                    f"The file is at `{file_path}`. "
                    f"Please review it for me."
                )
                st.session_state.messages.append(
                    {"role": "user", "content": f"I've uploaded **{uploaded.name}** for review."}
                )
                with st.spinner("Agent is reviewing your lease…"):
                    reply = _send_chat(trigger_msg)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
            except httpx.HTTPStatusError as exc:
                st.error(f"Upload failed: {exc.response.text}")
            except httpx.RequestError as exc:
                st.error(f"Cannot reach the API service: {exc}")

    st.divider()

    st.subheader("Session")
    st.code(st.session_state.session_id[:8] + "…", language=None)
    if st.button("🔄 New session"):
        for key in ["session_id", "messages", "uploaded_file_path", "_last_uploaded"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    st.caption(
        "This tool provides general information only and does **not** constitute "
        "legal advice. Always consult a qualified solicitor for legal matters."
    )

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
st.title("Lease Reviewer 📄")
st.caption(
    "Ask questions about your lease or upload a PDF for an automated review."
)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            _render_assistant_message(msg["content"])
        else:
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your lease…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                reply = _send_chat(prompt)
            except httpx.HTTPStatusError as exc:
                reply = f"⚠️ Error from API: {exc.response.text}"
            except httpx.RequestError as exc:
                reply = f"⚠️ Cannot reach the API service: {exc}"

        _render_assistant_message(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
