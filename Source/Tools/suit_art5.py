# Рисовальщик Зоны, стиль 5: у каждого костюма свой крой и снаряжение (SPEC), у каждого шлема своя форма.
# Основа — suit_art4 (запечённый цвет, тональные линии, тени, стропа, пряжки).
# Стекло — вырез: рамка и блики видны, сквозь стекло видно лицо.
import math, random
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
from suit_art import Fit, N, OUT
import suit_art4 as A
from suit_art4 import Canvas, camo, sh, BUCKLE, METAL, GUN, RUBBER, INK, YY

class C5(Canvas):
    def __init__(s):
        super().__init__(); s.holes=np.zeros((N,N),bool)
    def glass(s,m,frame=(60,62,60),rim=7,streaks=True):
        """Прозрачное стекло: рамка + блики, внутри вырез (видно лицо)."""
        d=ndimage.distance_transform_edt(m)
        s.shape(m,frame,shade=0.1,edge=2,drop=False)
        inner=d>rim; s.holes|=inner
        if streaks:
            ys,xs=np.where(inner)
            if len(ys):
                x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max(); w=x1-x0; h=y1-y0
                s.wire([(x0+w*0.15,y0+h*0.55),(x0+w*0.42,y0+h*0.12)],(205,222,228),3)
                s.wire([(x0+w*0.30,y0+h*0.62),(x0+w*0.50,y0+h*0.30)],(205,222,228),2)
    def finish(s,clip=None,out=OUT):
        im=super().finish(clip,out)
        if s.holes.any():
            a=np.array(im); keep=a[:,:,3].copy()
            a[:,:,3]=np.where(s.holes,0,keep)
            im=Image.fromarray(a,'RGBA')
            if s.post:   # блики поверх выреза
                dr=ImageDraw.Draw(im)
                for kind,pts,color,w in s.post:
                    if kind=='line': dr.line(pts,fill=tuple(int(v) for v in color)+(255,),width=w)
        return im

M=Canvas.M
def _X(fit,side):
    def X(cx,w,dx): return cx+(w*0.16 if side else 0)+dx*w*(0.55 if side else 1.0)
    return X

# ---------------------------------------------------------------- снаряжение поверх одежды
def rig_chest(c,fit,X,side,gear):            # нагрудная разгрузка: X-ремни + ряд подсумков
    at=fit.at
    for dx in ((-0.24,0.24) if not side else (0.14,)):
        y,l,r,cx,w=at(0.0); c.strap([(X(cx,w,dx),y),(X(cx,w,dx*0.9),at(0.36)[0])],sh(gear,0.9),14)
    y,l,r,cx,w=at(0.36); n=4 if not side else 2; span=0.70 if not side else 0.34; pw=w*span/n
    for i in range(n):
        x=X(cx,w,-span/2 if not side else 0.02)+i*pw; c.pouch((x+3,y,x+pw-3,y+60),gear,mag=(i%3!=0))
    c.rect((X(cx,w,-0.36),y+56,X(cx,w,0.36),y+70),sh(gear,0.8),r=3)
def rig_vest(c,fit,X,side,gear):             # лёгкий жилет: 2 подсумка + рация
    at=fit.at; y,l,r,cx,w=at(0.06); y2=at(0.50)[0]; k=0.34
    c.rect((X(cx,w,-k),y,X(cx,w,k),y2),gear,r=10)
    c.stitch((X(cx,w,-k)+8,y+12),(X(cx,w,-k)+8,y2-10),sh(gear,0.6)); c.stitch((X(cx,w,k)-8,y+12),(X(cx,w,k)-8,y2-10),sh(gear,0.6))
    for dx in ((-0.18,0.10) if not side else (0.06,)):
        yy=at(0.30)[0]; c.pouch((X(cx,w,dx)-26,yy,X(cx,w,dx)+26,yy+50),sh(gear,0.95),buckle=False)
    if not side: c.rect((X(cx,w,0.24)-10,at(0.14)[0],X(cx,w,0.24)+10,at(0.14)[0]+40),(44,46,44),r=3); c.wire([(X(cx,w,0.24)+4,at(0.14)[0]),(X(cx,w,0.25),at(0.14)[0]-30)],(30,30,30),4)
def rig_carrier(c,fit,X,side,gear,heavy=False):
    at=fit.at
    for dx in ((-0.26,0.26) if not side else (0.20,)):
        y,l,r,cx,w=at(0.0); c.strap([(X(cx,w,dx),y-2),(X(cx,w,dx*0.96),at(0.12)[0])],sh(gear,0.95),22)
    if heavy and not side:
        c.rect((fit.at(0)[3]-fit.at(0)[4]*0.30,fit.at(0)[0]-12,fit.at(0)[3]+fit.at(0)[4]*0.30,fit.at(0)[0]+22),sh(gear,0.85),r=12)
    y,l,r,cx,w=at(0.08); y2=at(0.41)[0]; k=0.36 if not heavy else 0.42
    c.rect((X(cx,w,-k),y,X(cx,w,k),y2),gear,r=12); c.molle((X(cx,w,-k)+8,y+50,X(cx,w,k)-8,y2-6),gear)
    if not side: c.velcro((X(cx,w,-0.22),y+12,X(cx,w,0.22),y+38),gear)
    y3,l3,r3,c3,w3=at(0.41); y4=at(0.56)[0]
    c.rect((X(c3,w3,-0.48),y3-4,X(c3,w3,0.48),y4),sh(gear,0.92),r=6); c.molle((X(c3,w3,-0.46),y3,X(c3,w3,0.46),y4-2),sh(gear,0.92))
    n,span=(3,0.62) if not heavy else (4,0.74)
    if side: n,span=2,0.5
    pw=w3*span*(0.55 if side else 1)/n
    for i in range(n):
        x=X(c3,w3,-span/2)+i*pw if not side else X(c3,w3,0.0)+i*pw
        c.pouch((x+3,y3-30,x+pw-3,y3+30),sh(gear,0.96),mag=True)
    if heavy and not side: c.rect((X(c3,w3,-0.17),y4,X(c3,w3,0.17),at(0.66)[0]),sh(gear,0.9),r=8)
def rig_plates(c,fit,X,side,plate):
    at=fit.at; y,l,r,cx,w=at(0.06); y2=at(0.38)[0]
    c.rect((X(cx,w,-0.37),y,X(cx,w,0.37),y2),plate,r=12)
    c.line([(X(cx,w,-0.3),(y+y2)/2),(X(cx,w,0.3),(y+y2)/2)],sh(plate,0.7),3)
    for xx in (X(cx,w,-0.31),X(cx,w,0.31)):
        for yy in (y+14,y2-14): c.ell([xx-4,yy-4,xx+4,yy+4],METAL,edge=1,drop=False)
    for i in range(3):
        yy,l2,r2,c2,w2=at(0.40+i*0.055); c.rect((X(c2,w2,-0.33),yy,X(c2,w2,0.33),yy+24),sh(plate,1.05-i*0.05),r=5)

def shoulders(c,fit,kind,col):
    y,l,r,cx,w=fit.at(0.05)
    for dx in (-1,1):
        if kind=='soft': c.ell([cx+dx*w*0.45-36,y-16,cx+dx*w*0.45+36,y+40],sh(col,0.9))
        else:
            for i in range(3): c.ell([cx+dx*w*(0.45-i*0.02)-34+i*3,y-18+i*15,cx+dx*w*(0.45-i*0.02)+34-i*3,y+24+i*15],sh(col,1.0-i*0.07))

# ---------------------------------------------------------------- костюм
def render_suit(spec, look, body, view, seed=0):
    kind,pal,gear,acc=look; g=spec.get
    fit=Fit(body,view); c=C5(); side=view=='east'; back=view=='north'; at=fit.at; X=_X(fit,side)
    rng=random.Random(seed); base=pal[0]; dk=sh(base,0.62)
    bodym=M(lambda d: d.polygon(fit.polygon(),fill=255))
    garment=g('garment','coverall')
    fab=camo(kind,pal,seed)
    c.shape(bodym,fab,shade=0.22,edge=0,drop=False)
    yT,lT,rT,cT,wT=at(0.0); yb=at(0.935)[0]; yE=at(1.0)[0]
    # низ одежды: брюки другого цвета у курток и плащей
    if garment in ('jacket','coat'):
        tr=g('trousers',(58,56,50)); ytr=at(0.60 if garment=='jacket' else 0.86)[0]
        trm=bodym & (YY>ytr); c.shape(trm,camo('solid',[tr],seed+1),shade=0.15,edge=0,drop=False)
    # ботинки
    c.rect((0,yb,N,yE+30),g('boots',(52,44,36)),r=0,shade=0.25,edge=0,drop=False)
    c.line([(0,yb),(N,yb)],(30,26,22),3); c.line([(0,yE-14),(N,yE-14)],(34,32,28),4)
    if not side: c.line([(at(0.80)[3],at(0.80)[0]),(at(0.93)[3],yb)],sh(g('trousers',base),0.6),3)
    # ноги
    yC,lC,rC,cC,wC=at(0.74); yK,lK,rK,cK,wK=at(0.865)
    dxs=(-0.26,0.26) if not side else (0.08,)
    for dx in dxs:
        if g('cargo',True) and not back: c.pouch((X(cC,wC,dx)-27,yC-16,X(cC,wC,dx)+27,yC+36),sh(g('trousers',base),0.96),buckle=False)
        if g('knees'):
            x=X(cK,wK,dx); kc=g('kneecol',(54,54,50)); c.rect((x-26,yK-22,x+26,yK+20),kc,r=12); c.rect((x-15,yK-12,x+15,yK+10),sh(kc,0.75),r=8,shade=0.05,edge=1.5)
        if g('thighplates'):
            c.rect((X(cC,wC,dx)-30,yC-24,X(cC,wC,dx)+30,yC+34),g('plate',GUN),r=7)
    if garment=='hazmat':
        for t in (0.84,0.90):
            y,l,r,cx,w=at(t); c.rect((l+6,y,r-6,y+10),(214,214,200),r=2,shade=0,edge=1.5)
    # подол куртки / плаща
    if garment=='jacket':
        y,l,r,cx,w=at(0.60); c.line([(l+4,y),(r-4,y)],sh(base,0.55),4)
    if garment=='coat':
        y,l,r,cx,w=at(0.86); c.line([(l+4,y),(r-4,y)],sh(base,0.5),4)
        if not side and not back: c.line([(at(0.58)[3],at(0.58)[0]),(at(0.86)[3],y)],sh(base,0.5),4)
        for t in (0.66,0.76): yy,l2,r2,c2,w2=at(t); c.line([(l2+14,yy),(l2+30,yy+20)],sh(base,0.7),2,0.6); c.line([(r2-14,yy),(r2-30,yy+20)],sh(base,0.7),2,0.6)
    # ремень
    if g('belt','tactical')!='none':
        yW,lW,rW,cW,wW=at(0.57); bc=(70,48,30) if g('belt')=='leather' else (44,42,36)
        c.rect((lW+4,yW,rW-4,yW+16),bc,r=3,shade=0.05,edge=1.5)
        if not back: c.rect((X(cW,wW,0)-12,yW-2,X(cW,wW,0)+12,yW+18),(170,160,120) if g('belt')=='leather' else BUCKLE,r=3,edge=1.5)
    # маскхалат: бахрома
    if garment=='ghillie':
        for _ in range(320):
            t=rng.uniform(0.0,0.90); y,l,r,cx,w=at(t); x=rng.uniform(l,r); col=pal[rng.randrange(len(pal))]
            c.line([(x,y),(x+rng.uniform(-6,6),y+rng.uniform(12,28))],sh(col,rng.uniform(0.8,1.15)),3,0.9)
    # швы
    c.stitch((lT+14,yT+40),(at(0.55)[1]+10,at(0.55)[0]),dk); c.stitch((rT-14,yT+40),(at(0.55)[2]-10,at(0.55)[0]),dk)
    # ---------------- верх ----------------
    if back:
        y0,l0,r0,c0,w0=at(0.07); y1=at(0.54)[0]
        rig=g('rig')
        if rig in ('carrier','heavy'):
            c.rect((c0-w0*0.37,y0,c0+w0*0.37,y1),gear,r=10); c.molle((c0-w0*0.33,y0+46,c0+w0*0.33,y1-8),gear); c.rect((c0-26,y0+8,c0+26,y0+26),sh(gear,0.7),r=6)
        elif rig=='chest':
            for a,b in (((lT+30,yT),(cT+wT*0.2,at(0.5)[0])),((rT-30,yT),(cT-wT*0.2,at(0.5)[0]))): c.strap([a,b],sh(gear,0.9),14)
        elif rig=='plates':
            for i in range(3):
                yy=y0+i*(y1-y0)/3; c.rect((c0-w0*0.37,yy,c0+w0*0.37,yy+(y1-y0)/3-6),g('plate',GUN),r=8)
        elif rig=='vest':
            c.rect((c0-w0*0.34,y0+10,c0+w0*0.34,y1-20),gear,r=10)
        if garment=='hazmat': c.rect((c0-w0*0.3,y0+10,c0+w0*0.3,y0+40),sh(base,0.8),r=6)
        if g('hood'): c.ell([c0-w0*0.31,y0-40,c0+w0*0.31,y0+22],sh(base,0.9),edge=2)
        if garment=='coat': c.line([(c0,at(0.6)[0]),(c0,at(0.86)[0])],sh(base,0.5),4)
    else:
        col=g('collar','normal')
        if col=='fur':  c.ell([X(cT,wT,-0.40),yT-14,X(cT,wT,0.40),yT+34],(150,132,108),edge=2)
        elif col=='ring': c.rect((X(cT,wT,-0.36),yT-6,X(cT,wT,0.36),yT+18),(150,152,148),r=8,edge=2)
        elif col=='high': c.rect((X(cT,wT,-0.32),yT-10,X(cT,wT,0.32),yT+26),sh(base,0.82),r=10,edge=2)
        elif col!='none': c.rect((X(cT,wT,-0.34),yT-4,X(cT,wT,0.34),yT+22),sh(base,0.86),r=10,edge=2)
        if g('hood'):
            for dx in (-1,1):
                if not side or dx>0: c.ell([X(cT,wT,dx*0.36)-30,yT-6,X(cT,wT,dx*0.36)+30,yT+30],sh(base,0.9),edge=2)
        if g('zipper') and not side:
            c.line([(cT,yT+22),(cT,at(0.56 if garment!='coat' else 0.84)[0])],(72,72,70),4)
            if garment=='coat':
                for t in (0.20,0.32,0.44): yy=at(t)[0]; c.ell([cT+12,yy-6,cT+24,yy+6],(60,50,40),edge=1)
        if garment=='coat' and not side:          # лацканы
            c.poly([(cT-6,yT+20),(cT-wT*0.30,yT+10),(cT-wT*0.18,at(0.22)[0])],sh(base,0.85),edge=2)
            c.poly([(cT+6,yT+20),(cT+wT*0.30,yT+10),(cT+wT*0.18,at(0.22)[0])],sh(base,0.85),edge=2)
        if garment=='jacket' and not side:
            for dx in (-0.23,0.23): yy=at(0.20)[0]; c.pouch((X(cT,wT,dx)-28,yy,X(cT,wT,dx)+28,yy+46),sh(base,0.95),buckle=False)
        if g('shoulders') and not side: shoulders(c,fit,g('shoulders'),g('plate',gear) if g('shoulders')=='segmented' else gear)
        rig=g('rig')
        if rig=='chest': rig_chest(c,fit,X,side,gear)
        elif rig=='vest': rig_vest(c,fit,X,side,gear)
        elif rig=='carrier': rig_carrier(c,fit,X,side,gear)
        elif rig=='heavy': rig_carrier(c,fit,X,side,gear,heavy=True)
        elif rig=='plates': rig_plates(c,fit,X,side,g('plate',GUN))
        if garment=='hazmat':
            y,l,r,cx,w=at(0.48); c.rect((l+6,y,r-6,y+10),(214,214,200),r=2,shade=0,edge=1.5)
            if not side and rig is None:
                y,l,r,cx,w=at(0.12); c.rect((cx-46,y,cx+46,y+70),(58,60,60),r=6)
                c.rect((cx-36,y+10,cx+36,y+34),(64,120,92),r=3,shade=0.05,edge=1.5)
                for i,cc in enumerate([(200,70,60),(220,180,60),(110,200,120)]): c.ell([cx-28+i*24-5,y+46,cx-28+i*24+5,y+56],cc,edge=1,drop=False)
            y0=at(0.06)[0]; c.strap([(X(cT,wT,-0.40),y0+6),(X(cT,wT,-0.36),y0+60),(X(cT,wT,-0.24),y0+96)],RUBBER,11)
        arm=g('armband')
        if arm:
            y,l,r,cx,w=at(0.20)
            if not side: c.rect((l+4,y,l+30,y+22),arm,r=2,shade=0.05,edge=1.5)
            else: c.rect((X(cx,w,0.42)-14,y,X(cx,w,0.42)+14,y+22),arm,r=2,shade=0.05,edge=1.5)
        if not side and g('patch',True):
            y,l,r,cx,w=at(0.16); x=cx-w*0.42+ (34 if arm else 0); c.rect((x-15,y,x+15,y+22),acc,r=3,shade=0.05,edge=1.5)
        if side and rig in ('carrier','heavy','vest'):
            y0,l0,r0,c0,w0=at(0.08); c.rect((l0+6,y0+10,l0+w0*0.2,at(0.5)[0]),gear,r=8)
    return c.finish(bodym)

# ---------------------------------------------------------------- шлемы (стройные, по голове)
HX=256
def render_head(style, look, view, seed=0):
    kind,pal,gear,acc=look; c=C5(); e=view=='east'; n=view=='north'; cx=HX if not e else 252
    cov=camo(kind,pal,seed+5); base=pal[0]
    # габарит головы: x ~150..362, макушка ~150, низ лица ~350
    def dome(top,bottom,wd,box_e=None):
        b=[cx-wd,top,cx+wd,top+2*(bottom-top)] if not e else (box_e or [cx-wd-6,top,cx+wd-6,top+2*(bottom-top)])
        return M(lambda d: d.ellipse(b,fill=255)) & (YY<bottom)
    if style=='beanie':
        c.shape(dome(160,246,96),sh(base,0.92),edge=2)
        c.rect((cx-98,214,cx+98,248),sh(base,0.78),r=8)
        for x in range(cx-92,cx+92,7): c.line([(x,218),(x,244)],sh(base,0.62),2,0.6)
    elif style=='cap':                                                # кепи / кепка с козырьком
        c.shape(dome(170,236,92),cov,edge=2)
        if not n:
            if e: c.poly([(300,226),(372,232),(368,242),(298,240)],sh(base,0.7),edge=2)
            else: c.ell([cx-78,222,cx+78,250],sh(base,0.72),edge=2)
        c.line([(cx-88 if not e else 160,230),(cx+88 if not e else 346,230)],sh(base,0.6),3)
    elif style=='flatcap':
        c.shape(dome(176,236,96),sh(base,0.9),edge=2)
        if not n: c.ell([cx-90 if not e else 220,220,cx+90 if not e else 370,248],sh(base,0.78),edge=2)
    elif style=='headset_cap':
        c.shape(dome(170,236,92),sh(base,0.92),edge=2)
        if not n: c.ell([cx-78,222,cx+78,250] if not e else [290,224,372,244],sh(base,0.72),edge=2)
        for xx in ((cx-104,cx+88) if not e else (196,)): c.rect((xx,236,xx+18,280),(38,40,38),r=6)
        if not e and not n: c.wire([(cx+96,276),(cx+50,318)],(30,30,30),3)
    elif style=='balaclava':
        m=M(lambda d: d.ellipse([cx-104,152,cx+104,356] if not e else [146,152,354,356],fill=255))
        if not n: m&=~M(lambda d: d.ellipse([cx-70,236,cx+70,282] if not e else [262,232,370,282],fill=255))
        c.shape(m,cov,edge=2)
    elif style in ('hood','ghillie_hood'):
        box=[cx-112,138,cx+112,366] if not e else [124,138,368,362]
        m=M(lambda d: d.ellipse(box,fill=255))
        if not n: m&=~M(lambda d: d.ellipse([cx-74,212,cx+74,348] if not e else [262,206,420,352],fill=255))
        c.shape(m,cov if style=='hood' else cov,edge=2)
        if style=='ghillie_hood':
            rng=random.Random(seed)
            for _ in range(140):
                a=rng.uniform(math.pi*1.05,math.pi*1.95); r=rng.uniform(96,116); x=cx+math.cos(a)*r; y=252+math.sin(a)*r*1.05
                col=pal[rng.randrange(len(pal))]; c.wire([(x,y),(x+rng.uniform(-8,8),y+rng.uniform(10,22))],sh(col,rng.uniform(0.8,1.1)),3)
        elif not n and not e:
            for dx in (-56,56): c.wire([(cx+dx,330),(cx+dx*1.04,378)],(60,58,52),3); c.wire_dot(cx+dx*1.04,380,5,BUCKLE)
    elif style in ('steel','tactical','psi','faceshield'):
        if style=='steel':                                            # классическая каска в чехле
            c.shape(dome(150,262,104),cov,edge=2.5)
            c.rect((cx-108 if not e else 142,246,cx+108 if not e else 358,262),sh(base,0.72),r=6)
            for k in range(3): c.line([(cx-90+k*12 if not e else 160+k*12,170+k*4),(cx+90-k*12 if not e else 340-k*12,170+k*4)],sh(base,0.7),2,0.4)
            if not n:
                for sx in ((cx-98,cx+98) if not e else (226,)): c.wire([(sx,258),(sx+(18 if sx<cx else -18),330),(cx,348)] if not e else [(sx,258),(296,338)],(70,56,40),3)
        else:                                                         # тактический с вырезом над ушами
            m=dome(150,258,102)
            if not n:
                cut=M(lambda d: (d.rectangle([cx-106,224,cx-80,258],fill=255),d.rectangle([cx+80,224,cx+106,258],fill=255))) if not e else M(lambda d: d.rectangle([206,226,242,258],fill=255))
                m&=~cut
            c.shape(m,cov,edge=2.5)
            for xx in ((cx-104,cx+86) if not e else (164,)):
                c.rect((xx,192,xx+18,222),sh(gear,0.75),r=3); [c.ell([xx+5,y,xx+13,y+8],(40,40,40),edge=0,drop=False) for y in (196,208)]
            c.velcro((cx-40 if not e else 182,160,cx+40 if not e else 250,178),base)
            if not n: c.rect((cx-16 if not e else 314,156,cx+16 if not e else 340,184),(54,56,54),r=4)
            if not n:
                for sx in ((cx-92,cx+92) if not e else (236,)): c.wire([(sx,250),(sx+(18 if sx<cx else -18),326),(cx,346)] if not e else [(sx,250),(298,336)],(96,70,46),3)
            if style=='psi':
                for i in range(2):
                    m2=M(lambda d: d.arc([cx-96+i*8,156+i*8,cx+96-i*8,330-i*8] if not e else [150+i*8,156+i*8,354-i*8,330-i*8],200,340,fill=255,width=5))
                    c.shape(m2,(176,112,56),edge=0,drop=False,shade=0)
                ax=cx+60 if not e else 204; c.wire([(ax,158),(ax+14,112)],(70,72,74),4); c.wire_dot(ax+15,110,6,acc)
            if style=='faceshield' and not n:                         # бронезабрало (прозрачное)
                if e: c.glass(M(lambda d: d.rounded_rectangle([292,214,380,330],radius=24,fill=255)),frame=(48,50,52),rim=8)
                else: c.glass(M(lambda d: d.rounded_rectangle([cx-92,212,cx+92,334],radius=28,fill=255)),frame=(48,50,52),rim=8)
                for xx in ((cx-98,cx+98) if not e else (234,)): c.ell([xx-8,214,xx+8,230],METAL,edge=1.5)
    elif style=='gasmask_hood':                                       # противогазный капюшон (химзащита)
        hc=sh(base,1.0)
        box=[cx-114,140,cx+114,370] if not e else [130,140,372,368]
        c.shape(M(lambda d: d.ellipse(box,fill=255)),camo('solid',[hc],seed),edge=2.5)
        for k in range(4): c.line([(cx-100 if not e else 150,190+k*30),(cx+100 if not e else 350,196+k*30)],sh(hc,0.82),2,0.4)
        if not n:
            if e:
                c.poly([(272,206),(338,214),(350,300),(312,338),(270,322)],RUBBER,edge=2)
                c.glass(M(lambda d: d.ellipse([300,226,346,284],fill=255)),frame=(70,72,70),rim=6)
                c.rect((322,304,378,350),(88,96,68),r=10)
            else:
                c.ell([cx-82,200,cx+82,348],RUBBER,edge=2)
                c.glass(M(lambda d: d.rounded_rectangle([cx-66,218,cx+66,286],radius=30,fill=255)),frame=(70,72,70),rim=7)   # панорамное стекло
                c.ell([cx-24,296,cx+24,342],(40,40,38))
                for i in range(3): c.line([(cx-14,306+i*10),(cx+14,306+i*10)],(26,26,24),3)
                c.rect((cx+58,296,cx+108,342),(88,96,68),r=10)                                                  # фильтр сбоку
                for i in range(3): c.line([(cx+64,306+i*12),(cx+102,306+i*12)],(62,68,48),3)
    elif style=='cbrn':                                               # изолирующий шлем: шлем + стекло + уплотнитель
        c.shape(dome(146,276,110),sh(base,1.0),edge=2.5)
        c.rect((cx-116 if not e else 138,260,cx+116 if not e else 368,372),(54,56,54),r=30)                 # прорезиненный капюшон
        if not n:
            if e: c.glass(M(lambda d: d.rounded_rectangle([288,212,382,340],radius=26,fill=255)),frame=(150,152,148),rim=8)
            else:
                c.glass(M(lambda d: d.rounded_rectangle([cx-88,206,cx+88,330],radius=30,fill=255)),frame=(150,152,148),rim=8)
                c.rect((cx-26,330,cx+26,362),(60,64,60),r=8); c.wire([(cx+20,350),(cx+92,372)],RUBBER,8)         # шланг к баллону
        for xx in ((cx-112,cx+104) if not e else (156,)): c.ell([xx-4,236,xx+12,252],METAL,edge=1.5)
    elif style in ('exo_mask','exo_mask_assault'):                    # тяжёлая каска + противогаз (без футуризма)
        heavy=style=='exo_mask_assault'
        steel=(70,74,70) if not heavy else (58,62,60)
        # назатыльник и щёчки (под каской)
        if n:
            c.rect((cx-104,236,cx+104,330),sh(steel,0.85),r=18)
            for i in range(3): c.line([(cx-96,262+i*22),(cx+96,262+i*22)],sh(steel,0.6),3)
        else:
            for dx in ((-1,1) if not e else (1,)):
                xx=cx+dx*86 if not e else 212
                c.rect((xx-24,226,xx+24,312),sh(steel,0.9),r=10)
                for yy in (240,296): c.ell([xx-5,yy-5,xx+5,yy+5],METAL,edge=1,drop=False)
        # каска с кромкой
        c.shape(dome(146,252,108),camo('solid',[steel],seed+9),edge=2.5)
        c.rect((cx-112 if not e else 140,240,cx+112 if not e else 364,256),sh(steel,0.75),r=5)
        for xx in ((cx-80,cx-30,cx+30,cx+80) if not e else (200,260,320)): c.ell([xx-4,244,xx+4,252],METAL,edge=1,drop=False)
        c.line([(cx-70 if not e else 170,176),(cx+70 if not e else 330,176)],sh(steel,0.7),2,0.5)
        if not n:
            if e:
                c.poly([(268,252),(334,258),(348,312),(316,346),(270,334)],RUBBER,edge=2.5)
                c.glass(M(lambda d: d.ellipse([302,262,342,302],fill=255)),frame=(96,98,96),rim=7)
                c.rect((318,312,374,350),(88,96,68),r=10)
                for i in range(3): c.line([(324,320+i*11),(368,320+i*11)],(62,68,48),3)
            else:
                c.ell([cx-74,250,cx+74,360],RUBBER,edge=2.5)                                     # маска
                for x in (cx-34,cx+34): c.glass(M(lambda d: d.ellipse([x-26,262,x+26,312],fill=255)),frame=(96,98,96),rim=7)
                c.ell([cx-20,314,cx+20,352],(40,40,38))                                           # переговорная мембрана
                for i in range(3): c.line([(cx-12,322+i*9),(cx+12,322+i*9)],(26,26,24),3)
                c.rect((cx+52,312,cx+100,354),(88,96,68),r=10)                                   # фильтр сбоку
                for i in range(3): c.line([(cx+58,320+i*11),(cx+94,320+i*11)],(62,68,48),3)
                if heavy:                                                                         # бронепластина подбородка
                    c.rect((cx-46,338,cx+46,372),sh(steel,0.95),r=8)
                    for xx in (cx-34,cx+34): c.ell([xx-4,350,xx+4,358],METAL,edge=1,drop=False)
    elif style=='closed':                                             # закрытый шлем экзоскелета
        pts=[(cx-98,290),(cx-104,200),(cx-70,148),(cx+70,148),(cx+104,200),(cx+98,290),(cx+62,350),(cx-62,350)] if not e else \
            [(140,290),(146,200),(186,148),(312,148),(364,196),(378,282),(338,350),(184,350)]
        c.poly(pts,GUN,edge=2.5)
        if not n:
            if e: c.glass(M(lambda d: d.polygon([(318,214),(384,220),(384,262),(324,262)],fill=255)),frame=(34,36,38),rim=6)
            else:
                c.glass(M(lambda d: d.rounded_rectangle([cx-86,212,cx+86,262],radius=10,fill=255)),frame=(34,36,38),rim=7)
                c.rect((cx-50,306,cx+50,334),(52,54,56),r=5)
                for i in range(6): c.line([(cx-40+i*16,312),(cx-40+i*16,328)],(30,30,30),3)
        else:
            c.rect((cx-62,176,cx+62,292),(58,62,64),r=8)
            for i in range(4): c.line([(cx-50,196+i*22),(cx+50,196+i*22)],(40,42,44),3)
    return c.finish(out=12)

# ---------------------------------------------------------------- противогаз с прозрачными линзами
def render_gasmask(view):
    c=C5(); OL=(92,100,70)
    if view=='south':
        c.ell([182,200,330,354],RUBBER,edge=2.5)
        for x in (220,292): c.glass(M(lambda d: d.ellipse([x-30,228,x+30,284],fill=255)),frame=(96,98,96),rim=8)
        c.ell([230,302,282,352],(40,40,38))
        for i in range(4): c.line([(240,312+i*10),(272,312+i*10)],(26,26,24),3)
        c.rect((300,302,354,348),OL,r=10)
        for i in range(3): c.line([(306,312+i*12),(348,312+i*12)],sh(OL,0.7),3)
        for a,b in (((186,234),(146,224)),((326,234),(366,224))): c.wire([a,b],(44,44,40),6)
    elif view=='east':
        c.poly([(268,204),(330,214),(342,300),(306,336),(266,320)],RUBBER,edge=2.5)
        c.glass(M(lambda d: d.ellipse([298,232,344,282],fill=255)),frame=(96,98,96),rim=7)
        c.rect((314,300,372,348),OL,r=10)
        for i in range(3): c.line([(320,310+i*12),(366,310+i*12)],sh(OL,0.7),3)
        c.wire([(272,240),(150,230)],(44,44,40),6)
    else:
        for y in (220,262,300): c.strap([(160,y),(352,y)],(52,52,48),9)
        c.strap([(256,206),(256,312)],(52,52,48),9); c.rect((240,250,272,274),METAL,r=3)
    return c.finish(out=12)
