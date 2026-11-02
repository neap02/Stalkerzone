# Рисовальщик снаряжения Зоны, стиль 3 ("детальный"):
# - серые текстуры + маска цвета (_m): R — основной цвет, G — второй; металл/стекло/резина — свои цвета;
# - толстая обводка только снаружи; внутри — тонкие линии (4 px при 512);
# - у каждой детали плавный свет сверху вниз, тень у нижнего края, тонкий блик;
# - плотные мелкие детали: стропа MOLLE, подсумки с клапанами и фастексами, липучки, строчка, заклёпки.
# Комбинезон — одна деталь. Экзоскелет — отдельная вещь поверх брони.
# Посадка по меркам тел/головы (suit_art.Fit). Все формы свои.
import math, random
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from suit_art import Fit, N, OUT

P,S='P','S'
TONE={P:212,S:196}
LINE=(40,40,42); INK=(22,20,18)
METAL=(160,162,160); STEEL=(118,120,122); DARK=(58,60,62); RUBBER=(66,68,64); GLASS=(92,120,138); LIGHT=(226,228,220)
OLIVE=(104,112,80); YELLOW=(222,182,48)

class Painter:
    """Совместим по вызовам с suit_art2.Painter (rect/ellipse/poly/line/strap/dot/mask/finish, dc)."""
    def __init__(s):
        s.col=np.zeros((N,N,4),np.float32); s.msk=np.zeros((N,N,3),np.uint8); s.sil=np.zeros((N,N),bool)
        s.yy=np.arange(N,dtype=np.float32)[:,None]
        s.over=Image.new('RGBA',(N,N),(0,0,0,0)); s.dc=ImageDraw.Draw(s.over)
        s.dm=ImageDraw.Draw(Image.new('RGB',(N,N)))          # заглушка для совместимости
    @staticmethod
    def M(fn):
        im=Image.new('L',(N,N),0); fn(ImageDraw.Draw(im)); return np.array(im)>127
    def paint(s,m,mat,tone=None,edge=4,grad=True,ao=True,hl=True,shade=0.26):
        if m is None or not m.any(): return
        ys=np.where(m.any(1))[0]; y0,y1=ys[0],ys[-1]+1
        if mat in (P,S): base=np.full(3,TONE[mat] if tone is None else tone,np.float32); mc=(255,0,0) if mat==P else (0,255,0)
        else: base=np.array(mat,np.float32); mc=(0,0,0)
        g=(1.07-shade*np.clip((s.yy-y0)/max(1,y1-y0),0,1)) if grad else np.ones((N,1),np.float32)
        rgb=np.broadcast_to(base[None,None,:]*g[:,:,None],(N,N,3))
        s.col[m,:3]=rgb[m]; s.col[m,3]=255; s.msk[m]=mc; s.sil|=m
        if ao:
            sh=m & ~np.roll(np.roll(m,-8,0),-6,1); s.col[sh,:3]*=0.74
        if hl:
            h=m & ~np.roll(np.roll(m,4,0),3,1); s.col[h,:3]=np.minimum(255,s.col[h,:3]*1.16+10)
        if edge:
            d=ndimage.distance_transform_edt(m); e=(d>0)&(d<=edge); s.col[e,:3]=LINE; s.msk[e]=0
    # ---- фигуры (как в suit_art2) ----
    def rect(s,box,mat,r=10,tone=None,edge=4,shadow=True,hl=True,grad=True):
        x0,y0,x1,y1=box; b=[min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)]
        s.paint(s.M(lambda d: d.rounded_rectangle(b,radius=r,fill=255)),mat,tone,edge,grad,shadow,hl)
    def ellipse(s,box,mat,tone=None,edge=4,shadow=True,hl=True,grad=True):
        s.paint(s.M(lambda d: d.ellipse(box,fill=255)),mat,tone,edge,grad,shadow,hl)
    def poly(s,pts,mat,tone=None,edge=4,shadow=True,hl=True,grad=True):
        s.paint(s.M(lambda d: d.polygon(pts,fill=255)),mat,tone,edge,grad,shadow,hl)
    def mask(s,m,mat,tone=None,shadow=True,hl=True,edge=0,grad=True):
        a=np.array(m)>127 if isinstance(m,Image.Image) else m
        s.paint(a,mat,tone,edge,grad,shadow,hl)
    def line(s,pts,col=LINE,w=4,mat=None):
        if mat in (P,S):
            s.paint(s.M(lambda d: d.line(pts,fill=255,width=w,joint='curve')),mat,None,0,False,False,False)
        else:
            c=tuple(col[:3]) if col is not None else LINE
            s.paint(s.M(lambda d: d.line(pts,fill=255,width=w,joint='curve')),c,None,0,False,False,False)
    def strap(s,pts,mat,w=18):
        s.paint(s.M(lambda d: d.line(pts,fill=255,width=w,joint='curve')),mat,None,3,False,False,True)
    def dot(s,x,y,r,col):
        s.paint(s.M(lambda d: d.ellipse([x-r,y-r,x+r,y+r],fill=255)),tuple(col),None,0,False,False,False)
    # ---- мелкие детали ----
    def rivet(s,x,y,r=5):
        s.paint(s.M(lambda d: d.ellipse([x-r,y-r,x+r,y+r],fill=255)),METAL,None,2,True,False,True)
    def stitch(s,a,b,dash=8,gap=6,col=(70,70,70)):
        (xa,ya),(xb,yb)=a,b; L=math.hypot(xb-xa,yb-ya); n=int(L//(dash+gap))
        for i in range(n+1):
            t0=i*(dash+gap)/max(L,1); t1=min(1,(i*(dash+gap)+dash)/max(L,1))
            s.dc.line([(xa+(xb-xa)*t0,ya+(yb-ya)*t0),(xa+(xb-xa)*t1,ya+(yb-ya)*t1)],fill=col+(150,),width=2)
    def molle(s,box,mat=S,tone=None):
        x0,y0,x1,y1=box; t=(TONE[mat] if tone is None else tone)-22
        y=y0+6
        while y+8<y1:
            s.rect((x0+4,y,x1-4,y+8),mat,r=2,tone=t,edge=2,shadow=False,hl=False,grad=False)
            for x in np.arange(x0+20,x1-10,24): s.dc.line([(x,y),(x,y+8)],fill=LINE+(255,),width=2)
            y+=16
    def velcro(s,box):
        x0,y0,x1,y1=box; s.rect(box,P,r=4,tone=176,edge=3,shadow=False,hl=False,grad=False)
        for x in range(int(x0)+4,int(x1)-2,5): s.dc.line([(x,y0+4),(x,y1-4)],fill=(150,150,150,140),width=1)
    def fastex(s,x,y):
        s.rect((x-9,y-6,x+9,y+8),DARK,r=3,edge=2,shadow=False); s.dc.line([(x-5,y+1),(x+5,y+1)],fill=(30,30,30,255),width=2)
    def pouch(s,box,mat=S,tone=None,buckle=True,shock=False):
        x0,y0,x1,y1=box; h=y1-y0
        s.rect(box,mat,r=6,tone=tone)
        s.rect((x0-2,y0-2,x1+2,y0+h*0.38),mat,r=6,tone=(TONE[mat] if tone is None else tone)-14)   # клапан
        if buckle: s.fastex((x0+x1)/2,y0+h*0.38)
        s.stitch((x0+5,y1-6),(x1-5,y1-6))
        if shock:
            for xx in (x0+8,x1-8): s.dc.line([(xx,y0-14),(xx,y0+4)],fill=(40,40,40,255),width=3)
    def finish(s,clip=None):
        sil=s.sil.copy()
        ov=np.array(s.over).astype(np.float32); a=ov[:,:,3:4]/255
        s.col[:,:,:3]=s.col[:,:,:3]*(1-a)+ov[:,:,:3]*a; sil|=ov[:,:,3]>100
        if clip is not None:
            c=np.array(clip)>127 if isinstance(clip,Image.Image) else clip; sil&=c
        # фактура ткани на окрашиваемых местах
        rng=np.random.default_rng(7); noise=rng.normal(0,3.2,(N,N)).astype(np.float32)
        tint=(s.msk[:,:,0]>0)|(s.msk[:,:,1]>0); s.col[tint,:3]+=noise[tint,None]
        d=ndimage.distance_transform_edt(sil); ring=(d>0)&(d<=OUT)
        col=np.clip(s.col,0,255).astype(np.uint8); col[ring,:3]=INK; col[:,:,3]=np.where(sil,255,0)
        msk=s.msk.copy(); msk[ring]=0
        return Image.fromarray(col,'RGBA'),Image.fromarray(msk,'RGB')

# ======================= КОМБИНЕЗОН =======================
def render_coverall(cls, body, view, seed=0, accent=(0.8,0.7,0.3)):
    fit=Fit(body,view); p=Painter(); side=view=='east'; back=view=='north'
    acc=tuple(int(v*255) for v in accent); rng=random.Random(seed)
    poly=fit.polygon(); bodym=Painter.M(lambda d: d.polygon(poly,fill=255))
    p.paint(bodym,P,edge=0,ao=False,hl=False,shade=0.30)
    sh=bodym & ~np.roll(np.roll(bodym,-20,0),-16,1); p.col[sh,:3]*=0.80          # объём тела
    def at(t): return fit.at(t)
    def X(cx,w,dx): return cx+(w*0.16 if side else 0)+dx*w*(0.55 if side else 1.0)
    yT,lT,rT,cT,wT=at(0.0)
    # --- низ: шов ног, наколенники, карманы, ботинки ---
    yb=at(0.935)[0]; yE=at(1.0)[0]
    p.rect((0,yb,N,yE+20),RUBBER,r=0,edge=0,shadow=False,hl=False); p.line([(0,yb),(N,yb)],LINE,4)
    p.line([(0,yE-12),(N,yE-12)],(40,40,40),3)
    if not side: p.line([(at(0.80)[3],at(0.80)[0]),(at(0.93)[3],yb)],LINE,4)
    dxs=(-0.27,0.27) if not side else (0.08,)
    yK,lK,rK,cK,wK=at(0.86); yC,lC,rC,cC,wC=at(0.72)
    for dx in dxs:
        if cls in ('light','medium','cloak') and not back:
            p.pouch((X(cC,wC,dx)-30,yC-18,X(cC,wC,dx)+30,yC+40),P,tone=196,buckle=False)
        if cls in ('medium','heavy','exo'):
            x=X(cK,wK,dx); p.rect((x-28,yK-22,x+28,yK+22),S,r=14,tone=170 if cls!='exo' else None)
            p.rect((x-18,yK-12,x+18,yK+12),S,r=8,tone=150 if cls!='exo' else 182,edge=3)
        if cls in ('heavy','exo'):
            p.rect((X(cC,wC,dx)-32,yC-26,X(cC,wC,dx)+32,yC+36),S,r=8)
            p.line([(X(cC,wC,dx)-26,yC+4),(X(cC,wC,dx)+26,yC+4)],LINE,3)
        if cls=='science':
            p.rect((X(cC,wC,dx)-30,at(0.84)[0],X(cC,wC,dx)+30,at(0.84)[0]+12),LIGHT,r=3,edge=3)
    if cls=='science':
        for dx in ((-0.43,0.43) if not side else (0.30,)):
            y,l,r,cx,w=at(0.02); p.rect((X(cx,w,dx)-12,y+10,X(cx,w,dx)+12,yb),S,r=5,edge=3)
    # --- пояс ---
    yW,lW,rW,cW,wW=at(0.57)
    p.rect((lW+6,yW,rW-6,yW+20),S if cls!='science' else P,r=4,tone=150 if cls!='science' else 190,edge=3)
    if not back: p.rect((X(cW,wW,0)-14,yW-3,X(cW,wW,0)+14,yW+23),METAL,r=3,edge=3)
    # --- верх ---
    if not back and cls not in ('science',):
        p.rect((X(cT,wT,-0.34),yT-4,X(cT,wT,0.34),yT+24),P,r=10,tone=192,edge=3)          # воротник
    if cls=='science':
        p.rect((X(cT,wT,-0.36),yT-6,X(cT,wT,0.36),yT+20),METAL,r=8,edge=3)                # кольцо под шлем
    if back:
        y0,l0,r0,c0,w0=at(0.07); y1=at(0.54)[0]
        if cls in ('medium','heavy'):
            p.rect((c0-w0*0.36,y0,c0+w0*0.36,y1),S); p.molle((c0-w0*0.32,y0+50,c0+w0*0.32,y1-10))
            p.rect((c0-28,y0+8,c0+28,y0+30),S,r=8,tone=170)                                 # ручка эвакуации
        elif cls=='exo':
            for i in range(3):
                yy=y0+i*(y1-y0)/3; p.rect((c0-w0*0.36,yy,c0+w0*0.36,yy+(y1-y0)/3-6),S,r=8)
        elif cls=='science':
            for dx in (-0.2,0.2): p.rect((c0+dx*w0-16,y0+20,c0+dx*w0+16,y0+70),METAL,r=6,edge=3)   # крепления баллонов
            p.stitch((c0-w0*0.3,y1-8),(c0+w0*0.3,y1-8))
        else:
            p.rect((c0-w0*0.22,y0+40,c0+w0*0.22,y1-30),P,r=8,tone=194,edge=3); p.stitch((c0,y0+10),(c0,y1))
        if cls=='cloak':
            for _ in range(36):
                t=rng.uniform(0.0,0.6); y,l,r,cx,w=at(t); x=rng.uniform(l,r); rr=rng.uniform(12,26)
                p.ellipse([x-rr,y-rr*0.55,x+rr,y+rr*0.55],S,tone=rng.choice((160,186,210)),edge=0,shadow=False,hl=False,grad=False)
            p.ellipse([c0-w0*0.32,y0-46,c0+w0*0.32,y0+18],P,tone=200)
    else:
        if cls=='cloak':
            for _ in range(46):
                t=rng.uniform(0.02,0.6); y,l,r,cx,w=at(t); x=rng.uniform(l,r); rr=rng.uniform(12,26)
                p.ellipse([x-rr,y-rr*0.55,x+rr,y+rr*0.55],S,tone=rng.choice((160,186,210)),edge=0,shadow=False,hl=False,grad=False)
            for _ in range(30):
                t=rng.uniform(0.56,0.62); y,l,r,cx,w=at(t); x=rng.uniform(l+6,r-6)
                p.line([(x,y),(x+rng.uniform(-5,5),y+rng.uniform(16,30))],None,4,mat=S)
        if cls=='light':
            if not side:
                p.line([(cT,yT+22),(cT,yW-2)],STEEL,5); p.rect((cT-6,yT+26,cT+6,yT+44),METAL,r=2,edge=2)
            for dx in ((-0.23,0.23) if not side else (0.10,)):
                y,l,r,cx,w=at(0.20); p.pouch((X(cx,w,dx)-30,y,X(cx,w,dx)+30,y+52),P,tone=196,buckle=False)
            if not side: p.velcro((X(cT,wT,0.16)-22,at(0.10)[0],X(cT,wT,0.16)+22,at(0.10)[0]+16))
        elif cls in ('medium','heavy'):
            heavy=cls=='heavy'
            if heavy and not side:                                                          # наплечники
                y,l,r,cx,w=at(0.05)
                for dx in (-1,1):
                    for i in range(3):
                        x=cx+dx*w*(0.44-i*0.02); yy=y+i*16
                        p.ellipse([x-34+i*3,yy-18,x+34-i*3,yy+26],S,tone=196-i*8)
            for dx in ((-0.26,0.26) if not side else (0.20,)):                            # лямки
                y,l,r,cx,w=at(0.0); p.strap([(X(cx,w,dx),y-2),(X(cx,w,dx*0.95),at(0.12)[0])],S,22)
            y,l,r,cx,w=at(0.08); y2=at(0.40)[0]; k=0.36 if not heavy else 0.42
            p.rect((X(cx,w,-k),y,X(cx,w,k),y2),S)                                          # плита
            p.velcro((X(cx,w,-0.22),y+12,X(cx,w,0.22),y+38))                               # липучка
            p.molle((X(cx,w,-k)+6,y+48,X(cx,w,k)-6,y2-6))
            y3,l3,r3,c3,w3=at(0.40); y4=at(0.555)[0]
            p.rect((X(c3,w3,-0.48),y3-4,X(c3,w3,0.48),y4),S,r=8,tone=176)                  # камербанд
            for xx in np.arange(X(c3,w3,-0.44),X(c3,w3,0.44),10): p.dc.line([(xx,y3),(xx,y4-4)],fill=(90,90,90,90),width=1)
            n=3 if not heavy else 4; span=0.66 if not heavy else 0.76
            if side: n=2; span=0.5
            pw=w3*span*(0.55 if side else 1)/n
            for i in range(n):
                x=X(c3,w3,-span/2)+i*pw+3 if not side else X(c3,w3,0.0)+i*pw
                p.rect((x+6,y3-46,x+pw-6,y3-30),DARK,r=3,edge=2,shadow=False)              # торцы магазинов
                p.pouch((x+2,y3-34,x+pw-2,y3+30),S,tone=184,shock=True)
            if heavy and not side:
                y5=at(0.60)[0]; p.rect((X(c3,w3,-0.17),y4+2,X(c3,w3,0.17),y5+28),S,r=8,tone=180)   # паховая защита
            if not side:                                                                    # рация
                y,l,r,cx,w=at(0.12); p.rect((cx+w*0.30,y,cx+w*0.42,y+56),DARK,r=5,edge=3); p.line([(cx+w*0.39,y),(cx+w*0.39,y-30)],DARK,4)
        elif cls=='science':
            for t in (0.48,):
                y,l,r,cx,w=at(t); p.rect((l+8,y,r-8,y+14),LIGHT,r=3,edge=3)
            if not side:
                y,l,r,cx,w=at(0.12)
                p.rect((cx-52,y,cx+52,y+84),DARK,r=8,edge=3)                                 # блок управления
                p.rect((cx-40,y+10,cx+40,y+40),(70,150,110),r=4,edge=2,shadow=False)
                for i in range(4): p.dc.line([(cx-34,y+16+i*6),(cx-34+rng.randint(20,68),y+16+i*6)],fill=(170,240,190,255),width=2)
                for i,c in enumerate([(220,70,60),(240,200,60),(120,230,140)]): p.dot(cx-28+i*28,y+58,6,c)
                p.rect((cx+32,y+52,cx+46,y+72),METAL,r=2,edge=2)
            y0=at(0.06)[0]; p.line([(X(cT,wT,-0.42),y0+10),(X(cT,wT,-0.30),y0+70),(X(cT,wT,-0.08),y0+92)],RUBBER,12)
            p.line([(X(cT,wT,-0.42),y0+10),(X(cT,wT,-0.30),y0+70),(X(cT,wT,-0.08),y0+92)],(96,98,94),4)
        elif cls=='exo':
            y,l,r,cx,w=at(0.06); y2=at(0.38)[0]
            p.rect((X(cx,w,-0.36),y,X(cx,w,0.36),y2),S,r=12)
            for xx in (X(cx,w,-0.30),X(cx,w,0.30)): p.rivet(xx,y+14); p.rivet(xx,y2-14)
            p.line([(X(cx,w,-0.30),y+(y2-y)*0.5),(X(cx,w,0.30),y+(y2-y)*0.5)],LINE,3)
            for i in range(3):
                yy,l2,r2,c2,w2=at(0.40+i*0.055); p.rect((X(c2,w2,-0.32),yy,X(c2,w2,0.32),yy+24),S,r=6,tone=184-i*6,edge=3)
            if not side:
                yS,lS,rS,cS,wS=at(0.04)
                for dx in (-1,1): p.ellipse([cS+dx*wS*0.45-34,yS-20,cS+dx*wS*0.45+34,yS+30],S,tone=186)
        if not side and cls!='cloak':                                                       # нашивка
            y,l,r,cx,w=at(0.16); x=cx-w*0.42
            p.rect((x-18,y,x+18,y+26),acc,r=4,edge=3,shadow=False)
        if side and cls in ('medium','heavy'):
            y0,l0,r0,c0,w0=at(0.08); p.rect((l0+6,y0+10,l0+w0*0.2,at(0.5)[0]),S,r=8)          # плита сзади
    return p.finish(bodym)

# ======================= ЭКЗОСКЕЛЕТ (отдельная вещь) =======================
def render_exo(kind, body, view, seed=0):
    fit=Fit(body,view); p=Painter(); side=view=='east'; back=view=='north'
    heavy=kind=='assault'
    def at(t): return fit.at(t)
    def strut(pts,w=14):
        p.paint(Painter.M(lambda d: d.line(pts,fill=255,width=w+8,joint='curve')),STEEL,None,3,True,False,True)
        p.paint(Painter.M(lambda d: d.line(pts,fill=255,width=max(4,w-8),joint='curve')),METAL,None,0,False,False,True)
    def joint(x,y,r=17):
        p.ellipse([x-r,y-r,x+r,y+r],DARK,edge=3); p.ellipse([x-r*0.45,y-r*0.45,x+r*0.45,y+r*0.45],METAL,edge=2)
    def piston(a,b):
        p.paint(Painter.M(lambda d: d.line([a,b],fill=255,width=12)),(80,82,84),None,3,True,False,True)
        mid=((a[0]+b[0])/2,(a[1]+b[1])/2); p.paint(Painter.M(lambda d: d.line([mid,b],fill=255,width=6)),(200,202,200),None,0,False,False,False)
    yH,lH,rH,cH,wH=at(0.58)
    if not back:                                                                           # тазовый пояс
        p.rect((lH+4,yH-6,rH-4,yH+24),S,r=6,edge=3); p.rect((cH+(wH*0.1 if side else 0)-22,yH-10,cH+(wH*0.1 if side else 0)+22,yH+28),DARK,r=4,edge=3)
    dxs=(-0.44,0.44) if not side else (0.10,)
    for dx in dxs:                                                                         # ноги
        pts=[]
        for t in (0.58,0.85,0.985):
            y,l,r,cx,w=at(t); pts.append((cx+(w*0.12 if side else 0)+dx*w*(0.55 if side else 0.92),y))
        strut(pts,16 if heavy else 13)
        joint(*pts[0],18); joint(*pts[1],16)
        piston((pts[0][0]+(10 if dx>0 else -10),pts[0][1]+20),(pts[1][0]+(10 if dx>0 else -10),pts[1][1]-24))
        p.rect((pts[2][0]-26,pts[2][1]-8,pts[2][0]+26,pts[2][1]+10),DARK,r=4,edge=3)       # опорная пластина стопы
    for dx in ((-0.48,0.48) if not side else (0.30,)):                                    # плечи
        pts=[]
        for t in (0.03,0.30,0.56):
            y,l,r,cx,w=at(t); pts.append((cx+(w*0.16 if side else 0)+dx*w*(0.55 if side else 1.0),y))
        strut(pts,12 if heavy else 10); joint(*pts[0],16)
    if back or side:                                                                       # силовой блок на спине
        y0,l0,r0,c0,w0=at(0.08); y1=at(0.50)[0]
        if back: box=(c0-w0*0.30,y0,c0+w0*0.30,y1)
        else:    box=(l0-w0*0.20,y0+6,l0+w0*0.20,y1)
        x0,yy0,x1,yy1=box; p.rect(box,S,r=10,edge=4)
        p.rect((x0+12,yy0+14,x1-12,yy0+54),DARK,r=4,edge=3)
        if back:
            p.rect((x0+20,yy0+20,x0+(x1-x0)*0.55,yy0+48),(70,150,110),r=3,edge=2,shadow=False)
            for i in range(3): p.dot(x1-26,yy0+22+i*10,4,[(120,230,140),(240,200,60),(220,70,60)][i])
        for i in range(5): p.dc.line([(x0+14,yy0+70+i*12),(x1-14,yy0+70+i*12)],fill=LINE+(255,),width=3)   # решётка
        yw=yy1-30
        for i in range(int((x1-x0-20)//16)):                                               # предупреждающая полоса
            xs=x0+10+i*16; p.poly([(xs,yw),(xs+8,yw),(xs+16,yw+16),(xs+8,yw+16)],YELLOW if i%2==0 else (30,30,30),edge=0,shadow=False,hl=False,grad=False)
        if back:
            p.line([(c0,yy1),(c0,yH)],STEEL,14); p.line([(c0,yy1),(c0,yH)],METAL,6)        # хребет
            for dx in (-0.22,0.22): p.line([(c0+dx*w0,yy1),(c0+dx*w0*1.6,yH)],RUBBER,8)     # кабели
    return p.finish()

# ======================= ШЛЕМЫ =======================
def render_helmet(style, view, seed=0, accent=(0.8,0.7,0.3)):
    p=Painter(); e=view=='east'; n=view=='north'; cx=256 if not e else 248
    acc=tuple(int(v*255) for v in accent)
    def dome(cut,box): return Painter.M(lambda d: d.ellipse(box,fill=255)) & (np.arange(N)[:,None]<cut)
    if style=='cap':
        p.paint(dome(252,[cx-104,150,cx+104,350] if not e else [140,150,360,350]),P)
        p.rect((cx-108 if not e else 136,214,cx+108 if not e else 364,254),S,r=10,edge=3)
        for x in range((cx-100 if not e else 144),(cx+100 if not e else 356),9): p.dc.line([(x,220),(x,248)],fill=(120,120,120,180),width=2)
        p.ellipse([cx-16 if not e else 236,136,cx+16 if not e else 268,166],S,edge=3)
    elif style=='hood':
        if n: m=Painter.M(lambda d: d.ellipse([cx-122,128,cx+122,372],fill=255))
        else:
            box=[cx-122,128,cx+122,372] if not e else [112,128,372,368]; hole=[cx-74,214,cx+74,346] if not e else [262,205,420,350]
            m=Painter.M(lambda d: d.ellipse(box,fill=255)) & ~Painter.M(lambda d: d.ellipse(hole,fill=255))
        p.paint(m,P)
        if not n and not e:
            p.line([(cx-56,330),(cx-60,380)],(60,60,60),4); p.line([(cx+56,330),(cx+60,380)],(60,60,60),4)
            p.dot(cx-60,382,6,METAL); p.dot(cx+60,382,6,METAL)
        p.stitch((cx-100 if not e else 130,250),(cx-60 if not e else 170,160))
    elif style in ('combat','psi'):
        box=[cx-116,140,cx+116,392] if not e else [112,140,382,392]
        m=dome(268,box)
        if not n:   # вырез над ушами (high-cut)
            ears=Painter.M(lambda d: (d.rectangle([cx-120,236,cx-92,272],fill=255),d.rectangle([cx+92,236,cx+120,272],fill=255))) if not e else Painter.M(lambda d: d.rectangle([196,236,236,272],fill=255))
            m=m & ~ears
        p.paint(m,P,edge=4)
        for xx in ((cx-118,cx+96) if not e else (150,)):                                   # рельсы
            p.rect((xx,196,xx+22,232),S,r=4,tone=170,edge=3); p.rivet(xx+11,204,4); p.rivet(xx+11,224,4)
        p.velcro((cx-50 if not e else 170,158,cx+50 if not e else 250,180))
        if not n:
            p.rect((cx-22 if not e else 318,170,cx+22 if not e else 350,200),METAL,r=4,edge=3)   # крепление ПНВ
            if e: p.rect((322,204,392,244),DARK,r=10,edge=3); p.rect((340,210,388,238),GLASS,r=8,edge=2)
            else:
                p.rect((cx-100,204,cx+100,248),DARK,r=16,edge=3)
                for x0 in (cx-90,cx+8): p.rect((x0,210,x0+82,242),GLASS,r=10,edge=2); p.dc.arc([x0+8,214,x0+60,238],200,260,fill=(220,235,240,200),width=3)
        else:
            p.rect((cx-116,206,cx+116,222),DARK,r=4,edge=2); p.rect((cx-30,170,cx+30,200),S,r=6,tone=170,edge=3)
        if style=='psi':
            for i in range(3): p.dc.arc([cx-98+i*10,152+i*10,cx+98-i*10,330-i*10],205,335,fill=(186,118,58,255),width=4)
            ax=cx+70 if not e else 200
            p.line([(ax,156),(ax+20,96)],STEEL,8); p.dot(ax+20,94,9,acc)
    elif style=='visor':
        box=[cx-118,138,cx+118,392] if not e else [110,138,384,392]
        p.paint(dome(274,box),P)
        if n: p.poly([(cx-112,250),(cx+112,250),(cx+96,342),(cx-96,342)],S); p.stitch((cx-90,300),(cx+90,300))
        else:
            fb=(cx-100,226,cx+100,356) if not e else (300,222,400,354)
            p.rect(fb,(70,76,80),r=20,edge=4)                                                # забрало
            p.rect((fb[0]+16,fb[1]+44,fb[2]-16,fb[1]+70),(30,34,38),r=4,edge=3)
            p.dc.line([(fb[0]+24,fb[1]+50),(fb[2]-60,fb[1]+50)],fill=acc+(200,),width=2)
            p.dc.arc([fb[0]+10,fb[1]+6,fb[2]-10,fb[3]-10],200,240,fill=(220,230,235,150),width=4)
            for xx in (fb[0]+10,fb[2]-10): p.rivet(xx,fb[1]+14,6)
        p.rect((cx-120 if not e else 108,252,cx+120 if not e else 386,276),S,r=6,tone=176,edge=3)
    elif style=='sealed':
        box=[cx-126,124,cx+126,376] if not e else [124,124,376,376]
        p.ellipse(box,P)
        if not n:
            fb=[cx-90,178,cx+90,338] if not e else [292,174,396,332]
            p.ellipse([fb[0]-16,fb[1]-16,fb[2]+16,fb[3]+16],S,edge=3)
            p.ellipse(fb,GLASS,edge=3); p.dc.arc([fb[0]+16,fb[1]+12,fb[2]-16,fb[3]-12],200,250,fill=(225,238,242,220),width=8)
            for xx in ((cx-136,cx+108) if not e else (150,)): p.rect((xx,262,xx+30,320),OLIVE,r=8,edge=3)   # фильтры
        else:
            p.rect((cx-40,190,cx+40,300),S,r=10,edge=3); p.rivet(cx-28,204); p.rivet(cx+28,204)
        p.rect((cx-120 if not e else 130,338,cx+120 if not e else 372,378),METAL,r=10,edge=3)
    elif style=='exo':
        pts=[(120,300),(126,198),(176,146),(318,146),(380,196),(396,288),(352,364),(170,364)] if e else \
            [(cx-112,300),(cx-118,200),(cx-80,144),(cx+80,144),(cx+118,200),(cx+112,300),(cx+72,366),(cx-72,366)]
        p.poly(pts,P)
        if not n:
            if e: p.poly([(330,226),(400,230),(400,266),(338,266)],(34,38,42)); p.dc.line([(340,246),(394,248)],fill=acc+(255,),width=4)
            else:
                p.rect((cx-96,222,cx+96,262),(34,38,42),r=6,edge=3); p.dc.line([(cx-84,242),(cx+84,242)],fill=acc+(255,),width=4)
                p.rect((cx-58,318,cx+58,352),S,r=6,edge=3)
                for i in range(6): p.dc.line([(cx-46+i*18,324),(cx-46+i*18,346)],fill=LINE+(255,),width=3)
            for xx in ((cx-100,cx+100) if not e else (150,)): p.rivet(xx,206,5); p.rivet(xx,296,5)
        else:
            p.rect((cx-70,180,cx+70,300),S,r=10,edge=3)
            for i in range(4): p.dc.line([(cx-56,200+i*22),(cx+56,200+i*22)],fill=LINE+(255,),width=3)
    return p.finish()

# ======================= ПРОТИВОГАЗ (свои цвета) =======================
def render_gasmask(view):
    p=Painter()
    if view=='south':
        p.ellipse([178,198,334,356],RUBBER,edge=4)
        for x in (220,292):
            p.ellipse([x-30,228,x+30,284],STEEL,edge=3); p.ellipse([x-22,236,x+22,276],GLASS,edge=3)
            p.dc.arc([x-16,240,x+12,270],200,250,fill=(220,235,240,200),width=4)
        p.ellipse([228,300,284,356],DARK,edge=3)
        for i in range(4): p.dc.line([(238,312+i*10),(274,312+i*10)],fill=(30,30,30,255),width=3)
        p.rect((300,300,352,346),OLIVE,r=10,edge=3)                                        # фильтр сбоку
        for i in range(3): p.dc.line([(306,310+i*12),(346,310+i*12)],fill=(70,76,52,255),width=3)
        for (a,b) in (((186,234),(146,224)),((326,234),(366,224))): p.line([a,b],(48,48,46),8)
    elif view=='east':
        p.poly([(268,204),(330,214),(342,300),(306,336),(266,320)],RUBBER,edge=4)
        p.ellipse([298,232,344,282],STEEL,edge=3); p.ellipse([306,240,336,274],GLASS,edge=3)
        p.rect((314,300,372,348),OLIVE,r=10,edge=3)
        for i in range(3): p.dc.line([(320,310+i*12),(366,310+i*12)],fill=(70,76,52,255),width=3)
        p.line([(272,240),(150,230)],(48,48,46),8)
    else:
        for y in (220,262,300): p.line([(160,y),(352,y)],(48,48,46),9)
        p.line([(256,206),(256,312)],(48,48,46),9); p.rect((240,250,272,274),METAL,r=3,edge=2)
    c,_=p.finish(); return c

# ======================= РЮКЗАКИ: рисунок из suit_art2 на новом "художнике" =======================
import suit_art2 as _a2
_a2.Painter=Painter
_a2.METAL=METAL; _a2.DARK=DARK; _a2.RUBBER=RUBBER; _a2.LIGHT=LIGHT
def render_pack(style, body, view, seed=0):
    return _a2.render_pack(style, body, view, seed)
