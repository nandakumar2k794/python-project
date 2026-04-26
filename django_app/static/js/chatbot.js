(function(){
  const w=document.getElementById("chat-widget");
  if(!w)return;
  
  let isOpen=false;
  let chatHistory=JSON.parse(localStorage.getItem("chatHistory")||"[]");
  
  w.innerHTML=`<style>
    @keyframes slidUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
    @keyframes fadeInScale{from{opacity:0;transform:scale(.9)}to{opacity:1;transform:scale(1)}}
    .chat-widget-wrapper{position:fixed;bottom:4px;right:4px;z-index:40;width:360px;max-width:90vw}
    .chat-widget-btn{position:absolute;bottom:0;right:0;width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#00C896,#00D9A3);border:none;cursor:pointer;box-shadow:0 8px 24px rgba(0,200,150,.3);transition:all 250ms;display:flex;align-items:center;justify-content:center;color:white;font-size:24px}
    .chat-widget-btn:hover{transform:scale(1.1);box-shadow:0 12px 32px rgba(0,200,150,.4)}
    .chat-widget-btn:active{transform:scale(0.95)}
    .chat-box{position:absolute;bottom:70px;right:0;width:100%;background:rgba(22,27,34,.95);border:1px solid rgba(0,200,150,.2);border-radius:12px;padding:16px;animation:slidUp 300ms ease-out;box-shadow:0 16px 48px rgba(0,0,0,.5);backdrop-filter:blur(10px)}
    .chat-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,.1)}
    .chat-header h3{margin:0;font-size:18px;color:#E6EDF3;font-family:"Syne",sans-serif}
    .chat-close{background:none;border:none;color:#93a4b8;cursor:pointer;font-size:20px;transition:color 250ms}
    .chat-close:hover{color:#E6EDF3}
    .chat-log{height:240px;overflow-y:auto;margin-bottom:12px;padding:8px 0;display:flex;flex-direction:column;gap:8px}
    .chat-log::-webkit-scrollbar{width:6px}
    .chat-log::-webkit-scrollbar-track{background:transparent}
    .chat-log::-webkit-scrollbar-thumb{background:rgba(0,200,150,.3);border-radius:3px}
    .chat-log::-webkit-scrollbar-thumb:hover{background:rgba(0,200,150,.5)}
    .chat-msg{padding:8px 12px;border-radius:8px;font-size:13px;line-height:1.4;animation:fadeInScale 200ms ease-out}
    .chat-msg.user{background:rgba(15,76,129,.4);color:#58c4dc;margin-left:24px;border-left:3px solid #0F4C81}
    .chat-msg.ai{background:rgba(0,200,150,.1);color:#00D9A3;margin-right:24px;border-left:3px solid #00C896}
    .chat-msg.error{background:rgba(255,107,53,.1);color:#ff7f66;border-left:3px solid #FF6B35}
    .chat-input-area{display:flex;gap:8px}
    .chat-input{flex:1;padding:8px 12px;background:#0f1724;border:1px solid #2d3f54;border-radius:6px;color:#E6EDF3;font-size:13px;font-family:inherit;transition:all 250ms}
    .chat-input:focus{outline:none;border-color:#00C896;box-shadow:0 0 0 2px rgba(0,200,150,.1)}
    .chat-input::placeholder{color:#6e8ba3}
    .chat-send-btn{padding:8px 12px;background:#00C896;color:white;border:none;border-radius:6px;cursor:pointer;font-weight:600;transition:all 250ms;font-size:13px}
    .chat-send-btn:hover{background:#00D9A3;transform:translateY(-1px)}
    .chat-send-btn:active{transform:translateY(0)}
    .chat-send-btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
    .chat-typing{display:flex;gap:4px;align-items:center;padding:8px 12px}
    .chat-typing span{width:8px;height:8px;border-radius:50%;background:#00C896;animation:pulse 1.2s infinite}
    .chat-typing span:nth-child(2){animation-delay:150ms}
    .chat-typing span:nth-child(3){animation-delay:300ms}
  </style>
  <div class="chat-widget-wrapper">
    <div class="chat-box hidden" id="chat-box">
      <div class="chat-header">
        <h3>💬 AI Assistant</h3>
        <button class="chat-close" id="chat-close">✕</button>
      </div>
      <div class="chat-log" id="chat-log"></div>
      <div class="chat-input-area">
        <input class="chat-input" id="chat-input" placeholder="Ask about issues..." autocomplete="off">
        <button class="chat-send-btn" id="chat-send">Send</button>
      </div>
    </div>
    <button class="chat-widget-btn" id="chat-toggle">💬</button>
  </div>`;
  
  const box=document.getElementById("chat-box");
  const log=document.getElementById("chat-log");
  const inp=document.getElementById("chat-input");
  const sendBtn=document.getElementById("chat-send");
  const toggleBtn=document.getElementById("chat-toggle");
  const closeBtn=document.getElementById("chat-close");
  
  const addMsg=(text,type="ai")=>{
    const m=document.createElement("div");
    m.className=`chat-msg ${type}`;
    m.textContent=text;
    log.appendChild(m);
    log.scrollTop=log.scrollHeight;
  };
  
  const addTyping=()=>{
    const t=document.createElement("div");
    t.className="chat-typing";
    t.innerHTML="<span></span><span></span><span></span>";
    t.id="chat-typing";
    log.appendChild(t);
    log.scrollTop=log.scrollHeight;
  };
  
  const removeTyping=()=>{
    const t=document.getElementById("chat-typing");
    if(t)t.remove();
  };
  
  const sendMessage=async()=>{
    const q=inp.value.trim();
    if(!q)return;
    inp.value="";
    sendBtn.disabled=true;
    addMsg(q,"user");
    chatHistory.push({role:"user",text:q});
    addTyping();
    try{
      const token=localStorage.getItem("access");
      const r=await fetch("/api/dashboard/ai/chat/",{
        method:"POST",
        headers:{"Content-Type":"application/json",...(token?{"Authorization":`Bearer ${token}`}:{})},
        body:JSON.stringify({message:q,context:{history:chatHistory.slice(-5)}})
      });
      if(!r.ok)throw new Error(`API error: ${r.status}`);
      const d=await r.json();
      removeTyping();
      const reply=d.reply||d.response||"Sorry, I couldn't process that.";
      addMsg(reply,"ai");
      chatHistory.push({role:"ai",text:reply});
    }catch(e){
      removeTyping();
      addMsg(e.message||"Connection error","error");
      chatHistory.push({role:"error",text:e.message});
    }finally{
      sendBtn.disabled=false;
      inp.focus();
    }
    localStorage.setItem("chatHistory",JSON.stringify(chatHistory.slice(-20)));
  };
  
  toggleBtn.addEventListener("click",()=>{
    isOpen=!isOpen;
    box.classList.toggle("hidden",!isOpen);
    toggleBtn.style.transform=isOpen?"scale(1.1)":"scale(1)";
    if(isOpen){
      inp.focus();
      if(chatHistory.length===0)addMsg("Hi! I'm here to help with civic issues. Ask me anything about reported problems, status updates, or how to submit issues."
, "ai");
      else chatHistory.slice(-5).forEach(h=>addMsg(h.text,h.role));
    }
  });
  
  closeBtn.addEventListener("click",()=>{
    isOpen=false;
    box.classList.add("hidden");
  });
  
  const send=()=>sendMessage();
  sendBtn.addEventListener("click",send);
  inp.addEventListener("keypress",(e)=>{if(e.key==="Enter")send()});
})();