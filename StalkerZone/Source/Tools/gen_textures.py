# Генератор анимированных текстур аномалий и пятен Зоны.
# Каждая аномалия — папка с 8 кадрами. В XML у неё graphicClass Graphic_Flicker:
# ванильный класс огня, он сам перебирает кадры (работает и без DLL).
import math, random, os
from PIL import Image, ImageDraw, ImageFilter

ROOT = '/mnt/user-data/outputs/StalkerZone/Common/Textures/Things/Building'
FRAMES = 8
FADE = 0.8          # видимость аномалий (1.0 = полностью непрозрачные; комета всегда яркая)
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
    """Заражённая земля: пятнистые жёлто-бурые разводы, сухая трава, лёгкое мерцание.
    Границу показывают знаки радиационной опасности (отдельные предметы на карте)."""
    out = []; n = 256; c = n / 2
    rnd0 = random.Random(77)
    blobs = [(c + rnd0.uniform(-90, 90), c + rnd0.uniform(-90, 90), rnd0.uniform(18, 48)) for _ in range(26)]
    specks = [(c + rnd0.uniform(-110, 110), c + rnd0.uniform(-110, 110)) for _ in range(160)]
    for i in range(FRAMES):
        t = i / FRAMES; rnd = random.Random(600 + i)
        img = blank(n); d = ImageDraw.Draw(img)
        for (x, y, r) in blobs:
            k = .85 + .15 * math.sin(t * 6.28 + x * .05)
            d.ellipse([x - r, y - r * .8, x + r, y + r * .8], fill=(int(150 * k), int(140 * k), 50, 70))
        img = img.filter(ImageFilter.GaussianBlur(10))
        d = ImageDraw.Draw(img)
        for (x, y) in specks:   # пожухлые травинки
            if math.hypot(x - c, y - c) < 115:
                d.line([(x, y), (x + rnd0.uniform(-2, 2), y - rnd0.uniform(3, 6))], fill=(170, 150, 70, 150), width=1)
        for _ in range(14):     # редкие светящиеся частицы (мерцают между кадрами)
            a = rnd.uniform(0, 6.28); r = rnd.uniform(0, 100)
            x, y = c + math.cos(a) * r, c + math.sin(a) * r
            d.ellipse([x - 1.2, y - 1.2, x + 1.2, y + 1.2], fill=(220, 255, 120, 140))
        # мягкий край, чтобы пятно сливалось с землёй
        px = img.load()
        for y in range(n):
            for x in range(n):
                dd = math.hypot(x - c + .5, y - c + .5) / c
                r_, g_, b_, a_ = px[x, y]
                px[x, y] = (r_, g_, b_, int(a_ * max(0, 1 - dd ** 3)))
        out.append(img)
    return out

def single(path, img):
    os.makedirs(os.path.dirname(path), exist_ok=True); img.save(path)

def trefoil(d, cx, cy, r, col, bg):
    """Знак радиационной опасности (международный символ): три сектора и центр."""
    for k in range(3):
        a0 = -90 + k * 120 - 30
        d.pieslice([cx - r, cy - r, cx + r, cy + r], a0, a0 + 60, fill=col)
    d.ellipse([cx - r * .38, cy - r * .38, cx + r * .38, cy + r * .38], fill=bg)
    d.ellipse([cx - r * .22, cy - r * .22, cx + r * .22, cy + r * .22], fill=col)

def radiation_sign():
    img = blank(64); d = ImageDraw.Draw(img)
    d.rectangle([29, 30, 34, 62], fill=(110, 80, 50, 255), outline=(60, 40, 20, 255))   # столб
    d.polygon([(32, 4), (56, 28), (32, 52), (8, 28)], fill=(250, 210, 40, 255), outline=(30, 30, 30, 255))  # ромб
    trefoil(d, 32, 28, 12, (20, 20, 20, 255), (250, 210, 40, 255))
    return img

def anomaly_marker():
    """Метка детектора над аномалией: оранжевое пунктирное кольцо с засечками."""
    n = 128; img = blank(n); d = ImageDraw.Draw(img)
    for k in range(24):
        a0 = k * 15; d.arc([6, 6, n - 6, n - 6], a0, a0 + 9, fill=(255, 150, 40, 230), width=5)
    for k in range(4):
        a = k * math.pi / 2; x1, y1 = n / 2 + math.cos(a) * 58, n / 2 + math.sin(a) * 58
        x2, y2 = n / 2 + math.cos(a) * 44, n / 2 + math.sin(a) * 44
        d.line([(x1, y1), (x2, y2)], fill=(255, 190, 80, 255), width=5)
    return img

def artifact_marker():
    """Метка найденного детектором артефакта: зелёный ромб со свечением."""
    n = 64; img = radial((120, 255, 160), 1.5, 120, n); d = ImageDraw.Draw(img)
    d.polygon([(32, 8), (52, 32), (32, 56), (12, 32)], outline=(170, 255, 190, 255), width=4)
    d.ellipse([28, 28, 36, 36], fill=(220, 255, 230, 255))
    return img

def detector(screen, body, accent, tier):
    img = blank(64); d = ImageDraw.Draw(img)
    d.rounded_rectangle([14, 8, 50, 58], radius=6, fill=body, outline=(25, 25, 25, 255))
    d.rectangle([19, 13, 45, 33], fill=screen, outline=(20, 20, 20, 255))
    for k in range(tier):   # полоски на экране = класс детектора
        d.line([(23, 29 - k * 5), (41, 29 - k * 5)], fill=accent, width=2)
    d.ellipse([22, 39, 30, 47], fill=accent); d.ellipse([34, 39, 42, 47], fill=(70, 70, 70, 255))
    d.line([(44, 8), (50, 0)], fill=(40, 40, 40, 255), width=3)   # антенна
    return img
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
B = ROOT
I = '/mnt/user-data/outputs/StalkerZone/Common/Textures/Things/Item'
FX = '/mnt/user-data/outputs/StalkerZone/Common/Textures/SZ_Fx'
single(f'{B}/SZ_Fields/RadiationSign.png', radiation_sign())
single(f'{FX}/AnomalyMarker.png', anomaly_marker())
single(f'{FX}/ArtifactMarker.png', artifact_marker())
single(f'{I}/SZ_Detectors/Basic.png', detector((60, 90, 60, 255), (150, 145, 130, 255), (120, 230, 120, 255), 1))
single(f'{I}/SZ_Detectors/Advanced.png', detector((50, 80, 110, 255), (110, 120, 130, 255), (110, 200, 255, 255), 2))
single(f'{I}/SZ_Detectors/Scanner.png', detector((90, 60, 110, 255), (70, 70, 80, 255), (220, 140, 255, 255), 3))
print('frames ok')
