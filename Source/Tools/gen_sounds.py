# Генератор звуков Зоны: всё синтезируется с нуля (шум, фильтры, синусы),
# никаких чужих записей. Результат — WAV 22 кГц моно в Common/Sounds/SZ/...
import math, random, struct, wave, os
SR = 22050
ROOT = '/mnt/user-data/outputs/StalkerZone/Common/Sounds/SZ'

def write(path, samples):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    peak = max(1e-9, max(abs(s) for s in samples))
    k = 0.9 / peak
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, s * k)) * 32767)) for s in samples))

def lp(x, a):          # однополюсный ФНЧ (a: 0..1, меньше — глуше)
    y, out = 0.0, []
    for s in x: y += a * (s - y); out.append(y)
    return out
def hp(x, a):
    l = lp(x, a); return [s - t for s, t in zip(x, l)]
def env(n, attack, decay_pow=2.0):
    out = []
    for i in range(n):
        t = i / n
        out.append(min(1.0, t / attack) * (1 - t) ** decay_pow if attack > 0 else (1 - t) ** decay_pow)
    return out
def noise(n, rnd): return [rnd.uniform(-1, 1) for _ in range(n)]
def mix(*tracks):
    n = max(len(t) for t in tracks); out = [0.0] * n
    for t in tracks:
        for i, s in enumerate(t): out[i] += s
    return out
def silence(sec): return [0.0] * int(sec * SR)

def electro_discharge(seed):
    rnd = random.Random(seed); n = int(.7 * SR)
    burst = [s * e for s, e in zip(hp(noise(n, rnd), .25), env(n, .01, 3))]
    clicks = [0.0] * n
    for _ in range(60):                 # треск: короткие импульсы
        p = int(rnd.uniform(0, .55) * SR); a = rnd.uniform(.4, 1)
        for j in range(60):
            if p + j < n: clicks[p + j] += a * (rnd.uniform(-1, 1)) * (1 - j / 60)
    buzz = [.35 * math.sin(2 * math.pi * 110 * i / SR) * (1 if math.sin(2 * math.pi * 55 * i / SR) > 0 else -.6) * (1 - i / n) ** 2 for i in range(n)]
    return mix([.7 * s for s in burst], clicks, buzz)
def electro_idle(seed):
    rnd = random.Random(seed); n = int(.9 * SR)
    hum = [(.5 * math.sin(2 * math.pi * 100 * i / SR) + .2 * math.sin(2 * math.pi * 300 * i / SR)) * (.6 + .4 * math.sin(2 * math.pi * 3 * i / SR)) for i in range(n)]
    cr = [0.0] * n
    for _ in range(8):
        p = int(rnd.uniform(0, .85) * SR)
        for j in range(40):
            if p + j < n: cr[p + j] += rnd.uniform(-1, 1) * (1 - j / 40)
    e = env(n, .15, .6)
    return [(h * .5 + c * .6) * k for h, c, k in zip(hum, cr, e)]
def gravity_discharge(seed):
    rnd = random.Random(seed); n = int(1.0 * SR); ph = 0.0; thump = []
    for i in range(n):
        f = 70 - 40 * (i / n); ph += 2 * math.pi * f / SR
        thump.append(math.sin(ph) * (1 - i / n) ** 2.5)
    whoosh = lp(noise(n, rnd), .04)
    we = [min(1, (i / n) / .25) * (1 - i / n) ** 1.5 for i in range(n)]
    return mix(thump, [3 * s * e for s, e in zip(whoosh, we)])
def gravity_idle(seed):
    rnd = random.Random(seed); n = int(1.2 * SR)
    wob = [math.sin(2 * math.pi * (45 + 6 * math.sin(2 * math.pi * 1.5 * i / SR)) * i / SR) for i in range(n)]
    wind = lp(noise(n, rnd), .02)
    e = env(n, .3, .8)
    return [(w * .6 + 4 * d) * k for w, d, k in zip(wob, wind, e)]
def fire_discharge(seed):
    rnd = random.Random(seed); n = int(1.0 * SR)
    roar = lp(noise(n, rnd), .08)
    e = [min(1, (i / n) / .08) * (1 - i / n) ** 1.2 for i in range(n)]
    cr = [0.0] * n
    for _ in range(40):
        p = int(rnd.uniform(0, .9) * SR)
        for j in range(25):
            if p + j < n: cr[p + j] += rnd.uniform(-.6, .6) * (1 - j / 25)
    return mix([3 * s * k for s, k in zip(roar, e)], cr)
def fire_idle(seed):
    rnd = random.Random(seed); n = int(.9 * SR)
    base = lp(noise(n, rnd), .05); cr = [0.0] * n
    for _ in range(25):
        p = int(rnd.uniform(0, .85) * SR)
        for j in range(20):
            if p + j < n: cr[p + j] += rnd.uniform(-.7, .7) * (1 - j / 20)
    e = env(n, .2, .7)
    return [(2 * b + c) * k for b, c, k in zip(base, cr, e)]
def bubbles(n, rnd, count, fmin, fmax):
    out = [0.0] * n
    for _ in range(count):
        p = int(rnd.uniform(0, n / SR - .1) * SR); f0 = rnd.uniform(fmin, fmax); L = int(rnd.uniform(.03, .07) * SR)
        for j in range(L):
            if p + j < n:
                f = f0 * (1 + 1.5 * j / L)            # пузырь: тон уходит вверх
                out[p + j] += math.sin(2 * math.pi * f * j / SR) * (1 - j / L) * .7
    return out
def acid_discharge(seed):
    rnd = random.Random(seed); n = int(.9 * SR)
    sizzle = [s * e for s, e in zip(hp(noise(n, rnd), .4), env(n, .02, 1.5))]
    return mix([.8 * s for s in sizzle], bubbles(n, rnd, 18, 300, 700))
def acid_idle(seed):
    rnd = random.Random(seed); n = int(1.0 * SR)
    return [s * e for s, e in zip(bubbles(n, rnd, 7, 200, 500), env(n, .1, .5))]
def fuzz_discharge(seed):
    rnd = random.Random(seed); n = int(.8 * SR)
    r = hp(lp(noise(n, rnd), .5), .15)
    mod = [(.5 + .5 * math.sin(2 * math.pi * 18 * i / SR)) for i in range(n)]
    return [s * m * e for s, m, e in zip(r, mod, env(n, .05, 1.3))]
def tone(f, sec, fade=.15):
    n = int(sec * SR)
    return [math.sin(2 * math.pi * f * i / SR) * min(1, i / (n * fade), (n - i) / (n * fade)) for i in range(n)]
def chirp(f0, f1, sec):
    n = int(sec * SR); ph = 0.0; out = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / n; ph += 2 * math.pi * f / SR
        out.append(math.sin(ph) * min(1, i / (n * .1), (n - i) / (n * .1)))
    return out
def click(seed):
    rnd = random.Random(seed); n = int(.012 * SR)
    return [rnd.uniform(-1, 1) * (1 - i / n) ** 3 for i in range(n)]

W = lambda sub, name, s: write(f'{ROOT}/{sub}/{name}.wav', s)
for i in range(3): W('Electro/Discharge', f'electro_discharge_{i}', electro_discharge(10 + i))
for i in range(2): W('Electro/Idle', f'electro_idle_{i}', electro_idle(20 + i))
for i in range(3): W('Gravity/Discharge', f'gravity_discharge_{i}', gravity_discharge(30 + i))
for i in range(2): W('Gravity/Idle', f'gravity_idle_{i}', gravity_idle(40 + i))
for i in range(3): W('Fire/Discharge', f'fire_discharge_{i}', fire_discharge(50 + i))
for i in range(2): W('Fire/Idle', f'fire_idle_{i}', fire_idle(60 + i))
for i in range(2): W('Acid/Discharge', f'acid_discharge_{i}', acid_discharge(70 + i))
for i in range(2): W('Acid/Idle', f'acid_idle_{i}', acid_idle(80 + i))
for i in range(2): W('Fuzz/Discharge', f'fuzz_discharge_{i}', fuzz_discharge(90 + i))
W('Detector/Beep', 'beep', tone(1300, .07))
W('Detector/Artifact', 'artifact', chirp(900, 1700, .18) + silence(.03) + chirp(900, 1700, .18))
for i in range(3): W('Detector/Geiger', f'geiger_{i}', click(100 + i))
print('sounds ok')
