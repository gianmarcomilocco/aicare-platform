import anthropic
import json
import requests as _req

client = anthropic.Anthropic()

INTENTS = {
    "stato_ordine":     "Stato ordine / tracking",
    "reso_rimborso":    "Reso e rimborso",
    "problema_tecnico": "Problema tecnico",
    "info_prodotto":    "Info prodotto / servizio",
    "fatturazione":     "Fatturazione / pagamento",
    "account_accesso":  "Account / accesso",
    "reclamo":          "Reclamo / lamentela",
    "spedizione":       "Spedizione / consegna",
    "prenotazione":     "Prenotazione / appuntamento",
    "altro":            "Altro / generico",
}

PRIORITY_MAP = {
    "angry":    "alta",
    "negative": "media",
    "neutral":  "bassa",
    "positive": "bassa",
}

def classify(message):
    """Classify intent, sentiment, and confidence of a customer message."""
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{"role": "user", "content": f"""Analizza il messaggio di un cliente e rispondi SOLO con JSON valido, nient'altro.

Messaggio: "{message}"

Categorie intent: {', '.join(INTENTS.keys())}
Sentiment: neutral, positive, negative, angry

JSON: {{"intent": "categoria", "confidence": 0-100, "sentiment": "valore"}}"""}]
        )
        text = resp.content[0].text.strip()
        s = text.find("{"); e = text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return {"intent": "altro", "confidence": 50, "sentiment": "neutral"}


def generate_response(user_message, history, kb_items, company):
    """Generate a grounded response using the company's KB and profile."""
    kb_ctx = ""
    if kb_items:
        kb_ctx = "KNOWLEDGE BASE:\n" + "\n\n".join(
            f"[{it['category']}] D: {it['question']}\nR: {it['answer']}"
            for it in kb_items[:15]
        )

    profile_ctx = build_profile_context(company.get("profile", {}))
    if profile_ctx:
        profile_ctx = f"PROFILO AZIENDA:\n{profile_ctx}\n"

    system = f"""Sei l'assistente virtuale di {company.get('name', 'Azienda')}.
Rispondi in {company.get('language', 'Italiano')} con tono {company.get('tone', 'Professionale')}.
Sei preciso, empatico e risolvi i problemi in modo efficiente.

{profile_ctx}
{kb_ctx}

REGOLE ASSOLUTE:
- Usa SOLO le informazioni presenti nella knowledge base
- Se non hai le informazioni necessarie, dillo chiaramente: "Non ho questa informazione, ti metto in contatto con un operatore"
- Non inventare prezzi, date, policy non presenti nella KB
- Rispondi in modo completo ma conciso (max 3-4 frasi)
- Non usare markdown, asterischi, grassetto o elenchi puntati
- Non usare trattini lunghi (— oppure –)
- Se il cliente è agitato, inizia con empatia prima di dare la soluzione
- Firma sempre come "Assistente {company.get('name', 'Azienda')}"
"""

    msgs = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
    msgs.append({"role": "user", "content": user_message})

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=450,
        system=system,
        messages=msgs
    )
    return resp.content[0].text.strip()


def should_escalate(classification, company):
    """Return True if the conversation should be escalated to a human ticket."""
    conf = classification.get("confidence", 100)
    threshold = company.get("escalation_threshold", 60)
    sentiment = classification.get("sentiment", "neutral")
    escalate_angry = bool(company.get("escalate_angry", 1))

    if conf < threshold:
        return True
    if escalate_angry and sentiment == "angry":
        return True
    return False


def summarize_for_ticket(messages):
    """Generate a concise ticket title from conversation history."""
    try:
        conv = "\n".join(
            f"{m['role']}: {m['content'][:120]}"
            for m in messages[:6]
        )
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content": f"Scrivi un titolo breve (massimo 8 parole) per questo ticket di assistenza. Solo il titolo, nient'altro:\n\n{conv}"}]
        )
        return resp.content[0].text.strip().strip('"').strip("'")
    except Exception:
        return "Richiesta assistenza clienti"


def priority_from_sentiment(sentiment):
    return PRIORITY_MAP.get(sentiment, "bassa")


# ── Company profile helpers ───────────────────────────────

def fetch_url_text(url: str) -> str:
    """Fetch text content from a URL (HTML page or PDF)."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CCAgent/1.0; +https://ccagent.io)"}
    r = _req.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    ct = r.headers.get("Content-Type", "")

    if "pdf" in ct or url.lower().endswith(".pdf"):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(r.content))
            return "\n".join(p.extract_text() or "" for p in reader.pages)[:12000]
        except Exception:
            return ""

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:12000]
    except Exception:
        return r.text[:12000]


def generate_kb_from_text(text: str, language: str = "Italiano") -> list[dict]:
    """Ask Claude to generate Q&A KB items from a block of company text."""
    CATS = ["Ordini","Resi","Rimborsi","Spedizioni","Pagamenti","Account",
            "Garanzia","Prodotti","Servizi","Prenotazioni","Contatti","Generale"]
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": f"""Sei un esperto di customer service. Analizza questo testo descrittivo di un'azienda e genera 15-20 domande e risposte che i clienti potrebbero fare all'assistenza clienti.

REGOLE:
- Scrivi domande e risposte in {language}
- Usa un tono professionale e diretto
- Copri tutte le informazioni presenti nel testo
- Formula domande come le farebbe un vero cliente
- Categorie disponibili: {', '.join(CATS)}
- Non inventare informazioni non presenti nel testo

TESTO AZIENDA:
{text[:8000]}

Rispondi SOLO con JSON valido:
{{"items":[{{"category":"Prodotti","question":"...","answer":"..."}}]}}"""}]
    )
    try:
        raw = resp.content[0].text.strip()
        s = raw.find("{"); e = raw.rfind("}") + 1
        return json.loads(raw[s:e]).get("items", [])
    except Exception:
        return []


def build_profile_context(profile: dict) -> str:
    """Convert a company profile dict into a readable context string for the AI."""
    if not profile:
        return ""
    fields = [
        ("Settore",            profile.get("sector", "")),
        ("Descrizione",        profile.get("description", "")),
        ("Prodotti/Servizi",   profile.get("products", "")),
        ("Politica di reso",   profile.get("return_policy", "")),
        ("Spedizioni",         profile.get("shipping", "")),
        ("Pagamenti",          profile.get("payment_methods", "")),
        ("Orari",              profile.get("hours", "")),
        ("Contatti",           profile.get("contacts", "")),
        ("Note aggiuntive",    profile.get("extra_notes", "")),
    ]
    lines = [f"{k}: {v}" for k, v in fields if v.strip()]
    return "\n".join(lines)
