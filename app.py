import streamlit as st
import yaml
import os
from pathlib import Path
from dotenv import load_dotenv
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import html as _html

load_dotenv(Path(__file__).parent.parent / ".env")
import db
import ai
db.init()

DEMO_MODE     = os.getenv("DEMO_MODE", "false").lower() == "true"
DEMO_MAX_USES = int(os.getenv("DEMO_MAX_USES", "5"))
CONTACT_NAME  = os.getenv("CONTACT_NAME", "Gianmarco")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "gianmarco.milocco@gmail.com")

st.set_page_config(
    page_title="AI Customer Care — Enterprise",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  --bg:       #f0f2f6;
  --sidebar:  #0d0f1a;
  --white:    #ffffff;
  --border:   #e4e8f0;
  --text-1:   #0d0f1a;
  --text-2:   #5a6278;
  --text-3:   #9aa0b4;
  --accent:   #4f46e5;
  --accent-h: #4338ca;
  --green:    #10b981;
  --yellow:   #f59e0b;
  --red:      #ef4444;
  --radius:   10px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);
}

*, *::before, *::after {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  box-sizing: border-box;
}

#MainMenu, footer, header,
[data-testid="stDecoration"], [data-testid="stToolbar"],
div[data-testid="stStatusWidget"] { display:none !important; }

.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #d1d5e0; border-radius: 8px; }

/* ── Page bg ── */
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--sidebar) !important;
  border-right: none !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,.75) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.06) !important; margin:.5rem 1.4rem !important; }

/* ── Radio nav ── */
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
[data-testid="stSidebar"] .stRadio label {
  border-radius: 7px !important;
  padding: .45rem .85rem !important;
  font-size: .84rem !important;
  font-weight: 500 !important;
  color: rgba(255,255,255,.6) !important;
  cursor: pointer !important;
  transition: background .15s !important;
}
[data-testid="stSidebar"] .stRadio label:hover { background: rgba(255,255,255,.06) !important; color: rgba(255,255,255,.9) !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:has(input:checked) label,
[data-testid="stSidebar"] .stRadio label:has(input:checked) {
  background: rgba(255,255,255,.1) !important;
  color: #fff !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] [class*="indicator"] { display:none !important; }

/* ── Main content padding ── */
[data-testid="stAppViewBlockContainer"] { padding: 2rem 2.4rem 3rem !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  border-radius: 8px !important;
  border: 1.5px solid var(--border) !important;
  background: var(--white) !important;
  font-size: .875rem !important;
  color: var(--text-1) !important;
  padding: .55rem .85rem !important;
  transition: border-color .15s, box-shadow .15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(79,70,229,.12) !important;
  outline: none !important;
}
.stTextInput > label, .stTextArea > label, .stSelectbox > label,
.stSlider > label, .stCheckbox > label {
  font-size: .75rem !important;
  font-weight: 600 !important;
  color: var(--text-2) !important;
  letter-spacing: .01em !important;
}
.stSelectbox [data-baseweb="select"] > div {
  border-radius: 8px !important;
  border: 1.5px solid var(--border) !important;
  background: var(--white) !important;
  font-size: .875rem !important;
}

/* ── Buttons ── */
.stButton > button[kind="primary"] {
  background: var(--text-1) !important;
  border: none !important;
  border-radius: 8px !important;
  font-size: .85rem !important;
  font-weight: 600 !important;
  color: #fff !important;
  padding: .5rem 1.2rem !important;
  letter-spacing: .01em !important;
  transition: background .15s, transform .1s !important;
}
.stButton > button[kind="primary"]:hover { background: var(--accent) !important; }
.stButton > button[kind="primary"]:active { transform: scale(.98) !important; }
.stButton > button:not([kind="primary"]) {
  background: var(--white) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text-2) !important;
  font-weight: 600 !important;
  font-size: .82rem !important;
  transition: border-color .15s, color .15s !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: var(--text-1) !important;
  color: var(--text-1) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 2px !important;
  background: #e8eaf2 !important;
  padding: 3px !important;
  border-radius: 9px !important;
  border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 7px !important;
  font-weight: 500 !important;
  font-size: .82rem !important;
  padding: 5px 14px !important;
  color: var(--text-2) !important;
  transition: all .15s !important;
}
.stTabs [aria-selected="true"] {
  background: var(--white) !important;
  color: var(--text-1) !important;
  font-weight: 700 !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ── Alerts ── */
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }
[data-testid="stInfo"]    { background: #f0f4ff !important; border: 1.5px solid #c7d2fe !important; border-radius: 8px !important; }
[data-testid="stInfo"] p  { color: #3730a3 !important; font-size: .84rem !important; }
[data-testid="stSuccess"] { border-radius: 8px !important; }
[data-testid="stWarning"] { border-radius: 8px !important; }

/* ── Chat bubbles ── */
[data-testid="stChatMessage"] { background: transparent !important; padding: .15rem 0 !important; border: none !important; box-shadow: none !important; }
[data-testid="stChatMessage"] > div { gap: .6rem !important; }

/* ── Chat input ── */
[data-testid="stChatInput"] { border-radius: 12px !important; border: 1.5px solid var(--border) !important; background: var(--white) !important; box-shadow: var(--shadow-sm) !important; }
[data-testid="stChatInput"]:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(79,70,229,.1) !important; }

/* ── Form ── */
[data-testid="stForm"] { border: none !important; padding: 0 !important; background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# HELPERS — HTML components
# ════════════════════════════════════════════════════════
SENT_MAP   = {"angry":"😡 Arrabbiato","negative":"😕 Negativo","neutral":"😐 Neutro","positive":"😊 Positivo"}
SENT_COLOR = {"angry":"#fee2e2","negative":"#fef9c3","neutral":"#f3f4f6","positive":"#d1fae5"}
SENT_TXT   = {"angry":"#991b1b","negative":"#92400e","neutral":"#374151","positive":"#065f46"}
INTENT_LABELS = ai.INTENTS

def _pill(text, bg="#f3f4f6", color="#374151"):
    return f'<span style="display:inline-flex;align-items:center;gap:.25rem;padding:2px 9px;border-radius:5px;font-size:.67rem;font-weight:600;background:{bg};color:{color};letter-spacing:.02em">{text}</span>'

def _prio_pill(p):
    m = {"alta":("#fff1f2","#be123c"),"media":("#fffbeb","#92400e"),"bassa":("#f0fdf4","#166534")}
    bg, tx = m.get(p, ("#f3f4f6","#374151"))
    return _pill(p.upper(), bg, tx)

def _sent_pill(s):
    return _pill(SENT_MAP.get(s,s), SENT_COLOR.get(s,"#f3f4f6"), SENT_TXT.get(s,"#374151"))

def _intent_pill(i):
    return _pill(INTENT_LABELS.get(i, i))

def _metric_card(value, label, sub="", color="var(--text-1)"):
    return f"""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.1rem 1.3rem;box-shadow:var(--shadow-sm)">
  <div style="font-size:1.75rem;font-weight:800;color:{color};line-height:1;letter-spacing:-.03em">{value}</div>
  <div style="font-size:.75rem;font-weight:600;color:var(--text-2);margin-top:.3rem">{label}</div>
  {'<div style="font-size:.7rem;color:var(--text-3);margin-top:.15rem">'+sub+'</div>' if sub else ''}
</div>"""

def _chat_bubble_user(content):
    safe = _html.escape(content).replace("\n","<br>")
    return f"""<div style="display:flex;justify-content:flex-end;align-items:flex-end;gap:.45rem;margin:.25rem 0">
  <div style="max-width:72%;background:var(--text-1);color:#fff;padding:.65rem 1rem;border-radius:16px 16px 3px 16px;font-size:.875rem;line-height:1.65;word-break:break-word">{safe}</div>
  <div style="width:28px;height:28px;background:var(--accent);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:.6rem;font-weight:700;color:#fff">TU</div>
</div>"""

def _chat_bubble_bot(content, intent="", sentiment="", show_meta=False):
    safe = _html.escape(content).replace("\n","<br>")
    meta = ""
    if show_meta and intent:
        meta = f'<div style="margin-top:.4rem;display:flex;gap:.3rem;flex-wrap:wrap">{_intent_pill(intent)}{_sent_pill(sentiment)}</div>'
    return f"""<div style="display:flex;align-items:flex-start;gap:.45rem;margin:.25rem 0">
  <div style="width:28px;height:28px;background:#eef2ff;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:.9rem;border:1.5px solid #c7d2fe">🤖</div>
  <div style="max-width:72%">
    <div style="background:var(--white);border:1.5px solid var(--border);padding:.65rem 1rem;border-radius:3px 16px 16px 16px;font-size:.875rem;line-height:1.65;color:var(--text-1);box-shadow:var(--shadow-sm);word-break:break-word">{safe}</div>
    {meta}
  </div>
</div>"""

def _ticket_card_html(tk, expanded=False):
    prio_color = {"alta":"#ef4444","media":"#f59e0b","bassa":"#10b981"}.get(tk["priority"],"#9aa0b4")
    cat_label  = INTENT_LABELS.get(tk.get("category",""), tk.get("category",""))
    return f"""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow-sm);margin-bottom:.6rem">
  <div style="display:flex;align-items:stretch">
    <div style="width:4px;background:{prio_color};flex-shrink:0"></div>
    <div style="padding:.9rem 1.1rem;flex:1">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.4rem">
        <div style="display:flex;align-items:center;gap:.5rem">
          <span style="font-size:.67rem;font-weight:700;color:var(--text-3);letter-spacing:.06em">#{tk['id']:04d}</span>
          {_prio_pill(tk['priority'])}
          {_intent_pill(tk.get('category',''))}
        </div>
        <span style="font-size:.72rem;color:var(--text-3)">{tk['created_at'][:16]}</span>
      </div>
      <div style="font-size:.92rem;font-weight:700;color:var(--text-1);margin:.35rem 0 .2rem;line-height:1.3">{_html.escape(tk['title'])}</div>
      <div style="font-size:.76rem;color:var(--text-2)">{tk['customer_name'] or 'Anonimo'}{(' · ' + tk['customer_email']) if tk.get('customer_email') else ''}</div>
    </div>
  </div>
</div>"""

def _reset_chat():
    for k in ["conv_id","chat_messages","ticket_opened","ticket_id","customer_name","customer_email"]:
        st.session_state.pop(k, None)

# ════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════
if DEMO_MODE:
    username = "demo"
    user_display = "Demo"
    db.seed_kb("demo")
else:
    # Credentials loaded from env vars (production) or auth_config.yaml (local dev).
    _admin_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    _admin_user = os.getenv("ADMIN_USERNAME", "admin")
    _cookie_key = os.getenv("AUTH_COOKIE_KEY", "")
    if _admin_hash and _cookie_key:
        cfg = {
            "credentials": {
                "usernames": {
                    _admin_user: {
                        "email": f"{_admin_user}@aicare.io",
                        "name": _admin_user.title(),
                        "password": _admin_hash,
                    }
                }
            },
            "cookie": {"name": "cc_agent_auth", "key": _cookie_key, "expiry_days": 7},
        }
    else:
        cfg_path = Path(__file__).parent / "auth_config.yaml"
        with open(cfg_path) as f:
            cfg = yaml.load(f, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        cfg["credentials"], cfg["cookie"]["name"],
        cfg["cookie"]["key"], cfg["cookie"]["expiry_days"]
    )
    authenticator.login()
    status = st.session_state.get("authentication_status")
    if status is False:
        st.error("Username o password non corretti.")
        st.stop()
    if status is None:
        st.markdown("""
<div style="max-width:380px;margin:5rem auto;text-align:center">
  <div style="width:56px;height:56px;background:#eef2ff;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.6rem;margin:0 auto 1.2rem">💬</div>
  <h2 style="font-size:1.35rem;font-weight:800;color:#0d0f1a;margin:0 0 .4rem;letter-spacing:-.025em">AI Customer Care</h2>
  <p style="color:#5a6278;font-size:.875rem;margin:0">Accedi con le credenziali fornite</p>
</div>""", unsafe_allow_html=True)
        st.stop()
    username     = st.session_state.get("username","")
    user_display = st.session_state.get("name", username)
    db.seed_kb(username)

company = db.get_company(username)
co_name = company.get("name","Azienda")
co_initials = "".join(w[0].upper() for w in co_name.split()[:2])

# ════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════
with st.sidebar:
    # Brand area
    st.markdown(f"""
<div style="padding:1.4rem 1.4rem .8rem">
  <div style="display:flex;align-items:center;gap:.7rem">
    <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f46e5,#7c3aed);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:800;color:#fff;letter-spacing:-.5px;flex-shrink:0">{co_initials}</div>
    <div>
      <div style="font-size:.875rem;font-weight:700;color:#fff;line-height:1.2">{co_name}</div>
      <div style="display:flex;align-items:center;gap:.3rem;margin-top:2px">
        <div style="width:6px;height:6px;background:#10b981;border-radius:50%"></div>
        <span style="font-size:.68rem;color:rgba(255,255,255,.4)">Online 24/7</span>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    st.divider()

    if DEMO_MODE:
        st.markdown("""<div style="padding:.2rem 1.4rem .8rem">
  <span style="display:inline-block;padding:3px 9px;background:rgba(79,70,229,.25);border:1px solid rgba(79,70,229,.4);border-radius:5px;font-size:.67rem;font-weight:700;color:#a5b4fc;letter-spacing:.05em">DEMO</span>
</div>""", unsafe_allow_html=True)
        nav = "💬 Chat"
    else:
        st.markdown(f"""<div style="padding:.2rem 1.4rem .6rem">
  <p style="font-size:.68rem;color:rgba(255,255,255,.35);margin:0 0 2px;text-transform:uppercase;letter-spacing:.07em">Operatore</p>
  <p style="font-size:.84rem;font-weight:600;color:rgba(255,255,255,.85);margin:0">{user_display}</p>
</div>""", unsafe_allow_html=True)

        nav = st.radio("",
                       ["💬 Chat", "🏢 Profilo Azienda", "📚 Knowledge Base", "🎫 Ticket", "📊 Dashboard", "⚙️ Setup"],
                       key="nav_cc", label_visibility="collapsed")

        st.divider()
        authenticator.logout(location="sidebar")

    st.markdown("""<div style="padding:.8rem 1.4rem 1.2rem">
  <p style="font-size:.65rem;color:rgba(255,255,255,.18);margin:0;letter-spacing:.03em">AI Customer Care · Enterprise v2</p>
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# MAIN CONTENT WRAPPER
# ════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════
# PAGE — CHAT
# ════════════════════════════════════════════════════════
if nav == "💬 Chat":
    stats = db.get_stats(username)

    if not DEMO_MODE:
        # Page header
        hc1, hc2, hc3, hc4 = st.columns(4, gap="small")
        with hc1: st.markdown(_metric_card(stats["today"], "Conversazioni oggi"), unsafe_allow_html=True)
        with hc2: st.markdown(_metric_card(stats["total"], "Totale conversazioni"), unsafe_allow_html=True)
        with hc3: st.markdown(_metric_card(str(stats["open_tickets"]), "Ticket aperti",
                              color="#ef4444" if stats["open_tickets"] > 0 else "var(--text-1)"), unsafe_allow_html=True)
        with hc4: st.markdown(_metric_card("24/7", "Disponibilità", "Nessun tempo di attesa", "#10b981"), unsafe_allow_html=True)
        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    # Two-column layout: chat | conversations history
    if not DEMO_MODE:
        col_chat, col_hist = st.columns([4, 1], gap="large")
    else:
        col_chat = st.container()
        col_hist = None

    with col_chat:
        # ── Chat container ──
        st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:var(--shadow-md)">""",
                    unsafe_allow_html=True)

        # Chat top bar
        cname_display = st.session_state.get("customer_name","Visitatore")
        conv_active   = "conv_id" in st.session_state

        bar1, bar2 = st.columns([5, 1])
        with bar1:
            if conv_active:
                st.markdown(f"""<div style="padding:.85rem 1.2rem 0">
  <div style="display:flex;align-items:center;gap:.5rem">
    <div style="width:8px;height:8px;background:#10b981;border-radius:50%"></div>
    <span style="font-size:.84rem;font-weight:600;color:var(--text-1)">{_html.escape(cname_display)}</span>
    <span style="font-size:.76rem;color:var(--text-3)">· Conversazione attiva</span>
  </div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style="padding:.85rem 1.2rem 0">
  <span style="font-size:.84rem;font-weight:600;color:var(--text-3)">Nuova conversazione</span>
</div>""", unsafe_allow_html=True)

        with bar2:
            if conv_active:
                if st.button("+ Nuova", use_container_width=True):
                    db.close_conversation(st.session_state.conv_id)
                    _reset_chat()
                    st.rerun()

        st.markdown("<div style='padding:0 1.2rem'>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Start screen (no active conversation) ──
        if not conv_active:
            st.markdown("""<div style="padding:1.2rem 1.4rem 1rem">
  <p style="font-size:.74rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 .9rem">Informazioni cliente</p>""",
                        unsafe_allow_html=True)
            si1, si2 = st.columns(2)
            with si1: cname  = st.text_input("Nome", placeholder="es. Mario Rossi", key="ci_name")
            with si2: cemail = st.text_input("Email", placeholder="es. mario@email.it", key="ci_email")

            sb1, sb2 = st.columns([2,1])
            with sb1:
                if st.button("Avvia chat →", type="primary", use_container_width=True):
                    st.session_state.customer_name  = cname or "Visitatore"
                    st.session_state.customer_email = cemail or ""
                    cid = db.new_conversation(username, st.session_state.customer_name,
                                             st.session_state.customer_email)
                    st.session_state.conv_id        = cid
                    st.session_state.chat_messages  = []
                    st.session_state.ticket_opened  = False
                    st.rerun()
            with sb2:
                if st.button("Salta", use_container_width=True):
                    st.session_state.customer_name  = "Visitatore"
                    st.session_state.customer_email = ""
                    cid = db.new_conversation(username)
                    st.session_state.conv_id        = cid
                    st.session_state.chat_messages  = []
                    st.session_state.ticket_opened  = False
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Active chat ──
        if conv_active:
            st.markdown("<div style='padding:.4rem 1.4rem'>", unsafe_allow_html=True)

            # Welcome message
            if not st.session_state.get("chat_messages"):
                welcome = company.get("welcome_msg","Ciao! Come posso aiutarti oggi?")
                st.markdown(_chat_bubble_bot(welcome), unsafe_allow_html=True)

            # Messages
            for msg in st.session_state.get("chat_messages", []):
                if msg["role"] == "user":
                    st.markdown(_chat_bubble_user(msg["content"]), unsafe_allow_html=True)
                else:
                    st.markdown(
                        _chat_bubble_bot(msg["content"], msg.get("intent",""),
                                         msg.get("sentiment",""), show_meta=not DEMO_MODE),
                        unsafe_allow_html=True
                    )

            # Ticket box
            if st.session_state.get("ticket_opened"):
                tid = st.session_state.get("ticket_id","")
                st.markdown(f"""<div style="display:flex;align-items:flex-start;gap:.7rem;background:#f0f4ff;border:1.5px solid #c7d2fe;border-radius:10px;padding:.8rem 1rem;margin:.6rem 0">
  <div style="font-size:1.2rem;flex-shrink:0">🎫</div>
  <div>
    <div style="font-size:.84rem;font-weight:700;color:#3730a3">Ticket #{tid:04d} aperto</div>
    <div style="font-size:.78rem;color:#4338ca;margin-top:2px">Un operatore ti contatterà al più presto, di solito entro 24 ore.</div>
  </div>
</div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Input
            if prompt := st.chat_input("Scrivi un messaggio..."):
                st.session_state.chat_messages.append({"role":"user","content":prompt})
                db.add_message(st.session_state.conv_id,"user",prompt)

                with st.spinner(""):
                    clf       = ai.classify(prompt)
                    intent    = clf.get("intent","altro")
                    confidence= clf.get("confidence",50)
                    sentiment = clf.get("sentiment","neutral")
                    db.update_conversation_meta(st.session_state.conv_id, sentiment, intent)

                    kb_items = db.get_kb(username)
                    response = ai.generate_response(prompt,
                                                    st.session_state.chat_messages[:-1],
                                                    kb_items, company)

                    if not st.session_state.get("ticket_opened") and ai.should_escalate(clf, company):
                        title    = ai.summarize_for_ticket(st.session_state.chat_messages)
                        priority = ai.priority_from_sentiment(sentiment)
                        tid      = db.create_ticket(username, st.session_state.conv_id, title,
                                                    intent, priority,
                                                    st.session_state.get("customer_name",""),
                                                    st.session_state.get("customer_email",""))
                        st.session_state.ticket_opened = True
                        st.session_state.ticket_id     = tid
                        esc = (f"Capisco la situazione e voglio assicurarmi che tu riceva la migliore assistenza. "
                               f"Ho aperto un ticket per te (#{tid:04d}). "
                               f"Un operatore ti contatterà entro 24 ore.")
                        db.add_message(st.session_state.conv_id,"assistant",esc,intent,confidence,sentiment)
                        st.session_state.chat_messages.append(
                            {"role":"assistant","content":esc,"intent":intent,"confidence":confidence,"sentiment":sentiment})

                db.add_message(st.session_state.conv_id,"assistant",response,intent,confidence,sentiment)
                st.session_state.chat_messages.append(
                    {"role":"assistant","content":response,"intent":intent,"confidence":confidence,"sentiment":sentiment})
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # close chat container

    if col_hist:
        with col_hist:
            st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:14px;padding:1rem;box-shadow:var(--shadow-sm)">
  <p style="font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 .7rem">Recenti</p>""",
                        unsafe_allow_html=True)
            convs = db.get_conversations(username, limit=12)
            for c in convs:
                dot = "🟢" if c["status"]=="open" else "⚫"
                if st.button(f"{dot} {c['customer_name']}\n{c['created_at'][:10]}",
                             key=f"conv_{c['id']}", use_container_width=True):
                    msgs = db.get_messages_verified(c["id"], username)
                    st.session_state.conv_id        = c["id"]
                    st.session_state.customer_name  = c["customer_name"]
                    st.session_state.customer_email = c["customer_email"]
                    st.session_state.chat_messages  = [
                        {"role":m["role"],"content":m["content"],
                         "intent":m.get("intent",""),"confidence":m.get("confidence",0),
                         "sentiment":m.get("sentiment","")}
                        for m in msgs
                    ]
                    st.session_state.ticket_opened = False
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if DEMO_MODE:
        st.markdown(f"""<div style="margin-top:1.2rem;background:#f0f4ff;border:1.5px solid #c7d2fe;border-radius:10px;padding:1rem 1.2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem">
  <span style="font-size:.84rem;color:#3730a3;font-weight:500">Versione demo — KB personalizzabile, ticket, analytics e multi-lingua nella versione completa.</span>
  <a href="mailto:{CONTACT_EMAIL}" style="font-size:.82rem;font-weight:700;color:#4f46e5;text-decoration:none">Contatta {CONTACT_NAME} →</a>
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# PAGE — PROFILO AZIENDA
# ════════════════════════════════════════════════════════
elif nav == "🏢 Profilo Azienda":
    st.markdown("""<h1 style="font-size:1.35rem;font-weight:800;color:var(--text-1);margin:0 0 .4rem;letter-spacing:-.025em">Profilo Azienda</h1>
<p style="font-size:.84rem;color:var(--text-2);margin:0 0 1.4rem">Inserisci le informazioni aziendali. L'agente le userà per rispondere in modo preciso e personalizzato. Puoi compilare manualmente o importare da un documento online.</p>""",
                unsafe_allow_html=True)

    profile = company.get("profile", {})

    tab_manual, tab_import = st.tabs(["✏️ Inserimento manuale", "🔗 Importa da documento"])

    # ── TAB MANUALE ──────────────────────────────────────
    with tab_manual:
        st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.4rem 1.6rem;box-shadow:var(--shadow-sm);margin-top:.8rem">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 1rem">Informazioni azienda</p>""",
                    unsafe_allow_html=True)

        with st.form("profile_form"):
            p1, p2 = st.columns(2)
            with p1:
                p_sector = st.text_input("Settore / Industria",
                                         value=profile.get("sector",""),
                                         placeholder="es. E-commerce moda, SaaS B2B, Ristorazione")
            with p2:
                p_contacts = st.text_input("Contatti principali",
                                           value=profile.get("contacts",""),
                                           placeholder="es. info@azienda.it · 02-1234567 · Via Roma 1, Milano")

            p_description = st.text_area("Descrizione azienda",
                                         value=profile.get("description",""),
                                         height=90,
                                         placeholder="Descrivi l'azienda: cosa fa, chi serve, la sua missione...")

            p_products = st.text_area("Prodotti e servizi",
                                      value=profile.get("products",""),
                                      height=90,
                                      placeholder="Elenca i prodotti/servizi principali con una breve descrizione di ognuno...")

            p3, p4 = st.columns(2)
            with p3:
                p_return = st.text_area("Politica di reso e rimborsi",
                                        value=profile.get("return_policy",""),
                                        height=80,
                                        placeholder="es. Reso gratuito entro 30 giorni, rimborso in 5 giorni lavorativi...")
                p_payment = st.text_area("Metodi di pagamento",
                                         value=profile.get("payment_methods",""),
                                         height=70,
                                         placeholder="es. Carta di credito, PayPal, bonifico, contrassegno...")
            with p4:
                p_shipping = st.text_area("Spedizioni e consegne",
                                          value=profile.get("shipping",""),
                                          height=80,
                                          placeholder="es. Consegna 3-5 giorni lavorativi, gratuita sopra €50...")
                p_hours = st.text_area("Orari e disponibilità",
                                       value=profile.get("hours",""),
                                       height=70,
                                       placeholder="es. Lun-Ven 9-18, assistenza chat 24/7...")

            p_extra = st.text_area("Note aggiuntive / FAQ speciali",
                                   value=profile.get("extra_notes",""),
                                   height=80,
                                   placeholder="Qualsiasi altra informazione utile che l'agente deve conoscere...")

            saved = st.form_submit_button("💾 Salva profilo", type="primary")
            if saved:
                new_profile = {
                    "sector": p_sector, "description": p_description,
                    "products": p_products, "return_policy": p_return,
                    "shipping": p_shipping, "payment_methods": p_payment,
                    "hours": p_hours, "contacts": p_contacts, "extra_notes": p_extra,
                    "imported_text": profile.get("imported_text",""),
                }
                db.save_company_profile(username, new_profile)
                st.success("Profilo salvato. L'agente userà queste informazioni da subito.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Generate KB from profile
        has_profile = any(profile.get(k,"") for k in ["description","products","return_policy","shipping"])
        if has_profile:
            st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
            st.markdown("""<div style="background:#f0f4ff;border:1.5px solid #c7d2fe;border-radius:var(--radius);padding:1.1rem 1.4rem">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.8rem">
    <div>
      <p style="font-size:.84rem;font-weight:700;color:#3730a3;margin:0 0 .2rem">Genera Knowledge Base dal profilo</p>
      <p style="font-size:.78rem;color:#4338ca;margin:0">Claude analizzerà il profilo e genererà automaticamente 15-20 domande e risposte per la KB.</p>
    </div>""", unsafe_allow_html=True)
            if st.button("⚡ Genera KB automatica", type="primary"):
                profile_text = ai.build_profile_context(profile)
                with st.spinner("Claude sta analizzando il profilo e generando la knowledge base..."):
                    items = ai.generate_kb_from_text(profile_text, company.get("language","Italiano"))
                if items:
                    st.session_state["_kb_preview"] = items
                    st.success(f"Generati {len(items)} voci. Rivedi e conferma qui sotto.")
                    st.rerun()
                else:
                    st.error("Generazione fallita. Riprova o aggiungi più dettagli al profilo.")
            st.markdown("</div></div>", unsafe_allow_html=True)

        # KB preview after generation
        if st.session_state.get("_kb_preview"):
            items = st.session_state["_kb_preview"]
            st.markdown(f"""<div style="margin-top:1rem;background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.4rem;box-shadow:var(--shadow-sm)">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
    <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0">{len(items)} voci generate — anteprima</p>
  </div>""", unsafe_allow_html=True)
            for it in items[:5]:
                st.markdown(f"""<div style="background:#f9fafb;border:1px solid var(--border);border-radius:8px;padding:.75rem 1rem;margin-bottom:.5rem">
  <div style="font-size:.67rem;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem">{it.get('category','')}</div>
  <div style="font-size:.84rem;font-weight:600;color:var(--text-1);margin-bottom:.25rem">{_html.escape(it.get('question',''))}</div>
  <div style="font-size:.8rem;color:var(--text-2);line-height:1.55">{_html.escape(it.get('answer','')[:180])}{'…' if len(it.get('answer',''))>180 else ''}</div>
</div>""", unsafe_allow_html=True)
            if len(items) > 5:
                st.caption(f"... e altre {len(items)-5} voci")
            st.markdown("</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Aggiungi tutte alla KB", type="primary", use_container_width=True):
                    for it in items:
                        db.add_kb_item(username, it.get("category","Generale"),
                                       it.get("question",""), it.get("answer",""))
                    del st.session_state["_kb_preview"]
                    st.success(f"{len(items)} voci aggiunte alla Knowledge Base.")
                    st.rerun()
            with c2:
                if st.button("✕ Scarta", use_container_width=True):
                    del st.session_state["_kb_preview"]
                    st.rerun()

    # ── TAB IMPORTA DA URL ───────────────────────────────
    with tab_import:
        st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.4rem 1.6rem;box-shadow:var(--shadow-sm);margin-top:.8rem">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 .4rem">Importa da URL</p>
  <p style="font-size:.82rem;color:var(--text-2);margin:0 0 1rem">Incolla il link a un sito web, un documento Google Docs, Notion o un PDF pubblico. Claude estrarrà automaticamente tutte le informazioni utili.</p>""",
                    unsafe_allow_html=True)

        url_input = st.text_input("", placeholder="https://www.tuaazienda.it   oppure   https://docs.google.com/...",
                                  label_visibility="collapsed")

        col_fetch, col_note = st.columns([1, 3])
        with col_fetch:
            fetch_btn = st.button("🔗 Importa", type="primary", use_container_width=True)
        with col_note:
            st.markdown("<p style='font-size:.76rem;color:var(--text-3);padding-top:.55rem'>Funziona con: siti web, Google Docs (pubblici), PDF pubblici, pagine Notion pubbliche</p>",
                        unsafe_allow_html=True)

        if fetch_btn and url_input:
            with st.spinner("Scaricando e analizzando il documento..."):
                try:
                    text = ai.fetch_url_text(url_input)
                    if len(text) < 100:
                        st.error("Contenuto insufficiente. Il documento potrebbe essere protetto o vuoto.")
                    else:
                        st.session_state["_imported_text"] = text
                        st.session_state["_imported_url"]  = url_input
                        st.success(f"Documento importato ({len(text):,} caratteri estratti).")
                        st.rerun()
                except Exception as e:
                    st.error(f"Errore nell'importazione: {e}")

        # Preview imported text
        if st.session_state.get("_imported_text"):
            text = st.session_state["_imported_text"]
            url  = st.session_state.get("_imported_url","")
            st.markdown(f"""<div style="margin-top:1rem;background:#f9fafb;border:1.5px solid var(--border);border-radius:8px;padding:.9rem 1.1rem">
  <div style="font-size:.67rem;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:.4rem">Anteprima testo estratto · {len(text):,} caratteri</div>
  <div style="font-size:.8rem;color:var(--text-2);line-height:1.6;max-height:180px;overflow:hidden">{_html.escape(text[:600])}{'…' if len(text)>600 else ''}</div>
</div>""", unsafe_allow_html=True)

            ia1, ia2, ia3 = st.columns(3)
            with ia1:
                if st.button("⚡ Genera KB da questo testo", type="primary", use_container_width=True):
                    with st.spinner("Claude sta generando la knowledge base..."):
                        items = ai.generate_kb_from_text(text, company.get("language","Italiano"))
                    if items:
                        st.session_state["_kb_preview_import"] = items
                        st.success(f"Generati {len(items)} voci.")
                        st.rerun()
                    else:
                        st.error("Generazione fallita.")
            with ia2:
                if st.button("💾 Salva come contesto agente", use_container_width=True):
                    new_profile = dict(profile)
                    new_profile["imported_text"] = text
                    db.save_company_profile(username, new_profile)
                    st.success("Testo salvato come contesto. L'agente lo userà nelle risposte.")
            with ia3:
                if st.button("✕ Rimuovi", use_container_width=True):
                    st.session_state.pop("_imported_text", None)
                    st.session_state.pop("_imported_url",  None)
                    st.rerun()

        # KB preview from import
        if st.session_state.get("_kb_preview_import"):
            items = st.session_state["_kb_preview_import"]
            st.markdown(f"""<div style="margin-top:1rem;background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.4rem;box-shadow:var(--shadow-sm)">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 .8rem">{len(items)} voci generate da documento</p>""",
                        unsafe_allow_html=True)
            for it in items[:5]:
                st.markdown(f"""<div style="background:#f9fafb;border:1px solid var(--border);border-radius:8px;padding:.75rem 1rem;margin-bottom:.5rem">
  <div style="font-size:.67rem;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.2rem">{it.get('category','')}</div>
  <div style="font-size:.84rem;font-weight:600;color:var(--text-1);margin-bottom:.2rem">{_html.escape(it.get('question',''))}</div>
  <div style="font-size:.8rem;color:var(--text-2);line-height:1.55">{_html.escape(it.get('answer','')[:180])}{'…' if len(it.get('answer',''))>180 else ''}</div>
</div>""", unsafe_allow_html=True)
            if len(items) > 5:
                st.caption(f"... e altre {len(items)-5} voci")
            st.markdown("</div>", unsafe_allow_html=True)

            d1, d2 = st.columns(2)
            with d1:
                if st.button("✅ Aggiungi alla KB", type="primary", use_container_width=True, key="add_kb_import"):
                    for it in items:
                        db.add_kb_item(username, it.get("category","Generale"),
                                       it.get("question",""), it.get("answer",""))
                    del st.session_state["_kb_preview_import"]
                    st.success(f"{len(items)} voci aggiunte alla Knowledge Base.")
                    st.rerun()
            with d2:
                if st.button("✕ Scarta", use_container_width=True, key="disc_kb_import"):
                    del st.session_state["_kb_preview_import"]
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# PAGE — KNOWLEDGE BASE
# ════════════════════════════════════════════════════════
elif nav == "📚 Knowledge Base":
    st.markdown("""<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.4rem">
  <h1 style="font-size:1.35rem;font-weight:800;color:var(--text-1);margin:0;letter-spacing:-.025em">Knowledge Base</h1>
</div>""", unsafe_allow_html=True)

    kb = db.get_kb(username)

    # Add form
    with st.container():
        st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.3rem 1.5rem;box-shadow:var(--shadow-sm);margin-bottom:1.4rem">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 .9rem">Aggiungi risposta</p>""", unsafe_allow_html=True)
        ka1, ka2 = st.columns([1, 3])
        CATS = ["Ordini","Resi","Rimborsi","Spedizioni","Pagamenti","Account","Garanzia","Prodotti","Servizi","Prenotazioni","Altro"]
        with ka1: new_cat = st.selectbox("Categoria", CATS)
        with ka2: new_q   = st.text_input("Domanda del cliente", placeholder="es. Come traccio il mio ordine?")
        new_a = st.text_area("Risposta", placeholder="Scrivi la risposta completa che l'agente darà al cliente...", height=90)
        if st.button("Aggiungi voce →", type="primary"):
            if new_q and new_a:
                db.add_kb_item(username, new_cat, new_q, new_a)
                st.success("Voce aggiunta.")
                st.rerun()
            else: st.error("Compila domanda e risposta.")
        st.markdown("</div>", unsafe_allow_html=True)

    if not kb:
        st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:2rem;text-align:center;box-shadow:var(--shadow-sm)">
  <div style="font-size:2rem;margin-bottom:.5rem">📚</div>
  <p style="font-size:.92rem;font-weight:600;color:var(--text-1);margin:0 0 .3rem">Knowledge base vuota</p>
  <p style="font-size:.8rem;color:var(--text-2);margin:0">Aggiungi risposte qui sopra oppure carica gli esempi demo.</p>
</div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
        if st.button("Carica 10 esempi demo", type="primary"):
            for cat, q, a in db.DEMO_KB:
                db.add_kb_item(username, cat, q, a)
            st.rerun()
    else:
        search_kb = st.text_input("", placeholder="🔍  Cerca nella knowledge base...", label_visibility="collapsed")
        items = [it for it in kb if not search_kb or
                 search_kb.lower() in (it["question"]+it["answer"]+it["category"]).lower()]

        cats = sorted(set(it["category"] for it in items))
        for cat in cats:
            cat_items = [it for it in items if it["category"]==cat]
            st.markdown(f"""<p style="font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:1.2rem 0 .5rem">{cat} &nbsp;·&nbsp; {len(cat_items)} voci</p>""",
                        unsafe_allow_html=True)
            for it in cat_items:
                c1, c2 = st.columns([6,1])
                with c1:
                    st.markdown(f"""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:8px;padding:.8rem 1rem;box-shadow:var(--shadow-sm)">
  <div style="font-size:.875rem;font-weight:600;color:var(--text-1);margin-bottom:.25rem">{_html.escape(it['question'])}</div>
  <div style="font-size:.8rem;color:var(--text-2);line-height:1.55">{_html.escape(it['answer'][:180])}{'…' if len(it['answer'])>180 else ''}</div>
</div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)
                    if st.button("✕", key=f"del_kb_{it['id']}", help="Elimina"):
                        db.delete_kb_item(it["id"])
                        st.rerun()

# ════════════════════════════════════════════════════════
# PAGE — TICKET
# ════════════════════════════════════════════════════════
elif nav == "🎫 Ticket":
    open_t    = db.get_tickets(username, status="aperto")
    resolved_t = db.get_tickets(username, status="risolto")

    st.markdown(f"""<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.4rem">
  <h1 style="font-size:1.35rem;font-weight:800;color:var(--text-1);margin:0;letter-spacing:-.025em">Ticket</h1>
  <div style="display:flex;gap:.5rem">
    <span style="background:#fff1f2;color:#be123c;border-radius:6px;padding:3px 10px;font-size:.75rem;font-weight:700">{len(open_t)} aperti</span>
    <span style="background:#f0fdf4;color:#166534;border-radius:6px;padding:3px 10px;font-size:.75rem;font-weight:700">{len(resolved_t)} risolti</span>
  </div>
</div>""", unsafe_allow_html=True)

    t1, t2 = st.tabs([f"Aperti ({len(open_t)})", f"Risolti ({len(resolved_t)})"])

    with t1:
        if not open_t:
            st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:2.5rem;text-align:center;box-shadow:var(--shadow-sm)">
  <div style="font-size:2rem;margin-bottom:.5rem">✅</div>
  <p style="font-size:.92rem;font-weight:600;color:var(--text-1);margin:0 0 .2rem">Nessun ticket aperto</p>
  <p style="font-size:.8rem;color:var(--text-2);margin:0">L'agente sta gestendo tutto correttamente.</p>
</div>""", unsafe_allow_html=True)
        else:
            for tk in open_t:
                st.markdown(_ticket_card_html(tk), unsafe_allow_html=True)
                with st.expander(f"Gestisci ticket #{tk['id']:04d}"):
                    if tk.get("customer_email"):
                        st.markdown(f"<span style='font-size:.8rem;color:var(--text-2)'>📧 {tk['customer_email']}</span>",
                                    unsafe_allow_html=True)
                    if tk.get("conversation_id"):
                        msgs = db.get_messages_verified(tk["conversation_id"], username)
                        if msgs:
                            st.markdown("<p style='font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3);margin:.6rem 0 .4rem'>Cronologia conversazione</p>",
                                        unsafe_allow_html=True)
                            for m in msgs:
                                icon = "👤" if m["role"]=="user" else "🤖"
                                st.markdown(f"<p style='font-size:.82rem;color:var(--text-2);margin:.2rem 0'><strong style='color:var(--text-1)'>{icon}</strong> {_html.escape(m['content'])}</p>",
                                            unsafe_allow_html=True)
                    g1, g2, g3 = st.columns([2,1,1])
                    with g1:
                        notes = st.text_area("Note interne", value=tk.get("notes",""),
                                             key=f"notes_{tk['id']}", height=65, label_visibility="visible")
                    with g2:
                        new_p = st.selectbox("Priorità", ["alta","media","bassa"],
                                             index=["alta","media","bassa"].index(tk["priority"]),
                                             key=f"prio_{tk['id']}")
                        if st.button("Salva", key=f"upd_{tk['id']}"):
                            db.update_ticket_priority(tk["id"], new_p)
                            db.update_ticket_notes(tk["id"], notes)
                            st.success("Aggiornato.")
                            st.rerun()
                    with g3:
                        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
                        if st.button("✅ Risolvi", key=f"res_{tk['id']}", type="primary", use_container_width=True):
                            db.resolve_ticket(tk["id"], notes)
                            st.success(f"Ticket #{tk['id']:04d} risolto.")
                            st.rerun()

    with t2:
        if not resolved_t:
            st.info("Nessun ticket risolto ancora.")
        else:
            for tk in resolved_t:
                st.markdown(f"""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow-sm);margin-bottom:.5rem;opacity:.7">
  <div style="display:flex;align-items:stretch">
    <div style="width:4px;background:#10b981;flex-shrink:0"></div>
    <div style="padding:.8rem 1.1rem;flex:1;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.4rem">
      <div>
        <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.2rem">
          <span style="font-size:.67rem;font-weight:700;color:var(--text-3)">#{tk['id']:04d}</span>
          <span style="background:#d1fae5;color:#065f46;padding:1px 7px;border-radius:4px;font-size:.65rem;font-weight:700">✅ RISOLTO</span>
        </div>
        <div style="font-size:.875rem;font-weight:600;color:var(--text-1)">{_html.escape(tk['title'])}</div>
        <div style="font-size:.74rem;color:var(--text-3);margin-top:2px">{tk['customer_name']} · Risolto {(tk['resolved_at'] or '')[:10]}</div>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# PAGE — DASHBOARD
# ════════════════════════════════════════════════════════
elif nav == "📊 Dashboard":
    st.markdown("""<h1 style="font-size:1.35rem;font-weight:800;color:var(--text-1);margin:0 0 1.4rem;letter-spacing:-.025em">Dashboard</h1>""",
                unsafe_allow_html=True)

    stats = db.get_stats(username)

    m1, m2, m3, m4 = st.columns(4, gap="small")
    with m1: st.markdown(_metric_card(stats["today"],   "Conversazioni oggi"), unsafe_allow_html=True)
    with m2: st.markdown(_metric_card(stats["total"],   "Totale conversazioni"), unsafe_allow_html=True)
    with m3: st.markdown(_metric_card(str(stats["open_tickets"]), "Ticket aperti",
                          color="#ef4444" if stats["open_tickets"]>0 else "var(--text-1)"), unsafe_allow_html=True)
    with m4: st.markdown(_metric_card(str(stats["resolved_tickets"]), "Ticket risolti", color="#10b981"), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.4rem;box-shadow:var(--shadow-sm)">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 1rem">Intent più frequenti</p>""",
                    unsafe_allow_html=True)
        if stats["intents"]:
            total_i = sum(r["n"] for r in stats["intents"])
            for r in stats["intents"]:
                pct   = int(r["n"]/total_i*100) if total_i else 0
                label = INTENT_LABELS.get(r["intent"], r["intent"])
                st.markdown(f"""<div style="margin-bottom:.7rem">
  <div style="display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:4px">
    <span style="color:var(--text-1);font-weight:500">{label}</span>
    <span style="color:var(--text-3);font-weight:600">{r['n']} · {pct}%</span>
  </div>
  <div style="background:#f0f2f6;border-radius:4px;height:5px">
    <div style="width:{pct}%;background:var(--accent);height:5px;border-radius:4px;transition:width .3s"></div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Nessun dato ancora.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.4rem;box-shadow:var(--shadow-sm)">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 1rem">Sentiment clienti</p>""",
                    unsafe_allow_html=True)
        if stats["sentiments"]:
            total_s = sum(r["n"] for r in stats["sentiments"])
            colors  = {"angry":"#ef4444","negative":"#f59e0b","neutral":"#6366f1","positive":"#10b981"}
            for r in stats["sentiments"]:
                pct   = int(r["n"]/total_s*100) if total_s else 0
                label = SENT_MAP.get(r["sentiment"], r["sentiment"])
                color = colors.get(r["sentiment"],"#6366f1")
                st.markdown(f"""<div style="margin-bottom:.7rem">
  <div style="display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:4px">
    <span style="color:var(--text-1);font-weight:500">{label}</span>
    <span style="color:var(--text-3);font-weight:600">{r['n']} · {pct}%</span>
  </div>
  <div style="background:#f0f2f6;border-radius:4px;height:5px">
    <div style="width:{pct}%;background:{color};height:5px;border-radius:4px"></div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("Nessun dato ancora.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow-sm)">
  <div style="padding:1.1rem 1.4rem;border-bottom:1.5px solid var(--border)">
    <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0">Ultime conversazioni</p>
  </div>""", unsafe_allow_html=True)

    convs = db.get_conversations(username, limit=8)
    if convs:
        rows = "".join(f"""<tr style="border-bottom:1px solid #f0f2f6">
  <td style="padding:.6rem 1.4rem;font-size:.84rem;font-weight:600;color:var(--text-1)">{c['customer_name']}</td>
  <td style="padding:.6rem .8rem;font-size:.8rem;color:var(--text-2)">{c['customer_email'] or '—'}</td>
  <td style="padding:.6rem .8rem">{_intent_pill(c['intent'])}</td>
  <td style="padding:.6rem .8rem">{_sent_pill(c['sentiment'])}</td>
  <td style="padding:.6rem 1.4rem;font-size:.78rem;color:var(--text-3)">{c['created_at'][:16]}</td>
</tr>""" for c in convs)
        st.markdown(f"""<table style="width:100%;border-collapse:collapse">
<thead><tr style="border-bottom:1.5px solid var(--border)">
  <th style="padding:.5rem 1.4rem;text-align:left;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3)">Cliente</th>
  <th style="padding:.5rem .8rem;text-align:left;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3)">Email</th>
  <th style="padding:.5rem .8rem;text-align:left;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3)">Intent</th>
  <th style="padding:.5rem .8rem;text-align:left;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3)">Sentiment</th>
  <th style="padding:.5rem 1.4rem;text-align:left;font-size:.67rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:var(--text-3)">Data</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# PAGE — SETUP
# ════════════════════════════════════════════════════════
elif nav == "⚙️ Setup":
    st.markdown("""<h1 style="font-size:1.35rem;font-weight:800;color:var(--text-1);margin:0 0 1.4rem;letter-spacing:-.025em">Configurazione</h1>""",
                unsafe_allow_html=True)

    st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.4rem 1.6rem;box-shadow:var(--shadow-sm);margin-bottom:1.2rem">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 1rem">Identità agente</p>""",
                unsafe_allow_html=True)

    with st.form("setup_form"):
        f1, f2 = st.columns(2)
        with f1: s_name = st.text_input("Nome azienda", value=company.get("name",""))
        with f2:
            tones = ["Professionale","Cordiale","Formale","Informale","Empatico"]
            s_tone = st.selectbox("Tono", tones,
                                  index=tones.index(company.get("tone","Professionale"))
                                  if company.get("tone") in tones else 0)
        f3, f4 = st.columns(2)
        with f3:
            langs = ["Italiano","Inglese","Spagnolo","Francese","Tedesco"]
            s_lang = st.selectbox("Lingua", langs,
                                  index=langs.index(company.get("language","Italiano"))
                                  if company.get("language") in langs else 0)
        with f4:
            s_thr = st.slider("Soglia escalation automatica (%)", 30, 90, step=5,
                              value=company.get("escalation_threshold", 60),
                              help="Sotto questa confidenza il bot apre un ticket automaticamente.")
        s_angry   = st.checkbox("Apri ticket automatico per clienti arrabbiati",
                                value=bool(company.get("escalate_angry",1)))
        s_welcome = st.text_area("Messaggio di benvenuto", height=80,
                                 value=company.get("welcome_msg","Ciao! Come posso aiutarti oggi?"))

        if st.form_submit_button("Salva configurazione →", type="primary"):
            db.save_company(username, s_name, s_tone, s_lang, s_thr, s_angry, s_welcome)
            st.success("Configurazione salvata.")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""<div style="background:var(--white);border:1.5px solid var(--border);border-radius:var(--radius);padding:1.2rem 1.5rem;box-shadow:var(--shadow-sm)">
  <p style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3);margin:0 0 .6rem">Zona pericolosa</p>
  <p style="font-size:.82rem;color:var(--text-2);margin:0 0 .8rem">Resetta la knowledge base agli esempi demo. L'operazione è irreversibile.</p>""",
                unsafe_allow_html=True)
    if st.button("🗑️ Resetta KB agli esempi demo"):
        for it in db.get_kb(username): db.delete_kb_item(it["id"])
        for cat, q, a in db.DEMO_KB: db.add_kb_item(username, cat, q, a)
        st.success("KB resettata.")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
