"""
ADK tools for the lease reviewer agent.

`convert_pdf_to_markdown` sends the uploaded PDF to the Docling sidecar
(POST /v1/convert/file) and stores the resulting Markdown in session state
under the key ``lease_markdown`` for downstream agents to consume.
"""

from pathlib import Path

import httpx
from google.adk.tools import ToolContext

from .settings import settings


def convert_pdf_to_markdown(file_path: str, tool_context: ToolContext) -> dict:
    """Convert an uploaded PDF file to Markdown using the Docling sidecar.

    Call this tool when the user has uploaded a PDF lease document and you
    need its text content for analysis.  Pass the file path exactly as
    provided by the user or API (e.g. '/uploads/abc123/lease.pdf').

    Args:
        file_path: Path to the PDF file inside the container.  May be
            absolute (e.g. '/uploads/abc/lease.pdf') or relative, in which
            case it is resolved against the configured UPLOAD_DIR.
        tool_context: Injected by ADK – provides access to session state.

    Returns:
        A dict with keys:
          - "markdown": the full Markdown text of the document, or
          - "error": a human-readable error message if conversion failed.
    """
    resolved = Path(file_path)

    if not resolved.is_absolute():
        resolved = Path(settings.upload_dir) / file_path

    if not resolved.exists():
        return {"error": f"File not found: {resolved}"}

    docling_url = settings.docling_url.rstrip("/")
    timeout = settings.docling_timeout

    try:
        with resolved.open("rb") as fh:
            response = httpx.post(
                f"{docling_url}/v1/convert/file",
                files={"files": (resolved.name, fh, "application/pdf")},
                timeout=timeout,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {"error": f"Docling HTTP error {exc.response.status_code}: {exc.response.text[:500]}"}
    except httpx.RequestError as exc:
        return {"error": f"Could not reach Docling at {docling_url}: {exc}"}

    payload = response.json()

    # Docling-serve v1 response: {"document": {"md_content": "...", ...}, "status": "..."}
    doc = payload.get("document") or {}
    md_content: str = doc.get("md_content") or ""
    if not md_content:
        return {"error": "Docling conversion succeeded but returned empty Markdown."}

    # Store the Markdown in session state under "lease_markdown" so the
    # checklist_agent can read it without calling Docling a second time.
    tool_context.state["lease_markdown"] = md_content

    return {"markdown": md_content}
