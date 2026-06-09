import os, json
from pathlib import Path
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg2, psycopg2.extras
    PH = "%s"
else:
    import sqlite3
    _SQLITE = Path(__file__).parent / "cc_agent.db"
    PH = "?"

@contextmanager
def _db():
    if USE_PG:
        c = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield c; c.commit()
        except:
            c.rollback(); raise
        finally:
            c.close()
    else:
        c = sqlite3.connect(str(_SQLITE)); c.row_factory = sqlite3.Row
        try:
            yield c; c.commit()
        except:
            c.rollback(); raise
        finally:
            c.close()

def _row(r):  return dict(r) if r else None
def _rows(rs): return [dict(r) for r in rs]

def _insert(cur, sql, params):
    if USE_PG:
        cur.execute(sql + " RETURNING id", params)
        return cur.fetchone()["id"]
    cur.execute(sql, params); return cur.lastrowid

def _count(r):
    if isinstance(r, dict): return list(r.values())[0]
    return r[0]

def init():
    with _db() as c:
        cur = c.cursor()
        if USE_PG: _init_pg(cur)
        else: _init_sqlite(cur)

def _init_pg(cur):
    for s in [
        f"""CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY, username TEXT NOT NULL UNIQUE, api_key TEXT,
            profile_json TEXT DEFAULT '{{}}', name TEXT NOT NULL DEFAULT 'La Nostra Azienda',
            tone TEXT DEFAULT 'Professionale', language TEXT DEFAULT 'Italiano',
            escalation_threshold INTEGER DEFAULT 60, escalate_angry INTEGER DEFAULT 1,
            welcome_msg TEXT DEFAULT 'Ciao! Come posso aiutarti oggi?',
            created_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS kb_items (
            id SERIAL PRIMARY KEY, username TEXT NOT NULL, category TEXT NOT NULL,
            question TEXT NOT NULL, answer TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY, username TEXT NOT NULL,
            customer_name TEXT DEFAULT 'Visitatore', customer_email TEXT DEFAULT '',
            status TEXT DEFAULT 'open', sentiment TEXT DEFAULT 'neutral', intent TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY, conversation_id INTEGER NOT NULL, role TEXT NOT NULL,
            content TEXT NOT NULL, intent TEXT DEFAULT '', confidence INTEGER DEFAULT 0,
            sentiment TEXT DEFAULT '', created_at TIMESTAMP DEFAULT NOW())""",
        """CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY, username TEXT NOT NULL, conversation_id INTEGER,
            title TEXT NOT NULL, category TEXT DEFAULT 'altro', priority TEXT DEFAULT 'media',
            status TEXT DEFAULT 'aperto', customer_name TEXT DEFAULT '', customer_email TEXT DEFAULT '',
            notes TEXT DEFAULT '', created_at TIMESTAMP DEFAULT NOW(), resolved_at TIMESTAMP)""",
    ]: cur.execute(s)

def _init_sqlite(cur):
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, api_key TEXT,
        profile_json TEXT DEFAULT '{}', name TEXT NOT NULL DEFAULT 'La Nostra Azienda',
        tone TEXT DEFAULT 'Professionale', language TEXT DEFAULT 'Italiano',
        escalation_threshold INTEGER DEFAULT 60, escalate_angry INTEGER DEFAULT 1,
        welcome_msg TEXT DEFAULT 'Ciao! Come posso aiutarti oggi?',
        created_at TEXT DEFAULT (datetime('now')));
    CREATE TABLE IF NOT EXISTS kb_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, category TEXT NOT NULL,
        question TEXT NOT NULL, answer TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')));
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,
        customer_name TEXT DEFAULT 'Visitatore', customer_email TEXT DEFAULT '',
        status TEXT DEFAULT 'open', sentiment TEXT DEFAULT 'neutral', intent TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now')));
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL, role TEXT NOT NULL,
        content TEXT NOT NULL, intent TEXT DEFAULT '', confidence INTEGER DEFAULT 0,
        sentiment TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')));
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, conversation_id INTEGER,
        title TEXT NOT NULL, category TEXT DEFAULT 'altro', priority TEXT DEFAULT 'media',
        status TEXT DEFAULT 'aperto', customer_name TEXT DEFAULT '', customer_email TEXT DEFAULT '',
        notes TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')), resolved_at TEXT);
    """)

DEMO_KB = [
    ("Ordini","Come posso tracciare il mio ordine?","Accedi alla tua area personale nella sezione 'I miei ordini', oppure usa il codice di tracking ricevuto via email."),
    ("Resi","Qual è la politica di reso?","Accettiamo resi entro 30 giorni dall'acquisto. Il prodotto deve essere integro nella confezione originale."),
    ("Spedizioni","Quanto tempo ci vuole per la consegna?","Consegna standard: 3-5 giorni lavorativi. Express disponibile in 24-48 ore a costo aggiuntivo."),
    ("Pagamenti","Quali metodi di pagamento accettate?","Carte di credito/debito (Visa, Mastercard), PayPal, Apple Pay, Google Pay e bonifico bancario."),
    ("Garanzia","Qual è la durata della garanzia?","Garanzia legale di 2 anni su tutti i prodotti. Assistenza o sostituzione gratuita entro questo periodo."),
    ("Account","Ho dimenticato la password, come faccio?","Clicca 'Password dimenticata' nella pagina di login e inserisci la tua email. Riceverai il link di reset in pochi minuti."),
    ("Rimborsi","Quando riceverò il rimborso?","I rimborsi vengono processati entro 3-5 giorni lavorativi dalla ricezione del reso."),
    ("Contatti","Come posso contattare l'assistenza?","Via email: assistenza@azienda.it. Telefono: 02-1234567 (lun-ven 9-18). Rispondiamo entro 24 ore."),
    ("Ordini","Posso modificare o annullare un ordine?","Puoi annullare o modificare l'ordine entro 24 ore dall'acquisto, prima della spedizione."),
    ("Prodotti","Il prodotto che cerco non è disponibile, quando torna?","Iscriviti alla notifica di disponibilità sulla pagina prodotto. Ti avviseremo via email non appena tornerà in stock."),
]

def seed_kb(username):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT COUNT(*) FROM kb_items WHERE username={PH}", (username,))
        if _count(cur.fetchone()) == 0:
            for cat,q,a in DEMO_KB:
                cur.execute(f"INSERT INTO kb_items (username,category,question,answer) VALUES ({PH},{PH},{PH},{PH})", (username,cat,q,a))

def get_company(username):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT * FROM companies WHERE username={PH}", (username,))
        r = _row(cur.fetchone())
    if r:
        r["profile"] = json.loads(r.get("profile_json") or "{}")
        return r
    return {"name":"Demo Azienda","tone":"Professionale","language":"Italiano","escalation_threshold":60,"escalate_angry":1,"welcome_msg":"Ciao! Come posso aiutarti oggi?","profile":{}}

def get_company_by_key(api_key):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT * FROM companies WHERE api_key={PH}", (api_key,))
        r = _row(cur.fetchone())
    if r:
        r["profile"] = json.loads(r.get("profile_json") or "{}")
        return r
    return None

def _upsert(cur, username, field, value):
    if USE_PG:
        cur.execute(f"INSERT INTO companies (username,{field}) VALUES ({PH},{PH}) ON CONFLICT(username) DO UPDATE SET {field}=EXCLUDED.{field}", (username, value))
    else:
        cur.execute(f"INSERT INTO companies (username,{field}) VALUES ({PH},{PH}) ON CONFLICT(username) DO UPDATE SET {field}=excluded.{field}", (username, value))

def save_company(username, name, tone, language, threshold, escalate_angry, welcome_msg):
    with _db() as c:
        cur = c.cursor()
        if USE_PG:
            cur.execute(f"""INSERT INTO companies (username,name,tone,language,escalation_threshold,escalate_angry,welcome_msg)
                VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH})
                ON CONFLICT(username) DO UPDATE SET name=EXCLUDED.name,tone=EXCLUDED.tone,language=EXCLUDED.language,
                escalation_threshold=EXCLUDED.escalation_threshold,escalate_angry=EXCLUDED.escalate_angry,welcome_msg=EXCLUDED.welcome_msg""",
                (username,name,tone,language,threshold,int(escalate_angry),welcome_msg))
        else:
            cur.execute(f"""INSERT INTO companies (username,name,tone,language,escalation_threshold,escalate_angry,welcome_msg)
                VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH})
                ON CONFLICT(username) DO UPDATE SET name=excluded.name,tone=excluded.tone,language=excluded.language,
                escalation_threshold=excluded.escalation_threshold,escalate_angry=excluded.escalate_angry,welcome_msg=excluded.welcome_msg""",
                (username,name,tone,language,threshold,int(escalate_angry),welcome_msg))

def save_api_key(username, api_key):
    with _db() as c: _upsert(c.cursor(), username, "api_key", api_key)

def save_company_profile(username, profile):
    with _db() as c: _upsert(c.cursor(), username, "profile_json", json.dumps(profile, ensure_ascii=False))

def get_kb(username):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT * FROM kb_items WHERE username={PH} ORDER BY category, id", (username,))
        return _rows(cur.fetchall())

def add_kb_item(username, category, question, answer):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"INSERT INTO kb_items (username,category,question,answer) VALUES ({PH},{PH},{PH},{PH})", (username,category,question,answer))

def delete_kb_item(kid):
    with _db() as c:
        cur = c.cursor(); cur.execute(f"DELETE FROM kb_items WHERE id={PH}", (kid,))

def log_consent(conv_id, ip_hash="", widget_version="1.1"):
    """Log that a user gave consent before chatting (GDPR Art. 6 evidence)."""
    with _db() as c:
        cur = c.cursor()
        ts = "NOW()" if USE_PG else "datetime('now')"
        if USE_PG:
            cur.execute(f"""INSERT INTO messages (conversation_id, role, content, intent)
                VALUES ({PH},{PH},{PH},{PH})""",
                (conv_id, "system",
                 f"[CONSENT GIVEN] widget_v={widget_version} ip_hash={ip_hash}",
                 "consent"))
        else:
            cur.execute(f"""INSERT INTO messages (conversation_id, role, content, intent)
                VALUES ({PH},{PH},{PH},{PH})""",
                (conv_id, "system",
                 f"[CONSENT GIVEN] widget_v={widget_version} ip_hash={ip_hash}",
                 "consent"))

def new_conversation(username, name="Visitatore", email=""):
    with _db() as c:
        cur = c.cursor()
        return _insert(cur, f"INSERT INTO conversations (username,customer_name,customer_email) VALUES ({PH},{PH},{PH})", (username,name,email))

def update_conversation_meta(conv_id, sentiment, intent):
    with _db() as c:
        cur = c.cursor()
        ts = "NOW()" if USE_PG else "datetime('now')"
        cur.execute(f"UPDATE conversations SET sentiment={PH},intent={PH},updated_at={ts} WHERE id={PH}", (sentiment,intent,conv_id))

def close_conversation(conv_id):
    with _db() as c:
        cur = c.cursor()
        ts = "NOW()" if USE_PG else "datetime('now')"
        cur.execute(f"UPDATE conversations SET status='closed',updated_at={ts} WHERE id={PH}", (conv_id,))

def get_conversations(username, limit=50):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT * FROM conversations WHERE username={PH} ORDER BY updated_at DESC LIMIT {PH}", (username,limit))
        return _rows(cur.fetchall())

def add_message(conv_id, role, content, intent="", confidence=0, sentiment=""):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"INSERT INTO messages (conversation_id,role,content,intent,confidence,sentiment) VALUES ({PH},{PH},{PH},{PH},{PH},{PH})", (conv_id,role,content,intent,confidence,sentiment))

def get_messages(conv_id):
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT * FROM messages WHERE conversation_id={PH} ORDER BY created_at", (conv_id,))
        return _rows(cur.fetchall())

def create_ticket(username, conv_id, title, category, priority, customer_name="", customer_email=""):
    with _db() as c:
        cur = c.cursor()
        return _insert(cur, f"INSERT INTO tickets (username,conversation_id,title,category,priority,customer_name,customer_email) VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH})", (username,conv_id,title,category,priority,customer_name,customer_email))

def get_tickets(username, status=None):
    with _db() as c:
        cur = c.cursor()
        if status:
            cur.execute(f"SELECT * FROM tickets WHERE username={PH} AND status={PH} ORDER BY created_at DESC", (username,status))
        else:
            cur.execute(f"SELECT * FROM tickets WHERE username={PH} ORDER BY created_at DESC", (username,))
        return _rows(cur.fetchall())

def resolve_ticket(tid, notes=""):
    with _db() as c:
        cur = c.cursor()
        ts = "NOW()" if USE_PG else "datetime('now')"
        cur.execute(f"UPDATE tickets SET status='risolto',resolved_at={ts},notes={PH} WHERE id={PH}", (notes,tid))

def update_ticket_priority(tid, priority):
    with _db() as c:
        cur = c.cursor(); cur.execute(f"UPDATE tickets SET priority={PH} WHERE id={PH}", (priority,tid))

def update_ticket_notes(tid, notes):
    with _db() as c:
        cur = c.cursor(); cur.execute(f"UPDATE tickets SET notes={PH} WHERE id={PH}", (notes,tid))

def export_customer_data(username, customer_email):
    """GDPR Art. 20 — data portability: returns all data for a customer email."""
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT * FROM conversations WHERE username={PH} AND customer_email={PH} ORDER BY created_at", (username, customer_email))
        convs = _rows(cur.fetchall())
        result = []
        for conv in convs:
            cur.execute(f"SELECT role, content, created_at FROM messages WHERE conversation_id={PH} ORDER BY created_at", (conv["id"],))
            msgs = _rows(cur.fetchall())
            cur.execute(f"SELECT title, category, priority, status, created_at FROM tickets WHERE conversation_id={PH}", (conv["id"],))
            tickets = _rows(cur.fetchall())
            result.append({"conversation": conv, "messages": msgs, "tickets": tickets})
    return {"customer_email": customer_email, "exported_at": None, "conversations": result}

def purge_old_conversations(username, days):
    """Delete conversations (and related data) older than `days` days."""
    with _db() as c:
        cur = c.cursor()
        if USE_PG:
            cur.execute(f"SELECT id FROM conversations WHERE username={PH} AND updated_at < NOW() - INTERVAL '{int(days)} days'", (username,))
        else:
            cur.execute(f"SELECT id FROM conversations WHERE username={PH} AND datetime(updated_at) < datetime('now', '-{int(days)} days')", (username,))
        conv_ids = [r["id"] for r in _rows(cur.fetchall())]
        for cid in conv_ids:
            cur.execute(f"DELETE FROM messages WHERE conversation_id={PH}", (cid,))
            cur.execute(f"DELETE FROM tickets WHERE conversation_id={PH}", (cid,))
        if conv_ids:
            placeholders = ",".join([PH] * len(conv_ids))
            cur.execute(f"DELETE FROM conversations WHERE id IN ({placeholders})", tuple(conv_ids))
    return len(conv_ids)

def purge_all_old_conversations(days):
    """Purge old conversations across all tenants (called at startup)."""
    with _db() as c:
        cur = c.cursor()
        if USE_PG:
            cur.execute(f"SELECT id FROM conversations WHERE updated_at < NOW() - INTERVAL '{int(days)} days'")
        else:
            cur.execute(f"SELECT id FROM conversations WHERE datetime(updated_at) < datetime('now', '-{int(days)} days')")
        conv_ids = [r["id"] for r in _rows(cur.fetchall())]
        for cid in conv_ids:
            cur.execute(f"DELETE FROM messages WHERE conversation_id={PH}", (cid,))
            cur.execute(f"DELETE FROM tickets WHERE conversation_id={PH}", (cid,))
        if conv_ids:
            placeholders = ",".join([PH] * len(conv_ids))
            cur.execute(f"DELETE FROM conversations WHERE id IN ({placeholders})", tuple(conv_ids))
    return len(conv_ids)

def delete_customer_data(username, customer_email):
    """GDPR Art. 17 — deletes all data for a specific customer email."""
    with _db() as c:
        cur = c.cursor()
        cur.execute(f"SELECT id FROM conversations WHERE username={PH} AND customer_email={PH}", (username, customer_email))
        conv_ids = [r["id"] for r in _rows(cur.fetchall())]
        for cid in conv_ids:
            cur.execute(f"DELETE FROM messages WHERE conversation_id={PH}", (cid,))
            cur.execute(f"DELETE FROM tickets WHERE conversation_id={PH}", (cid,))
        if conv_ids:
            placeholders = ",".join([PH] * len(conv_ids))
            cur.execute(f"DELETE FROM conversations WHERE id IN ({placeholders})", tuple(conv_ids))
    return len(conv_ids)

def get_stats(username):
    with _db() as c:
        cur = c.cursor()
        date_filter = "created_at::date=CURRENT_DATE" if USE_PG else "date(created_at)=date('now')"
        cur.execute(f"SELECT COUNT(*) FROM conversations WHERE username={PH} AND {date_filter}", (username,))
        today = _count(cur.fetchone())
        cur.execute(f"SELECT COUNT(*) FROM conversations WHERE username={PH}", (username,))
        total = _count(cur.fetchone())
        cur.execute(f"SELECT COUNT(*) FROM tickets WHERE username={PH} AND status='aperto'", (username,))
        open_t = _count(cur.fetchone())
        cur.execute(f"SELECT COUNT(*) FROM tickets WHERE username={PH} AND status='risolto'", (username,))
        resolved_t = _count(cur.fetchone())
        cur.execute(f"SELECT intent, COUNT(*) as n FROM conversations WHERE username={PH} AND intent!='' GROUP BY intent ORDER BY n DESC LIMIT 5", (username,))
        intents = _rows(cur.fetchall())
        cur.execute(f"SELECT sentiment, COUNT(*) as n FROM conversations WHERE username={PH} GROUP BY sentiment", (username,))
        sentiments = _rows(cur.fetchall())
    return {"today":today,"total":total,"open_tickets":open_t,"resolved_tickets":resolved_t,"intents":intents,"sentiments":sentiments}
