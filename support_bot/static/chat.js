// Chatbot front — robuste, avec historique + topics + CSRF + fallback
(function () {
  const $ = (id) => document.getElementById(id);

  const widget = $('chat-widget');
  const toggle = $('chatToggle');
  const body = $('chatBody');
  const convo = $('conversation');
  const form = $('chatForm');
  const input = $('messageInput');
  const quick = $('quickActions');

  const endpoint = widget?.dataset?.endpoint || '/api/ask/';

  /* CSRF (Django) */
  function getCookie(name){
    let v=null; if(document.cookie && document.cookie!==''){
      for(const raw of document.cookie.split(';')){
        const c=raw.trim();
        if(c.substring(0,name.length+1)===name+'='){v=decodeURIComponent(c.substring(name.length+1));break;}
      }
    } return v;
  }
  const CSRFTOKEN = getCookie('csrftoken');

  /* Historique local */
  const history = []; // {role:'user'|'assistant', content:'...'}

  /* Helpers UI */
  function sanitize(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}
  function addMsg(text, cls){
    if(!convo) return;
    const el=document.createElement('div');
    el.className='msg '+cls;
    el.innerHTML=sanitize(text);
    convo.appendChild(el);
    convo.scrollTop=convo.scrollHeight;
    history.push({role: cls==='user' ? 'user' : 'assistant', content: text});
    if(history.length>20) history.shift();
  }
  function showTyping(){
    const el=document.createElement('div');
    el.className='typing';
    el.innerHTML='<span></span><i></i>';
    convo.appendChild(el);
    convo.scrollTop=convo.scrollHeight;
    return el;
  }
  function getAnswer(data){
    return data?.answer ?? data?.response ?? data?.message ?? data?.reply ?? data?.text ?? null;
  }

  /* Envoi principal */
  async function sendQuestion(question, topic=null){
    if(!question) return;
    addMsg(question,'user');
    const typing=showTyping();

    const payload = {
      question,
      topic,
      history: history.slice(-10)
    };

    const baseHeaders = CSRFTOKEN ? {'X-CSRFToken': CSRFTOKEN} : {};
    try{
      // 1) JSON
      let res = await fetch(endpoint, {
        method:'POST',
        headers:{'Content-Type':'application/json', ...baseHeaders},
        body: JSON.stringify(payload)
      });

      // 2) fallback urlencoded si backend n’accepte pas JSON
      if(!res.ok && (res.status===415 || res.status===400)){
        res = await fetch(endpoint, {
          method:'POST',
          headers:{'Content-Type':'application/x-www-form-urlencoded', ...baseHeaders},
          body: 'message='+encodeURIComponent(question)
        });
      }

      const data = await res.json().catch(()=> ({}));
      typing.remove();

      const ans = getAnswer(data);
      if(ans){
        addMsg(ans,'bot');
      }else if(data?.error){
        addMsg('⚠️ '+data.error,'bot');
      }else{
        addMsg("Désolé, je n'ai pas compris 🤖",'bot');
      }

      // mini-sources
      if(Array.isArray(data?.context) && data.context.length){
        const tip=document.createElement('div');
        tip.className='msg bot';
        tip.style.fontSize='12px'; tip.style.color='#64748b';
        tip.innerHTML=sanitize('Sources :\n'+data.context.slice(0,2).map(c=>`• ${c.question} → ${c.answer}`).join('\n')).replace(/\n/g,'<br>');
        convo.appendChild(tip); convo.scrollTop=convo.scrollHeight;
      }
    }catch(err){
      typing.remove();
      addMsg('Erreur réseau : '+(err?.message||err),'bot');
    }
  }

  /* Toggle open/close */
  if(toggle){
    toggle.addEventListener('click',()=>{
      const open=widget.classList.toggle('chat-open');
      widget.classList.toggle('chat-closed', !open);
      toggle.setAttribute('aria-expanded', open?'true':'false');
      body.hidden=!open;
      if(open && convo.children.length===0){
        addMsg("👋 Bonjour ! Je suis le support TIC. Choisissez une action rapide ou posez votre question.","bot");
      }
    });
  }

  /* Quick actions → topic */
  if(quick){
    quick.addEventListener('click',(e)=>{
      const el=e.target;
      if(el && el.classList.contains('qa-btn')){
        const txt=el.innerText.trim();
        const topic = /d[ée]pannage/i.test(txt) ? 'depannage_pc'
                    : /logiciel/i.test(txt)     ? 'installation_logiciel'
                    : /wi-?fi/i.test(txt)       ? 'wifi'
                    : null;
        sendQuestion(txt, topic);
      }
    });
  }

  /* Form submit */
  if(form){
    form.addEventListener('submit',(e)=>{
      e.preventDefault();
      const q=input.value.trim();
      if(!q) return;
      sendQuestion(q,null);
      input.value='';
    });
  }

  /* Init */
  document.addEventListener('DOMContentLoaded',()=>{
    const y=document.getElementById('year'); if(y) y.textContent=new Date().getFullYear();
    // Ouvrir et message d’accueil une seule fois
    if(convo && convo.children.length===0){
      body.hidden=false;
      widget.classList.add('chat-open');
      addMsg("👋 Bonjour ! Je suis le support TIC. Choisissez une action rapide ou posez votre question.","bot");
    }
  });
})();
