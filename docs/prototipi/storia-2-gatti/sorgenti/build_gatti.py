import os, subprocess, shutil
from build_seq import build, hb, clicks, run, W, H, FPS, F

for k in ('g1', 'g2', 'g3'):
    if not os.path.exists(f'img/{k}.jpg'):
        shutil.copy(f'../r3/img/{k}.jpg', f'img/{k}.jpg')
os.makedirs('inserti_gatti', exist_ok=True)
os.makedirs('txt', exist_ok=True)


def single(nid, title, img, D, z, text, snd_expr, noise, out, br="0", xs=None):
    N = int(D * FPS)
    xs = xs or "iw/2-(iw/zoom/2)"
    p = f'txt/g{nid}.txt'
    open(p, 'w').write(text)
    v = (f"scale=3840:2160,zoompan=z='{z.format(N=N)}':x='{xs.format(N=N)}':y='ih/2-(ih/zoom/2)':d={N}:s={W}x{H}:fps={FPS},"
         f"eq=brightness='{br}':contrast=1.1:saturation=0.82:eval=frame,colorbalance=rs=-0.03:bs=0.04:rh=0.03:bh=-0.03,"
         "noise=alls=9:allf=t,vignette=PI/4.6,drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"
         f"fade=t=in:st=0:d=0.5,fade=t=out:st={D-0.6}:d=0.6,"
         f"drawtext=fontfile={F}/plexmono.ttf:textfile={p}:fontsize=30:fontcolor=0xf3ede4:x=(w-tw)/2:y=h-132-90:"
         f"alpha='min(1,max(0,(t-1.6)/0.9))*min(1,max(0,({D}-1.0-t)/0.6))',format=yuv420p")
    a = f'inserti_gatti/_a{nid}.wav'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f"aevalsrc='{snd_expr}':s=44100:d={D}",
         '-f', 'lavfi', '-i', f"anoisesrc=color={noise[0]}:amplitude=0.6:r=44100:d={D}",
         '-filter_complex', f"[1:a]{noise[1]}[n];[0:a][n]amix=inputs=2:normalize=0,afade=t=in:d=0.4,afade=t=out:st={D-0.8}:d=0.8,alimiter=limit=0.9,aformat=channel_layouts=stereo[a]",
         '-map', '[a]', a])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f'img/{img}.jpg', '-i', a, '-vf', v, '-map', '0:v', '-map', '1:a',
         '-t', str(D), '-r', str(FPS), '-c:v', 'libx264', '-crf', '21', '-preset', 'medium', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out])
    print(out, os.path.getsize(out) // 1024, 'KB')


drone = "0.33*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.1*t))+0.18*sin(2*PI*82.41*t)"
# 01 la villetta di notte: cicale d'estate
single('01', 'La villetta di notte', 'g1', 8, "1.0+0.12*on/{N}", 'BRESCIA · ESTATE 2005',
       f"0.5*({drone})", ('white', "bandpass=f=4800:width_type=h:w=1800,volume='0.35*(0.55+0.45*sin(2*PI*28*t))*(0.7+0.3*sin(2*PI*0.4*t))':eval=frame"),
       'inserti_gatti/Gatti-Inserto-01-La-villetta.mp4')
# 03 i boschi della Val Paisco: vento
single('03', 'I boschi della Val Paisco', 'g3', 10, "1.0+0.16*on/{N}", 'VAL PAISCO · 17 AGOSTO 2005',
       f"0.55*({drone})", ('pink', "lowpass=f=900,highpass=f=120,volume='0.22*(0.6+0.4*sin(2*PI*0.15*t))':eval=frame"),
       'inserti_gatti/Gatti-Inserto-03-Val-Paisco.mp4')
# 04 il corridoio del carcere: rimbombo di una porta di ferro
door = "1.0*gte(t,2.0)*(sin(2*PI*62*(t-2))+0.5*sin(2*PI*131*(t-2))+0.3*sin(2*PI*247*(t-2)))*exp(-2.2*(t-2))"
single('04', 'Il corridoio del carcere', 'carcere', 8, "1.0+0.22*pow(on/{N},1.2)", 'OPERA · GIUGNO 2023',
       f"0.45*({drone})+{door}", ('brown', "lowpass=f=300,volume=0.08"),
       'inserti_gatti/Gatti-Inserto-04-Il-carcere.mp4')


# 02 la strada del Vivione: versione lunga
def audio_vivione(total, cut, bounds):
    beats, tt, per = [], 2.0, 0.95
    while tt < cut - 0.2:
        beats.append(round(tt, 3)); per = max(0.45, per * 0.94); tt += per
    eng = f"0.22*(sin(2*PI*48*t)+0.6*sin(2*PI*96*t)+0.3*sin(2*PI*144*t))*(0.6+0.4*sin(2*PI*3*t))*lt(t,{bounds[1]})"
    b0 = bounds[0]
    whoosh = f"0.0"
    boom = f"1.25*gte(t,{cut})*(sin(2*PI*36*(t-{cut}))+0.6*sin(2*PI*54*(t-{cut})))*exp(-1.0*(t-{cut}))"
    dr = f"0.3*sin(2*PI*55*t)*lt(t,{cut})+0.16*sin(2*PI*82.41*t)*lt(t,{cut})"
    # il passaggio dell'auto: rumore che sale e scende intorno all'inizio della seconda inquadratura
    noise_vol = f"0.05+0.5*exp(-pow((t-{b0}-0.6)/0.45,2))+0.2*gte(t,{cut})*exp(-0.8*(t-{cut}))"
    return f"{hb(beats, 0.8)}+{eng}+{dr}+{boom}+{clicks(bounds)}", noise_vol


VIVIONE = [
    dict(img='g2', D=5.0, z="1.0+0.14*on/{N}", texts=[("1° AGOSTO 2005 · VERSO IL PASSO DEL VIVIONE", 0.8, 4.8)]),
    dict(img='g2', D=4.5, crop=(440, 600, 768, 432), z="1.0+0.25*on/{N}", shake=True, texts=[("UN'AUTO QUASI LO SFIORA", 0.4, 4.3)]),
    dict(img='g2', D=4.0, crop=(900, 250, 960, 540), z="1.0+0.20*on/{N}", pan='right', texts=[("AL VOLANTE, UN UOMO PALLIDO, SENZA FIATO", 0.4, 3.8)]),
    dict(img='g1', D=3.5, z="1.10+0.20*on/{N}", shake=True, texts=[("È IL NIPOTE DEI DUE ANZIANI SCOMPARSI", 0.3, 3.3)]),
]
build('vivione', VIVIONE, dict(D=4.0, big='UN RAGAZZO DI 14 ANNI LO RICONOSCE', size=44, small='e il padre lo segnala ai carabinieri'),
      audio_vivione, 'G02-Il-Vivione')
for f in ('Inserto-G02-Il-Vivione-HQ.mp4',):
    shutil.move(f, 'inserti_gatti/Gatti-Inserto-02-Il-Vivione-ALTA-QUALITA.mp4')
shutil.move('inserti/Inserto-G02-Il-Vivione.mp4', 'inserti_gatti/Gatti-Inserto-02-Il-Vivione.mp4')
