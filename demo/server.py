"""Demo UI: chat with your agent and watch each Strands Decider 2B decision as it happens.

    ./kit demo            # http://localhost:8501
    DEMO_TARGET=agentcore AGENTCORE_ARN=arn:... ./kit demo     # talk to the agent deployed on AWS

The page has the conversation on the left and a decision panel on the right (each question's
probability, the verdict, and how long the decider and the whole turn took). It is also what
`./kit video` records.
"""

from __future__ import annotations

import io
import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from decider_kit.config import load_dotenv

load_dotenv()
STATIC = Path(__file__).parent / "static"
app = FastAPI(title="Strands Decider hackathon demo")
_agent: Any = None

# ---------------------------------------------------------------------------
# Maximum file size for extraction (5 MB — prevents accidental huge uploads)
# ---------------------------------------------------------------------------
MAX_EXTRACT_BYTES = 5 * 1024 * 1024  # 5 MB
# Maximum characters returned from extraction (avoids flooding the LLM prompt)
MAX_EXTRACT_CHARS = 8_000


class Turn(BaseModel):
    message: str
    session_id: str = "demo"
    images: list[str] = []  # base64 (data: URLs accepted), from the attach button


def agent() -> Any:
    global _agent
    if _agent is None:
        if os.environ.get("DEMO_TARGET") == "agentcore":
            _agent = AgentCoreClient(os.environ["AGENTCORE_ARN"])
        else:
            from agent.agent import HackathonAgent

            _agent = HackathonAgent()
    return _agent


class AgentCoreClient:
    """The same `chat()` interface, served by the agent deployed on Amazon Bedrock AgentCore Runtime."""

    def __init__(self, arn: str):
        import boto3

        self.arn = arn
        self.client = boto3.client("bedrock-agentcore", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        self.sessions: dict[str, str] = {}

    def chat(self, message: str, session_id: str = "demo", images: list[str] | None = None) -> dict[str, Any]:
        sid = self.sessions.setdefault(session_id, f"demo-{session_id}-{uuid.uuid4().hex}")
        payload = {"prompt": message, **({"images": images} if images else {})}
        r = self.client.invoke_agent_runtime(agentRuntimeArn=self.arn, runtimeSessionId=sid,
                                             payload=json.dumps(payload).encode())
        body = r["response"].read() if hasattr(r["response"], "read") else r["response"]
        out = json.loads(body)
        out["served_by"] = "Amazon Bedrock AgentCore Runtime"
        return out


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


# ---------------------------------------------------------------------------
# /api/extract — server-side document text extraction
#
# Accepts a single file upload (multipart/form-data).
# Supported types: .pdf, .pptx, .docx, .txt
# Images are NOT extracted server-side; they are sent as base64 via /api/chat.
#
# Security notes:
#   - File contents are parsed in-memory and never written to disk.
#   - Extracted text is truncated to MAX_EXTRACT_CHARS before being returned.
#   - File size is validated before reading; oversized files are rejected.
#   - Only the extracted text is returned — no credentials or paths are logged.
# ---------------------------------------------------------------------------

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}

ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".ppt", ".docx", ".doc", ".txt"}


def _extract_pdf(data: bytes) -> tuple[str, int]:
    """Extract text from PDF bytes. Returns (text, page_count)."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {i}]\n{text.strip()}")
    return "\n\n".join(pages), len(reader.pages)


def _extract_pptx(data: bytes) -> tuple[str, int]:
    """Extract text from PPTX bytes. Returns (text, slide_count)."""
    from pptx import Presentation
    prs = Presentation(io.BytesIO(data))
    slides = []
    for i, slide in enumerate(prs.slides, 1):
        parts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                parts.append(shape.text.strip())
        if parts:
            slides.append(f"[Slide {i}]\n" + "\n".join(parts))
    return "\n\n".join(slides), len(prs.slides)


def _extract_docx(data: bytes) -> tuple[str, int]:
    """Extract text from DOCX bytes. Returns (text, paragraph_count)."""
    from docx import Document
    doc = Document(io.BytesIO(data))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs), len(paragraphs)


def _extract_txt(data: bytes) -> tuple[str, int]:
    """Decode plain-text bytes. Returns (text, line_count)."""
    text = data.decode("utf-8", errors="replace")
    lines = [l for l in text.splitlines() if l.strip()]
    return text, len(lines)


@app.post("/api/extract")
async def extract(file: UploadFile = File(...)) -> JSONResponse:
    """Extract text from an uploaded study-material file.

    The extracted text is returned as a plain string and is never stored on disk.
    File size is capped at MAX_EXTRACT_BYTES. Only .pdf/.pptx/.docx/.txt are supported.
    """
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            {"error": f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
             "filename": filename},
            status_code=400,
        )

    data = await file.read(MAX_EXTRACT_BYTES + 1)
    if len(data) > MAX_EXTRACT_BYTES:
        return JSONResponse(
            {"error": f"File too large. Maximum allowed size is {MAX_EXTRACT_BYTES // (1024*1024)} MB.",
             "filename": filename},
            status_code=413,
        )

    try:
        if ext == ".pdf":
            text, count = _extract_pdf(data)
            unit = "pages"
        elif ext in (".pptx", ".ppt"):
            text, count = _extract_pptx(data)
            unit = "slides"
        elif ext in (".docx", ".doc"):
            text, count = _extract_docx(data)
            unit = "paragraphs"
        else:  # .txt
            text, count = _extract_txt(data)
            unit = "lines"

        truncated = len(text) > MAX_EXTRACT_CHARS
        return JSONResponse({
            "filename": filename,
            "ext": ext,
            "text": text[:MAX_EXTRACT_CHARS],
            "char_count": len(text),
            "unit_count": count,
            "unit": unit,
            "truncated": truncated,
        })
    except Exception as e:  # noqa: BLE001
        return JSONResponse(
            {"error": f"Extraction failed: {type(e).__name__}: {e}", "filename": filename},
            status_code=500,
        )


@app.get("/api/info")
def info() -> dict[str, Any]:
    from decider_kit.config import settings

    s = settings()
    name = "Your agent"
    try:
        from agent import agent as mod

        name = getattr(mod, "NAME", name)
    except Exception:  # noqa: BLE001
        pass
    decider = s.decider_mode
    if os.environ.get("DEMO_TARGET") == "agentcore":
        dep = Path(__file__).resolve().parent.parent / "submission" / "deployment.json"
        if dep.exists():  # what the deployed agent uses, not this laptop's setting
            decider = json.loads(dep.read_text()).get("decider_mode", decider)
    from decider_kit.llm import describe

    llm = describe()
    if os.environ.get("DEMO_TARGET") == "agentcore":  # the deployed agent always uses Amazon Bedrock
        llm = f"Amazon Bedrock ({s.bedrock_model})"
    return {"agent": name, "llm": llm, "bedrock_model": s.bedrock_model, "decider": decider,
            "target": os.environ.get("DEMO_TARGET", "local")}


@app.post("/api/chat")
def chat(t: Turn) -> JSONResponse:
    try:
        a = agent()
        if t.images:
            import inspect

            if "images" not in inspect.signature(a.chat).parameters:
                return JSONResponse({"error": "this agent does not take images: add images=None to HackathonAgent.chat"},
                                    status_code=400)
            return JSONResponse(a.chat(t.message, t.session_id, images=t.images))
        return JSONResponse(a.chat(t.message, t.session_id))
    except Exception as e:  # noqa: BLE001 - shown in the UI
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=500)


@app.post("/api/reset")
def reset() -> dict[str, bool]:
    global _agent
    _agent = None
    return {"ok": True}
