# Генератор анимированных текстур аномалий и пятен Зоны.
# Каждая аномалия — папка с 8 кадрами. В XML у неё graphicClass Graphic_Flicker:
# ванильный класс огня, он сам перебирает кадры (работает и без DLL).
import math, random, os
from PIL import Image, ImageDraw, ImageFilter

ROOT = '/mnt/user-data/outputs/StalkerZone/Common/Textures/Things/Building'
FRAMES = 8
FADE = 0.4          # "еле заметны": общая прозрачность аномалий (комета ярче)
S = 128; C = S / 2

def blank(n=S): return Image.new('RGBA', (n, n), (0, 0, 0, 0))

def radial(color, power, amax, n=S, scale=1.0):
    img = blank(n); px = img.load(); c = n / 2
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c + .5, y - c + .5) / (c * scale)
            if d < 1: px[x, y] = (*color, int(amax * (1 - d) ** power))
    return img

def fade(img, k):
    r, g, b, a = img.split()
    return Image.merge('RGBA', (r, g, b, a.point(lambda v: int(v * k))))

def save(folder, name, frames, k):
    d = f'{ROOT}/{folder}/{name}'
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    for i, img in enumerate(frames):
        fade(img, k).save(f'{d}/{name}_{"abcdefgh"[i]}.png')

def spiral(t, arms, turns, width, col, glow, core, direction=1, debris=None):
    img = radial(glow, 1.8, 120 + int(30 * math.sin(t * 2 * math.pi)))
    d = ImageDraw.Draw(img); rot = direction * t * 2 * math.pi / arms
    for k in range(arms):
        p = []
        for i in range(120):
            u = i / 119; a = rot + k * 2 * math.pi / arms + u * turns * 2 * math.pi; r = 4 + u * 56
            p.append((C + math.cos(a) * r, C + math.sin(a) * r))
        d.line(p, fill=(*col, 210), width=width)
    if debris:
        rnd = random.Random(7)
        for j in range(14):
            r0 = rnd.uniform(14, 54); a0 = rnd.uniform(0, 6.28) + direction * t * 2 * math.pi * (40 / r0)
            x, y = C + math.cos(a0) * r0, C + math.sin(a0) * r0
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(*debris, 230))
    img = img.filter(ImageFilter.GaussianBlur(1.3))
    img.alpha_composite(radial(core, 2, 220))
    return img

def frames_electro():
    out = []
    for i in range(FRAMES):
        rnd = random.Random(100 + i)
        img = radial((110, 170, 255), 1.6, 150 + rnd.randint(0, 50)); d = ImageDraw.Draw(img)
        for _ in range(rnd.randint(5, 9)):
            a = rnd.uniform(0, 6.28); x, y = C, C; p = [(x, y)]
            for _ in range(rnd.randint(4, 7)):
                a += rnd.uniform(-.9, .9); r = rnd.uniform(6, 10); x += math.cos(a) * r; y += math.sin(a) * r; p.append((x, y))
            d.line(p, fill=(225, 240, 255, 255), width=rnd.choice((1, 2, 2)))
        img = img.filter(ImageFilter.GaussianBlur(.6))
        img.alpha_composite(radial((235, 245, 255), 3, 200 + rnd.randint(0, 55)))
        out.append(img)
    return out

def frames_burner():
    out = []
    for i in range(FRAMES):
        t = i / FRAMES; rnd = random.Random(200 + i)
        img = radial((255, 120, 40), 1.4, 170 + rnd.randint(0, 40)); d = ImageDraw.Draw(img)
        for base in (14, 28, 42):
            r = base + t * 14
            d.ellipse([C - r, C - r, C + r, C + r], outline=(255, 200, 90, int(140 * (1 - t * .6))), width=3)
        img = img.filter(ImageFilter.GaussianBlur(2.5))
        img.alpha_composite(radial((255, 230, 150), 2.5, 200 + rnd.randint(0, 50)))
        out.append(img)
    return out

def frames_springboard():
    out = []
    for i in range(FRAMES):
        t = i / FRAMES; ringr = .55 + .07 * math.sin(t * 2 * math.pi)
        img = blank(); px = img.load()
        for y in range(S):
            for x in range(S):
                dd = math.hypot(x - C + .5, y - C + .5) / C
                if dd < 1:
                    ring = math.exp(-((dd - ringr) / .17) ** 2); core = max(0, 1 - dd / .3)
                    px[x, y] = (int(150 * ring + 20 * core), int(90 * ring + 10 * core), int(230 * ring + 60 * core), int(min(255, 200 * ring + 170 * core)))
        d = ImageDraw.Draw(img)
        for j in range(8):   # пыль, кружащая по кольцу
            a = j * 2 * math.pi / 8 + t * 2 * math.pi / 8; r = ringr * C
            d.ellipse([C + math.cos(a) * r - 2, C + math.sin(a) * r - 2, C + math.cos(a) * r + 2, C + math.sin(a) * r + 2], fill=(210, 190, 255, 220))
        out.append(img.filter(ImageFilter.GaussianBlur(1.1)))
    return out

def frames_bubbles():   # холодец
    out = []
    for i in range(FRAMES):
        t = i / FRAMES; rnd = random.Random(300 + i)
        img = radial((90, 230, 90), 1.2, 190 + int(20 * math.sin(t * 6.28))); d = ImageDraw.Draw(img)
        r = 20 + t * 30
        d.ellipse([C - r, C - r, C + r, C + r], outline=(170, 255, 150, int(120 * (1 - t))), width=2)
        for _ in range(8):
            x, y = C + rnd.uniform(-32, 32), C + rnd.uniform(-32, 32); br = rnd.uniform(2, 7)
            d.ellipse([x - br, y - br, x + br, y + br], outline=(205, 255, 185, 230), width=2)
        out.append(img.filter(ImageFilter.GaussianBlur(.8)))
    return out

def frames_fuzz():
    out = []; rnd0 = random.Random(9)
    strands = [(C + rnd0.uniform(-40, 40), C + rnd0.uniform(-45, -10), rnd0.uniform(0, 6.28)) for _ in range(40)]
    for i in range(FRAMES):
        t = i / FRAMES
        img = radial((240, 230, 170), 1.6, 80 + int(20 * math.sin(t * 6.28))); d = ImageDraw.Draw(img)
        for (x0, y0, ph) in strands:
            x, y = x0, y0; p = [(x, y)]
            for k in range(5):
                x += 3.2 * math.sin(ph + t * 2 * math.pi + k * .7); y += 7; p.append((x, y))
            d.line(p, fill=(250, 245, 210, 175), width=1)
        out.append(img.filter(ImageFilter.GaussianBlur(.4)))
    return out

def frames_comet():
    out = []
    for i in range(FRAMES):
        rnd = random.Random(400 + i)
        img = radial((255, 110, 30), 1.3, 190 + rnd.randint(0, 40)); d = ImageDraw.Draw(img)
        for k in range(10):
            a = k / 10 * 2 * math.pi + rnd.uniform(-.2, .2); r = rnd.uniform(22, 44)
            d.line([(C, C), (C + math.cos(a) * r, C + math.sin(a) * r)], fill=(255, 190, 80, 170), width=rnd.choice((4, 5, 6)))
        img = img.filter(ImageFilter.GaussianBlur(2))
        img.alpha_composite(radial((255, 245, 200), 2.2, 230 + rnd.randint(0, 25)))
        out.append(img)
    return out

def frames_psi():
    out = []; n = 256; c = n / 2
    for i in range(FRAMES):
        t = i / FRAMES; img = blank(n); px = img.load()
        for y in range(n):
            for x in range(n):
                dd = math.hypot(x - c + .5, y - c + .5) / c
                if dd < 1:
                    wave = .5 + .5 * math.sin(dd * 26 - t * 2 * math.pi)   # волны расходятся
                    px[x, y] = (170, 110, 255, int((1 - dd) ** .8 * (30 + 45 * wave)))
        out.append(img.filter(ImageFilter.GaussianBlur(1.5)))
    return out

def frames_radiation():
    out = []; n = 256
    for i in range(FRAMES):
        t = i / FRAMES; rnd = random.Random(500 + i)
        img = radial((200, 230, 60), .7, 60 + int(15 * math.sin(t * 6.28)), n); d = ImageDraw.Draw(img)
        for k in range(36):    # пунктирная граница медленно вращается
            a0 = k * 10 + t * 10; d.arc([8, 8, n - 8, n - 8], a0, a0 + 5, fill=(220, 240, 90, 140), width=3)
        for _ in range(25):    # мерцающие частицы
            a = rnd.uniform(0, 6.28); r = rnd.uniform(0, n / 2 - 16)
            x, y = n / 2 + math.cos(a) * r, n / 2 + math.sin(a) * r
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(240, 255, 140, 170))
        out.append(img.filter(ImageFilter.GaussianBlur(1)))
    return out

A = 'SZ_Anomalies'
save(A, 'Electro', frames_electro(), FADE)
save(A, 'Burner', frames_burner(), FADE)
save(A, 'Springboard', frames_springboard(), FADE)
save(A, 'Vortex', [spiral(i / FRAMES, 3, 1.2, 4, (170, 150, 220), (120, 90, 180), (20, 10, 30), 1, (200, 190, 230)) for i in range(FRAMES)], FADE)
save(A, 'Whirligig', [spiral(i / FRAMES, 2, 2.0, 3, (140, 170, 255), (90, 110, 200), (20, 10, 30), 1, (190, 210, 255)) for i in range(FRAMES)], FADE)
save(A, 'Meatgrinder', [spiral(i / FRAMES, 4, 1.5, 3, (200, 60, 60), (150, 30, 40), (60, 0, 0), -1, (230, 120, 120)) for i in range(FRAMES)], FADE)
save(A, 'FruitPunch', frames_bubbles(), FADE)
save(A, 'BurntFuzz', frames_fuzz(), FADE)
save(A, 'Comet', frames_comet(), 1.0)
save('SZ_Fields', 'PsiField', frames_psi(), 1.0)
save('SZ_Fields', 'RadiationSpot', frames_radiation(), 1.0)
print('frames ok')
