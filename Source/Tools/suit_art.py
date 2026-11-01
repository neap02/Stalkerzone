# Рисовальщик костюмов Зоны, 512x512 (в 4 раза детальнее 128).
# PROFILE — посадка по телу: края силуэта (с обводкой) через каждые 16 px для каждого
# типа тела и стороны. Это только мерки (где проходит контур тела в кадре); рисунок свой.
# Сбоку капюшон эталона над плечом исключён: верх тела закрыт округлой "шапкой" плеч.
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

N=512; OUT=18                      # кадр и толщина обводки
INK=(28,25,22,255)                 # цвет обводки

PROFILE={
 ('Male','south'):[(151,225,286),(167,203,308),(183,190,321),(199,166,345),(215,159,352),(231,154,357),(247,151,360),(263,147,364),(279,150,361),(295,154,357),(311,159,352),(327,165,346),(343,172,339),(359,178,333),(375,182,329),(391,184,327),(407,189,322),(423,205,306),(432,240,272)],
 ('Male','north'):[(171,219,289),(187,174,332),(203,161,347),(219,154,354),(235,152,356),(251,149,359),(267,145,363),(283,148,360),(299,154,354),(315,159,349),(331,164,345),(347,170,340),(363,175,336),(379,178,336),(395,181,333),(411,187,325),(427,206,304),(434,240,272)],
 ('Male','east'):[(228,153,317),(244,174,341),(260,175,341),(276,176,340),(292,178,337),(308,180,331),(324,180,323),(340,181,314),(356,180,308),(372,180,304),(388,181,301),(404,190,294),(420,212,279),(427,230,262)],
 ('Female','south'):[(129,249,262),(145,210,301),(161,203,308),(177,202,309),(193,202,309),(209,197,314),(225,190,321),(241,184,327),(257,179,332),(273,182,329),(289,188,323),(305,193,318),(321,182,329),(337,171,340),(353,164,347),(369,163,348),(385,163,348),(401,168,343),(417,180,331),(433,199,312),(448,235,276)],
 ('Female','north'):[(187,218,293),(203,193,318),(219,187,324),(235,182,329),(251,180,331),(267,178,333),(283,179,332),(299,190,321),(315,184,328),(331,171,340),(347,165,346),(363,162,350),(379,162,350),(395,166,347),(411,173,339),(427,189,323),(443,219,292),(448,240,271)],
 ('Female','east'):[(249,188,318),(265,192,324),(281,192,326),(297,179,324),(313,166,311),(329,154,299),(345,149,306),(361,146,310),(377,146,310),(393,146,307),(409,151,301),(425,161,289),(441,180,268),(452,205,245)],
 ('Thin','south'):[(147,243,268),(163,220,291),(179,215,296),(195,207,304),(211,203,308),(227,199,312),(243,196,315),(259,196,315),(275,199,312),(291,201,310),(307,202,309),(323,202,309),(339,203,308),(355,203,308),(371,204,307),(387,206,305),(403,211,300),(419,220,291),(430,240,271)],
 ('Thin','north'):[(185,223,290),(201,203,310),(217,194,319),(233,199,314),(249,203,310),(265,203,310),(281,203,310),(297,204,309),(313,205,309),(329,205,309),(345,205,309),(361,205,309),(377,207,307),(393,209,304),(409,216,297),(425,230,283),(431,245,268)],
 ('Thin','east'):[(233,179,307),(249,186,305),(265,198,300),(281,193,296),(297,189,292),(313,184,287),(329,179,283),(345,176,279),(361,172,274),(377,170,270),(393,171,264),(409,178,253),(425,206,235)],
 ('Fat','south'):[(123,225,286),(139,185,326),(155,171,340),(171,163,348),(187,159,355),(203,140,371),(219,128,383),(235,120,391),(251,119,392),(267,118,391),(283,110,399),(299,106,405),(315,102,409),(331,99,412),(347,99,412),(363,99,412),(379,106,405),(395,113,398),(411,126,385),(427,142,369),(443,180,331),(452,225,286)],
 ('Fat','north'):[(157,216,292),(173,177,333),(189,153,357),(205,137,372),(221,127,382),(237,120,388),(253,112,396),(269,108,400),(285,100,408),(301,97,411),(317,95,413),(333,94,414),(349,94,414),(365,96,412),(381,102,406),(397,109,399),(413,120,388),(429,141,366),(445,180,328),(452,225,284)],
 ('Fat','east'):[(221,120,373),(237,110,379),(253,104,383),(269,98,384),(285,93,383),(301,91,383),(317,90,390),(333,89,397),(349,91,398),(365,97,395),(381,103,391),(397,111,384),(413,123,374),(429,143,360),(445,176,338),(458,230,290)],
 ('Hulk','south'):[(108,219,291),(124,179,331),(140,164,346),(156,160,350),(172,149,361),(188,136,374),(204,127,383),(220,121,390),(236,116,395),(252,111,399),(268,107,403),(284,106,404),(300,111,399),(316,115,395),(332,123,387),(348,131,380),(364,139,372),(380,148,363),(396,157,354),(412,166,344),(428,173,337),(444,178,332),(460,183,327),(476,188,322),(492,203,307),(506,235,275)],
 ('Hulk','north'):[(125,200,309),(141,177,332),(157,156,353),(173,139,370),(189,127,382),(205,116,393),(221,106,403),(237,97,412),(253,94,414),(269,94,414),(285,98,411),(301,106,403),(317,113,396),(333,119,389),(349,126,383),(365,134,375),(381,142,367),(397,151,358),(413,161,348),(429,169,339),(445,173,336),(461,178,332),(477,185,324),(493,202,304),(505,235,272)],
 ('Hulk','east'):[(212,128,294),(228,137,343),(244,136,369),(260,135,375),(276,134,375),(292,132,374),(308,131,370),(324,130,362),(340,128,355),(356,125,348),(372,120,337),(388,116,327),(404,112,316),(420,110,305),(436,108,296),(452,110,288),(468,119,279),(484,138,263),(500,185,236)],
}

class Fit:
    """Посадка: края силуэта по строкам, с интерполяцией."""
    def __init__(s, body, view):
        rows=PROFILE[(body,view)]
        if view=='east':      # округлая "шапка" плеч вместо капюшона эталона
            y0,l0,r0=rows[0]; w=r0-l0
            rows=[(y0-26,l0+0.30*w,r0-0.35*w),(y0-14,l0+0.10*w,r0-0.12*w)]+rows
        s.rows=rows; s.view=view
        s.top=rows[0][0]; s.bot=rows[-1][0]; s.H=s.bot-s.top
    def edge(s,y):
        r=s.rows
        if y<=r[0][0]: return r[0][1],r[0][2]
        for (ya,la,ra),(yb,lb,rb) in zip(r,r[1:]):
            if ya<=y<=yb:
                t=(y-ya)/max(1,yb-ya); return la+(lb-la)*t, ra+(rb-ra)*t
        return r[-1][1],r[-1][2]
    def at(s,t):              # t=0 верх, 1 низ -> (y, левый, правый, центр, ширина)
        y=s.top+t*s.H; l,r=s.edge(y); return y,l,r,(l+r)/2,r-l
    def polygon(s):
        r=s.rows; cx0=(r[0][1]+r[0][2])/2; cx1=(r[-1][1]+r[-1][2])/2
        return [(cx0,r[0][0]-4)]+[(l,y) for y,l,_ in r]+[(cx1,r[-1][0]+4)]+[(rr,y) for y,_,rr in reversed(r)]

def C(c,k=1.0,a=255): return tuple(max(0,min(255,int(v*255*k))) for v in c)+(a,)

def fabric(base, seed, grain=7, blotch=10):
    """Ткань: мелкое зерно + крупные пятна, чтобы цвет 'жил'."""
    rng=np.random.default_rng(seed)
    fine=rng.normal(0,grain,(N,N))
    coarse=np.array(Image.fromarray((rng.random((N//32,N//32))*255).astype(np.uint8)).resize((N,N),Image.BICUBIC),dtype=float)
    v=fine+(coarse-128)/128*blotch
    rgb=np.stack([np.clip(base[i]*255+v,0,255) for i in range(3)],-1).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb,np.full((N,N),255,np.uint8)]),'RGBA')

def bevel_rect(d,box,col,r=14,hl=1.25,sh=0.7,rivets=False):
    x0,y0,x1,y1=box
    d.rounded_rectangle(box,radius=r,fill=C(col))
    d.line([(x0+r,y0+3),(x1-r,y0+3)],fill=C(col,hl),width=5)          # блик сверху
    d.line([(x0+r,y1-3),(x1-r,y1-3)],fill=C(col,sh),width=5)          # тень снизу
    d.line([(x1-3,y0+r),(x1-3,y1-r)],fill=C(col,sh*1.05),width=4)
    if rivets:
        for (x,y) in ((x0+12,y0+12),(x1-12,y0+12),(x0+12,y1-12),(x1-12,y1-12)):
            d.ellipse([x-5,y-5,x+5,y+5],fill=(150,150,145,255)); d.ellipse([x-2,y-3,x+1,y],fill=(220,220,215,255))

def stitches(d,pts,col,dash=10,gap=8,w=3):
    for (xa,ya),(xb,yb) in zip(pts,pts[1:]):
        L=math.hypot(xb-xa,yb-ya); n=int(L//(dash+gap))
        for i in range(n+1):
            t0=i*(dash+gap)/max(L,1); t1=min(1,(i*(dash+gap)+dash)/max(L,1))
            d.line([(xa+(xb-xa)*t0,ya+(yb-ya)*t0),(xa+(xb-xa)*t1,ya+(yb-ya)*t1)],fill=col,width=w)

def pouch(d,x,y,w,h,col):
    bevel_rect(d,(x,y,x+w,y+h),col,r=8)
    d.rounded_rectangle([x-2,y-2,x+w+2,y+h*0.42],radius=8,fill=C(col,0.82))   # клапан
    d.ellipse([x+w/2-5,y+h*0.30,x+w/2+5,y+h*0.30+10],fill=(60,60,58,255))      # кнопка

def strap(d,pts,col,w=16):
    d.line(pts,fill=C(col,0.55),width=w,joint='curve')
    d.line(pts,fill=C(col,0.75),width=w-8,joint='curve')

def buckle(d,x,y):
    d.rectangle([x-12,y-9,x+12,y+9],outline=(165,165,160,255),width=4)
    d.line([(x,y-9),(x,y+9)],fill=(165,165,160,255),width=3)

def zipper(d,x,y0,y1):
    d.line([(x,y0),(x,y1)],fill=(45,45,45,255),width=6)
    for y in range(int(y0),int(y1),7): d.rectangle([x-5,y,x+5,y+3],fill=(150,150,145,255))
    d.rectangle([x-6,y0+10,x+6,y0+26],fill=(170,170,165,255))

def dirt(layer,seed,fit):
    """Лёгкая грязь у подола и редкие потёртости: отдельным слоем с размытием."""
    rng=random.Random(seed); g=Image.new('RGBA',(N,N),(0,0,0,0)); d=ImageDraw.Draw(g)
    for _ in range(14):
        t=rng.uniform(0.72,1.0); y,l,r,cx,w=fit.at(t); x=rng.uniform(l+12,r-12); rr=rng.uniform(5,11)
        d.ellipse([x-rr,y-rr*0.5,x+rr,y+rr*0.5],fill=(85,66,42,rng.randint(18,34)))
    g=g.filter(ImageFilter.GaussianBlur(4)); layer.alpha_composite(g)
    d=ImageDraw.Draw(layer,'RGBA')
    for _ in range(5):
        t=rng.uniform(0.2,0.85); y,l,r,cx,w=fit.at(t); x=rng.uniform(l+20,r-20); a=rng.uniform(-0.5,0.5)
        d.line([(x,y),(x+12*math.cos(a),y+12*math.sin(a))],fill=(255,255,255,28),width=2)

def render(key, cls, cols, body, view, seed=0):
    base,sec,acc=cols; fit=Fit(body,view)
    poly=fit.polygon()
    mask=Image.new('L',(N,N),0); ImageDraw.Draw(mask).polygon(poly,fill=255)
    layer=fabric(base,seed^hash((key,body,view))&0xffff)
    d=ImageDraw.Draw(layer,'RGBA')
    rng=random.Random(hash((key,body,view))&0xffff)
    side=view=='east'

    if cls=='cloak':                                             # камуфляж и бахрома
        for _ in range(140):
            t=rng.uniform(0,1); y,l,r,cx,w=fit.at(t); x=rng.uniform(l,r); rr=rng.uniform(10,26)
            d.ellipse([x-rr,y-rr*0.6,x+rr,y+rr*0.6],fill=C(sec if rng.random()<0.55 else acc,1.0,220))
        for _ in range(60):
            t=rng.uniform(0.75,1.0); y,l,r,cx,w=fit.at(t); x=rng.uniform(l,r)
            d.line([(x,y),(x+rng.uniform(-6,6),y+rng.uniform(14,30))],fill=C(sec,0.8),width=4)

    if view=='north':
        y0,l0,r0,cx0,w0=fit.at(0.12); y1,l1,r1,cx1,w1=fit.at(0.62)
        if cls in ('light','medium','cloak'):                    # рюкзак
            pw=w0*0.56
            bevel_rect(d,(cx0-pw/2,y0+20,cx0+pw/2,y1),C(sec,0.85)[:3] and tuple(v*0.85 for v in sec),r=22)
            d.rounded_rectangle([cx0-pw/2-4,y0+14,cx0+pw/2+4,y0+70],radius=20,fill=C(sec,0.7))
            buckle(d,cx0,y0+70)
            for dx in (-0.5,0.5): pouch(d,cx0+dx*pw-(18 if dx<0 else 0),y0+110,18,70,tuple(v*0.8 for v in sec))
            stitches(d,[(cx0-pw/2+14,y1-30),(cx0+pw/2-14,y1-30)],C(sec,1.2))
        elif cls=='science':                                     # два баллона и шланги
            for dx in (-0.17,0.17):
                x=cx0+dx*w0; bevel_rect(d,(x-24,y0+10,x+24,y1+20),sec,r=24)
                d.rectangle([x-10,y0-4,x+10,y0+12],fill=(150,150,145,255))
                d.line([(x-14,y0+40),(x-14,y1)],fill=(255,255,255,70),width=6)
            d.arc([cx0-w0*0.3,y0-30,cx0+w0*0.3,y0+40],200,340,fill=(40,40,40,255),width=8)
        elif cls=='exo':                                         # силовой блок
            bevel_rect(d,(cx0-w0*0.32,y0+6,cx0+w0*0.32,y1),sec,r=10,rivets=True)
            for i in range(6): d.line([(cx0-w0*0.22,y0+40+i*16),(cx0+w0*0.22,y0+40+i*16)],fill=C(sec,0.55),width=6)
            for dx in (-0.4,0.4):
                x=cx0+dx*w0; d.line([(x,y0),(x,fit.at(0.95)[0])],fill=(140,140,135,255),width=12)
        else:                                                    # тяжёлая: спинная плита
            bevel_rect(d,(cx0-w0*0.36,y0,cx0+w0*0.36,y1),sec,r=16,rivets=True)
            for t in (0.68,0.76,0.84):
                y,l,r,cx,w=fit.at(t); bevel_rect(d,(cx-w*0.38,y,cx+w*0.38,y+22),tuple(v*0.9 for v in sec),r=8)
    else:
        f=0.55 if side else 1.0                                  # сбоку всё уже и смещено вперёд
        def X(cx,w,dx): return cx+(w*0.18 if side else 0)+dx*w*f
        yS,lS,rS,cS,wS=fit.at(0.14); yC,lC,rC,cC,wC=fit.at(0.48); yW,lW,rW,cW,wW=fit.at(0.58)
        if cls=='light':
            d.rounded_rectangle([X(cS,wS,-0.32),yS-26,X(cS,wS,0.32),yS+10],radius=14,fill=C(base,0.72))   # воротник
            if not side: zipper(d,cS,yS+8,fit.at(0.97)[0])
            for dx in ((-0.24,0.24) if not side else (0.10,)): pouch(d,X(cC,wC,dx)-30,yC-70,60,52,tuple(v*0.85 for v in base))
            strap(d,[(lW+8,yW),(rW-8,yW)],sec,w=18); buckle(d,X(cW,wW,0),yW)
            stitches(d,[(X(cS,wS,-0.4),yS+30),(X(cW,wW,-0.42),yW-10)],C(base,1.25))
        elif cls in ('medium','heavy'):
            k=0.36 if cls=='medium' else 0.42
            bevel_rect(d,(X(cS,wS,-k),yS-6,X(cS,wS,k),yC+(0 if cls=='medium' else 20)),sec,r=18,rivets=(cls=='heavy'))
            if not side:
                for dx in (-1,1):                                # наплечники
                    x=cS+dx*wS*0.47; rr=34 if cls=='heavy' else 26
                    d.ellipse([x-rr,yS-rr*0.8,x+rr,yS+rr*0.8],fill=C(sec,0.92)); d.arc([x-rr,yS-rr*0.8,x+rr,yS+rr*0.8],200,340,fill=C(sec,1.25),width=5)
            if cls=='heavy':
                for i in range(3):                               # сегменты живота
                    y,l,r,cx,w=fit.at(0.6+i*0.09); bevel_rect(d,(X(cx,w,-0.4),y,X(cx,w,0.4),y+26),tuple(v*(0.92-i*0.06) for v in sec),r=8)
                d.rounded_rectangle([X(cS,wS,-0.3),yS-34,X(cS,wS,0.3),yS-4],radius=10,fill=C(sec,0.75))   # горжет
            strap(d,[(lW+6,yW+8),(rW-6,yW+8)],sec,w=20); buckle(d,X(cW,wW,0.05),yW+8)
            for dx in ((-0.3,-0.1,0.1,0.3) if not side else (0.0,0.25)):
                y,l,r,cx,w=fit.at(0.62); pouch(d,X(cx,w,dx)-20,y,40,46,tuple(v*0.8 for v in sec))
            if cls=='medium': stitches(d,[(X(cC,wC,-0.3),yC+30),(X(cC,wC,0.3),yC+30)],C(sec,1.3))
        elif cls=='science':
            for dx in ((-0.44,0.44) if not side else (0.3,)):    # цветные боковые вставки
                x=X(cS,wS,dx); d.rectangle([x-12,yS,x+12,fit.at(0.95)[0]],fill=C(sec))
            for t in (0.70,0.80):                                # светоотражающие полосы
                y,l,r,cx,w=fit.at(t); d.rectangle([l+6,y,r-6,y+12],fill=(222,222,212,255)); d.line([(l+6,y+3),(r-6,y+3)],fill=(255,255,250,255),width=3)
            if not side:
                bevel_rect(d,(cS-44,yS+30,cS+44,yS+96),acc,r=10)                             # панель приборов
                for i,colr in enumerate([(120,230,140),(240,200,60),(120,230,140)]):
                    d.ellipse([cS-30+i*24,yS+48,cS-18+i*24,yS+60],fill=colr+(255,))
                d.line([(cS-30,yS+80),(cS+30,yS+80)],fill=(60,60,60,255),width=4)
            d.arc([X(cS,wS,-0.45),yS-10,X(cS,wS,0.1),yS+90],270,360,fill=(40,40,40,255),width=8)  # шланг
            d.line([(X(cS,wS,-0.2),yS+20),(X(cS,wS,0.2),yS+20)],fill=(255,255,255,60),width=10)   # глянец
        elif cls=='exo':
            bevel_rect(d,(X(cS,wS,-0.34),yS-6,X(cS,wS,0.34),yC),sec,r=10,rivets=True)
            for i in range(2):
                y,l,r,cx,w=fit.at(0.6+i*0.12); bevel_rect(d,(X(cx,w,-0.36),y,X(cx,w,0.36),y+30),tuple(v*0.95 for v in sec),r=6,rivets=True)
            for dx in ((-0.5,0.5) if not side else (0.42,)):     # каркас и гидравлика
                pts=[]
                for t in (0.08,0.5,0.95):
                    y,l,r,cx,w=fit.at(t); pts.append((X(cx,w,dx*0.95),y))
                d.line(pts,fill=(118,118,112,255),width=16,joint='curve'); d.line(pts,fill=(170,170,165,255),width=6,joint='curve')
                for (x,y) in pts: d.ellipse([x-14,y-14,x+14,y+14],fill=(95,95,90,255)); d.ellipse([x-6,y-6,x+6,y+6],fill=(190,190,185,255))
        if not side and cls!='cloak':                            # нашивка фракции
            x=cS-wS*0.40; d.rounded_rectangle([x-20,yS+24,x+20,yS+58],radius=6,fill=C(acc),outline=C(acc,0.5),width=3)
        if side and cls in ('light','medium','cloak'):            # рюкзак виден сбоку
            y0,l0,r0,cx0,w0=fit.at(0.12); y1=fit.at(0.6)[0]
            bevel_rect(d,(l0+6,y0+10,l0+w0*0.22,y1),tuple(v*0.8 for v in sec),r=14)

    dirt(layer,seed+7,fit)
    # объём: свет сверху-слева, тень снизу-справа
    g=np.zeros((N,N),np.float32); yy,xx=np.mgrid[0:N,0:N]
    g=np.clip((yy-fit.top)/max(1,fit.H)*0.35+(xx-256)/512*0.25,0,0.45)
    shade=Image.fromarray((g*255).astype(np.uint8)); dark=Image.new('RGBA',(N,N),(0,0,0,255)); dark.putalpha(shade)
    layer.alpha_composite(dark)
    hl=Image.fromarray((np.clip(0.18-((yy-fit.top)/max(1,fit.H))*0.4,0,0.18)*255).astype(np.uint8))
    light=Image.new('RGBA',(N,N),(255,255,255,255)); light.putalpha(hl); layer.alpha_composite(light)
    # вырезать по силуэту и обвести (обводка только внутрь силуэта)
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
    ring=Image.new('L',(N,N),0); ImageDraw.Draw(ring).line(poly+[poly[0],poly[1]],fill=255,width=OUT*2,joint='curve')
    ring=ImageChops.multiply(ring,mask)
    ink=Image.new('RGBA',(N,N),INK); ink.putalpha(ring)
    out=Image.new('RGBA',(N,N),(0,0,0,0)); out.alpha_composite(layer); out.alpha_composite(ink)
    return out
