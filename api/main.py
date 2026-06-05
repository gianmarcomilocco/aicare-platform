"""
AICare API — FastAPI backend
Powers the embeddable widget and WhatsApp integration.
"""

from fastapi import FastAPI, HTTPException, Header, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sys, secrets, os, re
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import db as _db
import ai as _ai
_db.init()
_db.seed_kb("demo")

_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "365"))
_purged = _db.purge_all_old_conversations(_RETENTION_DAYS)
if _purged:
    import logging
    logging.getLogger("aicare").info("Purged %d old conversations (retention=%d days)", _purged, _RETENTION_DAYS)

# ── Rate limiter ──────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])

app = FastAPI(
    title="AICare API",
    version="1.0.0",
    docs_url="/api/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

WIDGET_PATH = Path(__file__).parent.parent / "widget" / "widget.js"

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers[k] = v
    return response

# ── Auth ─────────────────────────────────────────────────

def get_client(x_api_key: str = Header(..., alias="X-Api-Key")) -> dict:
    client = _db.get_company_by_key(x_api_key)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return client

# ── Schemas ───────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}$")

class ChatRequest(BaseModel):
    message:         str
    conversation_id: Optional[str] = None
    customer_name:   Optional[str] = "Visitatore"
    customer_email:  Optional[str] = ""

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > 2000:
            raise ValueError("message too long (max 2000 chars)")
        return v

    @field_validator("customer_name")
    @classmethod
    def name_length(cls, v):
        if v and len(v) > 120:
            raise ValueError("customer_name too long")
        return (v or "Visitatore").strip()

    @field_validator("customer_email")
    @classmethod
    def email_format(cls, v):
        if v and not _EMAIL_RE.match(v):
            raise ValueError("invalid email format")
        return (v or "").strip()

class GenerateKeyRequest(BaseModel):
    username: str
    secret:   str

    @field_validator("username")
    @classmethod
    def username_safe(cls, v):
        if not re.match(r"^[a-z0-9_]{2,40}$", v):
            raise ValueError("username must be 2-40 lowercase alphanumeric chars")
        return v

class GDPRDeleteRequest(BaseModel):
    customer_email: str

    @field_validator("customer_email")
    @classmethod
    def email_required(cls, v):
        v = v.strip()
        if not v or not _EMAIL_RE.match(v):
            raise ValueError("valid customer_email required")
        return v

# ── Routes ────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok", "service": "AICare API v1.0"}


@app.get("/widget.js")
def serve_widget():
    if not WIDGET_PATH.exists():
        raise HTTPException(404, "Widget not found")
    return FileResponse(WIDGET_PATH, media_type="application/javascript",
                        headers={"Cache-Control": "public, max-age=3600"})


@app.post("/v1/chat")
@limiter.limit("30/minute")
async def chat(request: Request, body: ChatRequest, client: dict = Depends(get_client)):
    """Main chat endpoint — called by the JS widget."""
    conv_id = body.conversation_id
    int_id  = 0

    if not conv_id:
        int_id  = _db.new_conversation(
            client["username"],
            body.customer_name,
            body.customer_email,
        )
        conv_id = f"api_{int_id}"
    else:
        try:
            int_id = int(conv_id.replace("api_", ""))
        except ValueError:
            int_id = 0

    history = []
    if int_id:
        msgs    = _db.get_messages(int_id)
        history = [{"role": m["role"], "content": m["content"]} for m in msgs[-10:]]

    kb_items  = _db.get_kb(client["username"])
    clf       = _ai.classify(body.message)
    intent    = clf.get("intent",    "altro")
    conf      = clf.get("confidence", 50)
    sentiment = clf.get("sentiment", "neutral")
    response  = _ai.generate_response(body.message, history, kb_items, client)

    if int_id:
        _db.add_message(int_id, "user",      body.message, intent, conf, sentiment)
        _db.add_message(int_id, "assistant", response,     intent, conf, sentiment)
        _db.update_conversation_meta(int_id, sentiment, intent)

    ticket_id = None
    if int_id and _ai.should_escalate(clf, client):
        title     = _ai.summarize_for_ticket([{"role": "user", "content": body.message}])
        priority  = _ai.priority_from_sentiment(sentiment)
        ticket_id = _db.create_ticket(
            client["username"], int_id, title, intent, priority,
            body.customer_name, body.customer_email,
        )

    return {
        "response":        response,
        "conversation_id": conv_id,
        "intent":          intent,
        "ticket_id":       ticket_id,
    }


@app.post("/v1/whatsapp")
@limiter.limit("60/minute")
async def whatsapp_webhook(request: Request,
                            x_api_key: str = Header(None, alias="X-Api-Key")):
    """Twilio WhatsApp webhook."""
    data     = await request.form()
    message  = (data.get("Body") or "").strip()[:2000]
    twiml_empty = '<?xml version="1.0"?><Response></Response>'

    if not message:
        return Response(content=twiml_empty, media_type="text/xml")

    client = _db.get_company_by_key(x_api_key) if x_api_key else None
    if not client:
        return Response(content=twiml_empty, media_type="text/xml")

    kb_items = _db.get_kb(client["username"])
    response = _ai.generate_response(message, [], kb_items, client)

    twiml = f'<?xml version="1.0"?><Response><Message>{response}</Message></Response>'
    return Response(content=twiml, media_type="text/xml")


@app.post("/v1/keys/generate")
@limiter.limit("5/minute")
def generate_key(request: Request, body: GenerateKeyRequest):
    """One-time call during client onboarding to create their API key."""
    admin_secret = os.getenv("ADMIN_SECRET", "")
    if not admin_secret or body.secret != admin_secret:
        raise HTTPException(403, "Forbidden")
    key = "aic_" + secrets.token_urlsafe(32)
    _db.save_api_key(body.username, key)
    return {"api_key": key, "username": body.username}


@app.get("/v1/keys/mine")
def get_my_key(client: dict = Depends(get_client)):
    return {
        "username":     client["username"],
        "company_name": client.get("name"),
        "tone":         client.get("tone"),
        "language":     client.get("language"),
    }


@app.post("/v1/gdpr/delete-customer")
@limiter.limit("10/minute")
async def gdpr_delete_customer(request: Request, body: GDPRDeleteRequest,
                                client: dict = Depends(get_client)):
    """
    GDPR Art. 17 — right to erasure.
    Deletes all conversations, messages and tickets for the given customer email
    within the company's account. Requires the company API key.
    """
    deleted = _db.delete_customer_data(client["username"], body.customer_email)
    return {
        "deleted_conversations": deleted,
        "email": body.customer_email,
        "message": f"Deleted {deleted} conversation(s) and related data.",
    }


@app.get("/v1/gdpr/export-customer")
@limiter.limit("10/minute")
async def gdpr_export_customer(request: Request, email: str,
                                client: dict = Depends(get_client)):
    """
    GDPR Art. 20 — right to data portability.
    Returns all conversations and messages for a customer email as JSON.
    Requires the company API key.
    """
    if not email or not re.match(r"^[^@\s]{1,64}@[^@\s]{1,255}$", email):
        raise HTTPException(400, "valid email required")
    data = _db.export_customer_data(client["username"], email)
    data["exported_at"] = datetime.now(timezone.utc).isoformat()
    return data
