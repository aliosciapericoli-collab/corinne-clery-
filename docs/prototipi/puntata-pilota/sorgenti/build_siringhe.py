import subprocess, os

W, H, FPS = 1920, 1080, 25
F = 'fonts'
os.makedirs('sir', exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(1)


def t(name, s):
    p = f'sir/{name}.txt'
    open(p, 'w').write(s)
    return p


def label(p, a, b, size=34, y='h-132-95'):
    return (f"drawtext=fontfile={F}/plexmono.ttf:textfile={p}:fontsize={size}:fontcolor=0xf3ede4:x=(w-tw)/2:y={y}:"
            f"alpha='min(1,max(0,(t-{a})/0.35))*min(1,max(0,({b}-t)/0.3))':enable='between(t,{a},{b})',")


BARS = "drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"
KEY = (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t('key','SCENA DECISIVA')}:fontsize=22:fontcolor=white:"
       "box=1:boxcolor=0xc8402f:boxborderw=10:x=w-tw-110:y=165,")
GRADE = "eq=contrast=1.12:saturation=0.8:eval=frame,colorbalance=rs=-0.03:bs=0.05:rh=0.04:bh=-0.03"

# (nome, immagine, crop sull'immagine 1920x1080 o None, durata, zoom, scritte, flash iniziale, tremolio)
shots = [
    ('a', 'porta', None, 4.0, "1.0+0.30*pow(on/{N},1.2)", [], False, False),
    ('b', 'siringhe', None, 5.0, "1.0+0.16*on/{N}", [('SUL COMODINO, DUE SIRINGHE', 0.8, 4.8)], True, False),
    ('c', 'siringhe', (720, 430, 960, 540), 4.5, "1.0+0.25*on/{N}", [('UNA È VUOTA', 0.4, 2.0), ("L'ALTRA È STATA LAVATA. IN FRETTA.", 2.1, 4.4)], True, True),
    ('d', 'siringhe', (797, 270, 640, 360), 3.0, "1.0+0.20*on/{N}", [('MA NON ABBASTANZA', 0.5, 2.9)], True, True),
]
parts = []
for name, img, crop, D, z, texts, flash, shake in shots:
    N = int(D * FPS)
    src = f"[0:v]crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "[0:v]"
    src += "scale=3840:2160,"
    xs = "iw/2-(iw/zoom/2)" + ("+18*sin(on*0.9)+9*sin(on*2.3)" if shake else "")
    ys = "ih/2-(ih/zoom/2)" + ("+12*sin(on*1.3)" if shake else "")
    br = "0.55*lt(t,0.08)+0.25*between(t,0.08,0.16)" if flash else "0"
    if name == 'a':
        br = "0.04*sin(2*PI*t*0.5)-0.03"
    v = (src + f"zoompan=z='{z.format(N=N)}':x='{xs}':y='{ys}':d={N}:s={W}x{H}:fps={FPS},"
         f"eq=brightness='{br}':eval=frame,{GRADE},noise=alls=11:allf=t,vignette=PI/4.2," + BARS)
    if name != 'a':
        v += KEY
    for k, (s, a, b) in enumerate(texts):
        v += label(t(f'{name}{k}', s), a, b)
    v += "format=yuv420p"
    out = f'sir/{name}.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f'img/{img}.jpg', '-vf', v.replace('[0:v]', ''),
         '-t', str(D), '-r', str(FPS), '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', out])
    parts.append((out, D))

# inquadratura finale: nero con la scritta, sul colpo
D = 3.5
v = (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t('e0','TRACCE DI UN DERIVATO DEL CURARO')}:fontsize=40:fontcolor=0xf3ede4:"
     f"x=(w-tw)/2:y=(h-th)/2:alpha='min(1,max(0,(t-0.15)/0.25))*min(1,max(0,({D}-0.2-t)/0.6))',"
     f"drawtext=fontfile={F}/corm-italic.ttf:textfile={t('e1','sincuranina')}:fontsize=34:fontcolor=0xd98b4a:"
     f"x=(w-tw)/2:y=(h/2)+50:alpha='min(1,max(0,(t-0.9)/0.5))*min(1,max(0,({D}-0.2-t)/0.6))',noise=alls=7:allf=t,format=yuv420p")
run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}', '-vf', v, '-t', str(D),
     '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', 'sir/e.mp4'])
parts.append(('sir/e.mp4', D))

total = sum(d for _, d in parts)
cut = sum(d for _, d in parts[:-1])  # istante del colpo finale

# --- suono: battito che accelera, fischio che sale, colpo e silenzio ---
beats, tt, per = [], 0.4, 0.95
while tt < cut - 0.1:
    beats.append(round(tt, 3))
    per = max(0.42, per * 0.93)
    tt += per
hb = '+'.join(f"gte(t,{b})*(sin(2*PI*54*(t-{b}))*exp(-24*(t-{b}))+0.65*gte(t,{b+0.2})*sin(2*PI*47*(t-{b+0.2}))*exp(-24*(t-{b+0.2})))" for b in beats)
drone = f"0.32*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.2*t))*lt(t,{cut})+0.18*sin(2*PI*82.41*t)*lt(t,{cut})"
whine = f"0.05*sin(2*PI*5800*t)*min(1,max(0,(t-4)/{cut-4}))*lt(t,{cut})"
boom = f"1.25*gte(t,{cut})*(sin(2*PI*36*(t-{cut}))+0.6*sin(2*PI*54*(t-{cut}))+0.3*sin(2*PI*73*(t-{cut})))*exp(-1.1*(t-{cut}))"
clicks = '+'.join(f"0.5*gte(t,{c})*sin(2*PI*1800*(t-{c}))*exp(-90*(t-{c}))" for c in [parts[0][1], parts[0][1] + parts[1][1], parts[0][1] + parts[1][1] + parts[2][1]])
expr = f"0.85*({hb})+{drone}+{whine}+{boom}+{clicks}"
run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=44100:d={total}",
     '-f', 'lavfi', '-i', f"anoisesrc=color=brown:amplitude=0.6:r=44100:d={total}",
     '-filter_complex', f"[1:a]lowpass=f=260,volume='0.10*lt(t,{cut})+0.22*gte(t,{cut})*exp(-0.8*(t-{cut}))':eval=frame[n];"
     f"[0:a][n]amix=inputs=2:normalize=0,afade=t=in:d=0.3,afade=t=out:st={total-0.6}:d=0.6,alimiter=limit=0.92,aformat=channel_layouts=stereo[a]",
     '-map', '[a]', 'sir/audio.wav'])

lst = ''.join(f"file '{os.path.basename(p)}'\n" for p, _ in parts)
open('sir/list.txt', 'w').write(lst)
run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'sir/list.txt', '-i', 'sir/audio.wav',
     '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '21', '-preset', 'slow', '-pix_fmt', 'yuv420p',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', 'inserti/Inserto-05-Le-due-siringhe.mp4'])
print('durata', total, 'colpo a', cut, 'battiti', len(beats))
