/* SoundSpace PWA layer: service worker, install button, and browser-side fallbacks for /api/lyrics and /api/youtube
   so the installed Android app works without the Python server. If the server is reachable it is still used first. */
(()=>{
'use strict';
if('serviceWorker'in navigator&&(location.protocol==='https:'||location.hostname==='localhost')){addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(e=>console.warn('SW registration failed',e)))}
const KEY='ss_yt_key',nativeFetch=window.fetch.bind(window);let serverUp=null;
const J=(o,s=200)=>new Response(JSON.stringify(o),{status:s,headers:{'Content-Type':'application/json'}});
const kind=u=>{try{const p=new URL(typeof u==='string'?u:u.url,location.href);if(p.origin!==location.origin)return null;return p.pathname.endsWith('/api/youtube')?'yt':p.pathname.endsWith('/api/lyrics')?'ly':null}catch{return null}};
/* ---- lyrics (port of server ranking) ---- */
const clean=s=>s.replace(/\([^)]*(official|lyrics?|audio|video|visualizer|remaster|hd|4k)[^)]*\)/gi,' ').replace(/\[[^\]]*(official|lyrics?|audio|video|visualizer|remaster|hd|4k)[^\]]*\]/gi,' ').replace(/\s+/g,' ').trim().replace(/^[-| ]+|[-| ]+$/g,'');
const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,''),toks=s=>new Set(String(s||'').toLowerCase().match(/[a-z0-9]+/g)||[]);
async function lyrics(track,artist){const cl=clean(track),qs=[];
 for(const t of new Set([track,cl])){if(artist)qs.push({track_name:t,artist_name:artist});qs.push({track_name:t},{q:(artist+' '+t).trim()},{q:t})}
 const res=await Promise.allSettled(qs.map(q=>nativeFetch('https://lrclib.net/api/search?'+new URLSearchParams(q),{headers:{Accept:'application/json'}}).then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()})));
 if(res.every(r=>r.status==='rejected'))return J({error:'LRCLIB lookup failed: check your internet connection.'},502);
 const found=new Map();res.forEach(r=>{if(r.status==='fulfilled'&&Array.isArray(r.value))r.value.forEach(x=>{if(x.id!=null)found.set(x.id,x)})});
 const A=toks(cl),score=x=>{const B=toks(x.trackName),u=new Set([...A,...B]),i=[...A].filter(z=>B.has(z)).length,ov=i/Math.max(1,u.size),art=artist&&(norm(artist).includes(norm(x.artistName))||norm(x.artistName).includes(norm(artist)))?1:0;return[+(norm(x.trackName)===norm(cl)),art,ov,+!!x.syncedLyrics,+!!x.plainLyrics]};
 const cmp=(a,b)=>{for(let i=0;i<5;i++)if(a[i]!==b[i])return b[i]-a[i];return 0};
 const m=[...found.values()].map(x=>[x,score(x)]).sort((p,q)=>cmp(p[1],q[1])).slice(0,12).filter(([,s])=>s[0]||s[2]>=.34).map(([x])=>x);
 return J({item:m[0]||null,matches:m,count:m.length})}
/* ---- YouTube (direct, using a key the user stores on this device) ---- */
function askKey(msg){return new Promise(res=>{const d=document.createElement('dialog');d.style.cssText='background:var(--s1,#1c1e21);color:var(--tx,#eee);border:1px solid var(--bd,#333);border-radius:18px;padding:20px;width:min(440px,92vw)';
 d.innerHTML=`<form method="dialog"><h3 style="margin:0 0 8px">YouTube API key</h3><p style="color:var(--mu,#999);font-size:13px;margin:0 0 10px">${msg||'Paste your own YouTube Data API v3 key. It is stored only on this device and sent only to Google. Restrict it to YouTube Data API v3 and to this app’s web address in Google Cloud Console.'}</p><input name="k" autocomplete="off" spellcheck="false" placeholder="AIza…" value="${(localStorage.getItem(KEY)||'').replace(/"/g,'')}" style="width:100%;padding:10px 12px;border-radius:10px;border:1px solid var(--bd,#333);background:var(--bg,#141517);color:inherit"><div style="display:flex;gap:8px;justify-content:flex-end;margin-top:14px"><button type="button" id="ssKc" style="padding:8px 15px;border-radius:999px;border:1px solid var(--bd,#333);background:var(--s2,#26292d);color:inherit">Cancel</button><button value="ok" style="padding:8px 18px;border-radius:999px;border:0;background:var(--ac,#b8f43c);color:var(--acx,#10140a);font-weight:700">Save key</button></div></form>`;
 document.body.append(d);d.querySelector('#ssKc').onclick=()=>d.close('x');d.onclose=()=>{const k=d.querySelector('input').value.trim();d.remove();if(d.returnValue==='ok'&&k){localStorage.setItem(KEY,k);res(k)}else res(null)};d.showModal()})}
async function youtube(url){const p=new URL(url,location.href).searchParams,q=(p.get('q')||'').trim();if(!q)return J({error:'Enter a search term.'},400);
 let key=localStorage.getItem(KEY);if(!key)key=await askKey();if(!key)return J({error:'Add a YouTube Data API key to search YouTube. Open Settings → “Set YouTube key”.'},503);
 const n=Math.max(1,Math.min(50,+p.get('maxResults')||25)),q2={part:'snippet',type:'video',videoEmbeddable:'true',maxResults:String(n),q,key};if(p.get('pageToken'))q2.pageToken=p.get('pageToken');
 let r;try{r=await nativeFetch('https://www.googleapis.com/youtube/v3/search?'+new URLSearchParams(q2))}catch(e){return J({error:'Cannot reach YouTube: check your internet connection.'},502)}
 const data=await r.json().catch(()=>({}));
 if(!r.ok){const m=data.error?.message||'YouTube API HTTP '+r.status;if((data.error?.errors||[]).some(e=>/keyInvalid|badRequest/.test(e.reason))&&/key/i.test(m))localStorage.removeItem(KEY);return J({error:m,details:data},r.status)}
 const ids=(data.items||[]).map(x=>x.id?.videoId).filter(Boolean);
 if(ids.length)try{const d=await(await nativeFetch('https://www.googleapis.com/youtube/v3/videos?'+new URLSearchParams({part:'contentDetails',id:ids.join(','),key}))).json(),dur={};
  (d.items||[]).forEach(v=>{const m=/^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/.exec(v.contentDetails?.duration||'');if(m)dur[v.id]=(+m[1]||0)*3600+(+m[2]||0)*60+(+m[3]||0)});
  data.items.forEach(x=>x.contentDetails={durationSeconds:dur[x.id?.videoId]||0})}catch{}
 return J(data)}
/* ---- fetch shim: server first, browser fallback ---- */
window.fetch=async function(input,init){const k=kind(input);if(!k)return nativeFetch(input,init);
 const url=typeof input==='string'?input:input.url;
 if(serverUp!==false){try{const r=await nativeFetch(input,init),ct=r.headers.get('content-type')||'';
  if(ct.includes('json')&&r.status!==404&&r.status!==405&&!(k==='yt'&&r.status===503&&localStorage.getItem(KEY))){serverUp=true;return r}
  if(ct.includes('json')&&r.status===503&&!localStorage.getItem(KEY)&&serverUp===true)return r;
  serverUp=false}catch{serverUp=false}}
 return k==='ly'?lyrics(new URL(url,location.href).searchParams.get('track')||'',new URL(url,location.href).searchParams.get('artist')||''):youtube(url)};
/* ---- Settings: key button ---- */
function addKeyButton(){const h=[...document.querySelectorAll('#view h2')].find(x=>x.textContent.trim()==='YouTube streaming');if(!h||document.getElementById('ssKeyBtn'))return;
 const b=document.createElement('button');b.id='ssKeyBtn';b.className='ghost';b.textContent=localStorage.getItem(KEY)?'Change YouTube key on this device':'Set YouTube key on this device';b.onclick=async()=>{const k=await askKey();if(k){b.textContent='Change YouTube key on this device';alert('YouTube key saved on this device.')}};
 const bar=document.createElement('div');bar.className='bar';bar.append(b);h.nextElementSibling?.after(bar)}
addEventListener('DOMContentLoaded',()=>{const v=document.getElementById('view');if(v)new MutationObserver(addKeyButton).observe(v,{childList:true,subtree:true});addKeyButton()});
/* ---- Install button (Android Chrome) ---- */
let ip=null;const standalone=()=>matchMedia('(display-mode: standalone)').matches||navigator.standalone;
addEventListener('beforeinstallprompt',e=>{e.preventDefault();ip=e;if(standalone()||sessionStorage.getItem('ssInstallHide'))return;
 const b=document.createElement('div');b.style.cssText='position:fixed;left:12px;bottom:calc(130px + env(safe-area-inset-bottom,0px));z-index:60;display:flex;gap:6px;background:var(--s2,#26292d);border:1px solid var(--bd,#333);border-radius:999px;padding:6px 8px 6px 14px;align-items:center;color:var(--tx,#eee);box-shadow:0 8px 24px #0006';
 b.innerHTML='<span>Install UNHEARD.</span><button id="ssI" style="border:0;border-radius:999px;padding:6px 14px;background:var(--ac,#b8f43c);color:var(--acx,#10140a);font-weight:700" >Install UNHEARD.</button><button id="ssX" aria-label="Dismiss" style="border:0;background:none;color:inherit;font-size:18px;padding:2px 8px">×</button>';
 document.body.append(b);b.querySelector('#ssI').onclick=async()=>{b.remove();ip.prompt();await ip.userChoice;ip=null};b.querySelector('#ssX').onclick=()=>{sessionStorage.setItem('ssInstallHide','1');b.remove()}});
addEventListener('appinstalled',()=>document.querySelectorAll('[id=ssI]').forEach(x=>x.parentElement.remove()));
})();
