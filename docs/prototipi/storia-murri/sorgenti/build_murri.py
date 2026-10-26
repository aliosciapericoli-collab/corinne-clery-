# Versione «master» degli inserti: sorgenti 4K, movimento calcolato a 8K (niente scatti),
# grana leggera, codifica ad alta qualità. Uscite: MASTER 1080p (per il montaggio) e web (per l'archivio).
import os, sys
from build_seq import run, hb, clicks, FPS, F

BARS = "drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"


def seq(name, shots, final, audio, noise, outname):
    wd = f'umaster_{name}'
    os.makedirs(wd, exist_ok=True)
    n = [0]

    def t(s):
        n[0] += 1
        p = f'{wd}/t{n[0]}.txt'
        open(p, 'w').write(s)
        return p

    parts = []
    for i, sh in enumerate(shots):
        D = sh['D']; N = int(D * FPS)
        c = sh.get('crop')
        v = (f"crop={c[2]}:{c[3]}:{c[0]}:{c[1]}," if c else "") + "scale=7680:4320:flags=lanczos,"
        sk = sh.get('shake')
        xs = "iw/2-(iw/zoom/2)" + ("+20*sin(on*0.7)+10*sin(on*1.9)" if sk else "")
        ys = "ih/2-(ih/zoom/2)" + ("+14*sin(on*1.1)" if sk else "")
        if sh.get('pan') == 'right':
            xs = f"(iw-iw/zoom)*(on/{N})"
        if sh.get('pan') == 'left':
            xs = f"(iw-iw/zoom)*(1-on/{N})"
        br = sh.get('br', "0")
        if i > 0:
            br = f"({br})+0.30*lt(t,0.06)"
        v += (f"zoompan=z='{sh['z'].format(N=N)}':x='{xs}':y='{ys}':d={N}:s=3840x2160:fps={FPS},"
              "scale=1920:1080:flags=lanczos,"
              f"eq=brightness='{br}':contrast=1.10:saturation={sh.get('sat', 0.85)}:eval=frame,"
              f"colorbalance=rs=-0.02:bs=0.04:rh=0.03:bh=-0.02,vignette=PI/4.5,noise=alls=3:allf=t,"
              f"fade=t=in:st=0:d={0.6 if i == 0 else 0.12}," + BARS)
        if sh.get('badge'):
            v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t(sh['badge'])}:fontsize=22:fontcolor=white:"
                  "box=1:boxcolor=0xc8402f:boxborderw=10:x=w-tw-110:y=165,")
        for s, a, b in sh.get('texts', []):
            v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t(s)}:fontsize=32:fontcolor=0xf3ede4:x=(w-tw)/2:y=h-132-92:"
                  f"alpha='min(1,max(0,(t-{a})/0.5))*min(1,max(0,({b}-t)/0.4))':enable='between(t,{a},{b})',")
        v += "format=yuv420p"
        out = f'{wd}/{i}.mov'
        run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f"img/{sh['img']}.jpg", '-vf', v,
             '-t', str(D), '-r', str(FPS), '-c:v', 'libx264', '-crf', '10', '-preset', 'medium', '-tune', 'film', '-pix_fmt', 'yuv420p', out])
        parts.append((out, D))
    if final:
        D = final['D']
        v = (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t(final['big'])}:fontsize={final.get('size', 54)}:fontcolor=0xf3ede4:"
             f"x=(w-tw)/2:y=(h-th)/2-20:alpha='min(1,max(0,(t-0.15)/0.3))*min(1,max(0,({D}-0.2-t)/0.5))',")
        if final.get('small'):
            v += (f"drawtext=fontfile={F}/corm-italic.ttf:textfile={t(final['small'])}:fontsize=38:fontcolor=0xd98b4a:"
                  f"x=(w-tw)/2:y=(h/2)+50:alpha='min(1,max(0,(t-0.7)/0.5))*min(1,max(0,({D}-0.2-t)/0.5))',")
        v += "noise=alls=3:allf=t,format=yuv420p"
        run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'color=black:s=1920x1080:r={FPS}', '-vf', v, '-t', str(D),
             '-c:v', 'libx264', '-crf', '10', '-pix_fmt', 'yuv420p', f'{wd}/e.mov'])
        parts.append((f'{wd}/e.mov', D))
    total = sum(d for _, d in parts)
    bounds, acc = [], 0
    for _, d in parts[:-1]:
        acc += d; bounds.append(round(acc, 3))
    expr = audio(total, bounds)
    ncol, nfilt = noise(total, bounds)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=48000:d={total}",
         '-f', 'lavfi', '-i', f"anoisesrc=color={ncol}:amplitude=0.6:r=48000:d={total}",
         '-filter_complex', f"[1:a]{nfilt}[n];[0:a][n]amix=inputs=2:normalize=0,afade=t=in:d=0.5,afade=t=out:st={total-0.7}:d=0.7,"
         "alimiter=limit=0.9,aformat=channel_layouts=stereo[a]", '-map', '[a]', f'{wd}/audio.wav'])
    open(f'{wd}/list.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p, _ in parts))
    os.makedirs('inserti_murri', exist_ok=True)
    master = f'inserti_murri/Murri-Inserto-{outname}-MASTER.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt', '-i', f'{wd}/audio.wav',
         '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-tune', 'film', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', master])
    web = f'inserti_murri/Murri-Inserto-{outname}.mp4'
    for p in (1, 2):
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', master, '-c:v', 'libx264', '-b:v', '8000k', '-maxrate', '12000k', '-bufsize', '16000k',
             '-pass', str(p), '-preset', 'slow', '-tune', 'film', '-passlogfile', f'{wd}/pass'] +
            (['-an', '-f', 'mp4', '/dev/null'] if p == 1 else ['-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', web]))
    print(outname, 'durata', total, os.path.getsize(master) // 1024, 'KB master', os.path.getsize(web) // 1024, 'KB web')


DRONE = "0.30*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.12*t))+0.15*sin(2*PI*82.41*t)"



def hbeats(start, end, per, k):
    out, tt = [], start
    while tt < end - 0.2:
        out.append(round(tt, 3)); per = max(0.42, min(1.6, per * k)); tt += per
    return out


def ring(t0, t1):
    # suoneria di un telefono anni Cinquanta: due toni a impulsi, 1 s di squillo e 2 s di pausa
    return f"0.22*between(t,{t0},{t1})*lt(mod(t-{t0},3),1)*(sin(2*PI*1000*t)+sin(2*PI*1250*t))*(0.5+0.5*sin(2*PI*22*t))"


def thud(x, a=0.9):
    return f"{a}*gte(t,{x})*(sin(2*PI*90*(t-{x}))+0.5*sin(2*PI*160*(t-{x})))*exp(-30*(t-{x}))"


SEQ = {}
hoof = '+'.join(thud(round(0.9 + 0.38 * i, 2), 0.18) for i in range(10))
SEQ['01'] = ([dict(img='u01a', D=4.5, z="1.0+0.06*on/{N}", texts=[("BOLOGNA · 1902", 1.2, 4.4)]),
              dict(img='u01b', D=3.5, z="1.02+0.06*on/{N}", texts=[("VIA MAZZINI, OGGI STRADA MAGGIORE", 0.4, 3.4)])],
             None, lambda T, b: f"0.5*({DRONE})+{hoof}+{clicks(b)}",
             lambda T, b: ('pink', "lowpass=f=2500,highpass=f=400,volume=0.09"),
             '01-La-palazzina')
def a02(T, b):
    clink = f"0.35*gte(t,1.6)*(sin(2*PI*3100*(t-1.6))+0.6*sin(2*PI*4700*(t-1.6)))*exp(-18*(t-1.6))"
    return f"0.4*({DRONE})+{thud(0.9, 1.0)}+{thud(1.2, 0.8)}+{clink}+{hb(hbeats(2.5, T, 0.8, 0.97), 0.7)}+{clicks(b)}"
SEQ['02'] = ([dict(img='u02a', D=5.0, z="1.0+0.07*on/{N}", shake=True, texts=[("IL PRIMO TENTATIVO · IN VACANZA", 1.0, 4.8)]),
              dict(img='u02b', D=5.0, z="1.0+0.08*on/{N}", texts=[("NELLA SIRINGA, IL CURARO", 0.5, 4.8)])],
             None, a02, lambda T, b: ('brown', "lowpass=f=300,volume=0.06"),
             '02-La-siringa')
def a03(T, b):
    cut = b[-1]
    hits = '+'.join(thud(x, 1.0) for x in (0.8, 1.6, 2.4, 3.2, 3.9, 4.6))
    crash = f"1.1*gte(t,5.2)*(sin(2*PI*70*(t-5.2))+0.7*sin(2*PI*140*(t-5.2)))*exp(-6*(t-5.2))"
    boom = f"1.2*gte(t,{cut})*(sin(2*PI*36*(t-{cut}))+0.6*sin(2*PI*54*(t-{cut})))*exp(-1.0*(t-{cut}))"
    return f"0.4*({DRONE})*lt(t,{cut})+{hits}+{crash}+{hb(hbeats(6.6, cut, 1.1, 0.96), 0.6)}+{boom}+{clicks(b)}"
SEQ['03'] = ([dict(img='u03a', D=6.5, z="1.0+0.06*on/{N}", shake=True, texts=[("2 SETTEMBRE 1902 · LA PORTA VIENE ABBATTUTA", 1.0, 6.3)]),
              dict(img='u03b', D=6.5, z="1.0+0.08*on/{N}", texts=[("IL CONTE BONMARTINI È MORTO DA CINQUE GIORNI", 0.5, 6.3)], sat=0.8)],
             dict(D=5.0, big='UN LADRO? UNA RAPINA?', size=58, small="così si pensa, all'inizio"),
             a03, lambda T, b: ('brown', "lowpass=f=300,volume=0.07"),
             '03-La-porta')
steps = '+'.join(thud(round(6.3 + 0.62 * i, 2), 0.35) for i in range(9))
tick = '+'.join(f"0.25*gte(t,{x})*sin(2*PI*2400*(t-{x}))*exp(-150*(t-{x}))" for x in [0.5, 1.5, 2.5, 3.5, 4.5, 5.5])
SEQ['04'] = ([dict(img='u04a', D=6.0, z="1.0+0.07*on/{N}", texts=[("UNA LETTERA DEL FIGLIO TULLIO", 1.0, 5.8)]),
              dict(img='u04b', D=6.0, z="1.0+0.07*on/{N}", texts=[("IL PADRE DENUNCIA IL FIGLIO", 0.6, 5.8)], sat=0.75)],
             None, lambda T, b: f"0.4*({DRONE})+{tick}+{steps}+{clicks(b)}",
             lambda T, b: ('pink', f"lowpass=f=900,highpass=f=150,volume='0.02+0.15*gte(t,{b[0]})':eval=frame"),
             '04-La-lettera-del-padre')
SEQ['05'] = ([dict(img='u05n', D=4.0, z="1.0+0.08*on/{N}", texts=[("IL CASO DIVIDE L'ITALIA", 0.6, 3.9)]),
              dict(img='u05a', D=5.0, z="1.0+0.07*on/{N}", texts=[("TORINO · 21 FEBBRAIO 1905", 0.4, 4.8)]),
              dict(img='u05b', D=6.0, z="1.0+0.07*on/{N}", texts=[("PER LA PRIMA VOLTA, GLI PSICHIATRI IN AULA", 0.4, 5.8)])],
             None, lambda T, b: f"0.35*({DRONE})+{clicks(b)}",
             lambda T, b: ('pink', f"bandpass=f=900:width_type=h:w=1400,volume='0.05+0.40*gte(t,{b[0]})*(0.7+0.3*sin(2*PI*0.5*t))':eval=frame"),
             '05-Laula-di-Torino')
bell = '+'.join(f"0.4*gte(t,{x})*(sin(2*PI*392*(t-{x}))+0.5*sin(2*PI*784*(t-{x}))+0.3*sin(2*PI*1176*(t-{x})))*exp(-0.9*(t-{x}))" for x in (1.5,))
SEQ['06'] = ([dict(img='u06a', D=8.0, z="1.0+0.07*on/{N}", texts=[], sat=0.75)],
             None, lambda T, b: f"0.3*({DRONE})+{bell}",
             lambda T, b: ('pink', "lowpass=f=700,highpass=f=100,volume='0.22*(0.6+0.4*sin(2*PI*0.18*t))':eval=frame"),
             '06-La-palazzina-vuota')

for k in [a for a in sys.argv[1:] if a in SEQ]:
    shots, final, aud, noi, out = SEQ[k]
    seq(k, shots, final, aud, noi, out)
