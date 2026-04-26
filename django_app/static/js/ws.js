(function(){
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  if(!user || !['citizen','officer','admin'].includes(user.role)) return;
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${location.host}/ws/notifications/?uid=${encodeURIComponent(user.id)}`);
  socket.onmessage = (evt) => {
    try { const data = JSON.parse(evt.data); if(window.Civic){window.Civic.toast(data.message || 'New update');} } catch {}
  };
})();
