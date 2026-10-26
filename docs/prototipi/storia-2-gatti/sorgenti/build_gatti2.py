# Inserti A, B, C della Storia 2: più inquadrature dalla stessa immagine 4K, senza voce.
import os, sys
from build_seq import run, hb, clicks, W, H, FPS, F

BARS = "drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"


def seq(name, shots, final, audio, noise, outname):
    wd = f'seq_{name}'
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
        v = (f"crop={c[2]}:{c[3]}:{c[0]}:{c[1]}," if c else "") + "scale=3840:2160,"
        sk = sh.get('shake')
        xs = "iw/2-(iw/zoom/2)" + ("+10*sin(on*0.7)+5*sin(on*1.9)" if sk else "")
        ys = "ih/2-(ih/zoom/2)" + ("+7*sin(on*1.1)" if sk else "")
        if sh.get('pan') == 'right':
            xs = f"(iw-iw/zoom)*(on/{N})"
        if sh.get('pan') == 'left':
            xs = f"(iw-iw/zoom)*(1-on/{N})"
        br = sh.get('br', "0")
        if i > 0:
            br = f"({br})+0.35*lt(t,0.06)"
        v += (f"zoompan=z='{sh['z'].format(N=N)}':x='{xs}':y='{ys}':d={N}:s={W}x{H}:fps={FPS},"
              f"eq=brightness='{br}':contrast=1.12:saturation={sh.get('sat', 0.85)}:eval=frame,"
              f"colorbalance=rs=-0.02:bs=0.04:rh=0.03:bh=-0.02,noise=alls=10:allf=t,vignette=PI/4.3,"
              f"fade=t=in:st=0:d={0.6 if i == 0 else 0.15}," + BARS)
        for s, a, b in sh.get('texts', []):
            v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t(s)}:fontsize=32:fontcolor=0xf3ede4:x=(w-tw)/2:y=h-132-92:"
                  f"alpha='min(1,max(0,(t-{a})/0.5))*min(1,max(0,({b}-t)/0.4))':enable='between(t,{a},{b})',")
        v += "format=yuv420p"
        out = f'{wd}/{i}.mp4'
        run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f"img/{sh['img']}.jpg", '-vf', v,
             '-t', str(D), '-r', str(FPS), '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', out])
        parts.append((out, D))
    if final:
        D = final['D']
        v = (f"drawtext=fontfile={F}/plexmono.ttf:textfile={t(final['big'])}:fontsize={final.get('size', 54)}:fontcolor=0xf3ede4:"
             f"x=(w-tw)/2:y=(h-th)/2-20:alpha='min(1,max(0,(t-0.15)/0.3))*min(1,max(0,({D}-0.2-t)/0.5))',")
        if final.get('small'):
            v += (f"drawtext=fontfile={F}/corm-italic.ttf:textfile={t(final['small'])}:fontsize=36:fontcolor=0xd98b4a:"
                  f"x=(w-tw)/2:y=(h/2)+50:alpha='min(1,max(0,(t-0.7)/0.5))*min(1,max(0,({D}-0.2-t)/0.5))',")
        v += "noise=alls=7:allf=t,format=yuv420p"
        run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}', '-vf', v, '-t', str(D),
             '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', f'{wd}/e.mp4'])
        parts.append((f'{wd}/e.mp4', D))
    total = sum(d for _, d in parts)
    bounds, acc = [], 0
    for _, d in parts[:-1]:
        acc += d; bounds.append(round(acc, 3))
    expr = audio(total, bounds)
    ncol, nfilt = noise(total, bounds)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=44100:d={total}",
         '-f', 'lavfi', '-i', f"anoisesrc=color={ncol}:amplitude=0.6:r=44100:d={total}",
         '-filter_complex', f"[1:a]{nfilt}[n];[0:a][n]amix=inputs=2:normalize=0,afade=t=in:d=0.5,afade=t=out:st={total-0.7}:d=0.7,"
         "alimiter=limit=0.9,aformat=channel_layouts=stereo[a]", '-map', '[a]', f'{wd}/audio.wav'])
    open(f'{wd}/list.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p, _ in parts))
    os.makedirs('inserti_gatti', exist_ok=True)
    hq = f'inserti_gatti/Gatti-Inserto-{outname}-ALTA-QUALITA.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt', '-i', f'{wd}/audio.wav',
         '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '19', '-preset', 'slow', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', hq])
    web = f'inserti_gatti/Gatti-Inserto-{outname}.mp4'
    for p in (1, 2):
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', hq, '-c:v', 'libx264', '-b:v', '4500k', '-pass', str(p), '-preset', 'slow',
             '-passlogfile', f'{wd}/pass'] + (['-an', '-f', 'mp4', '/dev/null'] if p == 1 else ['-c:a', 'copy', '-movflags', '+faststart', web]))
    print(outname, 'durata', total, os.path.getsize(hq) // 1024, 'KB HQ', os.path.getsize(web) // 1024, 'KB web')


DRONE = "0.30*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.12*t))+0.15*sin(2*PI*82.41*t)"

# A · L'appello in tv: ronzio del televisore, una voce lontana e incomprensibile
A = [
    dict(img='gA', D=5.0, z="1.0+0.10*on/{N}", br="0.03*sin(2*PI*t*9)-0.05*lt(mod(t,1.7),0.05)", texts=[("4 AGOSTO 2005", 1.0, 4.8)]),
    dict(img='gA', D=5.0, crop=(760, 120, 1600, 900), z="1.0+0.22*on/{N}", br="0.04*sin(2*PI*t*11)-0.07*lt(mod(t,1.3),0.04)",
         texts=[("UN NIPOTE CHIEDE AIUTO IN TELEVISIONE", 0.5, 4.8)]),
]
aA = lambda T, b: f"0.5*({DRONE})+0.08*(sin(2*PI*50*t)+0.5*sin(2*PI*100*t))+{clicks(b)}"
nA = lambda T, b: ('white', "bandpass=f=700:width_type=h:w=900,volume='0.5*(0.35+0.65*gt(sin(2*PI*3.7*t)+0.6*sin(2*PI*5.3*t),0.1))*(0.5+0.5*gte(t,5))':eval=frame")

# B · Il garage e il luminol: spruzzi, battito lento, colpo finale
B = [
    dict(img='gB', D=5.0, z="1.0+0.10*on/{N}", texts=[("19 AGOSTO 2005 · IL GARAGE", 1.0, 4.8)], sat=0.9),
    dict(img='gB', D=5.0, crop=(1800, 900, 2040, 1148), z="1.0+0.18*on/{N}", shake=True,
         texts=[("TRACCE RIPULITE · FINO A UN METRO DA TERRA", 0.4, 4.8)], sat=0.9),
    dict(img='gB', D=3.0, crop=(200, 1060, 2000, 1012), z="1.08", pan='right', texts=[("IL DNA: È IL SANGUE DEGLI ZII", 0.3, 2.9)], sat=0.9),
]
aB = lambda T, b: (f"0.5*({DRONE})*lt(t,{b[2]})+{hb([1.0, 2.4, 3.9, 5.5, 7.0, 8.4, 9.7, 10.9, 12.0], 0.7)}"
                   f"+1.2*gte(t,{b[2]})*(sin(2*PI*34*(t-{b[2]}))+0.6*sin(2*PI*51*(t-{b[2]})))*exp(-1.2*(t-{b[2]}))+{clicks(b)}")
nB = lambda T, b: ('white', "highpass=f=2500,volume='0.02+0.45*(between(t,1.6,2.3)+between(t,3.3,3.8)+between(t,6.2,7.0)+between(t,8.6,9.1))':eval=frame")

# C · Lo scontrino: un orologio, poi il vento nel bosco
C = [
    dict(img='gC1', D=5.0, crop=(700, 1000, 2240, 1260), z="1.0+0.16*on/{N}", texts=[("LO SCONTRINO DELLA SPESA DEGLI ZII", 0.8, 4.8)]),
    dict(img='gC2', D=5.0, z="1.0+0.20*pow(on/{N},1.2)", texts=[("E VICINO AI SACCHI, IL SEDANO", 0.5, 4.8)], sat=0.8),
]
tick = '+'.join(f"0.3*gte(t,{x/1.0})*sin(2*PI*2400*(t-{x/1.0}))*exp(-150*(t-{x/1.0}))" for x in [0.4, 1.4, 2.4, 3.4, 4.4])
aC = lambda T, b: f"0.5*({DRONE})+{tick}+{clicks(b)}"
nC = lambda T, b: ('pink', f"lowpass=f=900,highpass=f=120,volume='0.03+0.30*gte(t,{b[0]})*(0.6+0.4*sin(2*PI*0.2*t))':eval=frame")

if 'A' in sys.argv:
    seq('gA', A, None, aA, nA, 'A-Lappello-in-tv')
if 'B' in sys.argv:
    seq('gB', B, dict(D=2.0, big='IL MATTATOIO', size=64, small='così lo chiameranno i giornali'), aB, nB, 'B-Il-garage-e-il-luminol')
if 'C' in sys.argv:
    seq('gC', C, None, aC, nC, 'C-Lo-scontrino')
