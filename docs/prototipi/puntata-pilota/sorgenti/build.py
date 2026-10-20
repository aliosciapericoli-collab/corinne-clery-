import json, subprocess, os, textwrap

W, H, FPS = 1280, 720, 25
T = 1.0  # durata dissolvenza incrociata
F = 'fonts'
os.makedirs('clips', exist_ok=True)
os.makedirs('txt', exist_ok=True)
d = json.load(open('script.json'))


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(1)


def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))


def txt(name, s):
    p = f'txt/{name}.txt'
    open(p, 'w').write(s)
    return p


FX = {
    'lamp':  "0.03*sin(2*PI*t*0.9)+0.015*sin(2*PI*t*5.7)",
    'hearth': "0.035*sin(2*PI*t*1.3)+0.02*sin(2*PI*t*4.1)+0.012*sin(2*PI*t*9.3)",
    'bulb':  "0.025*sin(2*PI*t*0.7)-0.10*lt(mod(t,4.7),0.07)-0.06*between(mod(t,4.7),0.15,0.2)",
    'neon':  "0.03*sin(2*PI*t*0.5)+0.07*lt(mod(t,3.9),0.06)-0.05*between(mod(t,3.9),0.1,0.16)",
    'neon_cold': "-0.09*lt(mod(t,5.3),0.05)-0.06*between(mod(t,5.3),0.12,0.17)+0.01*sin(2*PI*t*7)",
    'breath': "0.045*sin(2*PI*t*0.22)-0.02",
    'dust':  "0.02*sin(2*PI*t*0.3)",
    'rain':  "0.01*sin(2*PI*t*0.4)",
    '': "0",
}


def zoom(move, N):
    c = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if move == 'in':
        return f"z='1.0+0.12*on/{N}':{c}"
    if move == 'in2':
        return f"z='1.12+0.10*on/{N}':x='iw*0.06+(iw-iw/zoom)*0.4':y='ih/2-(ih/zoom/2)'"
    if move == 'deep':
        return f"z='1.0+0.38*pow(on/{N},1.3)':{c}"
    if move == 'left':
        return f"z='1.14':x='(iw-iw/zoom)*(1-on/{N})':y='ih/2-(ih/zoom/2)'"
    if move == 'right':
        return f"z='1.14':x='(iw-iw/zoom)*(on/{N})':y='ih/2-(ih/zoom/2)'"
    return f"z='1.06':{c}"


scenes = []
for si, s in enumerate(d):
    out = f'clips/{si:02d}.mp4'
    aout = f'clips/{si:02d}.wav'
    if os.path.exists(out) and os.path.exists(aout) and os.path.getsize(out) > 10000:
        scenes.append({'D': dur(aout), 'key': s.get('key', False)})
        print(si, 'riuso')
        continue
    if 'title' in s:
        D = 6.0 if si < len(d) - 1 else 7.0
        k = txt(f'{si}_k', s['sub'].upper())
        t = txt(f'{si}_t', s['title'])
        vf = (f"drawtext=fontfile={F}/plexmono.ttf:textfile={k}:fontsize=17:fontcolor=0xd98b4a:x=(w-tw)/2:y=h/2-70:alpha='min(1,max(0,(t-0.6)/1.2))',"
              f"drawtext=fontfile={F}/corm-italic.ttf:textfile={t}:fontsize=72:fontcolor=0xf3ede4:x=(w-tw)/2:y=h/2-20:alpha='min(1,max(0,(t-1.4)/1.6))',"
              f"noise=alls=8:allf=t,format=yuv420p")
        run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', f'color=black:s={W}x{H}:r={FPS}', '-vf', vf, '-t', str(D),
             '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', out])
        run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', str(D), aout])
        scenes.append({'D': D, 'key': False})
        continue

    key = s.get('key', False)
    lead = 1.3 if s['m'] == 'rec' else 0.9
    gap = 1.25 if key else 0.8
    tail = 1.6
    files = [f'audio/{si:02d}_{li}.mp3' for li in range(len(s['lines']))]
    lens = [dur(f) for f in files]
    # traccia voce: silenzio + battute separate da pause
    inputs, parts, t0, subs = [], [], lead, []
    fc = f"anullsrc=r=44100:cl=stereo,atrim=0:{lead}[s0];"
    parts.append('[s0]')
    for li, (f, L) in enumerate(zip(files, lens)):
        inputs += ['-i', f]
        fc += f"[{li}:a]aresample=44100,aformat=channel_layouts=stereo[v{li}];"
        parts.append(f'[v{li}]')
        subs.append((t0, t0 + L, s['lines'][li]))
        t0 += L
        g = gap if li < len(files) - 1 else tail
        fc += f"anullsrc=r=44100:cl=stereo,atrim=0:{g}[g{li}];"
        parts.append(f'[g{li}]')
        t0 += g
    D = t0
    fc += ''.join(parts) + f"concat=n={len(parts)}:v=0:a=1[a]"
    run(['ffmpeg', '-y', '-loglevel', 'error'] + inputs + ['-filter_complex', fc, '-map', '[a]', aout])

    N = int(D * FPS)
    fx = s.get('fx', '')
    grade = "colorbalance=rs=-0.03:gs=-0.01:bs=0.04:rh=0.03:bh=-0.03"
    if s['m'] == 'cor' or fx == 'hearth':
        grade = "colorbalance=rs=0.02:bs=-0.03:rh=0.04:bh=-0.04"
    chain = (f"[0:v]scale=2560:1440,zoompan={zoom(s.get('move','in'), N)}:d={N}:s={W}x{H}:fps={FPS},"
             f"eq=brightness='{FX.get(fx,'0')}':contrast=1.08:saturation=0.84:eval=frame,{grade}[bg];")
    extra_in = []
    if fx == 'rain':
        extra_in = ['-loop', '1', '-framerate', str(FPS), '-i', 'rain1.png', '-loop', '1', '-framerate', str(FPS), '-i', 'rain2.png']
        chain += ("[1:v]scale=1280:1440[ra];[2:v]scale=1280:1440[rb];[bg]format=yuva420p[bgy];[bgy][ra]overlay=x=0:y='-720+mod(t*870\\,720)':shortest=1[r1];"
                  "[r1][rb]overlay=x=0:y='-720+mod(t*1400\\,720)':shortest=1,format=yuv420p[bg2];")
    else:
        chain += "[bg]null[bg2];"
    v = "[bg2]noise=alls=9:allf=t,vignette=PI/4.6,"
    v += "drawbox=x=0:y=0:w=iw:h=88:color=black:t=fill,drawbox=x=0:y=ih-88:w=iw:h=88:color=black:t=fill,"
    v += f"fade=t=in:st=0:d=0.6,fade=t=out:st={D-0.6:.2f}:d=0.6,"
    if s.get('cap'):
        c = txt(f'{si}_cap', s['cap'].upper())
        v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={c}:fontsize=17:fontcolor=0xece6dc:x=70:y=112:"
              f"alpha='min(1,max(0,(t-1.0)/1.0))*min(1,max(0,({D}-1.2-t)/1.0))',")
    if key:
        k = txt(f'{si}_key', 'SCENA DECISIVA')
        v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={k}:fontsize=15:fontcolor=white:box=1:boxcolor=0xc8402f:boxborderw=7:"
              f"x=w-tw-76:y=110:alpha='min(1,max(0,(t-0.6)/0.6))',")
    if s['m'] == 'cor':
        k = txt(f'{si}_cor', 'QUI CORINNE IN CAMERA')
        v += (f"drawtext=fontfile={F}/plexmono.ttf:textfile={k}:fontsize=15:fontcolor=0x1a1006:box=1:boxcolor=0xd98b4a:boxborderw=7:"
              f"x=w-tw-76:y=110,")
    for j, (a, b, line) in enumerate(subs):
        wrapped = '\n'.join(textwrap.wrap(line, 62))
        p = txt(f'{si}_s{j}', wrapped)
        v += (f"drawtext=fontfile={F}/corm.ttf:textfile={p}:fontsize=33:line_spacing=6:fontcolor=0xf4efe6:"
              f"shadowcolor=black@0.9:shadowx=2:shadowy=2:x=(w-tw)/2:y=h-102-th:enable='between(t,{a:.2f},{b+0.25:.2f})',")
    v += "format=yuv420p[v]"
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f"img/{s['img']}.jpg"] + extra_in +
        ['-filter_complex', chain + v, '-map', '[v]', '-t', f'{D:.3f}', '-r', str(FPS),
         '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', out])
    scenes.append({'D': D, 'key': key})
    print(si, f'{D:.1f}s', s.get('img'))

# --- montaggio con dissolvenze incrociate ---
n = len(scenes)
offs, acc = [], 0.0
for i in range(n - 1):
    acc += scenes[i]['D'] - T
    offs.append(acc)
total = sum(s['D'] for s in scenes) - T * (n - 1)
starts = [0.0] + offs
json.dump({'scenes': [dict(s, start=st) for s, st in zip(scenes, starts)], 'total': total}, open('timeline.json', 'w'), indent=1)

inp = []
for i in range(n):
    inp += ['-i', f'clips/{i:02d}.mp4']
for i in range(n):
    inp += ['-i', f'clips/{i:02d}.wav']
fc = ''
prev = '[0:v]'
for i in range(1, n):
    o = f'[x{i}]' if i < n - 1 else '[vout]'
    fc += f"{prev}[{i}:v]xfade=transition=fade:duration={T}:offset={offs[i-1]:.3f}{o};"
    prev = o
prev = f'[{n}:a]'
for i in range(1, n):
    o = f'[y{i}]' if i < n - 1 else '[voice]'
    fc += f"{prev}[{n+i}:a]acrossfade=d={T}:c1=tri:c2=tri{o};"
    prev = o
fc = fc.rstrip(';')
run(['ffmpeg', '-y', '-loglevel', 'error'] + inp + ['-filter_complex', fc, '-map', '[vout]', '-map', '[voice]',
     '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-c:a', 'pcm_s16le', 'assembled.mkv'])

# --- musica: bordone grave + battito sulle scene decisive ---
keyw = [(st, st + s['D']) for s, st in zip(scenes, starts) if s['key']]
gate = '+'.join(f'between(t,{a:.2f},{b:.2f})' for a, b in keyw) or '0'
beat = ("(0.9*sin(2*PI*52*t)*exp(-22*mod(t,0.9))+0.6*sin(2*PI*46*t)*exp(-22*mod(t-0.24,0.9))*gt(mod(t,0.9),0.24))")
run(['ffmpeg', '-y', '-loglevel', 'error',
     '-f', 'lavfi', '-i', f"aevalsrc='0.5*sin(2*PI*55*t)*(0.7+0.3*sin(2*PI*0.07*t))+0.3*sin(2*PI*82.41*t)*(0.6+0.4*sin(2*PI*0.05*t+1))+0.15*sin(2*PI*110.3*t)':s=44100:d={total:.2f}",
     '-f', 'lavfi', '-i', f"anoisesrc=color=brown:amplitude=0.5:r=44100:d={total:.2f}",
     '-f', 'lavfi', '-i', f"aevalsrc='min(1\\,{gate})*{beat}':s=44100:d={total:.2f}",
     '-filter_complex',
     "[0:a]lowpass=f=300,volume=0.20[a0];[1:a]lowpass=f=220,volume=0.10[a1];[2:a]lowpass=f=160,volume=0.55[a2];"
     f"[a0][a1][a2]amix=inputs=3:normalize=0,afade=t=in:d=3,afade=t=out:st={total-4:.2f}:d=4,aformat=channel_layouts=stereo[m]",
     '-map', '[m]', 'music.wav'])

run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'assembled.mkv', '-i', 'music.wav', '-filter_complex',
     "[0:a]volume=1.0[v];[1:a]volume=0.9[m];[v][m]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
     '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-crf', '24', '-preset', 'slow', '-movflags', '+faststart',
     '-c:a', 'aac', '-b:a', '128k', 'pilota.mp4'])
print('TOTALE', round(total, 1), 's')
