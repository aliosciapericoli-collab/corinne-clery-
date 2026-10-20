import subprocess, os, sys

W, H, FPS = 1920, 1080, 25
F = 'fonts'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(1)


def build(name, shots, final, audio_fn, outname):
    wd = f'seq_{name}'
    os.makedirs(wd, exist_ok=True)
    n = [0]

    def t(s):
        n[0] += 1
        p = f'{wd}/t{n[0]}.txt'
        open(p, 'w').write(s)
        return p

    BARS = "drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"
    KEY = (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t('SCENA DECISIVA')}:fontsize=22:fontcolor=white:"
           "box=1:boxcolor=0xc8402f:boxborderw=10:x=w-tw-110:y=165,")
    parts = []
    for i, sh in enumerate(shots):
        D = sh['D']; N = int(D * FPS)
        crop = sh.get('crop')
        v = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else ""
        v += "scale=3840:2160,"
        sk = sh.get('shake')
        xs = "iw/2-(iw/zoom/2)" + ("+18*sin(on*0.9)+9*sin(on*2.3)" if sk else "")
        ys = "ih/2-(ih/zoom/2)" + ("+12*sin(on*1.3)" if sk else "")
        if sh.get('pan') == 'left':
            xs = f"(iw-iw/zoom)*(1-on/{N})"
        if sh.get('pan') == 'right':
            xs = f"(iw-iw/zoom)*(on/{N})"
        br = sh.get('br', "0")
        if i > 0:
            br = f"({br})+0.55*lt(t,0.08)+0.25*between(t,0.08,0.16)"
        v += (f"zoompan=z='{sh['z'].format(N=N)}':x='{xs}':y='{ys}':d={N}:s={W}x{H}:fps={FPS},"
              f"eq=brightness='{br}':contrast=1.12:saturation={sh.get('sat', 0.8)}:eval=frame,"
              f"colorbalance=rs=-0.03:bs=0.05:rh=0.04:bh=-0.03,noise=alls=11:allf=t,vignette=PI/4.2," + BARS + KEY)
        for s, a, b in sh.get('texts', []):
            v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t(s)}:fontsize=34:fontcolor=0xf3ede4:x=(w-tw)/2:y=h-132-95:"
                  f"alpha='min(1,max(0,(t-{a})/0.35))*min(1,max(0,({b}-t)/0.3))':enable='between(t,{a},{b})',")
        v += "format=yuv420p"
        out = f'{wd}/{i}.mp4'
        run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f"img/{sh['img']}.jpg", '-vf', v,
             '-t', str(D), '-r', str(FPS), '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', out])
        parts.append((out, D))
    D = final['D']
    v = (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t(final['big'])}:fontsize={final.get('size', 40)}:fontcolor=0xf3ede4:"
         f"x=(w-tw)/2:y=(h-th)/2-20:alpha='min(1,max(0,(t-0.12)/0.2))*min(1,max(0,({D}-0.2-t)/0.6))',")
    if final.get('small'):
        v += (f"drawtext=fontfile={F}/corm-italic.ttf:textfile={t(final['small'])}:fontsize=34:fontcolor=0xd98b4a:"
              f"x=(w-tw)/2:y=(h/2)+50:alpha='min(1,max(0,(t-1.0)/0.5))*min(1,max(0,({D}-0.2-t)/0.6))',")
    v += "noise=alls=7:allf=t,format=yuv420p"
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}', '-vf', v, '-t', str(D),
         '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', f'{wd}/e.mp4'])
    parts.append((f'{wd}/e.mp4', D))
    total = sum(d for _, d in parts)
    cut = total - D
    bounds, acc = [], 0
    for _, d in parts[:-1]:
        acc += d
        bounds.append(round(acc, 3))
    expr, noise_vol = audio_fn(total, cut, bounds)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=44100:d={total}",
         '-f', 'lavfi', '-i', f"anoisesrc=color=brown:amplitude=0.6:r=44100:d={total}",
         '-filter_complex', f"[1:a]lowpass=f=300,volume='{noise_vol}':eval=frame[n];"
         f"[0:a][n]amix=inputs=2:normalize=0,afade=t=in:d=0.3,afade=t=out:st={total-0.6}:d=0.6,alimiter=limit=0.92,aformat=channel_layouts=stereo[a]",
         '-map', '[a]', f'{wd}/audio.wav'])
    open(f'{wd}/list.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p, _ in parts))
    hq = f'Inserto-{outname}-HQ.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt', '-i', f'{wd}/audio.wav',
         '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '21', '-preset', 'slow', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', hq])
    web = f'inserti/Inserto-{outname}.mp4'
    for p in (1, 2):
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', hq, '-c:v', 'libx264', '-b:v', '4800k', '-pass', str(p), '-preset', 'slow',
             '-passlogfile', f'{wd}/pass'] + (['-an', '-f', 'mp4', '/dev/null'] if p == 1 else ['-c:a', 'copy', '-movflags', '+faststart', web]))
    print(name, 'durata', total, 'colpo', cut, os.path.getsize(web) // 1024, 'KB')


def hb(times, a=0.85):
    return '+'.join(f"{a}*gte(t,{b})*(sin(2*PI*54*(t-{b}))*exp(-24*(t-{b}))+0.65*gte(t,{b+0.2})*sin(2*PI*47*(t-{b+0.2}))*exp(-24*(t-{b+0.2})))" for b in times)


def clicks(bounds):
    return '+'.join(f"0.5*gte(t,{c})*sin(2*PI*1800*(t-{c}))*exp(-90*(t-{c}))" for c in bounds)


def audio_autopsia(total, cut, bounds):
    beats, tt, per = [], 0.5, 0.75
    while tt < cut - 0.2:
        beats.append(round(tt, 3)); per = min(1.6, per * 1.07); tt += per   # il battito rallenta
    hum = f"0.12*(sin(2*PI*100*t)+0.5*sin(2*PI*200*t)+0.3*sin(2*PI*300*t))*(1-0.9*lt(mod(t,2.9),0.05))*lt(t,{cut})"
    drone = f"0.3*sin(2*PI*55*t)*lt(t,{cut})+0.16*sin(2*PI*82.41*t)*lt(t,{cut})"
    flat = f"0.22*gte(t,{cut}+0.3)*sin(2*PI*1000*t)"   # elettrocardiogramma piatto
    boom = f"1.1*gte(t,{cut})*(sin(2*PI*36*(t-{cut}))+0.5*sin(2*PI*54*(t-{cut})))*exp(-1.6*(t-{cut}))"
    return f"{hb(beats)}+{hum}+{drone}+{flat}+{boom}+{clicks(bounds)}", f"0.08*lt(t,{cut})"


def audio_sentenza(total, cut, bounds):
    ticks, tt, per = [], 0.3, 0.9
    while tt < cut - 2.0:
        ticks.append(round(tt, 3)); per = max(0.35, per * 0.94); tt += per   # orologio che accelera
    tick = '+'.join(f"0.35*gte(t,{b})*sin(2*PI*2600*(t-{b}))*exp(-140*(t-{b}))" for b in ticks)
    gav = [round(cut - 1.6, 2), round(cut - 1.0, 2), round(cut - 0.4, 2)]   # tre colpi di martelletto
    gavel = '+'.join(f"1.0*gte(t,{g})*(sin(2*PI*190*(t-{g}))+0.6*sin(2*PI*310*(t-{g})))*exp(-38*(t-{g}))" for g in gav)
    drone = f"0.3*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.15*t))*lt(t,{cut})+0.18*sin(2*PI*73.4*t)*lt(t,{cut})"
    boom = f"1.3*gte(t,{cut})*(sin(2*PI*34*(t-{cut}))+0.6*sin(2*PI*51*(t-{cut}))+0.3*sin(2*PI*68*(t-{cut})))*exp(-0.9*(t-{cut}))"
    # brusio dell'aula durante le inquadrature 2-3
    murmur = f"0.16*between(t,{bounds[0]},{bounds[2]})"
    return f"{tick}+{gavel}+{drone}+{boom}+{clicks(bounds)}", f"{murmur}+0.06+0.2*gte(t,{cut})*exp(-0.8*(t-{cut}))"


AUTOPSIA = [
    dict(img='lab', D=5.0, z="1.0+0.14*on/{N}", br="-0.10*lt(mod(t,2.3),0.05)-0.06*between(mod(t,2.3),0.12,0.17)", texts=[("L'AUTOPSIA", 0.8, 4.8)], sat=0.7),
    dict(img='lab', D=4.5, crop=(100, 360, 960, 540), z="1.0+0.22*on/{N}", shake=True, br="-0.08*lt(mod(t,1.9),0.05)", texts=[("NEL CORPO DI OMBRETTA", 0.4, 4.3)], sat=0.7),
    dict(img='lab', D=4.0, crop=(960, 200, 960, 540), z="1.0+0.25*on/{N}", br="-0.08*lt(mod(t,1.7),0.05)", texts=[("UN DERIVATO DEL CURARO", 0.4, 3.8)], sat=0.7),
    dict(img='siringhe', D=3.5, crop=(640, 480, 640, 360), z="1.0+0.30*on/{N}", shake=True, texts=[("UN SOLO SEGNO DI INIEZIONE", 0.4, 3.3)]),
]
SENTENZA = [
    dict(img='giornali', D=4.5, z="1.14", pan='right', texts=[("BOLOGNA, 1965 · IL GIALLO DEL CURARO", 0.8, 4.3)]),
    dict(img='aula', D=5.0, z="1.0+0.14*on/{N}", br="0.02*sin(2*PI*t*0.3)", texts=[("CORTE D'ASSISE DI BOLOGNA", 0.8, 4.8)]),
    dict(img='aula', D=4.0, crop=(960, 200, 960, 540), z="1.0+0.22*on/{N}", shake=True, texts=[("QUARANTAQUATTRO UDIENZE", 0.4, 3.8)]),
    dict(img='carcere', D=4.0, z="1.0+0.30*pow(on/{N},1.3)", texts=[("15 FEBBRAIO 1965", 0.4, 3.8)]),
]

if 'autopsia' in sys.argv:
    build('autopsia', AUTOPSIA, dict(D=4.0, big='CEDIMENTO DEL CUORE · EDEMA AI POLMONI', small='sincuranina'), audio_autopsia, '06-Lautopsia')
if 'sentenza' in sys.argv:
    build('sentenza', SENTENZA, dict(D=4.5, big='ERGASTOLO', size=96, small='in appello 24 anni · definitiva in Cassazione nel 1969'), audio_sentenza, '08-La-sentenza')
