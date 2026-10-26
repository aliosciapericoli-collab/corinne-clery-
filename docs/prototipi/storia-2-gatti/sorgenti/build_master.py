# Versione «master» degli inserti: sorgenti 4K, movimento calcolato a 8K (niente scatti),
# grana leggera, codifica ad alta qualità. Uscite: MASTER 1080p (per il montaggio) e web (per l'archivio).
import os, sys
from build_seq import run, hb, clicks, FPS, F

BARS = "drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"


def seq(name, shots, final, audio, noise, outname):
    wd = f'master_{name}'
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
    os.makedirs('inserti_master', exist_ok=True)
    master = f'inserti_master/Gatti-Inserto-{outname}-MASTER.mp4'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{wd}/list.txt', '-i', f'{wd}/audio.wav',
         '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-tune', 'film', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', master])
    web = f'inserti_master/Gatti-Inserto-{outname}.mp4'
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


SEQ = {}
# 01 · La villetta di notte: cicale d'estate
SEQ['01'] = ([dict(img='m01a', D=4.5, z="1.0+0.06*on/{N}", texts=[("BRESCIA · ESTATE 2005", 1.2, 4.4)]),
              dict(img='m01b', D=3.5, z="1.04+0.06*on/{N}", texts=[("QUARTIERE SANT'ANNA", 0.4, 3.4)])],
             None, lambda T, b: f"0.5*({DRONE})+{clicks(b)}",
             lambda T, b: ('white', "bandpass=f=4800:width_type=h:w=1800,volume='0.35*(0.55+0.45*sin(2*PI*28*t))*(0.7+0.3*sin(2*PI*0.4*t))':eval=frame"),
             '01-La-villetta')
# A · L'appello in tv
SEQ['A'] = ([dict(img='gA', D=5.0, z="1.0+0.07*on/{N}", br="0.03*sin(2*PI*t*9)-0.05*lt(mod(t,1.7),0.05)", texts=[("4 AGOSTO 2005", 1.0, 4.8)]),
             dict(img='mA2', D=5.0, z="1.0+0.10*on/{N}", br="0.04*sin(2*PI*t*11)-0.07*lt(mod(t,1.3),0.04)", texts=[("UN NIPOTE CHIEDE AIUTO IN TELEVISIONE", 0.5, 4.8)])],
            None, lambda T, b: f"0.5*({DRONE})+0.08*(sin(2*PI*50*t)+0.5*sin(2*PI*100*t))+{clicks(b)}",
            lambda T, b: ('white', "bandpass=f=700:width_type=h:w=900,volume='0.5*(0.35+0.65*gt(sin(2*PI*3.7*t)+0.6*sin(2*PI*5.3*t),0.1))*(0.5+0.5*gte(t,5))':eval=frame"),
            'A-Lappello-in-tv')
# 02 · La strada del Vivione: battito che accelera, motore, colpo sul nero
def a02(T, b):
    cut = b[-1]
    eng = f"0.22*(sin(2*PI*48*t)+0.6*sin(2*PI*96*t)+0.3*sin(2*PI*144*t))*(0.6+0.4*sin(2*PI*3*t))*between(t,{b[0]},{b[2]})"
    boom = f"1.25*gte(t,{cut})*(sin(2*PI*36*(t-{cut}))+0.6*sin(2*PI*54*(t-{cut})))*exp(-1.0*(t-{cut}))"
    dr = f"0.3*sin(2*PI*55*t)*lt(t,{cut})+0.16*sin(2*PI*82.41*t)*lt(t,{cut})"
    return f"{hb(hbeats(1.5, cut, 0.95, 0.94), 0.8)}+{eng}+{dr}+{boom}+{clicks(b)}"
SEQ['02'] = ([dict(img='m02a', D=5.0, z="1.0+0.07*on/{N}", texts=[("AGOSTO 2005 · VERSO IL PASSO DEL VIVIONE", 0.8, 4.8)]),
              dict(img='m02b', D=4.5, z="1.02+0.08*on/{N}", shake=True, texts=[("UN'AUTO QUASI LI INVESTE", 0.4, 4.3)]),
              dict(img='m02c', D=4.0, z="1.0+0.08*on/{N}", shake=True, texts=[("AL VOLANTE, UN UOMO PALLIDO, SENZA FIATO", 0.4, 3.8)]),
              dict(img='m02d', D=3.5, z="1.0+0.06*on/{N}", texts=[("È IL NIPOTE DEI DUE ANZIANI SCOMPARSI", 0.3, 3.3)])],
             dict(D=4.0, big='UN RAGAZZO DI 14 ANNI LO RICONOSCE', size=46, small='e il padre lo segnala ai carabinieri'),
             a02, lambda T, b: ('brown', f"lowpass=f=300,volume='0.05+0.5*exp(-pow((t-{b[0]}-0.6)/0.45,2))+0.2*gte(t,{b[-1]})*exp(-0.8*(t-{b[-1]}))':eval=frame"),
             '02-Il-Vivione')
# 03 · I boschi: vento
SEQ['03'] = ([dict(img='m03a', D=5.5, z="1.0+0.07*on/{N}", texts=[("17 AGOSTO 2005 · I BOSCHI SOTTO IL VIVIONE", 0.8, 5.3)], sat=0.8),
              dict(img='m03b', D=4.5, z="1.0+0.08*on/{N}", texts=[("SETTE, FORSE OTTO SACCHI NERI", 0.4, 4.3)], sat=0.8)],
             None, lambda T, b: f"0.55*({DRONE})+{clicks(b)}",
             lambda T, b: ('pink', "lowpass=f=900,highpass=f=120,volume='0.22*(0.6+0.4*sin(2*PI*0.15*t))':eval=frame"),
             '03-I-boschi')
# B · Il garage e il luminol
SEQ['B'] = ([dict(img='gB', D=5.0, z="1.0+0.07*on/{N}", texts=[("19 AGOSTO 2005 · IL GARAGE", 1.0, 4.8)], sat=0.9),
             dict(img='mB2', D=5.0, z="1.0+0.08*on/{N}", shake=True, texts=[("TRACCE RIPULITE · FINO A UN METRO DA TERRA", 0.4, 4.8)], sat=0.9),
             dict(img='mB3', D=3.0, z="1.04", pan='right', texts=[("IL DNA: È IL SANGUE DEGLI ZII", 0.3, 2.9)], sat=0.9)],
            dict(D=2.0, big='IL MATTATOIO', size=64, small='così lo chiameranno i giornali'),
            lambda T, b: (f"0.5*({DRONE})*lt(t,{b[2]})+{hb([1.0, 2.4, 3.9, 5.5, 7.0, 8.4, 9.7, 10.9, 12.0], 0.7)}"
                          f"+1.2*gte(t,{b[2]})*(sin(2*PI*34*(t-{b[2]}))+0.6*sin(2*PI*51*(t-{b[2]})))*exp(-1.2*(t-{b[2]}))+{clicks(b)}"),
            lambda T, b: ('white', "highpass=f=2500,volume='0.02+0.45*(between(t,1.6,2.3)+between(t,3.3,3.8)+between(t,6.2,7.0)+between(t,8.6,9.1))':eval=frame"),
            'B-Il-garage-e-il-luminol')
# C · Lo scontrino
tick = '+'.join(f"0.3*gte(t,{x})*sin(2*PI*2400*(t-{x}))*exp(-150*(t-{x}))" for x in [0.4, 1.4, 2.4, 3.4, 4.4])
SEQ['C'] = ([dict(img='gC1', D=5.0, z="1.0+0.08*on/{N}", texts=[("LO SCONTRINO DELLA SPESA DEGLI ZII", 0.8, 4.8)]),
             dict(img='gC2', D=5.0, z="1.0+0.10*pow(on/{N},1.2)", texts=[("E VICINO AI SACCHI, IL SEDANO", 0.5, 4.8)], sat=0.8)],
            None, lambda T, b: f"0.5*({DRONE})+{tick}+{clicks(b)}",
            lambda T, b: ('pink', f"lowpass=f=900,highpass=f=120,volume='0.03+0.30*gte(t,{b[0]})*(0.6+0.4*sin(2*PI*0.2*t))':eval=frame"),
            'C-Lo-scontrino')
# 04 · Il corridoio del carcere: una porta di ferro che rimbomba
door = "1.0*gte(t,2.0)*(sin(2*PI*62*(t-2))+0.5*sin(2*PI*131*(t-2))+0.3*sin(2*PI*247*(t-2)))*exp(-2.2*(t-2))"
SEQ['04'] = ([dict(img='carcere_4k', D=4.5, z="1.0+0.10*pow(on/{N},1.2)", texts=[("CARCERE DI OPERA · GIUGNO 2023", 0.8, 4.4)], sat=0.75),
              dict(img='m04b', D=3.5, z="1.0+0.06*on/{N}", texts=[("NESSUNO LO SAPRÀ PER QUASI TRE ANNI", 0.4, 3.4)], sat=0.75)],
             None, lambda T, b: f"0.45*({DRONE})+{door}+{clicks(b)}",
             lambda T, b: ('brown', "lowpass=f=300,volume=0.08"),
             '04-Il-carcere')
# D · La croce senza nome: vento, una campana lontana
bell = '+'.join(f"0.45*gte(t,{x})*(sin(2*PI*392*(t-{x}))+0.5*sin(2*PI*784*(t-{x}))+0.3*sin(2*PI*1176*(t-{x})))*exp(-0.9*(t-{x}))" for x in (1.2, 6.0))
SEQ['D'] = ([dict(img='gD', D=5.5, z="1.0+0.06*on/{N}", texts=[("MILANO · CIMITERO MAGGIORE", 1.0, 5.3)], sat=0.7),
             dict(img='mD2', D=4.5, z="1.0+0.06*on/{N}", texts=[("UNA CROCE. E UN NUMERO.", 0.6, 4.4)], sat=0.7)],
            None, lambda T, b: f"0.35*({DRONE})+{bell}",
            lambda T, b: ('pink', "lowpass=f=700,highpass=f=100,volume='0.30*(0.6+0.4*sin(2*PI*0.18*t))':eval=frame"),
            'D-La-croce-senza-nome')

for k in [a for a in sys.argv[1:] if a in SEQ]:
    shots, final, aud, noi, out = SEQ[k]
    seq(k, shots, final, aud, noi, out)
