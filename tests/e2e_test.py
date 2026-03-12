"""End-to-end test for the Lease Reviewer stack."""

import sys
import time
from pathlib import Path

import httpx

API = "http://localhost:8001"
PDF_PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "tests/test-lease.pdf")

with httpx.Client(timeout=180) as client:
    # 1. Health check
    r = client.get(f"{API}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("[OK] API healthy")

    # 2. Upload
    with PDF_PATH.open("rb") as f:
        r = client.post(f"{API}/upload", files={"file": (PDF_PATH.name, f, "application/pdf")})
    assert r.status_code == 200, f"Upload failed ({r.status_code}): {r.text}"
    file_path = r.json()["file_path"]
    print(f"[OK] Uploaded to {file_path}")

    # 3. Chat - trigger review
    session_id = f"e2e-test-{int(time.time())}"
    print(f"[..] Sending chat (session={session_id}), this may take 1-2 minutes...")
    r = client.post(f"{API}/chat", json={
        "session_id": session_id,
        "message": f"I have uploaded my lease agreement. The file is at `{file_path}`. Please review it for me.",
    })
    assert r.status_code == 200, f"Chat failed ({r.status_code}): {r.text}"
    reply = r.json()["reply"]
    print(f"[OK] Agent replied ({len(reply)} chars)")
    print(f"\n--- Reply preview ---\n{reply[:1000]}\n---")
