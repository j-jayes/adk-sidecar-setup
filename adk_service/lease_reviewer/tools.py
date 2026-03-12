"""
ADK tools for the lease reviewer agent.

`convert_pdf_to_markdown` sends the uploaded PDF to the Docling sidecar
and returns the Markdown representation of the document.
"""

import os
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
        file_path: Absolute path to the PDF file inside the container.
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
                f"{docling_url}/v1alpha/convert/file",
                files={"files": (resolved.name, fh, "application/pdf")},
                data={"options": '{"to_formats":["md"]}'},
                timeout=timeout,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {"error": f"Docling HTTP error {exc.response.status_code}: {exc.response.text[:500]}"}
    except httpx.RequestError as exc:
        return {"error": f"Could not reach Docling at {docling_url}: {exc}"}

    payload = response.json()

    # Docling-serve response: {"documents": [{"md_content": "...", ...}]}
    documents = payload.get("documents") or []
    if not documents:
        return {"error": "Docling returned no documents in the response."}

    doc = documents[0]
    md_content: str = doc.get("md_content") or doc.get("content") or ""
    if not md_content:
        return {"error": "Docling conversion succeeded but returned empty Markdown."}

    # Persist the markdown in session state so other agents can reuse it
    # without calling Docling again.
    tool_context.state["lease_markdown"] = md_content
    tool_context.state["lease_file_path"] = str(resolved)

    return {"markdown": md_content}
