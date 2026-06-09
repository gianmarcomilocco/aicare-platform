/*!
 * AICare Widget v1.1
 * Embeddable AI Customer Care — one line installation
 * Usage: <script src="https://your-api.com/widget.js" data-key="YOUR_API_KEY" data-name="Acme Srl"></script>
 */
(function (w, d) {
  'use strict';

  var me = d.currentScript || (function () {
    var s = d.getElementsByTagName('script');
    return s[s.length - 1];
  })();

  var cfg = {
    key:         me.getAttribute('data-key')         || '',
    api:         me.getAttribute('data-api')         || 'https://api.aicare.io',
    name:        me.getAttribute('data-name')        || 'Assistente AI',
    greeting:    me.getAttribute('data-greeting')    || 'Ciao! Come posso aiutarti oggi?',
    color:       me.getAttribute('data-color')       || '#4f46e5',
    position:    me.getAttribute('data-position')    || 'right',
    placeholder: me.getAttribute('data-placeholder') || 'Scrivi un messaggio...',
    lang:        me.getAttribute('data-lang')        || 'it',
    privacyUrl:  me.getAttribute('data-privacy-url') || '',
  };

  var CONSENT_KEY = 'aic_consent_' + cfg.key;

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function hexToRgb(hex) {
    var r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
    return r+','+g+','+b;
  }
  function shade(hex, amount) {
    var n = parseInt(hex.replace('#',''),16);
    var r = Math.min(255,Math.max(0,(n>>16)+amount));
    var g = Math.min(255,Math.max(0,((n>>8)&0xff)+amount));
    var b = Math.min(255,Math.max(0,(n&0xff)+amount));
    return '#'+((1<<24)+(r<<16)+(g<<8)+b).toString(16).slice(1);
  }

  var side  = cfg.position === 'left' ? 'left' : 'right';
  var oside = cfg.position === 'left' ? 'right' : 'left';

  var css = [
    '#aic{all:initial;position:fixed;bottom:24px;'+side+':24px;z-index:2147483647;display:flex;flex-direction:column;align-items:'+(side==='left'?'flex-start':'flex-end')+'}',
    '#aic *{box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Inter","Segoe UI",Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}',
    '#aic-btn{width:56px;height:56px;border-radius:50%;background:'+cfg.color+';box-shadow:0 4px 24px rgba('+hexToRgb(cfg.color)+',.45),0 2px 8px rgba(0,0,0,.12);cursor:pointer;border:none;outline:none;display:flex;align-items:center;justify-content:center;transition:transform .2s cubic-bezier(.34,1.56,.64,1),box-shadow .2s;position:relative}',
    '#aic-btn:hover{transform:scale(1.1);box-shadow:0 6px 28px rgba('+hexToRgb(cfg.color)+',.55),0 3px 12px rgba(0,0,0,.15)}',
    '#aic-btn:active{transform:scale(.95)}',
    '#aic-btn-icon{transition:opacity .2s,transform .2s;position:absolute}',
    '#aic-btn-icon.hidden{opacity:0;transform:scale(.5) rotate(45deg)}',
    '#aic-btn svg{width:24px;height:24px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}',
    '#aic-badge{position:absolute;top:-2px;'+oside+':-2px;width:18px;height:18px;background:#ef4444;border-radius:50%;font-size:11px;font-weight:700;color:#fff;display:flex;align-items:center;justify-content:center;border:2px solid #fff;display:none}',
    '#aic-win{width:380px;max-width:calc(100vw - 32px);height:600px;max-height:calc(100dvh - 96px);background:#fff;border-radius:20px;box-shadow:0 24px 64px rgba(0,0,0,.14),0 8px 24px rgba(0,0,0,.08);margin-bottom:12px;display:flex;flex-direction:column;overflow:hidden;transition:opacity .25s cubic-bezier(.4,0,.2,1),transform .25s cubic-bezier(.4,0,.2,1);transform-origin:bottom '+side+';opacity:0;transform:scale(.88) translateY(12px);pointer-events:none}',
    '#aic-win.open{opacity:1;transform:scale(1) translateY(0);pointer-events:all}',
    '#aic-hdr{flex-shrink:0;padding:16px 18px;background:'+cfg.color+';display:flex;align-items:center;justify-content:space-between;gap:8px}',
    '#aic-hdr-l{display:flex;align-items:center;gap:10px}',
    '#aic-av{width:38px;height:38px;background:rgba(255,255,255,.18);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;border:1.5px solid rgba(255,255,255,.25)}',
    '#aic-hdr-info{display:flex;flex-direction:column;gap:2px}',
    '#aic-hdr-name{font-size:15px;font-weight:700;color:#fff;line-height:1.2;letter-spacing:-.01em}',
    '#aic-hdr-sub{display:flex;align-items:center;gap:5px;font-size:12px;color:rgba(255,255,255,.75)}',
    '#aic-dot{width:7px;height:7px;background:#4ade80;border-radius:50%;box-shadow:0 0 0 2px rgba(74,222,128,.3)}',
    '#aic-cls{background:rgba(255,255,255,.15);border:none;border-radius:8px;width:30px;height:30px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;line-height:1;transition:background .15s;flex-shrink:0}',
    '#aic-cls:hover{background:rgba(255,255,255,.28)}',

    /* Consent overlay */
    '#aic-consent{position:absolute;inset:0;background:#fff;z-index:10;display:flex;align-items:center;justify-content:center;padding:24px}',
    '#aic-consent-box{max-width:300px;width:100%;display:flex;flex-direction:column;gap:16px}',
    '#aic-consent h3{margin:0;font-size:1.05rem;font-weight:700;color:#111;letter-spacing:-.02em}',
    '#aic-consent p{margin:0;font-size:.84rem;color:#5a6278;line-height:1.55}',
    '#aic-consent a{font-size:.82rem;color:'+cfg.color+';text-decoration:underline}',
    '#aic-consent-chk-row{display:flex;align-items:flex-start;gap:10px;cursor:pointer}',
    '#aic-consent-chk-row input{margin-top:3px;accent-color:'+cfg.color+';cursor:pointer;flex-shrink:0}',
    '#aic-consent-chk-row span{font-size:.83rem;color:#374151;line-height:1.45}',
    '#aic-consent-btn{padding:11px 20px;background:'+cfg.color+';color:#fff;border:none;border-radius:10px;font-size:.88rem;font-weight:600;cursor:pointer;transition:background .15s,opacity .15s}',
    '#aic-consent-btn:disabled{opacity:.45;cursor:not-allowed}',
    '#aic-consent-btn:not(:disabled):hover{background:'+shade(cfg.color,-20)+'}',
    '#aic-consent-note{font-size:.75rem;color:#9ca3af;text-align:center;line-height:1.4}',

    '#aic-msgs{flex:1;overflow-y:auto;padding:16px 14px 8px;display:flex;flex-direction:column;gap:2px;scroll-behavior:smooth}',
    '#aic-msgs::-webkit-scrollbar{width:3px}',
    '#aic-msgs::-webkit-scrollbar-thumb{background:#e5e7eb;border-radius:4px}',
    '.am{display:flex;align-items:flex-end;gap:6px;max-width:85%;margin:2px 0}',
    '.am.b{align-self:flex-start}',
    '.am.u{align-self:flex-end;flex-direction:row-reverse}',
    '.am-av{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;background:#f1f5f9}',
    '.am-bbl{padding:10px 14px;font-size:14px;line-height:1.55;word-break:break-word;letter-spacing:.01em}',
    '.am.b .am-bbl{background:#f1f5f9;color:#111;border-radius:4px 16px 16px 16px}',
    '.am.u .am-bbl{background:'+cfg.color+';color:#fff;border-radius:16px 4px 16px 16px}',
    '.am-sep{align-self:center;font-size:11px;color:#9ca3af;padding:8px 0 4px;font-weight:500;letter-spacing:.02em}',
    '#aic-typing{display:flex;align-items:flex-end;gap:6px;max-width:85%;margin:2px 0;align-self:flex-start}',
    '#aic-typing .am-av{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;background:#f1f5f9}',
    '.aic-dots{background:#f1f5f9;border-radius:4px 16px 16px 16px;padding:12px 16px;display:flex;gap:4px;align-items:center}',
    '.aic-d{width:6px;height:6px;background:#9ca3af;border-radius:50%;animation:aic-b .9s infinite}',
    '.aic-d:nth-child(2){animation-delay:.15s}',
    '.aic-d:nth-child(3){animation-delay:.3s}',
    '@keyframes aic-b{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}',
    '#aic-inp-wrap{flex-shrink:0;padding:10px 12px;border-top:1px solid #f1f5f9;background:#fff;display:flex;gap:8px;align-items:flex-end}',
    '#aic-inp{flex:1;border:1.5px solid #e5e7eb;border-radius:12px;padding:10px 14px;font-size:14px;resize:none;outline:none;height:42px;max-height:120px;color:#111;background:#fff;line-height:1.45;transition:border-color .15s}',
    '#aic-inp:focus{border-color:'+cfg.color+';box-shadow:0 0 0 3px rgba('+hexToRgb(cfg.color)+',.12)}',
    '#aic-inp::placeholder{color:#9ca3af}',
    '#aic-snd{width:42px;height:42px;border-radius:12px;background:'+cfg.color+';border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s,transform .1s}',
    '#aic-snd:hover{background:'+shade(cfg.color,-25)+'}',
    '#aic-snd:active{transform:scale(.92)}',
    '#aic-snd:disabled{opacity:.5;cursor:default}',
    '#aic-snd svg{width:18px;height:18px;fill:none;stroke:#fff;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}',
    '#aic-ftr{flex-shrink:0;text-align:center;padding:6px 12px;border-top:1px solid #f8f9fa;background:#fafafa;display:flex;align-items:center;justify-content:center;gap:12px}',
    '#aic-ftr a{font-size:11px;color:#c4cad4;text-decoration:none;letter-spacing:.02em}',
    '#aic-ftr a:hover{color:#9ca3af}',
    '.aic-ticket{background:#eef2ff;border:1px solid #c7d2fe;border-radius:10px;padding:10px 12px;margin:6px 0;font-size:13px;color:#3730a3;display:flex;gap:8px;align-items:flex-start;align-self:stretch}',
    '.aic-ticket-icon{font-size:16px;flex-shrink:0;margin-top:1px}',
    '@media(max-width:480px){#aic{bottom:0;'+side+':0;width:100%;align-items:stretch}#aic-win{width:100%;max-width:100%;height:85dvh;max-height:100dvh;border-radius:20px 20px 0 0;margin:0;transform-origin:bottom center}#aic-btn{position:fixed;bottom:16px;'+side+':16px}}',
  ].join('');

  var styleEl = d.createElement('style');
  styleEl.textContent = css;
  d.head.appendChild(styleEl);

  // ── Consent screen HTML ───────────────────────────────
  var privacyLink = cfg.privacyUrl
    ? '<a href="' + esc(cfg.privacyUrl) + '" target="_blank" rel="noopener noreferrer">Leggi la nostra Privacy Policy</a>'
    : '<span style="font-size:.82rem;color:#9ca3af">Privacy Policy fornita dall\'azienda</span>';

  var consentHtml =
    '<div id="aic-consent">' +
      '<div id="aic-consent-box">' +
        '<h3>Prima di iniziare</h3>' +
        '<p>Chattando con il nostro assistente, i tuoi messaggi vengono trattati per fornirti supporto. I dati non vengono ceduti a terzi e puoi richiederne la cancellazione in qualsiasi momento.</p>' +
        privacyLink +
        '<label id="aic-consent-chk-row">' +
          '<input type="checkbox" id="aic-chk">' +
          '<span>Ho letto l\'informativa e accetto il trattamento dei miei dati per ricevere assistenza.</span>' +
        '</label>' +
        '<button id="aic-consent-btn" disabled>Inizia la chat</button>' +
        '<p id="aic-consent-note">Puoi richiedere la cancellazione dei tuoi dati scrivendo all\'azienda.</p>' +
      '</div>' +
    '</div>';

  // ── Footer HTML ───────────────────────────────────────
  var ftrLinks = '<a href="https://aicare.io" target="_blank" rel="noopener">Powered by AICare</a>';
  if (cfg.privacyUrl) {
    ftrLinks += '<a href="' + esc(cfg.privacyUrl) + '" target="_blank" rel="noopener noreferrer">Privacy</a>';
  }

  // ── Build DOM ─────────────────────────────────────────
  var root = d.createElement('div');
  root.id = 'aic';
  root.innerHTML =
    '<div id="aic-win">' +
      '<div id="aic-hdr">' +
        '<div id="aic-hdr-l">' +
          '<div id="aic-av">🤖</div>' +
          '<div id="aic-hdr-info">' +
            '<div id="aic-hdr-name">' + esc(cfg.name) + '</div>' +
            '<div id="aic-hdr-sub"><div id="aic-dot"></div>Online ora</div>' +
          '</div>' +
        '</div>' +
        '<button id="aic-cls" onclick="window.__aicToggle()">&#x2715;</button>' +
      '</div>' +
      consentHtml +
      '<div id="aic-msgs"></div>' +
      '<div id="aic-inp-wrap">' +
        '<textarea id="aic-inp" placeholder="' + esc(cfg.placeholder) + '" rows="1"></textarea>' +
        '<button id="aic-snd">' +
          '<svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>' +
        '</button>' +
      '</div>' +
      '<div id="aic-ftr">' + ftrLinks + '</div>' +
    '</div>' +
    '<button id="aic-btn">' +
      '<span id="aic-btn-icon">' +
        '<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' +
      '</span>' +
      '<div id="aic-badge">1</div>' +
    '</button>';

  d.body.appendChild(root);

  // ── State ─────────────────────────────────────────────
  var state = {
    open:        false,
    convId:      null,
    typing:      false,
    initialized: false,
    consented:   false,
  };

  var msgsEl    = d.getElementById('aic-msgs');
  var inpEl     = d.getElementById('aic-inp');
  var sndEl     = d.getElementById('aic-snd');
  var winEl     = d.getElementById('aic-win');
  var btnEl     = d.getElementById('aic-btn');
  var consentEl = d.getElementById('aic-consent');
  var chkEl     = d.getElementById('aic-chk');
  var conBtnEl  = d.getElementById('aic-consent-btn');

  // ── Consent logic ─────────────────────────────────────
  function hasConsent() {
    try {
      var stored = localStorage.getItem(CONSENT_KEY);
      if (!stored) return false;
      var obj = JSON.parse(stored);
      // Consent valid for 365 days
      return obj && obj.ts && (Date.now() - obj.ts) < 365 * 24 * 3600 * 1000;
    } catch (e) { return false; }
  }

  function saveConsent() {
    try {
      localStorage.setItem(CONSENT_KEY, JSON.stringify({ ts: Date.now(), v: '1.1' }));
    } catch (e) {}
  }

  function showChat() {
    state.consented = true;
    if (consentEl) consentEl.style.display = 'none';
    if (!state.initialized) {
      state.initialized = true;
      setTimeout(function () { addMsg('bot', cfg.greeting); }, 280);
    }
    setTimeout(function () { inpEl.focus(); }, 300);
  }

  if (chkEl) {
    chkEl.addEventListener('change', function () {
      conBtnEl.disabled = !this.checked;
    });
  }

  if (conBtnEl) {
    conBtnEl.addEventListener('click', function () {
      if (!chkEl || !chkEl.checked) return;
      saveConsent();
      showChat();
    });
  }

  // ── Message rendering ─────────────────────────────────
  function addMsg(role, text) {
    var wrap = d.createElement('div');
    wrap.className = 'am ' + (role === 'user' ? 'u' : 'b');
    var av   = role === 'user' ? '👤' : '🤖';
    var safe = esc(text).replace(/\n/g, '<br>');
    wrap.innerHTML =
      '<div class="am-av">' + av + '</div>' +
      '<div class="am-bbl">' + safe + '</div>';
    msgsEl.appendChild(wrap);
    msgsEl.scrollTop = msgsEl.scrollHeight;
    return wrap;
  }

  function addTicketNotice(ticketId) {
    var el = d.createElement('div');
    el.className = 'aic-ticket';
    el.innerHTML =
      '<div class="aic-ticket-icon">🎫</div>' +
      '<div><strong>Ticket #' + ticketId + ' aperto</strong><br>Un operatore ti risponderà presto, di solito entro 24 ore.</div>';
    msgsEl.appendChild(el);
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  function showTyping() {
    if (d.getElementById('aic-typing')) return;
    var el = d.createElement('div');
    el.id = 'aic-typing';
    el.innerHTML =
      '<div class="am-av">🤖</div>' +
      '<div class="aic-dots"><div class="aic-d"></div><div class="aic-d"></div><div class="aic-d"></div></div>';
    msgsEl.appendChild(el);
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  function removeTyping() {
    var el = d.getElementById('aic-typing');
    if (el) el.remove();
  }

  // ── Send message ──────────────────────────────────────
  function send() {
    var text = inpEl.value.trim();
    if (!text || state.typing) return;
    if (text.length > 2000) { text = text.slice(0, 2000); }
    inpEl.value = '';
    inpEl.style.height = '42px';
    sndEl.disabled = true;
    addMsg('user', text);
    state.typing = true;
    showTyping();

    var body = { message: text, customer_name: 'Visitatore', consented: state.consented };
    if (state.convId) body.conversation_id = state.convId;

    fetch(cfg.api + '/v1/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', 'X-Api-Key': cfg.key },
      body:    JSON.stringify(body),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      state.convId = data.conversation_id;
      removeTyping();
      addMsg('bot', data.response || 'Risposta non disponibile.');
      if (data.ticket_id) addTicketNotice(data.ticket_id);
    })
    .catch(function () {
      removeTyping();
      addMsg('bot', 'Si è verificato un errore. Riprova tra qualche istante.');
    })
    .finally(function () {
      state.typing   = false;
      sndEl.disabled = false;
      msgsEl.scrollTop = msgsEl.scrollHeight;
    });
  }

  // ── Toggle open/close ─────────────────────────────────
  w.__aicToggle = function () {
    state.open = !state.open;
    if (state.open) {
      winEl.classList.add('open');
      if (hasConsent()) {
        showChat();
      }
      // else: consent screen is already visible by default
    } else {
      winEl.classList.remove('open');
    }
  };

  btnEl.onclick = w.__aicToggle;

  // ── Input events ──────────────────────────────────────
  sndEl.onclick = send;

  inpEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });

  inpEl.addEventListener('input', function () {
    this.style.height = '42px';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
  });

}(window, document));
