# Versione «master» degli inserti: sorgenti 4K, movimento calcolato a 8K (niente scatti),
# grana leggera, codifica ad alta qualità. Uscite: MASTER 1080p (per il montaggio) e web (per l'archivio).
import os, sys
from build_seq import run, hb, clicks, FPS, F

BARS = "drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"


def seq(name, shots, final, audio, noise, outname):
    wd = f'dmaster_{name}'
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
    os.makedirs('inserti_borden', exist_ok=True)
    master = f'inserti_borden/Borden-Inserto-{outname}-MASTER.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt', '-i', f'{wd}/audio.wav',
         '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-tune', 'film', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', master])
    web = f'inserti_borden/Borden-Inserto-{outname}.mp4'
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
night = lambda T, b: ('brown', "lowpass=f=400,volume=0.06")
heat = lambda T, b: ('pink', "lowpass=f=900,highpass=f=150,volume='0.08*(0.7+0.3*sin(2*PI*0.25*t))':eval=frame")
SEQ['01'] = ([dict(img='d01a', D=5.0, z="1.0+0.07*on/{N}", texts=[("FALL RIVER · 4 AGOSTO 1892", 0.9, 4.9)]),
              dict(img='d01b', D=5.0, z="1.0+0.08*on/{N}", texts=[("TRE SERRATURE", 0.5, 4.8)])],
             None, lambda T, b: f"0.35*({DRONE})+{thud(b[0] + 0.6, 0.5)}+{thud(b[0] + 1.6, 0.5)}+{thud(b[0] + 2.6, 0.6)}+{clicks(b)}", heat,
             '01-La-porta-a-tre-mandate')
SEQ['02'] = ([dict(img='d02a', D=5.0, z="1.0+0.08*on/{N}", texts=[("«AVEVA RICEVUTO UN BIGLIETTO»", 0.8, 4.9)]),
              dict(img='d02b', D=5.0, z="1.0+0.06*on/{N}", texts=[("NESSUNO LO TROVÒ MAI", 0.5, 4.8)])],
             None, lambda T, b: f"0.35*({DRONE})+{hb(hbeats(0.4, T, 1.0, 1.0), 0.35)}+{clicks(b)}", heat, '02-Il-biglietto')
SEQ['03'] = ([dict(img='d03a', D=5.0, z="1.0+0.07*on/{N}", texts=[("IL FIENILE, DIETRO CASA", 0.8, 4.9)]),
              dict(img='d03b', D=5.0, z="1.0+0.08*on/{N}", texts=[("QUINDICI, VENTI MINUTI. FORSE DIECI.", 0.5, 4.8)])],
             None, lambda T, b: f"0.35*({DRONE})+{clicks(b)}",
             lambda T, b: ('pink', "bandpass=f=300:width_type=h:w=200,volume='0.12*(0.6+0.4*sin(2*PI*7*t))':eval=frame"), '03-Il-fienile')
SEQ['04'] = ([dict(img='d04a', D=5.0, z="1.0+0.07*on/{N}", texts=[("LA DOMENICA DOPO", 0.8, 4.9)]),
              dict(img='d04b', D=5.0, z="1.0+0.09*on/{N}", texts=[("«È TUTTA SPORCA DI VERNICE»", 0.5, 4.8)])],
             None, lambda T, b: f"0.4*({DRONE})+{hb(hbeats(b[0], T, 0.95, 0.96), 0.55)}+{clicks(b)}",
             lambda T, b: ('brown', "lowpass=f=600,volume='0.10*(0.8+0.2*sin(2*PI*3.3*t))':eval=frame"), '04-Il-vestito-nella-stufa')
SEQ['05'] = ([dict(img='d05a', D=5.0, z="1.0+0.06*on/{N}", sat=0.75, texts=[("NEW BEDFORD · 20 GIUGNO 1893", 0.8, 4.9)]),
              dict(img='d05b', D=5.0, z="1.0+0.10*on/{N}", texts=[("«SIGNORI, SONO INNOCENTE»", 0.5, 4.8)])],
             dict(D=5.0, big='NON COLPEVOLE', size=80, small="dopo circa un'ora"),
             lambda T, b: f"0.4*({DRONE})+{hb(hbeats(b[0], b[1], 0.8, 0.94), 0.65)}+{thud(b[1] - 0.1, 0.9)}+{clicks(b)}",
             lambda T, b: ('pink', f"lowpass=f=2000,highpass=f=200,volume='0.06+0.20*gte(t,{b[1]+0.6})*min(1,(t-{b[1]}-0.6)/1.5)':eval=frame"),
             '05-Il-verdetto')
SEQ['06'] = ([dict(img='d06a', D=6.0, z="1.0+0.06*on/{N}", sat=0.7, texts=[("LA CASA SULLA COLLINA", 1.0, 5.8)])],
             dict(D=4.0, big='ASSOLTA', size=72, small="Per la città, la sola sospettata"),
             lambda T, b: f"0.35*({DRONE})+{thud(6.0, 0.7)}",
             lambda T, b: ('pink', "lowpass=f=700,highpass=f=100,volume='0.14*(0.7+0.3*sin(2*PI*0.15*t))':eval=frame"), '06-La-casa-sulla-collina')

for k in [a for a in sys.argv[1:] if a in SEQ]:
    shots, final, aud, noi, out = SEQ[k]
    seq(k, shots, final, aud, noi, out)
