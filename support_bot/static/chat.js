// chat.js
// Widget logic: open/close, send message to /api/ask/, render conversation.
// Designed to be simple, robust and easy to customize.

(function () {
  const toggle = document.getElementById('chatToggle');
  const widget = document.getElementById('chat-widget');
  const body = document.getElementById('chatBody');
  const convo = document.getElementById('conversation');
  const form = document.getElementById('chatForm');
  const input = document.getElementById('messageInput');
  const quick = document.getElementById('quickActions');

  // initial messages
  const welcomeBot = `Bonjour ! Je suis le support TIC. Choisissez une action rapide ou tapez votre question.`;
  function botWelcome() {
    addBotMsg(welcomeBot);
  }

  // Helpers to create message nodes
  function addBotMsg(text) {
    const el = document.createElement('div');
    el.className = 'msg bot';
    el.innerText = text;
    convo.appendChild(el);
    convo.scrollTop = convo.scrollHeight;
  }
  function addUserMsg(text) {
    const el = document.createElement('div');
    el.className = 'msg user';
    el.innerText = text;
    convo.appendChild(el);
    convo.scrollTop = convo.scrollHeight;
  }
  function addTyping() {
    const el = document.createElement('div');
    el.className = 'msg bot typing';
    el.innerText = '…';
    convo.appendChild(el);
    convo.scrollTop = convo.scrollHeight;
    return el;
  }

  // Toggle widget open/close
  toggle.addEventListener('click', () => {
    const open = widget.classList.toggle('chat-open');
    widget.classList.toggle('chat-closed', !open);
    const expanded = open;
    toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    if (expanded) {
      body.hidden = false;
      // if first open and no messages, show welcome
      if (convo.children.length === 0) botWelcome();
      input.focus();
    } else {
      body.hidden = true;
    }
  });

  // Quick action buttons
  quick.addEventListener('click', (ev) => {
    if (ev.target && ev.target.classList.contains('qa-btn')) {
      const q = ev.target.innerText.trim();
      sendQuestion(q);
    }
  });

  // Submit handler
  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    sendQuestion(q);
    input.value = '';
  });

  // Main function to call backend
  async function sendQuestion(question) {
    addUserMsg(question);
    const typingEl = addTyping();

    try {
      const res = await fetch('/api/ask/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // if CSRF used on server, include token (we read it in template)
          'X-CSRFToken': typeof CSRFTOKEN !== 'undefined' ? CSRFTOKEN : ''
        },
        body: JSON.stringify({ question })
      });

      if (!res.ok) {
        const txt = await res.text();
        typingEl.innerText = 'Erreur : ' + (res.status + ' ' + txt);
        return;
      }

      const data = await res.json();
      // remove typing
      typingEl.remove();

      if (data.answer) {
        addBotMsg(data.answer);
      } else if (data.error) {
        addBotMsg('Erreur : ' + data.error);
      } else {
        addBotMsg('Aucune réponse reçue.');
      }

      // Optionally render top context (first 2 items) as small captions
      if (Array.isArray(data.context) && data.context.length > 0) {
        const ctx = data.context.slice(0, 2).map(c => `• ${c.question} → ${c.answer}`).join('\n');
        const ctr = document.createElement('div');
        ctr.style.fontSize = '12px';
        ctr.style.color = '#6c757d';
        ctr.style.whiteSpace = 'pre-wrap';
        ctr.innerText = 'Sources:\n' + ctx;
        convo.appendChild(ctr);
        convo.scrollTop = convo.scrollHeight;
      }

    } catch (err) {
      typingEl.innerText = 'Erreur réseau : ' + (err.message || err);
    }
  }

  // Expose simple API if needed
  window.chatWidget = {
    open: () => { if (!widget.classList.contains('chat-open')) toggle.click(); },
    close: () => { if (widget.classList.contains('chat-open')) toggle.click(); },
    send: (q) => sendQuestion(q)
  };

  // Auto open small on first load (optional)
  // toggle.click();

})();
