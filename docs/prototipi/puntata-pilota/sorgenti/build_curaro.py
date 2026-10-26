# Versione «master» degli inserti: sorgenti 4K, movimento calcolato a 8K (niente scatti),
# grana leggera, codifica ad alta qualità. Uscite: MASTER 1080p (per il montaggio) e web (per l'archivio).
import os, sys
from build_seq import run, hb, clicks, FPS, F

BARS = "drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"


def seq(name, shots, final, audio, noise, outname):
    wd = f'cmaster_{name}'
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
    os.makedirs('inserti_curaro', exist_ok=True)
    master = f'inserti_curaro/Curaro-Inserto-{outname}-MASTER.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt', '-i', f'{wd}/audio.wav',
         '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-tune', 'film', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', master])
    web = f'inserti_curaro/Curaro-Inserto-{outname}.mp4'
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
rain = lambda T, b: ('pink', "lowpass=f=6000,highpass=f=1200,volume=0.10")
SEQ['01'] = ([dict(img='c01x', D=3.0, z="1.0+0.05*on/{N}", texts=[("BOLOGNA · MARZO 1963", 0.8, 2.9)]),
              dict(img='c01a', D=2.5, z="1.02+0.05*on/{N}", pan='right'),
              dict(img='c01b', D=2.5, z="1.0+0.07*on/{N}", texts=[("VICOLO MALGRADO 11", 0.3, 2.4)])],
             None, lambda T, b: f"0.5*({DRONE})+{clicks(b)}", rain, '01-La-finestra-accesa')
steps2 = '+'.join(thud(round(4.8 + 0.4 * i, 2), 0.3) for i in range(8))
SEQ['02'] = ([dict(img='c02a', D=4.5, z="1.0+0.08*on/{N}", texts=[("14 MARZO · POCO PRIMA DELLE UNDICI", 0.8, 4.4)]),
              dict(img='c02b', D=3.5, z="1.0+0.06*on/{N}", shake=True, texts=[("ARRIVA UN COLLEGA", 0.4, 3.4)])],
             None, lambda T, b: f"0.4*({DRONE})+{ring(0.3, 4.3)}+{steps2}+{clicks(b)}",
             lambda T, b: ('brown', "lowpass=f=300,volume=0.05"), '02-La-telefonata-delle-undici')
SEQ['03'] = ([dict(img='c03a', D=5.0, z="1.0+0.06*on/{N}", sat=0.8),
              dict(img='c03b', D=4.0, z="1.0+0.09*on/{N}", sat=0.7)],
             None, lambda T, b: f"0.35*({DRONE})+{hb(hbeats(0.4, 7.6, 0.8, 1.13), 0.75)}+{clicks(b)}",
             lambda T, b: ('brown', "lowpass=f=250,volume=0.04"), '03-Il-respiro-che-si-ferma')
steps4 = '+'.join(thud(round(0.6 + 0.75 * i, 2), 0.32) for i in range(9))
buzz = "0.05*sin(2*PI*100*t)*(0.6+0.4*sin(2*PI*7*t))"
SEQ['04'] = ([dict(img='c04a', D=8.0, z="1.0+0.08*on/{N}", br="-0.10*lt(mod(t,1.9),0.07)-0.06*lt(mod(t+0.5,3.1),0.05)",
                   texts=[("IL PADRE, IL PROFESSOR PIETRO NIGRISOLI", 1.2, 7.8)])],
             None, lambda T, b: f"0.4*({DRONE})+{buzz}+{steps4}",
             lambda T, b: ('pink', "lowpass=f=800,highpass=f=150,volume=0.03"), '04-Il-padre-sulle-scale')
def a05(T, b):
    return f"0.4*({DRONE})+{hb(hbeats(0.5, T - 1.4, 1.0, 0.95), 0.7)}+{thud(T - 1.2, 1.2)}+{clicks(b)}"
SEQ['05'] = ([dict(img='c05a', D=5.5, z="1.0+0.07*on/{N}", texts=[("DUE SIRINGHE SUL COMODINO", 1.0, 5.3)]),
              dict(img='c05b', D=5.0, z="1.0+0.10*on/{N}", texts=[("UNA È STATA LAVATA", 0.5, 4.8)]),
              dict(img='c05c', D=4.5, z="1.0+0.08*on/{N}", sat=0.75),
              dict(img='c05d', D=5.0, z="1.0+0.09*on/{N}")],
             None, a05, lambda T, b: ('brown', "lowpass=f=300,volume=0.05"), '05-Le-due-siringhe')
def a06(T, b):
    c = b[-1]
    beeps = '+'.join(f"0.25*between(t,{x},{x}+0.12)*sin(2*PI*1000*t)" for x in [round(0.5 + 1.0 * i, 2) for i in range(int(c - 1))])
    flat = f"0.25*gte(t,{c})*sin(2*PI*1000*t)*min(1,({T}-t)/0.6)"
    return f"0.3*({DRONE})+{beeps}+{flat}+{clicks(b)}"
SEQ['06'] = ([dict(img='c06a', D=4.5, z="1.0+0.06*on/{N}", sat=0.75, texts=[("L'AUTOPSIA", 0.8, 4.3)]),
              dict(img='c06b', D=4.5, z="1.0+0.08*on/{N}", sat=0.75),
              dict(img='c06c', D=4.5, z="1.0+0.08*on/{N}", sat=0.75),
              dict(img='c06d', D=3.5, z="1.0+0.10*on/{N}", sat=0.7)],
             dict(D=3.0, big='UN DERIVATO DEL CURARO', size=58),
             a06, lambda T, b: ('pink', "lowpass=f=600,highpass=f=100,volume=0.03"), '06-Lautopsia')
SEQ['07'] = ([dict(img='c07a', D=8.0, z="1.08", pan='right', texts=[("IL GIALLO DEL CURARO", 0.8, 4.0), ("BOLOGNA SI DIVIDE", 4.3, 7.8)])],
             None, lambda T, b: f"0.35*({DRONE})",
             lambda T, b: ('pink', "bandpass=f=900:width_type=h:w=1400,volume='0.35*(0.7+0.3*sin(2*PI*0.5*t))':eval=frame"),
             '07-Il-giallo-del-curaro')
def a08(T, b):
    gavel = '+'.join(thud(round(b[1] + 1.5 + 0.35 * i, 2), 1.0) for i in range(3))
    boom = f"1.2*gte(t,{b[-1]})*(sin(2*PI*36*(t-{b[-1]}))+0.6*sin(2*PI*54*(t-{b[-1]})))*exp(-1.0*(t-{b[-1]}))"
    door = thud(b[1] + 0.3, 1.1)
    return f"0.35*({DRONE})*lt(t,{b[-1]})+{gavel}+{door}+{boom}+{clicks(b)}"
SEQ['08'] = ([dict(img='c08a', D=5.0, z="1.0+0.06*on/{N}", texts=[("BOLOGNA · 15 FEBBRAIO 1965", 0.8, 4.8)]),
              dict(img='c08b', D=5.5, z="1.0+0.07*on/{N}", texts=[("DOPO 44 UDIENZE, LA SENTENZA", 0.4, 5.3)]),
              dict(img='c08c', D=4.5, z="1.0+0.08*on/{N}", sat=0.7)],
             dict(D=5.0, big='ERGASTOLO', size=72, small="in appello 24 anni · definitiva in Cassazione nel 1969"),
             a08, lambda T, b: ('pink', f"bandpass=f=900:width_type=h:w=1400,volume='0.30*lt(t,{b[0]})+0.04':eval=frame"),
             '08-La-sentenza')

for k in [a for a in sys.argv[1:] if a in SEQ]:
    shots, final, aud, noi, out = SEQ[k]
    seq(k, shots, final, aud, noi, out)
