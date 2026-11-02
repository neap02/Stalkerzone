# Рисовальщик снаряжения Зоны, стиль "чистый cel-shading":
# - текстура светло-серая + маска цвета (_m): R = основной цвет, G = второй цвет.
#   Цвет задаётся в описании предмета (color / colorTwo), шейдер CutoutComplex красит серое.
#   Металл, стекло, резина, огоньки рисуются своим цветом (в маске чёрные — не перекрашиваются);
# - толстая тёмная обводка у силуэта и у каждой детали;
# - плоская заливка + одна тень снизу-справа + тонкий блик сверху-слева.
# Посадка — мерки тел и головы (suit_art.Fit, HCX). Рисунки свои.
import math, random
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageChops
from suit_art import Fit, N, OUT, INK, PANTS_T, TOP_T

P,S='P','S'                         # материалы под маску: основной / второй цвет
TONE={P:226,S:214}                  # базовая яркость серого
METAL=(150,152,150); DARK=(52,54,56); RUBBER=(62,64,60); GLASS=(88,124,146); LIGHT=(232,232,224)
EDGE=7                              # обводка деталей

class Painter:
    def __init__(s):
        s.col=Image.new('RGBA',(N,N),(0,0,0,0)); s.msk=Image.new('RGB',(N,N),(0,0,0)); s.sil=Image.new('L',(N,N),0)
        s.dc=ImageDraw.Draw(s.col); s.dm=ImageDraw.Draw(s.msk); s.ds=ImageDraw.Draw(s.sil)
    def _paint(s,m,mat,tone=None,shadow=True,hl=True):
        if mat in (P,S):
            t=TONE[mat] if tone is None else tone
            c=(t,t,t,255); mc=(255,0,0) if mat==P else (0,255,0)
            dark=(int(t*0.74),)*3+(255,); light=(min(255,int(t*1.12)),)*3+(255,)
        else:
            c=tuple(mat)+(255,); mc=(0,0,0)
            dark=tuple(int(v*0.72) for v in mat)+(255,); light=tuple(min(255,int(v*1.25+12)) for v in mat)+(255,)
        s.col.paste(c,(0,0),m); s.msk.paste(mc,(0,0),m); s.sil.paste(255,(0,0),m)
        if shadow:   # тень: та часть формы, что не перекрыта копией, сдвинутой вверх-влево
            sh=ImageChops.subtract(m,ImageChops.offset(m,10,12)); s.col.paste(dark,(0,0),sh)
        if hl:       # блик: тонкий край сверху-слева
            h=ImageChops.subtract(m,ImageChops.offset(m,-4,-5)); s.col.paste(light,(0,0),h)
    def _new(s): return Image.new('L',(N,N),0)
    def rect(s,box,mat,r=12,tone=None,edge=EDGE,shadow=True,hl=True):
        x0,y0,x1,y1=box; box=[min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)]
        m=s._new(); ImageDraw.Draw(m).rounded_rectangle(box,radius=r,fill=255); s._paint(m,mat,tone,shadow,hl)
        if edge: s.dc.rounded_rectangle(box,radius=r,outline=INK,width=edge); s.dm.rounded_rectangle(box,radius=r,outline=(0,0,0),width=edge)
    def ellipse(s,box,mat,tone=None,edge=EDGE,shadow=True,hl=True):
        m=s._new(); ImageDraw.Draw(m).ellipse(box,fill=255); s._paint(m,mat,tone,shadow,hl)
        if edge: s.dc.ellipse(box,outline=INK,width=edge); s.dm.ellipse(box,outline=(0,0,0),width=edge)
    def poly(s,pts,mat,tone=None,edge=EDGE,shadow=True,hl=True):
        m=s._new(); ImageDraw.Draw(m).polygon(pts,fill=255); s._paint(m,mat,tone,shadow,hl)
        if edge: s.dc.polygon(pts,outline=INK,width=edge); s.dm.polygon(pts,outline=(0,0,0),width=edge)
    def mask(s,m,mat,tone=None,shadow=True,hl=True): s._paint(m,mat,tone,shadow,hl)
    def line(s,pts,col=INK,w=6,mat=None):
        if mat in (P,S):
            t=TONE[mat]; s.dc.line(pts,fill=(t,t,t,255),width=w,joint='curve'); s.dm.line(pts,fill=(255,0,0) if mat==P else (0,255,0),width=w,joint='curve')
        else:
            s.dc.line(pts,fill=col if len(col)==4 else tuple(col)+(255,),width=w,joint='curve'); s.dm.line(pts,fill=(0,0,0),width=w,joint='curve')
        s.ds.line(pts,fill=255,width=w,joint='curve')
    def strap(s,pts,mat,w=22):   # лямка с обводкой
        s.line(pts,INK,w+2*EDGE); s.line(pts,None,w,mat=mat)
    def dot(s,x,y,r,col):
        s.dc.ellipse([x-r,y-r,x+r,y+r],fill=tuple(col)+(255,)); s.dm.ellipse([x-r,y-r,x+r,y+r],fill=(0,0,0)); s.ds.ellipse([x-r,y-r,x+r,y+r],fill=255)
    def finish(s,clip=None):
        sil=s.sil if clip is None else ImageChops.multiply(s.sil,clip)
        a=np.array(sil)>127; dist=ndimage.distance_transform_edt(a)
        ring=Image.fromarray(((dist>0)&(dist<=OUT)).astype(np.uint8)*255)
        col=s.col.copy(); col.paste(INK,(0,0),ring); col.putalpha(sil)
        msk=s.msk.copy(); msk.paste((0,0,0),(0,0),ring)
        return col,msk

def body_mask(poly):
    m=Image.new('L',(N,N),0); ImageDraw.Draw(m).polygon(poly,fill=255); return m

# ---------- подсумки и плитоноска ----------
def mag_pouch(p,x,y,w,h,mat=S):
    p.rect((x,y,x+w,y+h),mat,r=8)
    p.rect((x+4,y-10,x+w-4,y+12),DARK,r=4,shadow=False)                  # торцы магазинов
    p.line([(x+8,y+h*0.42),(x+w-8,y+h*0.42)],INK,4)                         # клапан

def carrier(p,fit,X,side,heavy=False):
    yS,lS,rS,cS,wS=fit.at(0.10); yM,lM,rM,cM,wM=fit.at(0.40); yB,lB,rB,cB,wB=fit.at(0.55)
    k=0.34 if not heavy else 0.40
    for dx in ((-0.26,0.26) if not side else (0.18,)):                      # плечевые лямки
        p.strap([(X(cS,wS,dx),fit.at(0.0)[0]),(X(cS,wS,dx*0.95),yS+30)],S,20)
    p.rect((X(cS,wS,-k),yS,X(cS,wS,k),yM),S,r=18)                           # бронеплита
    p.line([(X(cS,wS,-k)+16,yS+24),(X(cS,wS,k)-16,yS+24)],INK,4)
    p.rect((X(cB,wB,-0.47),yM-6,X(cB,wB,0.47),yB+10),S,r=10,tone=200)      # камербанд
    n=3 if not heavy else 4; span=(0.62 if not heavy else 0.72)*(0.6 if side else 1)
    pw=wM*span/n
    for i in range(n if not side else 2):
        x=X(cM,wM,-span/2)+i*pw+4 if not side else X(cM,wM,0.05)+i*pw*0.9
        mag_pouch(p,x,yM-34,pw-8,58)
    if heavy and not side:
        p.rect((X(cB,wB,-0.18),yB+4,X(cB,wB,0.18),fit.at(0.66)[0]+6),S,r=8,tone=200)   # паховый щиток

def pauldrons(p,fit):
    y,l,r,cx,w=fit.at(0.08)
    for dx in (-1,1):
        x=cx+dx*w*0.46; p.ellipse([x-38,y-26,x+38,y+40],P,tone=205)

def render_top(cls, body, view, seed=0, accent=(0.8,0.7,0.3)):
    fit=Fit(body,view); p=Painter(); side=view=='east'; back=view=='north'
    poly=fit.band(0,TOP_T); clip=body_mask(poly)
    p.mask(clip,P,shadow=False,hl=False)
    # мягкая тень по нижнему правому краю куртки
    sh=ImageChops.subtract(clip,ImageChops.offset(clip,-16,-22)); p.col.paste((168,168,168,255),(0,0),sh)
    def X(cx,w,dx): return cx+(w*0.16 if side else 0)+dx*w*(0.55 if side else 1.0)
    rng=random.Random(seed)
    yT,lT,rT,cT,wT=fit.at(0.0); yH=fit.at(TOP_T)[0]
    p.line([(0,yH-10),(N,yH-10)],INK,5)                                      # шов подола
    if not back and cls!='science':                                          # воротник
        p.rect((X(cT,wT,-0.34),yT-6,X(cT,wT,0.34),yT+26),P,r=12,tone=200)
    if back:
        y0,l0,r0,c0,w0=fit.at(0.08); y1=fit.at(0.6)[0]
        if cls in ('light','medium','cloak'):
            p.rect((c0-w0*0.28,y0+16,c0+w0*0.28,y1),S,r=22)
            p.rect((c0-w0*0.30,y0+10,c0+w0*0.30,y0+70),S,r=20,tone=196)
            p.rect((c0-w0*0.16,y0+110,c0+w0*0.16,y1-20),S,r=10,tone=226)
        elif cls=='heavy':
            p.rect((c0-w0*0.38,y0,c0+w0*0.38,y1),S,r=18)
            for i in range(3): p.rect((c0-w0*0.4+i*w0*0.27,y1-6,c0-w0*0.4+i*w0*0.27+w0*0.25,y1+44),S,r=8,tone=200)
        elif cls=='science':
            for dx in (-0.17,0.17):
                x=c0+dx*w0; p.rect((x-26,y0+16,x+26,y1+10),S,r=26); p.rect((x-10,y0-2,x+10,y0+20),METAL,r=4)
            p.line([(c0-w0*0.17,y0+4),(c0,y0-24),(c0+w0*0.17,y0+4)],RUBBER,10)
        elif cls=='exo':
            p.rect((c0-w0*0.32,y0+4,c0+w0*0.32,y1),DARK,r=10)
            for i in range(5): p.line([(c0-w0*0.22,y0+36+i*18),(c0+w0*0.22,y0+36+i*18)],(32,32,34),6)
            for dx in (-0.45,0.45): p.line([(c0+dx*w0,y0),(c0+dx*w0,yH)],METAL,14)
        if cls=='cloak': p.ellipse([c0-w0*0.3,y0-40,c0+w0*0.3,y0+22],P,tone=210)
    else:
        if cls=='cloak':
            for _ in range(40):
                t=rng.uniform(0.05,0.62); y,l,r,cx,w=fit.at(t); x=rng.uniform(l,r); rr=rng.uniform(14,30)
                p.ellipse([x-rr,y-rr*0.6,x+rr,y+rr*0.6],S,tone=rng.choice((185,205,232)),edge=0,shadow=False,hl=False)
            p.line([(X(cT,wT,-0.3),yT+4),(X(cT,wT,0.3),yT+4)],INK,6)
        if cls=='light':
            if not side:
                p.line([(cT,yT+24),(cT,yH-12)],DARK,7); p.rect((cT-7,yT+30,cT+7,yT+52),METAL,r=3,edge=3)
            for dx in ((-0.24,0.24) if not side else (0.12,)):
                y,l,r,cx,w=fit.at(0.22); p.rect((X(cx,w,dx)-32,y,X(cx,w,dx)+32,y+56),P,r=8,tone=210)
                p.line([(X(cx,w,dx)-28,y+20),(X(cx,w,dx)+28,y+20)],INK,4)
            y,l,r,cx,w=fit.at(0.56); p.rect((l+10,y,r-10,y+22),S,r=6); p.rect((X(cx,w,0)-14,y-4,X(cx,w,0)+14,y+26),METAL,r=4,edge=4)
        elif cls in ('medium','heavy'):
            if cls=='heavy' and not side: pauldrons(p,fit)
            carrier(p,fit,X,side,heavy=(cls=='heavy'))
            if not side:                                                     # рация на плече
                y,l,r,cx,w=fit.at(0.14); p.rect((cx+w*0.30,y,cx+w*0.42,y+60),DARK,r=6); p.line([(cx+w*0.39,y),(cx+w*0.39,y-34)],DARK,5)
        elif cls=='science':
            for dx in ((-0.42,0.42) if not side else (0.30,)):
                y,l,r,cx,w=fit.at(0.04); p.rect((X(cx,w,dx)-14,y,X(cx,w,dx)+14,yH-12),S,r=6)
            y,l,r,cx,w=fit.at(0.52); p.rect((l+8,y,r-8,y+16),LIGHT,r=4,edge=4)
            if not side:
                y,l,r,cx,w=fit.at(0.14); p.rect((cx-48,y,cx+48,y+72),DARK,r=10)
                for i,c in enumerate([(120,230,140),(240,200,60),(120,230,140)]): p.dot(cx-28+i*28,y+22,7,c)
                p.rect((cx-34,y+42,cx+34,y+58),(90,170,120),r=4,edge=3,shadow=False)
            y0=fit.at(0.08)[0]; p.line([(X(cT,wT,-0.42),y0),(X(cT,wT,-0.25),y0+60),(X(cT,wT,-0.05),y0+80)],RUBBER,12)
        elif cls=='exo':
            y,l,r,cx,w=fit.at(0.10); y1=fit.at(0.40)[0]
            p.rect((X(cx,w,-0.32),y,X(cx,w,0.32),y1),S,r=10)
            for i in range(2):
                yy,l2,r2,c2,w2=fit.at(0.43+i*0.08); p.rect((X(c2,w2,-0.3),yy,X(c2,w2,0.3),yy+30),S,r=6,tone=200)
            for dx in ((-0.48,0.48) if not side else (0.40,)):
                pts=[(X(c,ww,dx),yy) for yy,_,_,c,ww in (fit.at(0.04),fit.at(0.33),fit.at(TOP_T-0.02))]
                p.line(pts,INK,24); p.line(pts,METAL,12)
                for (x,yy) in pts[:2]: p.ellipse([x-16,yy-16,x+16,yy+16],DARK,edge=5); p.dot(x,yy,6,METAL)
        if not side and cls not in ('cloak',):                                # нашивка
            y,l,r,cx,w=fit.at(0.16); x=cx-w*0.40
            p.rect((x-20,y,x+20,y+30),tuple(int(v*255) for v in accent),r=5,edge=4,shadow=False)
        if side and cls in ('light','medium','cloak'):
            y0,l0,r0,c0,w0=fit.at(0.10); p.rect((l0+4,y0+14,l0+w0*0.24,fit.at(0.58)[0]),S,r=14)
    return p.finish(clip)

def render_pants(cls, body, view, seed=0):
    fit=Fit(body,view); p=Painter(); side=view=='east'; back=view=='north'
    clip=body_mask(fit.band(PANTS_T,1.0))
    p.mask(clip,P,tone=212,shadow=False,hl=False)
    sh=ImageChops.subtract(clip,ImageChops.offset(clip,-16,-22)); p.col.paste((158,158,158,255),(0,0),sh)
    def X(cx,w,dx): return cx+(w*0.12 if side else 0)+dx*w*(0.55 if side else 1.0)
    yT,lT,rT,cT,wT=fit.at(0.74); yK,lK,rK,cK,wK=fit.at(0.87); yE=fit.at(1.0)[0]
    if not side: p.line([(fit.at(0.80)[3],fit.at(0.80)[0]),(fit.at(0.99)[3],yE-4)],INK,6)        # шов между ногами
    yb=fit.at(0.95)[0]; p.rect((0,yb,N,yE+10),DARK,r=0,edge=0,shadow=False)                       # ботинки
    p.line([(0,yb),(N,yb)],INK,6)
    dxs=(-0.27,0.27) if not side else (0.10,)
    if cls=='cloak':
        rng=random.Random(seed)
        for _ in range(26):
            t=rng.uniform(0.6,0.94); y,l,r,cx,w=fit.at(t); x=rng.uniform(l,r); rr=rng.uniform(12,24)
            p.ellipse([x-rr,y-rr*0.6,x+rr,y+rr*0.6],S,tone=rng.choice((185,205,232)),edge=0,shadow=False,hl=False)
    if cls in ('light','cloak','medium','heavy'):
        for dx in dxs:
            if cls=='heavy':
                p.rect((X(cT,wT,dx)-32,yT-22,X(cT,wT,dx)+32,yT+40),S,r=10)
            else:
                p.rect((X(cT,wT,dx)-30,yT-14,X(cT,wT,dx)+30,yT+40),P,r=8,tone=196); p.line([(X(cT,wT,dx)-26,yT+2),(X(cT,wT,dx)+26,yT+2)],INK,4)
            if cls in ('medium','heavy'):
                x=X(cK,wK,dx); p.rect((x-28,yK-20,x+28,yK+24),S,r=16)
    elif cls=='science':
        for dx in ((-0.42,0.42) if not side else (0.30,)):
            p.rect((X(cT,wT,dx)-14,fit.at(0.6)[0],X(cT,wT,dx)+14,yb),S,r=6)
        for t in (0.80,0.90):
            y,l,r,cx,w=fit.at(t); p.rect((l+8,y,r-8,y+14),LIGHT,r=4,edge=4)
    elif cls=='exo':
        for dx in dxs:
            p.rect((X(cT,wT,dx)-30,yT-18,X(cT,wT,dx)+30,yT+40),S,r=8)
            pts=[(X(c,ww,dx*1.45),yy) for yy,_,_,c,ww in (fit.at(0.62),fit.at(0.86),fit.at(0.97))]
            p.line(pts,INK,24); p.line(pts,METAL,12)
            x,yy=pts[1]; p.ellipse([x-17,yy-17,x+17,yy+17],DARK,edge=5); p.dot(x,yy,6,METAL)
    if back and cls in ('light','medium','cloak'):
        for dx in (-0.22,0.22): p.rect((X(cT,wT,dx)-24,yT-34,X(cT,wT,dx)+24,yT+4),P,r=6,tone=200)
    return p.finish(clip)

# ======================= ШЛЕМЫ =======================
HCX=256
def render_helmet(style, view, seed=0, accent=(0.8,0.7,0.3)):
    p=Painter(); e=view=='east'; n=view=='north'; cx=HCX if not e else 248
    acc=tuple(int(v*255) for v in accent)
    def dome(y_cut,box):
        m=Image.new('L',(N,N),0); ImageDraw.Draw(m).ellipse(box,fill=255)
        a=np.array(m); a[int(y_cut):]=0; return Image.fromarray(a)
    def edge_of(m):
        a=np.array(m)>127; d=ndimage.distance_transform_edt(a); return Image.fromarray(((d>0)&(d<=EDGE)).astype(np.uint8)*255)
    def put(m,mat,tone=None):
        p.mask(m,mat,tone); p.col.paste(INK,(0,0),edge_of(m)); p.msk.paste((0,0,0),(0,0),edge_of(m))
    if style=='cap':
        put(dome(252,[cx-104,150,cx+104,350] if not e else [140,150,360,350]),P)
        p.rect((cx-108 if not e else 136,214,cx+108 if not e else 364,252),S,r=10)
        for x in range((cx-100 if not e else 144),(cx+100 if not e else 356),14): p.line([(x,220),(x,246)],(150,150,150),3)
    elif style=='hood':
        if n: m=Image.new('L',(N,N),0); ImageDraw.Draw(m).ellipse([cx-122,128,cx+122,372],fill=255)
        else:
            m=Image.new('L',(N,N),0); dm=ImageDraw.Draw(m)
            dm.ellipse([cx-122,128,cx+122,372] if not e else [112,128,372,368],fill=255)
            dm.ellipse([cx-74,214,cx+74,346] if not e else [262,205,420,350],fill=0)
        put(m,P)
        if not n: p.ellipse([cx-80,206,cx+80,352] if not e else [256,198,300,356],P,tone=190,edge=0,shadow=False,hl=False) if False else None
    elif style in ('combat','psi'):
        put(dome(268,[cx-116,140,cx+116,392] if not e else [112,140,382,392]),P)
        p.rect((cx-120 if not e else 110,248,cx+120 if not e else 384,272),S,r=8)           # кромка
        for xx in ((cx-126,cx+104) if not e else (214,)): p.rect((xx,236,xx+24,298),S,r=8,tone=200)   # наушники/крепления
        if not n:
            if e: p.rect((318,186,392,238),DARK,r=10); p.rect((338,194,388,230),GLASS,r=8,edge=4)
            else:
                p.rect((cx-100,182,cx+100,238),DARK,r=18)
                p.rect((cx-90,190,cx-8,230),GLASS,r=12,edge=4); p.rect((cx+8,190,cx+90,230),GLASS,r=12,edge=4)
            p.rect((cx-20 if not e else 300,150,cx+20 if not e else 332,176),METAL,r=4,edge=4)   # крепление
        else:
            p.line([(cx-116,212),(cx+116,212)],DARK,16)
        if style=='psi':
            for i in range(3): p.dc.arc([cx-96+i*10,152+i*10,cx+96-i*10,330-i*10],205,335,fill=(190,120,55,255),width=6)
            ax=cx+70 if not e else 200
            p.line([(ax,156),(ax+20,96)],INK,12); p.line([(ax,156),(ax+20,96)],METAL,6); p.dot(ax+20,94,10,acc)
    elif style=='visor':
        put(dome(272,[cx-118,138,cx+118,392] if not e else [110,138,384,392]),P)
        if n: p.poly([(cx-112,250),(cx+112,250),(cx+96,342),(cx-96,342)],S)
        else:
            box=(cx-98,234,cx+98,354) if not e else (300,230,398,352)
            p.rect(box,S,r=18); p.rect((box[0]+20,284,box[2]-20,302),DARK,r=4,edge=4,shadow=False)
            p.line([(box[0]+26,288),(box[2]-26,288)],acc,3)
            for xx in (box[0]+14,box[2]-14): p.dot(xx,box[1]+16,5,METAL)
        p.rect((cx-120 if not e else 108,252,cx+120 if not e else 386,274),S,r=8,tone=196)
    elif style=='sealed':
        m=Image.new('L',(N,N),0); ImageDraw.Draw(m).ellipse([cx-126,124,cx+126,376] if not e else [124,124,376,376],fill=255); put(m,P)
        if not n:
            box=[cx-92,180,cx+92,340] if not e else [292,176,396,334]
            p.ellipse([box[0]-14,box[1]-14,box[2]+14,box[3]+14],S); p.ellipse(box,GLASS,shadow=False)
            p.dc.arc([box[0]+14,box[1]+12,box[2]-14,box[3]-12],200,250,fill=(220,235,240,220),width=10)
        else:
            p.rect((cx-40,190,cx+40,300),S,r=12); p.line([(cx,300),(cx,372)],RUBBER,12)
        p.rect((cx-120 if not e else 130,340,cx+120 if not e else 372,378),S,r=12)
        for xx in ((cx-116,cx+116) if not e else (176,)): p.ellipse([xx-14,250,xx+14,278],METAL,edge=5)
    elif style=='exo':
        pts=[(120,300),(126,198),(176,146),(318,146),(380,196),(396,288),(352,364),(170,364)] if e else \
            [(cx-112,300),(cx-118,200),(cx-80,144),(cx+80,144),(cx+118,200),(cx+112,300),(cx+72,366),(cx-72,366)]
        p.poly(pts,P)
        if not n:
            if e: p.poly([(330,228),(400,232),(400,264),(338,264)],DARK); p.line([(340,246),(394,248)],acc,6)
            else:
                p.poly([(cx-94,222),(cx+94,222),(cx+86,258),(cx+18,258),(cx+14,322),(cx-14,322),(cx-18,258),(cx-86,258)],DARK)
                p.line([(cx-80,240),(cx+80,240)],acc,6)
                p.rect((cx-56,330,cx+56,356),S,r=6)
                for i in range(4): p.line([(cx-40+i*26,334),(cx-40+i*26,352)],INK,4)
        else:
            p.rect((cx-70,180,cx+70,300),S,r=10)
        p.line([(pts[1][0],pts[1][1]),(pts[4][0],pts[4][1])],INK,5)
    return p.finish()

# ======================= ПРОТИВОГАЗ (свои цвета, без маски) =======================
def render_gasmask(view):
    p=Painter(); OL=(96,106,72)
    if view=='south':
        p.ellipse([180,200,332,352],RUBBER)
        for x in (220,292): p.ellipse([x-28,232,x+28,282],DARK,edge=6); p.ellipse([x-20,240,x+20,276],GLASS,edge=4,shadow=False)
        p.ellipse([226,300,286,356],OL)
        for r in (22,14): p.dc.ellipse([256-r,328-r,256+r,328+r],outline=INK,width=4)
        p.line([(186,236),(150,226)],INK,8); p.line([(326,236),(362,226)],INK,8)
    elif view=='east':
        p.poly([(270,206),(330,216),(340,300),(304,334),(268,318)],RUBBER)
        p.ellipse([300,236,342,280],DARK,edge=6); p.ellipse([306,242,336,274],GLASS,edge=4,shadow=False)
        p.rect((316,300,368,344),OL,r=10)
        p.line([(272,240),(150,230)],INK,10)
    else:
        for y in (220,262,300): p.line([(160,y),(352,y)],INK,12); p.line([(160,y),(352,y)],RUBBER,6)
        p.line([(256,206),(256,312)],INK,12); p.line([(256,206),(256,312)],RUBBER,6)
    col,msk=p.finish(); return col

# ======================= РЮКЗАКИ И БАЛЛОНЫ =======================
def render_pack(style, body, view, seed=0):
    fit=Fit(body,view); p=Painter()
    big={'frame':1.25,'raid':1.1,'lead':1.0,'closed':1.05,'cooling':1.0,'tourist':1.0,'medic':0.85,'sack':0.9,'tank1':0.9,'tank2':1.0}[style]
    yA,lA,rA,cA,wA=fit.at(0.10); yB=fit.at(min(0.72,0.56*big+0.06))[0]
    tanky=style in ('tank1','tank2','closed','cooling')
    def tank(x,y0,y1,r,mat):
        p.rect((x-r,y0,x+r,y1),mat,r=int(r)); p.rect((x-r*0.45,y0-20,x+r*0.45,y0+6),METAL,r=4,edge=5); p.ellipse([x-r*0.6,y0-34,x+r*0.6,y0-14],METAL,edge=5)
    def pack(box):
        x0,y0,x1,y1=box; w=x1-x0; h=y1-y0; cx=(x0+x1)/2
        if style=='sack':
            p.ellipse([x0,y0+h*0.15,x1,y1],P); p.poly([(cx-w*0.18,y0+h*0.22),(cx+w*0.18,y0+h*0.22),(cx+w*0.08,y0),(cx-w*0.08,y0)],P,tone=205)
            p.line([(cx-w*0.17,y0+h*0.22),(cx+w*0.17,y0+h*0.22)],S and DARK,8)
        elif style in ('tourist','raid','frame','medic'):
            if style=='frame':
                for x in (x0+6,x1-6): p.line([(x,y0-32),(x,y1+14)],INK,20); p.line([(x,y0-32),(x,y1+14)],METAL,10)
            if style in ('tourist','raid','frame'):
                for xx in (x0-20,x1-6): p.rect((xx,y0+h*0.40,xx+26,y0+h*0.86),S,r=10)
            p.rect((x0,y0,x1,y1),P,r=26)
            p.rect((x0-6,y0-6,x1+6,y0+h*0.3),P,r=24,tone=204)
            p.rect((cx-14,y0+h*0.3-12,cx+14,y0+h*0.3+12),METAL,r=3,edge=4)
            if style=='medic':
                p.rect((cx-12,y0+h*0.44,cx+12,y0+h*0.84),LIGHT,r=2,edge=4,shadow=False); p.rect((cx-34,y0+h*0.56,cx+34,y0+h*0.72),LIGHT,r=2,edge=4,shadow=False)
            else:
                p.rect((cx-w*0.28,y0+h*0.5,cx+w*0.28,y0+h*0.86),S,r=10); p.line([(cx-w*0.26,y0+h*0.6),(cx+w*0.26,y0+h*0.6)],INK,4)
            if style in ('raid','frame'):
                yb=y0-36 if style=='raid' else y1-12
                p.rect((x0-16,yb,x1+16,yb+42),S,r=21,tone=196)
                for x in (x0+16,x1-16): p.line([(x,yb-2),(x,yb+44)],DARK,8)
        elif style=='lead':
            p.rect((x0,y0,x1,y1),P,r=12,tone=200)
            for i in range(1,3): p.line([(x0+10,y0+i*h/3),(x1-10,y0+i*h/3)],INK,5)
            r=min(w,h)*0.18; cy=y0+h*0.5; p.ellipse([cx-r,cy-r,cx+r,cy+r],(240,200,40),edge=5,shadow=False)
            for a in (90,210,330): p.dc.pieslice([cx-r*0.86,cy-r*0.86,cx+r*0.86,cy+r*0.86],a-30,a+30,fill=(30,30,30,255))
            p.dot(cx,cy,r*0.2,(30,30,30))
        elif style=='tank1':
            tank(cx,y0+22,y1,w*0.26,S)
        elif style=='tank2':
            for dx in (-0.22,0.22): tank(cx+dx*w,y0+22,y1,w*0.2,S)
            p.rect((cx-w*0.3,y0-8,cx+w*0.3,y0+12),METAL,r=4,edge=5)
        elif style=='closed':
            p.rect((x0,y0,x1,y1),P,r=20)
            for dx in (-0.2,0.2): tank(cx+dx*w,y0+30,y1-16,w*0.14,S)
            for i in range(2): p.ellipse([cx-46+i*60,y0+6,cx-14+i*60,y0+38],LIGHT,edge=5,shadow=False)
        elif style=='cooling':
            p.rect((x0,y0,x1,y1),P,r=14)
            for i in range(7): p.line([(x0+18,y0+22+i*(h-44)/7),(x1-18,y0+22+i*(h-44)/7)],INK,5)
            for xx in (x0+12,x1-12): p.line([(xx,y0+10),(xx,y1-10)],INK,16); p.line([(xx,y0+10),(xx,y1-10)],None,8,mat=S)
    if view=='north':
        pw=wA*0.58*min(big,1.15); pack((cA-pw/2,yA+12,cA+pw/2,yB))
    elif view=='east':
        depth=wA*0.42*big; pack((lA-depth*0.55,yA+12,lA+depth*0.45,yB))
        p.strap([(lA+depth*0.25,yA+24),(cA,yA+2),(rA-wA*0.14,fit.at(0.38)[0])],S if not tanky else None and S,16) if not tanky else \
            (p.line([(lA+depth*0.25,yA+24),(cA,yA+2),(rA-wA*0.14,fit.at(0.38)[0])],INK,24), p.line([(lA+depth*0.25,yA+24),(cA,yA+2),(rA-wA*0.14,fit.at(0.38)[0])],RUBBER,12))
    else:
        if style=='sack': p.strap([(cA-wA*0.3,yA),(cA+wA*0.25,fit.at(0.5)[0])],S,18)
        else:
            for dx in (-0.24,0.24): p.strap([(cA+dx*wA,yA-6),(cA+dx*wA*0.9,fit.at(0.42)[0])],S,18)
            yc=fit.at(0.30)[0]; p.strap([(cA-wA*0.22,yc),(cA+wA*0.22,yc)],S,10); p.rect((cA-14,yc-11,cA+14,yc+11),METAL,r=3,edge=4)
            if style in ('tank1','tank2','closed'):
                pts=[(cA+wA*0.3,yA-10),(cA+wA*0.22,fit.at(0.22)[0]),(cA+wA*0.06,fit.at(0.18)[0])]
                p.line(pts,INK,22); p.line(pts,RUBBER,10)
                gx,gy=pts[-1]; p.rect((gx-18,gy-14,gx+18,gy+14),METAL,r=6,edge=5)
            if style=='cooling':
                for dx in (-0.12,0.12):
                    pts=[(cA+dx*wA,yA),(cA+dx*wA*1.4,fit.at(0.45)[0])]; p.line(pts,INK,18); p.line(pts,None,8,mat=S)
    return p.finish()
