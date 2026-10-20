import json, subprocess, os

W, H, FPS = 1920, 1080, 25
F = 'fonts'
os.makedirs('inserti', exist_ok=True)
os.makedirs('txt', exist_ok=True)
d = [x for x in json.load(open('inserti.json')) if not os.environ.get('ONLY') or x['id']==os.environ['ONLY']]

FX = {
    'lamp':  "0.03*sin(2*PI*t*0.9)+0.015*sin(2*PI*t*5.7)",
    'bulb':  "0.025*sin(2*PI*t*0.7)-0.12*lt(mod(t,3.1),0.07)-0.07*between(mod(t,3.1),0.15,0.2)",
    'neon_cold': "-0.10*lt(mod(t,2.9),0.05)-0.07*between(mod(t,2.9),0.12,0.17)+0.01*sin(2*PI*t*7)",
    'breath': "0.05*sin(2*PI*t*0.25)-0.02-0.25*gt(t,6.6)*min(1,(t-6.6)/1.2)",
    'dust':  "0.02*sin(2*PI*t*0.3)",
    'rain':  "0.01*sin(2*PI*t*0.4)",
    '': "0",
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(1)


def zoom(move, N):
    c = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    return {
        'in': f"z='1.0+0.14*on/{N}':{c}",
        'deep': f"z='1.0+0.45*pow(on/{N},1.4)':{c}",
        'left': f"z='1.15':x='(iw-iw/zoom)*(1-on/{N})':y='ih/2-(ih/zoom/2)'",
        'right': f"z='1.15':x='(iw-iw/zoom)*(on/{N})':y='ih/2-(ih/zoom/2)'",
    }[move]


def beats(times, f1=52, f2=46, amp=0.9):
    return '+'.join(f"{amp}*gte(t,{t})*(sin(2*PI*{f1}*(t-{t}))*exp(-22*(t-{t}))+0.6*gte(t,{t+0.24})*sin(2*PI*{f2}*(t-{t+0.24}))*exp(-22*(t-{t+0.24})))" for t in times)


def sound(kind, D):
    drone = "0.35*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.1*t))+0.2*sin(2*PI*82.41*t)"
    noise = None
    if kind == 'rain':
        expr, noise = f"0.5*({drone})", ('white', 'highpass=f=1200,lowpass=f=7000,volume=0.22')
    elif kind == 'phone':
        on = "(between(t,1.5,2.5)+between(t,4.5,5.5))"
        expr = f"0.4*({drone})+0.35*{on}*(sin(2*PI*950*t)+0.7*sin(2*PI*1180*t))*(0.5+0.5*sin(2*PI*22*t))"
    elif kind == 'heart_stop':
        ts = [0.6, 1.5, 2.5, 3.6, 4.9, 6.4]
        expr = f"0.4*({drone})*(1-0.8*gt(t,7))+{beats(ts)}*(1-t/12)"
    elif kind == 'steps':
        ts = [0.8, 1.5, 2.2, 2.9, 3.6, 4.3, 5.0]
        expr = f"0.45*({drone})+" + '+'.join(f"0.8*gte(t,{t})*sin(2*PI*85*(t-{t}))*exp(-35*(t-{t}))" for t in ts)
        noise = ('brown', 'lowpass=f=400,volume=0.08')
    elif kind == 'heart':
        ts = [0.5 + i * 0.85 for i in range(int((D - 0.5) / 0.85))]
        expr = f"0.45*({drone})+{beats(ts)}"
    elif kind == 'hum':
        expr = f"0.35*({drone})+0.12*(sin(2*PI*100*t)+0.5*sin(2*PI*200*t)+0.3*sin(2*PI*300*t))*(1-0.9*lt(mod(t,2.9),0.05))"
    elif kind == 'sting':
        expr = f"0.45*({drone})+1.1*gte(t,3.2)*(sin(2*PI*38*(t-3.2))+0.5*sin(2*PI*57*(t-3.2)))*exp(-1.4*(t-3.2))"
        noise = ('brown', 'lowpass=f=300,volume=0.12')
    else:
        expr = f"0.6*({drone})"
        noise = ('brown', 'lowpass=f=250,volume=0.08')
    out = f'inserti/_{kind}.wav'
    inputs = ['-f', 'lavfi', '-i', f"aevalsrc='{expr}':s=44100:d={D}"]
    fc = "[0:a]lowpass=f=4000[a0];"
    if noise:
        inputs += ['-f', 'lavfi', '-i', f"anoisesrc=color={noise[0]}:amplitude=0.6:r=44100:d={D}"]
        fc += f"[1:a]{noise[1]}[a1];[a0][a1]amix=inputs=2:normalize=0[m];"
    else:
        fc += "[a0]anull[m];"
    fc += f"[m]afade=t=in:d=0.4,afade=t=out:st={D-0.8}:d=0.8,alimiter=limit=0.9,aformat=channel_layouts=stereo[a]"
    run(['ffmpeg', '-y', '-loglevel', 'error'] + inputs + ['-filter_complex', fc, '-map', '[a]', out])
    return out


for s in d:
    D = s['D']
    N = int(D * FPS)
    fx = s['fx']
    grade = "colorbalance=rs=-0.03:gs=-0.01:bs=0.04:rh=0.03:bh=-0.03"
    chain = (f"[0:v]scale=3840:2160,zoompan={zoom(s['move'], N)}:d={N}:s={W}x{H}:fps={FPS},"
             f"eq=brightness='{FX[fx]}':contrast=1.08:saturation=0.84:eval=frame,{grade}[bg];")
    extra = []
    if fx == 'rain':
        extra = ['-loop', '1', '-framerate', str(FPS), '-i', 'rain1.png', '-loop', '1', '-framerate', str(FPS), '-i', 'rain2.png']
        chain += ("[bg]format=yuva420p[bgy];[bgy][1:v]overlay=x=0:y='-1080+mod(t*1300\\,1080)':shortest=1[r1];"
                  "[r1][2:v]overlay=x=0:y='-1080+mod(t*2100\\,1080)':shortest=1,format=yuv420p[bg2];")
    else:
        chain += "[bg]null[bg2];"
    v = "[bg2]noise=alls=9:allf=t,vignette=PI/4.6,drawbox=x=0:y=0:w=iw:h=132:color=black:t=fill,drawbox=x=0:y=ih-132:w=iw:h=132:color=black:t=fill,"
    v += f"fade=t=in:st=0:d=0.5,fade=t=out:st={D-0.6}:d=0.6,"
    if s['testo']:
        p = f"txt/ins{s['id']}.txt"
        open(p, 'w').write(s['testo'])
        v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={p}:fontsize=30:fontcolor=0xf3ede4:x=(w-tw)/2:y=h-132-90:"
              f"alpha='min(1,max(0,(t-1.6)/0.9))*min(1,max(0,({D}-1.0-t)/0.6))',")
    if s.get('key'):
        p = 'txt/key.txt'
        open(p, 'w').write('SCENA DECISIVA')
        v += f"drawtext=fontfile={F}/plexmono.ttf:textfile={p}:fontsize=22:fontcolor=white:box=1:boxcolor=0xc8402f:boxborderw=10:x=w-tw-110:y=165:alpha='min(1,max(0,(t-0.4)/0.5))',"
    v += "format=yuv420p[v]"
    a = sound(s['snd'], D)
    out = f"inserti/Inserto-{s['id']}-{s['titolo'].replace(' ', '-').replace(chr(39), '')}.mp4"
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f"img/{s['img']}.jpg"] + extra + ['-i', a,
         '-filter_complex', chain + v, '-map', '[v]', '-map', f'{3 if extra else 1}:a', '-t', str(D), '-r', str(FPS),
         '-c:v', 'libx264', '-crf', os.environ.get('CRF','21'), '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
         '-movflags', '+faststart', out])
    print(out, os.path.getsize(out) // 1024, 'KB')
