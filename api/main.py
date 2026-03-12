"""
FastAPI gateway between the Streamlit frontend and the ADK agent service.

Endpoints
---------
POST /upload          – Accept a PDF file, save it to /uploads, return the path.
POST /chat            – Forward a chat message (+ optional file path) to ADK.
GET  /health          – Liveness probe.
"""

import os
import uuid
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ADK_URL = os.getenv("ADK_URL", "http://adk:8000")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "lease_reviewer"   # must match the ADK module directory name
DEFAULT_USER_ID = "user_1"

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Lease Reviewer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: str = DEFAULT_USER_ID


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class UploadResponse(BaseModel):
    file_path: str
    filename: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_ADK_RUN_URL = f"{ADK_URL}/run"


async def _ensure_session(session_id: str, user_id: str) -> None:
    """Ensure an ADK session exists, creating it if necessary.

    The ADK session API does not support upsert, so we GET first and POST
    only on a 404 to avoid duplicate-session errors.
    """
    url = f"{ADK_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        if r.status_code == 404:
            await client.post(url, json={})


async def _run_agent(session_id: str, user_id: str, message: str) -> str:
    """Send a message to the ADK agent and return the text reply."""
    payload = {
        "app_name": APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": message}],
        },
        "streaming": False,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(_ADK_RUN_URL, json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"ADK error {exc.response.status_code}: {exc.response.text[:500]}",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Cannot reach ADK service: {exc}",
            ) from exc

    events = resp.json()

    # Concatenate all model-role text parts from the event stream.
    reply_parts: list[str] = []
    for event in events:
        content = event.get("content") or {}
        if content.get("role") == "model":
            for part in content.get("parts", []):
                if text := part.get("text"):
                    reply_parts.append(text)

    return "".join(reply_parts) or "(no response)"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Save an uploaded PDF to the shared uploads directory."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Use a UUID subdirectory to avoid collisions
    dest_dir = UPLOAD_DIR / str(uuid.uuid4())
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename

    contents = await file.read()
    dest_path.write_bytes(contents)

    return UploadResponse(file_path=str(dest_path), filename=file.filename)


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Forward a chat message to the ADK agent and return the reply."""
    await _ensure_session(req.session_id, req.user_id)
    reply = await _run_agent(req.session_id, req.user_id, req.message)
    return ChatResponse(session_id=req.session_id, reply=reply)
