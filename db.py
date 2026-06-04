import sqlite3
import json
from pathlib import Path

DB = Path(__file__).parent / "cc_agent.db"

DEMO_KB = [
    ("Ordini",     "Come posso tracciare il mio ordine?",          "Accedi alla tua area personale nella sezione 'I miei ordini', oppure usa il codice di tracking ricevuto via email."),
    ("Resi",       "Qual è la politica di reso?",                   "Accettiamo resi entro 30 giorni dall'acquisto. Il prodotto deve essere integro nella confezione originale. Contattaci con il numero d'ordine per avviare la procedura."),
    ("Spedizioni", "Quanto tempo ci vuole per la consegna?",        "Consegna standard: 3-5 giorni lavorativi. Consegna express disponibile in 24-48 ore a costo aggiuntivo."),
    ("Pagamenti",  "Quali metodi di pagamento accettate?",          "Carte di credito/debito (Visa, Mastercard), PayPal, Apple Pay, Google Pay e bonifico bancario."),
    ("Garanzia",   "Qual è la durata della garanzia?",              "Garanzia legale di 2 anni su tutti i prodotti. Per problemi entro questo periodo, assistenza o sostituzione gratuita."),
    ("Account",    "Ho dimenticato la password, come faccio?",      "Clicca 'Password dimenticata' nella pagina di login e inserisci la tua email. Riceverai il link di reset in pochi minuti."),
    ("Rimborsi",   "Quando riceverò il rimborso?",                  "I rimborsi vengono processati entro 3-5 giorni lavorativi dalla ricezione del reso. L'accredito sul conto avviene tipicamente entro 5-10 giorni."),
    ("Contatti",   "Come posso contattare l'assistenza?",           "Via email: assistenza@azienda.it. Telefono: 02-1234567 (lun-ven 9-18). Rispondiamo entro 24 ore."),
    ("Ordini",     "Posso modificare o annullare un ordine?",       "Puoi annullare o modificare l'ordine entro 24 ore dall'acquisto, prima della spedizione. Dopo la spedizione è necessario attendere la consegna e procedere con un reso."),
    ("Prodotti",   "Il prodotto che cerco non è disponibile, quando torna?", "Iscriviti alla notifica di disponibilità sulla pagina prodotto. Ti avviseremo via email non appena tornerà in stock."),
]

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            username             TEXT NOT NULL UNIQUE,
            api_key              TEXT UNIQUE,
            profile_json         TEXT DEFAULT '{}',
            name                 TEXT NOT NULL DEFAULT 'La Nostra Azienda',
            tone                 TEXT DEFAULT 'Professionale',
            language             TEXT DEFAULT 'Italiano',
            escalation_threshold INTEGER DEFAULT 60,
            escalate_angry       INTEGER DEFAULT 1,
            welcome_msg          TEXT DEFAULT 'Ciao! Sono il tuo assistente virtuale. Come posso aiutarti oggi?',
            created_at           TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS kb_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            category   TEXT NOT NULL,
            question   TEXT NOT NULL,
            answer     TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT NOT NULL,
            customer_name  TEXT DEFAULT 'Visitatore',
            customer_email TEXT DEFAULT '',
            status         TEXT DEFAULT 'open',
            sentiment      TEXT DEFAULT 'neutral',
            intent         TEXT DEFAULT '',
            created_at     TEXT DEFAULT (datetime('now')),
            updated_at     TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role            TEXT NOT NULL,
            content         TEXT NOT NULL,
            intent          TEXT DEFAULT '',
            confidence      INTEGER DEFAULT 0,
            sentiment       TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tickets (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT NOT NULL,
            conversation_id INTEGER,
            title          TEXT NOT NULL,
            category       TEXT DEFAULT 'altro',
            priority       TEXT DEFAULT 'media',
            status         TEXT DEFAULT 'aperto',
            customer_name  TEXT DEFAULT '',
            customer_email TEXT DEFAULT '',
            notes          TEXT DEFAULT '',
            created_at     TEXT DEFAULT (datetime('now')),
            resolved_at    TEXT
        );
        """)

# ── Company ──────────────────────────────────────────────

def get_company(username):
    with conn() as c:
        r = c.execute("SELECT * FROM companies WHERE username=?", (username,)).fetchone()
        if r:
            d = dict(r)
            d["profile"] = json.loads(d.get("profile_json") or "{}")
            return d
    return {
        "name": "Demo Azienda", "tone": "Professionale", "language": "Italiano",
        "escalation_threshold": 60, "escalate_angry": 1,
        "welcome_msg": "Ciao! Sono il tuo assistente virtuale. Come posso aiutarti oggi?",
        "profile": {}
    }

def save_company(username, name, tone, language, threshold, escalate_angry, welcome_msg):
    with conn() as c:
        c.execute("""
            INSERT INTO companies (username,name,tone,language,escalation_threshold,escalate_angry,welcome_msg)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(username) DO UPDATE SET
                name=excluded.name, tone=excluded.tone, language=excluded.language,
                escalation_threshold=excluded.escalation_threshold,
                escalate_angry=excluded.escalate_angry, welcome_msg=excluded.welcome_msg
        """, (username, name, tone, language, threshold, int(escalate_angry), welcome_msg))

def get_company_by_key(api_key: str):
    with conn() as c:
        r = c.execute("SELECT * FROM companies WHERE api_key=?", (api_key,)).fetchone()
        if r:
            d = dict(r)
            d["profile"] = json.loads(d.get("profile_json") or "{}")
            return d
    return None

def save_api_key(username: str, api_key: str):
    with conn() as c:
        c.execute("""
            INSERT INTO companies (username, api_key)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET api_key=excluded.api_key
        """, (username, api_key))

def save_company_profile(username, profile: dict):
    with conn() as c:
        c.execute("""
            INSERT INTO companies (username, profile_json)
            VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET profile_json=excluded.profile_json
        """, (username, json.dumps(profile, ensure_ascii=False)))

# ── Knowledge Base ────────────────────────────────────────

def get_kb(username):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM kb_items WHERE username=? ORDER BY category, id", (username,)
        ).fetchall()]

def add_kb_item(username, category, question, answer):
    with conn() as c:
        c.execute("INSERT INTO kb_items (username,category,question,answer) VALUES (?,?,?,?)",
                  (username, category, question, answer))

def delete_kb_item(kid):
    with conn() as c:
        c.execute("DELETE FROM kb_items WHERE id=?", (kid,))

def seed_kb(username):
    with conn() as c:
        count = c.execute("SELECT COUNT(*) FROM kb_items WHERE username=?", (username,)).fetchone()[0]
        if count == 0:
            c.executemany(
                "INSERT INTO kb_items (username,category,question,answer) VALUES (?,?,?,?)",
                [(username, cat, q, a) for cat, q, a in DEMO_KB]
            )

# ── Conversations ─────────────────────────────────────────

def new_conversation(username, name="Visitatore", email=""):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO conversations (username,customer_name,customer_email) VALUES (?,?,?)",
            (username, name, email)
        )
        return cur.lastrowid

def update_conversation_meta(conv_id, sentiment, intent):
    with conn() as c:
        c.execute("""UPDATE conversations SET sentiment=?, intent=?, updated_at=datetime('now')
                     WHERE id=?""", (sentiment, intent, conv_id))

def close_conversation(conv_id):
    with conn() as c:
        c.execute("UPDATE conversations SET status='closed', updated_at=datetime('now') WHERE id=?", (conv_id,))

def get_conversations(username, limit=50):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM conversations WHERE username=? ORDER BY updated_at DESC LIMIT ?",
            (username, limit)
        ).fetchall()]

# ── Messages ──────────────────────────────────────────────

def add_message(conv_id, role, content, intent="", confidence=0, sentiment=""):
    with conn() as c:
        c.execute("""INSERT INTO messages (conversation_id,role,content,intent,confidence,sentiment)
                     VALUES (?,?,?,?,?,?)""",
                  (conv_id, role, content, intent, confidence, sentiment))

def get_messages(conv_id):
    with conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at", (conv_id,)
        ).fetchall()]

# ── Tickets ───────────────────────────────────────────────

def create_ticket(username, conv_id, title, category, priority, customer_name="", customer_email=""):
    with conn() as c:
        cur = c.execute("""
            INSERT INTO tickets (username,conversation_id,title,category,priority,customer_name,customer_email)
            VALUES (?,?,?,?,?,?,?)
        """, (username, conv_id, title, category, priority, customer_name, customer_email))
        return cur.lastrowid

def get_tickets(username, status=None):
    with conn() as c:
        if status:
            rows = c.execute(
                "SELECT * FROM tickets WHERE username=? AND status=? ORDER BY created_at DESC",
                (username, status)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM tickets WHERE username=? ORDER BY created_at DESC",
                (username,)
            ).fetchall()
        return [dict(r) for r in rows]

def resolve_ticket(tid, notes=""):
    with conn() as c:
        c.execute("""UPDATE tickets SET status='risolto', resolved_at=datetime('now'), notes=?
                     WHERE id=?""", (notes, tid))

def update_ticket_priority(tid, priority):
    with conn() as c:
        c.execute("UPDATE tickets SET priority=? WHERE id=?", (priority, tid))

def update_ticket_notes(tid, notes):
    with conn() as c:
        c.execute("UPDATE tickets SET notes=? WHERE id=?", (notes, tid))

# ── Stats ─────────────────────────────────────────────────

def get_stats(username):
    with conn() as c:
        today = c.execute(
            "SELECT COUNT(*) FROM conversations WHERE username=? AND date(created_at)=date('now')",
            (username,)
        ).fetchone()[0]
        total = c.execute("SELECT COUNT(*) FROM conversations WHERE username=?", (username,)).fetchone()[0]
        open_t = c.execute(
            "SELECT COUNT(*) FROM tickets WHERE username=? AND status='aperto'", (username,)
        ).fetchone()[0]
        resolved_t = c.execute(
            "SELECT COUNT(*) FROM tickets WHERE username=? AND status='risolto'", (username,)
        ).fetchone()[0]
        intents = c.execute("""
            SELECT intent, COUNT(*) as n FROM conversations
            WHERE username=? AND intent != ''
            GROUP BY intent ORDER BY n DESC LIMIT 5
        """, (username,)).fetchall()
        sentiments = c.execute("""
            SELECT sentiment, COUNT(*) as n FROM conversations
            WHERE username=? GROUP BY sentiment
        """, (username,)).fetchall()
    return {
        "today": today, "total": total,
        "open_tickets": open_t, "resolved_tickets": resolved_t,
        "intents": [dict(r) for r in intents],
        "sentiments": [dict(r) for r in sentiments],
    }
