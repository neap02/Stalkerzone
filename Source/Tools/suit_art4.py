# Рисовальщик снаряжения Зоны, стиль 4 ("реалистичный"):
# - цвета и камуфляж запечены в текстуру (без маски);
# - толстая чёрная обводка только снаружи; внутри — тональные линии (тёмный оттенок своего цвета);
# - мягкий объём: свет сверху, затемнение у краёв, тени под деталями;
# - стропа MOLLE рядами, пластиковые пряжки, лямки, липучки, швы, клапаны;
# - шлемы стройные, по голове, лицо открыто.
# Камуфляжи — свои обобщённые (лес, цифра, полосы, город). Посадка — мерки suit_art.Fit.
import math, random
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFilter
from suit_art import Fit, N, OUT

INK=(16,14,12)
BUCKLE=(176,178,170); METAL=(150,152,150); GUN=(70,73,76); RUBBER=(48,48,44); GLASS=(70,96,110)
YY=np.arange(N,dtype=np.float32)[:,None]

def _noise(seed,scale,blur):
    rng=np.random.default_rng(seed); a=rng.random((N//scale+2,N//scale+2)).astype(np.float32)
    im=Image.fromarray((a*255).astype(np.uint8)).resize((N,N),Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    return np.array(im,np.float32)/255

def camo(kind,pal,seed=0):
    """Камуфляж N×N×3 (свои обобщённые узоры)."""
    pal=[np.array(c,np.float32) for c in pal]; out=np.broadcast_to(pal[0],(N,N,3)).copy()
    if kind=='solid':
        pass
    elif kind=='woodland':
        for i,c in enumerate(pal[1:]):
            n=_noise(seed+i*11,28-i*4,6); thr=0.56+i*0.03; out[n>thr]=c
    elif kind=='digital':
        for i,c in enumerate(pal[1:]):
            n=_noise(seed+i*13,24,4); blk=np.array(Image.fromarray((n*255).astype(np.uint8)).resize((N//10,N//10),Image.NEAREST).resize((N,N),Image.NEAREST),np.float32)/255
            out[blk>0.55+i*0.04]=c
    elif kind=='flora':
        x=np.arange(N,dtype=np.float32)[None,:]
        for i,c in enumerate(pal[1:]):
            n=_noise(seed+i*7,40,8)
            band=np.sin((x+n*90+i*37)/(14+i*3)); out[(band>0.55)&(n>0.35)]=c
    elif kind=='urban':
        for i,c in enumerate(pal[1:]):
            n=_noise(seed+i*5,20,3); out[(n>0.58+i*0.04)]=c
    fine=np.random.default_rng(seed+99).normal(0,4,(N,N,1)).astype(np.float32)
    return np.clip(out+fine,0,255)

class Canvas:
    def __init__(s):
        s.rgb=np.zeros((N,N,3),np.float32); s.a=np.zeros((N,N),bool); s.post=[]
    def wire(s,pts,color,w=4):
        """Тонкий элемент (ремешок, антенна, шнурок): рисуется поверх обводки, без своей толстой обводки."""
        s.post.append(('line',pts,color,w))
    def wire_dot(s,x,y,r,color): s.post.append(('dot',(x,y,r),color,0))
    @staticmethod
    def M(fn):
        im=Image.new('L',(N,N),0); fn(ImageDraw.Draw(im)); return np.array(im)>127
    def shape(s,m,fill,shade=0.16,edge=2.5,drop=True,dark=0.55,soft=True):
        """fill: (r,g,b) или массив N×N×3. Тень под деталью, объём, тональный край."""
        if m is None or not m.any(): return
        if drop:
            sh=np.array(Image.fromarray((np.roll(np.roll(m,5,0),3,1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)),np.float32)/255
            sh=sh*(s.a & ~m); s.rgb*=(1-0.45*sh)[:,:,None]
        col=np.broadcast_to(np.array(fill,np.float32),(N,N,3)) if not isinstance(fill,np.ndarray) else fill
        ys=np.where(m.any(1))[0]; y0,y1=ys[0],ys[-1]+1
        g=1.05-shade*np.clip((YY-y0)/max(1,y1-y0),0,1)
        d=ndimage.distance_transform_edt(m)
        rim=1-0.16*np.exp(-d/7.0) if soft else 1
        c=col*(g*rim)[:,:,None] if soft else col*g[:,:,None]
        s.rgb[m]=c[m]; s.a|=m
        if edge:
            e=(d>0)&(d<=edge); s.rgb[e]=col[e]*dark
    def rect(s,b,fill,r=8,**k):
        x0,y0,x1,y1=b; b=[min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)]
        s.shape(s.M(lambda d: d.rounded_rectangle(b,radius=r,fill=255)),fill,**k)
    def ell(s,b,fill,**k): s.shape(s.M(lambda d: d.ellipse(b,fill=255)),fill,**k)
    def poly(s,pts,fill,**k): s.shape(s.M(lambda d: d.polygon(pts,fill=255)),fill,**k)
    def line(s,pts,color,w=3,alpha=1.0):
        m=s.M(lambda d: d.line(pts,fill=255,width=w,joint='curve'))
        s.rgb[m]=s.rgb[m]*(1-alpha)+np.array(color,np.float32)*alpha
    def strap(s,pts,color,w=16):
        s.shape(s.M(lambda d: d.line(pts,fill=255,width=w,joint='curve')),color,shade=0.05,edge=2)
    def stitch(s,a,b,color,dash=7,gap=5):
        (xa,ya),(xb,yb)=a,b; L=math.hypot(xb-xa,yb-ya); n=int(L//(dash+gap))
        for i in range(n+1):
            t0=i*(dash+gap)/max(L,1); t1=min(1,(i*(dash+gap)+dash)/max(L,1))
            s.line([(xa+(xb-xa)*t0,ya+(yb-ya)*t0),(xa+(xb-xa)*t1,ya+(yb-ya)*t1)],color,2,0.6)
    def molle(s,b,base):
        x0,y0,x1,y1=b; web=tuple(v*0.70 for v in base); gap=tuple(v*0.92 for v in base)
        y=y0+4
        while y+9<=y1:
            s.rect((x0,y,x1,y+9),web,r=1,shade=0.0,edge=1.2,drop=False,soft=False)
            for x in np.arange(x0+18,x1-6,20): s.line([(x,y),(x,y+9)],gap,2,0.9)
            y+=16
    def buckle(s,x,y,horiz=True):
        if horiz:
            s.rect((x-16,y-9,x+16,y+9),BUCKLE,r=3,shade=0.1,edge=2)
            for xx in (x-8,x+6): s.rect((xx-2,y-6,xx+2,y+6),(90,92,88),r=1,shade=0,edge=0,drop=False)
        else:
            s.rect((x-9,y-16,x+9,y+16),BUCKLE,r=3,shade=0.1,edge=2)
            for yy in (y-8,y+6): s.rect((x-6,yy-2,x+6,yy+2),(90,92,88),r=1,shade=0,edge=0,drop=False)
    def velcro(s,b,base):
        s.rect(b,tuple(v*0.86 for v in base),r=3,shade=0.02,edge=1.5)
        x0,y0,x1,y1=b
        for x in range(int(x0)+3,int(x1)-2,4): s.line([(x,y0+3),(x,y1-3)],tuple(v*0.78 for v in base),1,0.5)
    def pouch(s,b,base,mag=False,buckle=True):
        x0,y0,x1,y1=b; h=y1-y0
        if mag: s.rect((x0+6,y0-16,x1-6,y0+6),(52,50,46),r=3,shade=0.1,edge=1.5)    # торцы магазинов
        s.rect(b,base,r=5)
        s.rect((x0-1,y0-2,x1+1,y0+h*0.36),tuple(v*0.9 for v in base),r=5,shade=0.05)
        if buckle: s.buckle((x0+x1)/2,y0+h*0.36,horiz=False) if h>50 else s.rect(((x0+x1)/2-6,y0+h*0.3,(x0+x1)/2+6,y0+h*0.42),BUCKLE,r=2,edge=1)
        s.stitch((x0+5,y1-5),(x1-5,y1-5),tuple(v*0.6 for v in base))
    def finish(s,clip=None,out=OUT):
        a=s.a if clip is None else (s.a & clip)
        d=ndimage.distance_transform_edt(a); ring=(d>0)&(d<=out)
        o=np.zeros((N,N,4),np.uint8); o[:,:,:3]=np.clip(s.rgb,0,255).astype(np.uint8)
        o[ring,:3]=INK; o[:,:,3]=np.where(a,255,0)
        im=Image.fromarray(o,'RGBA')
        if s.post:
            dr=ImageDraw.Draw(im)
            for kind,pts,color,w in s.post:
                if kind=='line':
                    dr.line(pts,fill=INK+(255,),width=w+4,joint='curve'); dr.line(pts,fill=tuple(int(v) for v in color)+(255,),width=w,joint='curve')
                else:
                    x,y,r=pts; dr.ellipse([x-r-2,y-r-2,x+r+2,y+r+2],fill=INK+(255,)); dr.ellipse([x-r,y-r,x+r,y+r],fill=tuple(int(v) for v in color)+(255,))
        return im

def sh(c,k): return tuple(min(255,v*k) for v in c)

# ======================= КОМБИНЕЗОН =======================
# look: камуфляж/палитра, снаряжение, цвет снаряжения, акцент
def render_coverall(cls, look, body, view, seed=0):
    kind,pal,gear,acc=look
    fit=Fit(body,view); c=Canvas(); side=view=='east'; back=view=='north'
    at=fit.at; rng=random.Random(seed)
    def X(cx,w,dx): return cx+(w*0.16 if side else 0)+dx*w*(0.55 if side else 1.0)
    base=pal[0]; dk=sh(base,0.62)
    bodym=Canvas.M(lambda d: d.polygon(fit.polygon(),fill=255))
    c.shape(bodym,camo(kind,pal,seed),shade=0.22,edge=0,drop=False)
    yT,lT,rT,cT,wT=at(0.0); yW,lW,rW,cW,wW=at(0.57); yb=at(0.935)[0]; yE=at(1.0)[0]
    # ботинки
    c.rect((0,yb,N,yE+30),(54,46,38),r=0,shade=0.25,edge=0,drop=False)
    c.line([(0,yb),(N,yb)],(30,26,22),3); c.line([(0,yE-14),(N,yE-14)],(36,34,30),4)
    for xx in np.arange(fit.at(0.97)[1]+10,fit.at(0.97)[2]-6,14): c.line([(xx,yb+6),(xx+6,yb+18)],(80,70,58),2,0.8)  # шнуровка
    # швы и складки
    if not side: c.line([(at(0.80)[3],at(0.80)[0]),(at(0.93)[3],yb)],dk,3)
    for t in (0.30,0.46,0.78):
        y,l,r,cx,w=at(t); c.line([(l+12,y),(l+40,y+6)],dk,2,0.5); c.line([(r-12,y),(r-40,y+6)],dk,2,0.5)
    c.stitch((lT+14,yT+40),(at(0.55)[1]+10,at(0.55)[0]),dk); c.stitch((rT-14,yT+40),(at(0.55)[2]-10,at(0.55)[0]),dk)
    # пояс
    c.rect((lW+4,yW,rW-4,yW+18),(46,44,38),r=3,shade=0.05,edge=1.5)
    if not back: c.buckle(X(cW,wW,0),yW+9)
    # ноги: карманы, наколенники, щитки
    yC,lC,rC,cC,wC=at(0.72); yK,lK,rK,cK,wK=at(0.865)
    dxs=(-0.26,0.26) if not side else (0.08,)
    for dx in dxs:
        if cls in ('light','medium','cloak','heavy','exo') and not back:
            c.pouch((X(cC,wC,dx)-28,yC-16,X(cC,wC,dx)+28,yC+38),sh(base,0.95),buckle=False)
        if cls in ('medium','heavy'):
            x=X(cK,wK,dx); c.rect((x-27,yK-22,x+27,yK+20),sh(gear,0.85),r=12); c.rect((x-16,yK-12,x+16,yK+10),sh(gear,0.7),r=8,shade=0.05,edge=1.5)
        if cls in ('heavy','exo'):
            plate=GUN if cls=='exo' else sh(gear,0.9)
            c.rect((X(cC,wC,dx)-30,yC-24,X(cC,wC,dx)+30,yC+34),plate,r=7)
            if cls=='exo': c.ell([X(cK,wK,dx)-26,yK-22,X(cK,wK,dx)+26,yK+22],GUN)
    if cls=='science':
        for t in (0.84,):
            y,l,r,cx,w=at(t); c.rect((l+6,y,r-6,y+12),(214,214,200),r=2,shade=0,edge=1.5)
    # ---------- верх ----------
    if cls=='cloak':                                                  # маскхалат: бахрома
        for _ in range(260):
            t=rng.uniform(0.0,0.62); y,l,r,cx,w=at(t); x=rng.uniform(l,r)
            col=pal[rng.randrange(len(pal))]
            c.line([(x,y),(x+rng.uniform(-6,6),y+rng.uniform(12,26))],sh(col,rng.uniform(0.8,1.1)),3,0.9)
    if back:
        y0,l0,r0,c0,w0=at(0.07); y1=at(0.54)[0]
        if cls in ('medium','heavy'):
            c.rect((c0-w0*0.37,y0,c0+w0*0.37,y1),gear,r=10); c.molle((c0-w0*0.33,y0+46,c0+w0*0.33,y1-8),gear)
            c.rect((c0-26,y0+8,c0+26,y0+26),sh(gear,0.7),r=6)
        elif cls=='light':
            for a,b in (((lT+30,yT),(cT+wT*0.2,at(0.5)[0])),((rT-30,yT),(cT-wT*0.2,at(0.5)[0]))): c.strap([a,b],sh(gear,0.9),14)
        elif cls=='exo':
            for i in range(3):
                yy=y0+i*(y1-y0)/3; c.rect((c0-w0*0.37,yy,c0+w0*0.37,yy+(y1-y0)/3-6),GUN,r=8)
                for xx in (c0-w0*0.31,c0+w0*0.31): c.ell([xx-4,yy+8,xx+4,yy+16],METAL,edge=1)
        elif cls=='science':
            c.rect((c0-w0*0.3,y0+10,c0+w0*0.3,y0+40),sh(base,0.8),r=6)
        if cls in ('light','medium','cloak','bandit'):
            c.ell([c0-w0*0.3,y0-40,c0+w0*0.3,y0+20],sh(base,0.92),edge=2)      # капюшон сзади
    else:
        if cls!='science': c.rect((X(cT,wT,-0.34),yT-4,X(cT,wT,0.34),yT+22),sh(base,0.86),r=10,edge=2)   # воротник
        else: c.rect((X(cT,wT,-0.36),yT-6,X(cT,wT,0.36),yT+18),(150,152,148),r=8,edge=2)
        if cls=='light':                                               # нагрудник-разгрузка
            for dx in ((-0.24,0.24) if not side else (0.14,)):
                y,l,r,cx,w=at(0.0); c.strap([(X(cx,w,dx),y),(X(cx,w,dx*0.9),at(0.36)[0])],sh(gear,0.9),14)
            y,l,r,cx,w=at(0.36); n=3 if not side else 2; pw=w*(0.62 if not side else 0.32)/n
            for i in range(n):
                x=X(cx,w,-0.31 if not side else 0.02)+i*pw
                c.pouch((x+3,y,x+pw-3,y+58),gear,mag=True)
            if not side: c.velcro((cT+wT*0.12,at(0.12)[0],cT+wT*0.34,at(0.12)[0]+18),base)
        elif cls in ('medium','heavy'):
            heavy=cls=='heavy'
            for dx in ((-0.26,0.26) if not side else (0.20,)):
                y,l,r,cx,w=at(0.0); c.strap([(X(cx,w,dx),y-2),(X(cx,w,dx*0.96),at(0.12)[0])],sh(gear,0.95),22)
            if heavy and not side:                                     # мягкие наплечники
                y,l,r,cx,w=at(0.05)
                for dx in (-1,1): c.ell([cx+dx*w*0.45-36,y-16,cx+dx*w*0.45+36,y+40],sh(gear,0.9))
                c.rect((cT-wT*0.30,yT-12,cT+wT*0.30,yT+22),sh(gear,0.85),r=12)       # защита горла
            y,l,r,cx,w=at(0.08); y2=at(0.41)[0]; k=0.36 if not heavy else 0.42
            c.rect((X(cx,w,-k),y,X(cx,w,k),y2),gear,r=12)                          # плита
            c.molle((X(cx,w,-k)+8,y+50,X(cx,w,k)-8,y2-6),gear)
            if not side: c.velcro((X(cx,w,-0.22),y+12,X(cx,w,0.22),y+38),gear)
            y3,l3,r3,c3,w3=at(0.41); y4=at(0.56)[0]
            c.rect((X(c3,w3,-0.48),y3-4,X(c3,w3,0.48),y4),sh(gear,0.92),r=6)             # камербанд
            c.molle((X(c3,w3,-0.46),y3,X(c3,w3,0.46),y4-2),sh(gear,0.92))
            n=3 if not heavy else 4; span=0.64 if not heavy else 0.74
            if side: n,span=2,0.5
            pw=w3*span*(0.55 if side else 1)/n
            for i in range(n):
                x=X(c3,w3,-span/2)+i*pw if not side else X(c3,w3,0.0)+i*pw
                c.pouch((x+3,y3-30,x+pw-3,y3+30),sh(gear,0.96),mag=True)
            if heavy and not side:
                c.rect((X(c3,w3,-0.17),y4,X(c3,w3,0.17),at(0.66)[0]),sh(gear,0.9),r=8)    # пах
            if not side:                                                                  # рация
                y,l,r,cx,w=at(0.12); c.rect((cx+w*0.30,y,cx+w*0.42,y+54),(44,46,44),r=4); c.wire([(cx+w*0.39,y),(cx+w*0.40,y-34)],(30,30,30),4)
        elif cls=='science':
            y,l,r,cx,w=at(0.48); c.rect((l+6,y,r-6,y+12),(214,214,200),r=2,shade=0,edge=1.5)
            for dx in ((-0.43,0.43) if not side else (0.30,)):
                y,l,r,cx,w=at(0.02); c.rect((X(cx,w,dx)-7,y+12,X(cx,w,dx)+7,yb),sh(base,0.72),r=3,shade=0.1)
            if not side:
                y,l,r,cx,w=at(0.12)
                c.rect((cx-50,y,cx+50,y+80),(56,58,58),r=6)
                c.rect((cx-38,y+10,cx+38,y+38),(64,120,92),r=3,shade=0.05,edge=1.5)
                for i in range(3): c.line([(cx-32,y+16+i*7),(cx-32+rng.randint(20,60),y+16+i*7)],(160,230,180),2)
                for i,cc in enumerate([(200,70,60),(220,180,60),(110,200,120)]): c.ell([cx-30+i*26-5,y+52,cx-30+i*26+5,y+62],cc,edge=1,drop=False)
            y0=at(0.06)[0]; c.strap([(X(cT,wT,-0.40),y0+6),(X(cT,wT,-0.36),y0+60),(X(cT,wT,-0.24),y0+96)],RUBBER,12)
        elif cls=='exo':
            y,l,r,cx,w=at(0.06); y2=at(0.38)[0]
            c.rect((X(cx,w,-0.37),y,X(cx,w,0.37),y2),GUN,r=12)
            c.line([(X(cx,w,-0.3),y+(y2-y)*0.5),(X(cx,w,0.3),y+(y2-y)*0.5)],(48,50,52),3)
            for xx in (X(cx,w,-0.31),X(cx,w,0.31)):
                for yy in (y+14,y2-14): c.ell([xx-4,yy-4,xx+4,yy+4],METAL,edge=1,drop=False)
            for i in range(3):
                yy,l2,r2,c2,w2=at(0.40+i*0.055); c.rect((X(c2,w2,-0.33),yy,X(c2,w2,0.33),yy+24),sh(GUN,1.06-i*0.05),r=5)
            if not side:
                yS,lS,rS,cS,wS=at(0.04)
                for dx in (-1,1): c.ell([cS+dx*wS*0.45-34,yS-20,cS+dx*wS*0.45+34,yS+30],GUN)
        elif cls=='bandit':                                             # кожанка поверх
            y,l,r,cx,w=at(0.0)
            if not side: c.line([(cx-6,y+20),(cx-14,at(0.56)[0])],(26,24,22),4)
        if not side and cls not in ('cloak',):                          # нашивка
            y,l,r,cx,w=at(0.16); x=cx-w*0.42; c.rect((x-16,y,x+16,y+24),acc,r=3,shade=0.05,edge=1.5)
        if side and cls in ('medium','heavy'):
            y0,l0,r0,c0,w0=at(0.08); c.rect((l0+6,y0+10,l0+w0*0.2,at(0.5)[0]),gear,r=8)
    return c.finish(bodym)

# ======================= ЭКЗОСКЕЛЕТ =======================
def render_exo(kind, body, view, seed=0):
    fit=Fit(body,view); c=Canvas(); side=view=='east'; back=view=='north'; at=fit.at
    heavy=kind=='assault'; frame=(84,88,92) if not heavy else (66,70,74)
    def X(cx,w,dx,k=0.92): return cx+(w*0.12 if side else 0)+dx*w*(0.55 if side else k)
    def strut(pts,w):
        c.strap(pts,frame,w+8); c.line(pts,sh(frame,1.45),max(3,w//4),0.8)
    def joint(x,y,r):
        c.ell([x-r,y-r,x+r,y+r],(44,46,48)); c.ell([x-r*0.45,y-r*0.45,x+r*0.45,y+r*0.45],METAL,edge=1.5)
    def piston(a,b):
        c.strap([a,b],(60,62,64),10); m=((a[0]+b[0])/2,(a[1]+b[1])/2); c.line([m,b],(205,208,205),5)
    yH,lH,rH,cH,wH=at(0.58)
    if not back:
        c.rect((lH+2,yH-6,rH-2,yH+22),(52,54,56),r=5)
        c.rect((X(cH,wH,0)-22,yH-10,X(cH,wH,0)+22,yH+26),frame,r=4)
    for dx in ((-0.44,0.44) if not side else (0.10,)):
        pts=[(X(cx,w,dx),y) for (y,_,_,cx,w) in (at(0.58),at(0.85),at(0.985))]
        strut(pts,18 if heavy else 14); joint(*pts[0],19); joint(*pts[1],17)
        off=10 if dx>0 else -10; piston((pts[0][0]+off,pts[0][1]+22),(pts[1][0]+off,pts[1][1]-24))
        c.rect((pts[2][0]-26,pts[2][1]-8,pts[2][0]+26,pts[2][1]+10),(46,48,50),r=4)
    for dx in ((-0.48,0.48) if not side else (0.30,)):
        pts=[(X(cx,w,dx,1.0),y) for (y,_,_,cx,w) in (at(0.03),at(0.30),at(0.56))]
        strut(pts,13 if heavy else 11); joint(*pts[0],17)
    if back or side:
        y0,l0,r0,c0,w0=at(0.08); y1=at(0.50)[0]
        box=(c0-w0*0.31,y0,c0+w0*0.31,y1) if back else (l0-w0*0.22,y0+6,l0+w0*0.20,y1)
        x0,yy0,x1,yy1=box; c.rect(box,(58,62,64),r=10)
        c.rect((x0+12,yy0+12,x1-12,yy0+52),(34,36,38),r=4)
        if back:
            c.rect((x0+20,yy0+18,x0+(x1-x0)*0.55,yy0+46),(54,110,84),r=3,shade=0.05,edge=1.5)
            for i,cc in enumerate([(110,200,120),(220,180,60),(200,70,60)]): c.ell([x1-30,yy0+18+i*10,x1-22,yy0+26+i*10],cc,edge=1,drop=False)
        for i in range(5): c.line([(x0+14,yy0+68+i*12),(x1-14,yy0+68+i*12)],(36,38,40),3)
        yw=yy1-28
        for i in range(int((x1-x0-20)//16)):
            xs=x0+10+i*16; c.poly([(xs,yw),(xs+8,yw),(xs+16,yw+16),(xs+8,yw+16)],(206,170,52) if i%2==0 else (32,32,32),edge=0,drop=False,soft=False,shade=0)
        if back:
            c.strap([(c0,yy1),(c0,yH)],frame,14)
            for dx in (-0.22,0.22): c.strap([(c0+dx*w0,yy1),(c0+dx*w0*1.6,yH)],(40,40,40),7)
    return c.finish(out=8)

# ======================= ШЛЕМЫ (стройные, по голове) =======================
def render_helmet(style, look, view, seed=0):
    kind,pal,gear,acc=look; c=Canvas(); e=view=='east'; n=view=='north'
    cx=256 if not e else 250
    cover=camo(kind,pal,seed+5) if style in ('combat','psi','visor','hood','cap') else None
    if style=='cap':                                                     # вязаная шапка
        m=Canvas.M(lambda d: d.ellipse([cx-98,150,cx+98,330] if not e else [150,150,350,330],fill=255)) & (YY<246)
        c.shape(m,sh(pal[0],0.9),edge=2)
        c.rect((cx-102 if not e else 146,214,cx+102 if not e else 354,248),sh(pal[0],0.78),r=8)
        for x in range(cx-96 if not e else 150,cx+96 if not e else 350,7): c.line([(x,218),(x,244)],sh(pal[0],0.62),2,0.6)
    elif style=='hood':
        box=[cx-118,132,cx+118,370] if not e else [118,132,368,366]
        m=Canvas.M(lambda d: d.ellipse(box,fill=255))
        if not n: m&=~Canvas.M(lambda d: d.ellipse([cx-76,212,cx+76,350] if not e else [262,206,420,352],fill=255))
        c.shape(m,cover,edge=2)
        if not n and not e:
            for dx in (-58,58): c.wire([(cx+dx,332),(cx+dx*1.05,384)],(60,58,52),3); c.wire_dot(cx+dx*1.05,386,5,BUCKLE)
    elif style in ('combat','psi'):
        box=[cx-112,132,cx+112,380] if not e else [116,132,380,380]
        m=Canvas.M(lambda d: d.ellipse(box,fill=255)) & (YY<262)
        if not n:
            cut=Canvas.M(lambda d: (d.rectangle([cx-116,226,cx-86,262],fill=255),d.rectangle([cx+86,226,cx+116,262],fill=255))) if not e else Canvas.M(lambda d: d.rectangle([200,228,240,262],fill=255))
            m&=~cut
        c.shape(m,cover,edge=2.5)
        for xx in ((cx-112,cx+92) if not e else (156,)):                            # боковые рельсы
            c.rect((xx,188,xx+20,224),sh(gear,0.75),r=3); [c.ell([xx+6,y,xx+14,y+8],(40,40,40),edge=0,drop=False) for y in (194,208)]
        c.velcro((cx-44 if not e else 176,150,cx+44 if not e else 246,170),pal[0])
        if not n:
            c.rect((cx-20 if not e else 318,150,cx+20 if not e else 348,182),(54,56,54),r=4)   # крепление прибора
            if not e: c.rect((cx-12,182,cx+12,196),(44,46,44),r=2)
        for side_x in ((cx-100,cx+100) if not e else (230,)):                               # подбородочный ремень
            if not n: c.wire([(side_x,250),(side_x+(20 if side_x<cx else -20),330),(cx,350)] if not e else [(side_x,250),(300,340)],(96,70,46),4)
        if style=='psi':
            for i in range(2):
                m2=Canvas.M(lambda d: d.arc([cx-104+i*8,140+i*8,cx+104-i*8,330-i*8] if not e else [124+i*8,140+i*8,372-i*8,330-i*8],200,340,fill=255,width=5))
                c.shape(m2,(176,112,56),edge=0,drop=False,shade=0)
            ax=cx+64 if not e else 196; c.wire([(ax,150),(ax+16,100)],(70,72,74),5); c.wire_dot(ax+17,98,7,acc)
    elif style=='visor':
        box=[cx-114,130,cx+114,382] if not e else [114,130,382,382]
        m=Canvas.M(lambda d: d.ellipse(box,fill=255)) & (YY<264)
        c.shape(m,cover,edge=2.5)
        if not n:
            fb=(cx-92,206,cx+92,236) if not e else (300,204,392,236)                          # поднятое забрало
            c.rect(fb,(38,44,50),r=8); c.line([(fb[0]+10,fb[1]+8),(fb[2]-40,fb[1]+8)],(120,140,150),2,0.7)
            for xx in ((cx-104,cx+104) if not e else (226,)): c.ell([xx-9,214,xx+9,232],METAL,edge=1.5)
        c.rect((cx-114 if not e else 114,246,cx+114 if not e else 382,264),sh(gear,0.85),r=5)
    elif style=='sealed':                                                 # капюшон-респиратор
        box=[cx-120,130,cx+120,372] if not e else [126,130,374,372]
        c.ell(box,(222,140,52) if pal[0][0]>180 and pal[0][1]<160 else sh(pal[0],1.0),edge=2.5)
        if not n:
            fb=[cx-80,192,cx+80,318] if not e else [296,188,392,312]
            c.rect(fb,(46,52,58),r=30); c.rect((fb[0]+8,fb[1]+8,fb[2]-8,fb[3]-8),GLASS,r=24,shade=0.3)
            c.line([(fb[0]+20,fb[1]+20),(fb[0]+60,fb[1]+14)],(200,220,228),4,0.7)
            c.rect((cx-22 if not e else 360,318,cx+22 if not e else 400,352),(80,86,70),r=8)   # фильтр
        c.rect((cx-116 if not e else 132,342,cx+116 if not e else 368,372),(120,122,118),r=8)
    elif style=='exo':
        pts=[(cx-104,292),(cx-110,198),(cx-74,140),(cx+74,140),(cx+110,198),(cx+104,292),(cx+66,356),(cx-66,356)] if not e else \
            [(126,292),(132,198),(178,140),(316,140),(372,194),(388,284),(346,356),(172,356)]
        c.poly(pts,GUN,edge=2.5)
        if not n:
            if e: c.poly([(330,222),(394,226),(394,258),(336,258)],(28,32,36)); c.line([(340,240),(390,242)],acc,3)
            else:
                c.rect((cx-90,218,cx+90,254),(28,32,36),r=5); c.line([(cx-80,236),(cx+80,236)],acc,3)
                c.rect((cx-52,314,cx+52,344),(52,54,56),r=5)
                for i in range(6): c.line([(cx-42+i*17,320),(cx-42+i*17,338)],(30,30,30),3)
        else:
            c.rect((cx-66,178,cx+66,296),(60,64,66),r=8)
            for i in range(4): c.line([(cx-54,198+i*22),(cx+54,198+i*22)],(40,42,44),3)
    return c.finish()

# ======================= ПРОТИВОГАЗ =======================
def render_gasmask(view):
    c=Canvas(); OL=(92,100,70)
    if view=='south':
        c.ell([180,198,332,354],RUBBER,edge=2.5)
        for x in (220,292):
            c.ell([x-30,228,x+30,284],(96,98,96),edge=2); c.ell([x-22,236,x+22,276],GLASS,shade=0.3)
            c.line([(x-12,244),(x+2,240)],(200,220,228),3,0.7)
        c.ell([230,300,282,352],(40,40,38))
        for i in range(4): c.line([(240,312+i*10),(272,312+i*10)],(26,26,24),3)
        c.rect((300,302,354,348),OL,r=10)
        for i in range(3): c.line([(306,312+i*12),(348,312+i*12)],sh(OL,0.7),3)
        for a,b in (((186,234),(146,224)),((326,234),(366,224))): c.wire([a,b],(44,44,40),7)
    elif view=='east':
        c.poly([(268,204),(330,214),(342,300),(306,336),(266,320)],RUBBER,edge=2.5)
        c.ell([298,232,344,282],(96,98,96),edge=2); c.ell([306,240,336,274],GLASS,shade=0.3)
        c.rect((314,300,372,348),OL,r=10)
        for i in range(3): c.line([(320,310+i*12),(366,310+i*12)],sh(OL,0.7),3)
        c.wire([(272,240),(150,230)],(44,44,40),7)
    else:
        for y in (220,262,300): c.strap([(160,y),(352,y)],(52,52,48),9)
        c.strap([(256,206),(256,312)],(52,52,48),9); c.rect((240,250,272,274),METAL,r=3)
    return c.finish()

# ======================= РЮКЗАКИ И БАЛЛОНЫ =======================
def render_pack(style, look, body, view, seed=0):
    kind,pal,gear,acc=look
    fit=Fit(body,view); c=Canvas(); at=fit.at
    big={'frame':1.25,'raid':1.1,'lead':1.0,'closed':1.05,'cooling':1.0,'tourist':1.0,'medic':0.85,'sack':0.9,'tank1':0.9,'tank2':1.0}[style]
    yA,lA,rA,cA,wA=at(0.10); yB=at(min(0.72,0.56*big+0.06))[0]
    fab=camo(kind,pal,seed+3)
    tanky=style in ('tank1','tank2','closed','cooling')
    def tank(x,y0,y1,r,col):
        c.rect((x-r,y0,x+r,y1),col,r=int(r),shade=0.3); c.line([(x-r*0.45,y0+r),(x-r*0.45,y1-r)],(255,255,255),max(3,int(r*0.18)),0.35)
        c.rect((x-r*0.45,y0-20,x+r*0.45,y0+6),METAL,r=4); c.ell([x-r*0.6,y0-34,x+r*0.6,y0-14],sh(METAL,0.9))
    def pack(box):
        x0,y0,x1,y1=box; w=x1-x0; h=y1-y0; cx=(x0+x1)/2
        if style=='sack':
            c.ell([x0,y0+h*0.15,x1,y1],fab); c.poly([(cx-w*0.18,y0+h*0.22),(cx+w*0.18,y0+h*0.22),(cx+w*0.08,y0),(cx-w*0.08,y0)],fab)
            c.line([(cx-w*0.17,y0+h*0.22),(cx+w*0.17,y0+h*0.22)],(60,52,40),5)
        elif style in ('tourist','raid','frame','medic'):
            if style=='frame':
                for x in (x0+6,x1-6): c.strap([(x,y0-32),(x,y1+14)],(110,112,110),10)
            c.rect((x0,y0,x1,y1),fab,r=24)
            c.rect((cx-34,y0-16,cx+34,y0+6),sh(gear,0.75),r=8)                          # ручка
            c.molle((x0+14,y0+h*0.42,x1-14,y1-14),pal[0])
            c.velcro((cx-34,y0+h*0.12,cx+34,y0+h*0.12+22),pal[0])
            for yy in (y0+h*0.3,y0+h*0.72):                                              # стяжки
                for xx in (x0-4,x1+4): c.rect((xx-10,yy-12,xx+10,yy+12),sh(gear,0.85),r=3); c.buckle(xx,yy,horiz=False)
            if style=='medic':
                c.rect((cx-12,y0+h*0.48,cx+12,y0+h*0.82),(214,214,206),r=2,edge=1.5,drop=False); c.rect((cx-34,y0+h*0.58,cx+34,y0+h*0.72),(214,214,206),r=2,edge=1.5,drop=False)
            if style in ('raid','frame'):
                yb=y0-38 if style=='raid' else y1-12
                c.rect((x0-14,yb,x1+14,yb+42),sh(gear,0.9),r=20)
                for x in (x0+18,x1-18): c.strap([(x,yb-2),(x,yb+44)],(40,38,34),7)
        elif style=='lead':
            c.rect((x0,y0,x1,y1),(120,124,126),r=10)
            for i in range(1,3): c.line([(x0+10,y0+i*h/3),(x1-10,y0+i*h/3)],(80,84,86),3)
            for xx in (x0+12,x1-12):
                for yy in (y0+12,y1-12): c.ell([xx-4,yy-4,xx+4,yy+4],METAL,edge=1,drop=False)
            r=min(w,h)*0.17; cy=y0+h*0.5; c.ell([cx-r,cy-r,cx+r,cy+r],(214,174,44),edge=1.5)
            for a0 in (60,180,300):
                m=Canvas.M(lambda d: d.pieslice([cx-r*0.85,cy-r*0.85,cx+r*0.85,cy+r*0.85],a0,a0+60,fill=255)); c.shape(m,(30,30,30),edge=0,drop=False,shade=0)
            c.ell([cx-r*0.2,cy-r*0.2,cx+r*0.2,cy+r*0.2],(30,30,30),edge=0,drop=False)
        elif style=='tank1': tank(cx,y0+22,y1,w*0.26,sh(pal[0],1.0))
        elif style=='tank2':
            for dx in (-0.22,0.22): tank(cx+dx*w,y0+22,y1,w*0.2,sh(pal[0],1.0))
            c.rect((cx-w*0.3,y0-8,cx+w*0.3,y0+12),METAL,r=4)
        elif style=='closed':
            c.rect((x0,y0,x1,y1),sh(pal[0],1.0),r=18)
            for dx in (-0.2,0.2): tank(cx+dx*w,y0+30,y1-16,w*0.14,sh(gear,1.0))
            for i in range(2): c.ell([cx-46+i*60,y0+6,cx-14+i*60,y0+38],(220,220,214),edge=1.5)
        elif style=='cooling':
            c.rect((x0,y0,x1,y1),(70,76,82),r=12)
            for i in range(7): c.line([(x0+18,y0+22+i*(h-44)/7),(x1-18,y0+22+i*(h-44)/7)],(44,48,52),4)
            for xx in (x0+12,x1-12): c.strap([(xx,y0+10),(xx,y1-10)],(60,130,180),8)
    if view=='north': pw=wA*0.58*min(big,1.15); pack((cA-pw/2,yA+12,cA+pw/2,yB))
    elif view=='east':
        depth=wA*0.42*big; pack((lA-depth*0.55,yA+12,lA+depth*0.45,yB))
        c.strap([(lA+depth*0.25,yA+24),(cA,yA+2),(rA-wA*0.14,at(0.38)[0])],RUBBER if tanky else sh(gear,0.9),12)
    else:
        if style=='sack': c.strap([(cA-wA*0.3,yA),(cA+wA*0.25,at(0.5)[0])],sh(gear,0.9),16)
        else:
            for dx in (-0.24,0.24): c.strap([(cA+dx*wA,yA-6),(cA+dx*wA*0.9,at(0.42)[0])],sh(gear,0.9),16)
            yc=at(0.30)[0]; c.strap([(cA-wA*0.22,yc),(cA+wA*0.22,yc)],sh(gear,0.8),8); c.buckle(cA,yc)
            if style in ('tank1','tank2','closed'):
                pts=[(cA+wA*0.3,yA-10),(cA+wA*0.22,at(0.22)[0]),(cA+wA*0.06,at(0.18)[0])]
                c.strap(pts,RUBBER,10); c.rect((pts[-1][0]-18,pts[-1][1]-14,pts[-1][0]+18,pts[-1][1]+14),METAL,r=6)
            if style=='cooling':
                for dx in (-0.12,0.12): c.strap([(cA+dx*wA,yA),(cA+dx*wA*1.4,at(0.45)[0])],(60,130,180),7)
    return c.finish(out=10)
