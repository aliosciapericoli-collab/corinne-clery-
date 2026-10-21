import json, html, base64, os, sys

g = json.load(open('gobbo2.json'))
e = html.escape
VID = {'01': '../pilot/inserti_gatti/Gatti-Inserto-01-La-villetta.mp4',
       '02': '../pilot/inserti_gatti/Gatti-Inserto-02-Il-Vivione.mp4',
       '03': '../pilot/inserti_gatti/Gatti-Inserto-03-Val-Paisco.mp4',
       '04': '../pilot/inserti_gatti/Gatti-Inserto-04-Il-carcere.mp4'}
embed = '--no-video' not in sys.argv
vids = {}
if embed:
    for k, p in VID.items():
        vids[k] = 'data:video/mp4;base64,' + base64.b64encode(open(p, 'rb').read()).decode()

blocks = []
for i, b in enumerate(g['blocks']):
    if b['t'] == 'ins':
        blocks.append(f'<div class="b ins" data-i="{i}" data-ins="{b["n"]}" data-sec="{b["sec"]}">'
                      f'<div class="lab">▶ INSERTO {b["n"]} · {b["sec"]} SECONDI</div><div class="it">{e(b["title"])}</div>'
                      f'<div class="hint">pausa · poi riprendi</div></div>')
    else:
        lab = 'IN CAMERA' if b['t'] == 'cam' else 'VOCE · SULLE IMMAGINI'
        cls = 'cam' if b['t'] == 'cam' else 'vo'
        txt = e(b['text'])
        if txt.startswith('['):
            txt = f'<em>{txt}</em>'
        blocks.append(f'<div class="b {cls}" data-i="{i}"><div class="lab">{lab}</div><p>{txt}</p></div>')
pron = ' · '.join(f'{e(a)} = <b>{e(c)}</b>' for a, c in g['pron'])

page = f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gobbo · {e(g["title"])}</title>
<style>
:root{{--fs:64px;--speed:1}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:#000;color:#fff;font-family:Georgia,"Times New Roman",serif;height:100%}}
#bar{{position:fixed;top:0;left:0;right:0;z-index:20;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 14px;background:#111;border-bottom:1px solid #333;font:14px/1.3 system-ui,sans-serif}}
#bar b{{color:#e3a35f}}
#bar button{{font:600 14px system-ui,sans-serif;background:#222;color:#fff;border:1px solid #444;border-radius:4px;padding:6px 10px;cursor:pointer}}
#bar button.on{{background:#e3a35f;color:#111;border-color:#e3a35f}}
#bar .sp{{flex:1}}
#bar.hide{{display:none}}
#scroller{{position:fixed;inset:0;overflow-y:scroll;scrollbar-width:none}}
#scroller::-webkit-scrollbar{{display:none}}
#text{{max-width:1500px;margin:0 auto;padding:55vh 6vw 90vh;font-size:var(--fs);line-height:1.38}}
body.mirror #text{{transform:scaleX(-1)}}
.head{{font-family:system-ui,sans-serif;font-size:calc(var(--fs)*.38);color:#aaa;margin-bottom:1.2em}}
.head h1{{font-family:Georgia,serif;font-size:calc(var(--fs)*1.1);color:#fff;margin:.1em 0 .2em}}
.pron{{font-size:calc(var(--fs)*.42);color:#ddd;border:2px solid #444;padding:.5em .7em;border-radius:6px;line-height:1.5}}
.pron b{{color:#ffd28a;font-weight:700}}
.b{{margin:1.1em 0}}
.lab{{font-family:system-ui,sans-serif;font-weight:700;font-size:calc(var(--fs)*.3);letter-spacing:.14em;color:#888;margin-bottom:.2em}}
.cam .lab{{color:#e3a35f}}
.b p{{margin:0}}
.vo p{{color:#d8e6ff}}
em{{color:#9a9a9a}}
.ins{{background:#a3221a;border-radius:10px;padding:.35em .6em;font-family:system-ui,sans-serif}}
.ins .lab{{color:#fff;font-size:calc(var(--fs)*.42)}}
.ins .it{{font-size:calc(var(--fs)*.6);font-weight:600}}
.ins .hint{{font-size:calc(var(--fs)*.32);opacity:.8}}
#line{{position:fixed;left:0;right:0;top:40vh;height:0;border-top:3px solid rgba(227,163,95,.55);z-index:10;pointer-events:none}}
#line::before{{content:"▶";position:absolute;left:8px;top:-.62em;color:#e3a35f;font-size:28px}}
#ov{{position:fixed;inset:0;z-index:30;display:none;align-items:center;justify-content:center;flex-direction:column;gap:16px;background:rgba(0,0,0,.82);font-family:system-ui,sans-serif}}
#ov.show{{display:flex}}
#ov .t{{font-size:4vw;font-weight:700;color:#ff6b5e;letter-spacing:.08em}}
#ov .c{{font-size:16vw;font-weight:800;line-height:1}}
#ov video{{width:min(60vw,900px);max-height:45vh;background:#000;border:2px solid #a3221a}}
#ov small{{font-size:18px;color:#aaa}}
</style></head><body>
<div id="bar"><b>GOBBO</b><span>{e(g["title"])}</span>
<button id="play">▶ Avvia (spazio)</button>
<button id="slow">− velocità</button><span id="spv">1.0</span><button id="fast">+ velocità</button>
<button id="small">A−</button><button id="big">A+</button>
<button id="mir">Specchio</button><button id="auto" class="on">Pausa inserti</button><button id="vid" class="{'on' if embed else ''}">Mostra video inserti</button>
<button id="top">Da capo</button><span class="sp"></span><button id="hidebar">Nascondi barra (H)</button></div>
<div id="line"></div>
<div id="scroller"><div id="text">
<div class="head">PARLANE CON CORINNE CLÉRY · STORIA 2<h1>{e(g["title"])}</h1>{e(g["where"])}</div>
<div class="pron">{pron}</div>
{''.join(blocks)}
<div class="b cam"><div class="lab">FINE</div><p><em>Fine della storia.</em></p></div>
</div></div>
<div id="ov"><div class="t" id="ovt"></div><video id="ovv" muted playsinline></video><div class="c" id="ovc"></div><small>tocca o premi spazio per saltare</small></div>
<script>
const VIDS={json.dumps(vids)};
const sc=document.getElementById('scroller'),root=document.documentElement;
let playing=false,speed=1,fs=64,last=0,acc=0,pausedUntil=null,done=new Set(),timer=null;
const $=id=>document.getElementById(id);
function setFs(v){{fs=Math.max(28,Math.min(140,v));root.style.setProperty('--fs',fs+'px')}}
function setSpeed(v){{speed=Math.max(.2,Math.min(4,Math.round(v*10)/10));$('spv').textContent=speed.toFixed(1)}}
function play(on){{playing=on;$('play').textContent=on?'❚❚ Pausa (spazio)':'▶ Avvia (spazio)';$('play').classList.toggle('on',on);last=performance.now()}}
function loop(t){{
  const dt=(t-last)/1000; last=t;
  if(playing && !$('ov').classList.contains('show')){{
    acc+=dt*speed*fs*0.55; const step=Math.floor(acc); if(step){{sc.scrollTop+=step; acc-=step;}}
    if($('auto').classList.contains('on')) checkIns();
  }}
  requestAnimationFrame(loop);
}}
function checkIns(){{
  const ly=window.innerHeight*0.40;
  document.querySelectorAll('.ins').forEach(el=>{{
    const r=el.getBoundingClientRect(); const id=el.dataset.i;
    if(!done.has(id) && r.top<=ly && r.bottom>ly){{ done.add(id); showIns(el); }}
  }});
}}
function showIns(el){{
  const n=el.dataset.ins, sec=+el.dataset.sec; let left=sec;
  $('ovt').textContent='INSERTO '+n+' · '+el.querySelector('.it').textContent;
  const v=$('ovv');
  if($('vid').classList.contains('on') && VIDS[n]){{ v.style.display='block'; v.src=VIDS[n]; v.muted=false; v.currentTime=0; v.play().catch(()=>{{v.muted=true;v.play()}}); }}
  else {{ v.style.display='none'; }}
  $('ovc').textContent=left; $('ov').classList.add('show');
  clearInterval(timer);
  timer=setInterval(()=>{{ left--; $('ovc').textContent=Math.max(0,left); if(left<=0) closeIns(); }},1000);
}}
function closeIns(){{ clearInterval(timer); const v=$('ovv'); v.pause(); $('ov').classList.remove('show'); last=performance.now(); }}
$('ov').onclick=closeIns;
$('play').onclick=()=>play(!playing);
$('slow').onclick=()=>setSpeed(speed-.1); $('fast').onclick=()=>setSpeed(speed+.1);
$('small').onclick=()=>setFs(fs-6); $('big').onclick=()=>setFs(fs+6);
$('mir').onclick=e=>{{document.body.classList.toggle('mirror');e.target.classList.toggle('on')}};
$('auto').onclick=e=>e.target.classList.toggle('on');
$('vid').onclick=e=>e.target.classList.toggle('on');
$('top').onclick=()=>{{sc.scrollTop=0;done.clear();play(false)}};
$('hidebar').onclick=()=>$('bar').classList.add('hide');
document.addEventListener('keydown',ev=>{{
  if(ev.code==='Space'){{ev.preventDefault(); if($('ov').classList.contains('show')) closeIns(); else play(!playing)}}
  else if(ev.key==='ArrowUp'){{ev.preventDefault();setSpeed(speed+.1)}}
  else if(ev.key==='ArrowDown'){{ev.preventDefault();setSpeed(speed-.1)}}
  else if(ev.key==='+'||ev.key==='='){{setFs(fs+6)}}
  else if(ev.key==='-'){{setFs(fs-6)}}
  else if(ev.key==='h'||ev.key==='H'){{$('bar').classList.toggle('hide')}}
  else if(ev.key==='m'||ev.key==='M'){{$('mir').click()}}
  else if(ev.key==='ArrowRight'||ev.key==='ArrowLeft'){{
    const bs=[...document.querySelectorAll('.b')], ly=window.innerHeight*0.40;
    const cur=bs.findIndex(b=>b.getBoundingClientRect().bottom>ly);
    const nx=bs[Math.max(0,Math.min(bs.length-1,cur+(ev.key==='ArrowRight'?1:-1)))];
    sc.scrollTop+=nx.getBoundingClientRect().top-ly+4; }}
}});
requestAnimationFrame(t=>{{last=t;loop(t)}});
</script></body></html>'''
out = 'Gobbo-Storia-2-Il-nipote-del-piano-di-sopra.html' if embed else 'gobbo_novideo.html'
open(out, 'w').write(page)
print(out, round(len(page) / 1e6, 1), 'MB')

# --- versione testo per app da gobbo ---
lines = [f'PARLANE CON CORINNE CLÉRY · STORIA 2', g['title'].upper(), g['where'], '',
         'PRONUNCIA: ' + ' · '.join(f'{a} = {c}' for a, c in g['pron']), '']
for b in g['blocks']:
    if b['t'] == 'ins':
        lines += [f'>>> INSERTO {b["n"]} · {b["title"]} · {b["sec"]} SECONDI · PAUSA <<<', '']
    else:
        lines += [('[IN CAMERA] ' if b['t'] == 'cam' else '[VOCE SULLE IMMAGINI] ') + b['text'], '']
open('Gobbo-Storia-2.txt', 'w').write('\n'.join(lines))
