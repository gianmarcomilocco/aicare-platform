"""
AICare API — FastAPI backend
Powers the embeddable widget and WhatsApp integration.
"""

from fastapi import FastAPI, HTTPException, Header, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import sys, uuid, secrets, os

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import db as _db
import ai as _ai
_db.init()
_db.seed_kb("demo")  # ensure demo KB is always available

app = FastAPI(title="AICare API", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

WIDGET_PATH = Path(__file__).parent.parent / "widget" / "widget.js"

# ── Auth ─────────────────────────────────────────────────

def get_client(x_api_key: str = Header(..., alias="X-Api-Key")) -> dict:
    client = _db.get_company_by_key(x_api_key)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return client

# ── Schemas ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    customer_name:   Optional[str] = "Visitatore"
    customer_email:  Optional[str] = ""

class GenerateKeyRequest(BaseModel):
    username: str
    secret:   str

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
async def chat(body: ChatRequest, client: dict = Depends(get_client)):
    """Main chat endpoint — called by the JS widget."""
    conv_id = body.conversation_id
    int_id  = 0

    if not conv_id:
        int_id  = _db.new_conversation(
            client["username"],
            body.customer_name or "Visitatore",
            body.customer_email or ""
        )
        conv_id = f"api_{int_id}"
    else:
        try:
            int_id = int(conv_id.replace("api_", ""))
        except ValueError:
            int_id = 0

    # History
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
            body.customer_name or "", body.customer_email or ""
        )

    return {
        "response":        response,
        "conversation_id": conv_id,
        "intent":          intent,
        "ticket_id":       ticket_id,
    }


@app.post("/v1/whatsapp")
async def whatsapp_webhook(request: Request,
                            x_api_key: str = Header(None, alias="X-Api-Key")):
    """Twilio WhatsApp webhook."""
    data     = await request.form()
    message  = (data.get("Body") or "").strip()
    from_num = data.get("From", "")
    twiml_empty = '<?xml version="1.0"?><Response></Response>'

    if not message:
        return Response(content=twiml_empty, media_type="text/xml")

    client = _db.get_company_by_key(x_api_key) if x_api_key else None
    if not client:
        return Response(content=twiml_empty, media_type="text/xml")

    kb_items = _db.get_kb(client["username"])
    clf      = _ai.classify(message)
    response = _ai.generate_response(message, [], kb_items, client)

    twiml = f'<?xml version="1.0"?><Response><Message>{response}</Message></Response>'
    return Response(content=twiml, media_type="text/xml")


@app.post("/v1/keys/generate")
def generate_key(body: GenerateKeyRequest):
    """One-time call during client onboarding to create their API key."""
    admin_secret = os.getenv("ADMIN_SECRET", "changeme")
    if body.secret != admin_secret:
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
