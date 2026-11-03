# Рюкзаки и баллоны Зоны: Belt/Shoulders/renderUtilityAsPack как в RH2 (1.6).
# Названия, характеристики и рисунки свои. Посадка — по меркам тел из suit_art.py.
import math, os, random, sys
import numpy as np
from xml.sax.saxutils import escape as esc
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suit_art import Fit, N, C, bevel_rect, pouch, buckle, stitches, finish

M='/mnt/user-data/outputs/StalkerZone/Common'
L=f'{M}/Languages/Russian/DefInjected'
T=f'{M}/Textures'
APP='Things/Pawn/Humanlike/Apparel/SZ_Packs'

# key, en, ru, стиль, (основной, второй), характеристики, цена, масса, (исследование, верстаки, материалы, навык, работа), фракции, описание en/ru
ITEMS=[
 ('Bag','canvas sack','вещмешок','sack',((0.45,0.42,0.30),(0.30,0.27,0.18)),
   dict(carry=20),60,0.8,('ComplexClothing',['HandTailoringBench','ElectricTailoringBench'],{'Cloth':30},2,1500),['Loners','Bandits'],
   'A simple canvas sack on a single strap. Holds a little, weighs nothing.','Простой брезентовый мешок на одной лямке. Вмещает немного, зато ничего не весит.'),
 ('Tourist','hiking backpack','туристический рюкзак','tourist',((0.30,0.38,0.42),(0.20,0.25,0.28)),
   dict(carry=35,move=-0.05),180,1.5,('ComplexClothing',['HandTailoringBench','ElectricTailoringBench'],{'Cloth':50},3,2500),['Loners','Freedom'],
   'An old hiking backpack with a top flap and side pockets.','Старый туристический рюкзак с клапаном и боковыми карманами.'),
 ('Raid','raid backpack','рейдовый рюкзак','raid',((0.36,0.38,0.26),(0.24,0.26,0.17)),
   dict(carry=50,move=-0.1,cold=4),350,2.5,('ComplexClothing',['HandTailoringBench','ElectricTailoringBench'],{'Cloth':70,'Steel':10},4,4000),['Loners','Duty','Freedom','Military','Mercenaries'],
   'A sturdy pack for multi-day raids, with a bedroll strapped on top.','Крепкий рюкзак для многодневных рейдов, со скаткой сверху.'),
 ('Frame','expedition frame pack','экспедиционный рюкзак с каркасом','frame',((0.42,0.30,0.20),(0.28,0.20,0.13)),
   dict(carry=75,move=-0.2,cold=4),600,4,('Smithing',['TableMachining'],{'Cloth':80,'Steel':40},5,6000),['Monolith','Mercenaries'],
   'A huge pack on a steel frame. Carries a lot, but slows its owner down.','Огромный рюкзак на стальном каркасе. Несёт очень много, но замедляет владельца.'),
 ('Lead','lead-lined backpack','рюкзак со свинцовой подкладкой','lead',((0.50,0.52,0.54),(0.35,0.37,0.39)),
   dict(carry=25,move=-0.1,shield=2,rad=0.05),700,6,('Smithing',['TableMachining'],{'Cloth':40,'Steel':80},5,5000),['Freedom','Scientists'],
   'A heavy pack lined with lead sheets. Blocks the radiation of two active artifacts, like two lead containers.','Тяжёлый рюкзак, проложенный свинцовыми листами. Гасит излучение двух активных артефактов, как два свинцовых контейнера.'),
 ('Medic','medic satchel','медицинский ранец','medic',((0.25,0.36,0.24),(0.17,0.25,0.16)),
   dict(carry=20,tend=0.15),400,1.5,('ComplexClothing',['HandTailoringBench','ElectricTailoringBench'],{'Cloth':40,'MedicineHerbal':2},4,3000),['Duty','Military','Scientists'],
   'A field medic satchel with everything laid out at hand: treatment goes faster.','Ранец полевого медика, где всё разложено под рукой: лечение идёт быстрее.'),
 ('Tank','breathing tank','дыхательный баллон','tank1',((0.55,0.58,0.60),(0.25,0.26,0.27)),
   dict(tox=0.30,rad=0.10,move=-0.03),450,4,('MicroelectronicsBasics',['TableMachining'],{'Steel':40,'ComponentIndustrial':2},4,4000),['Military'],
   'A single air tank with a regulator. Clean air: protects from toxic fumes and radioactive dust.','Один баллон с редуктором. Чистый воздух защищает от ядовитых паров и радиоактивной пыли.'),
 ('TwinTank','twin air tanks','сдвоенные баллоны','tank2',((0.86,0.52,0.18),(0.28,0.28,0.28)),
   dict(tox=0.50,rad=0.15,move=-0.05),800,7,('MicroelectronicsBasics',['TableMachining'],{'Steel':70,'ComponentIndustrial':3},5,6000),['Monolith','Scientists'],
   'Two air tanks with a shared manifold. Breathe longer and safer.','Два баллона с общим коллектором. Дышать дольше и безопаснее.'),
 ('ClosedCycle','closed-cycle breathing unit','система замкнутого цикла','closed',((0.90,0.90,0.86),(0.30,0.55,0.75)),
   dict(tox=0.70,rad=0.20,psi=0.05,move=-0.1,heat=8),1500,9,('AdvancedFabrication',['FabricationBench'],{'Plasteel':40,'ComponentIndustrial':4,'ComponentSpacer':1},7,10000),['Scientists'],
   'A sealed unit that recycles exhaled air. The best protection for the lungs the Zone allows.','Герметичный блок, который очищает выдыхаемый воздух. Лучшая защита лёгких, какую позволяет Зона.'),
 ('Cooling','cooling pack','охлаждающий ранец','cooling',((0.30,0.34,0.38),(0.25,0.55,0.80)),
   dict(heat=20,tox=0.10,move=-0.05),900,6,('AdvancedFabrication',['FabricationBench'],{'Steel':50,'Plasteel':20,'ComponentIndustrial':3},6,7000),['Scientists'],
   'A radiator pack that pumps coolant through tubes under the suit. Helps near thermal anomalies and in the heat.','Ранец-радиатор, гоняющий хладагент по трубкам под костюмом. Помогает у термических аномалий и в жару.'),
]
OFFS={'carry':'SZ_InventoryCapacity','move':'MoveSpeed','rad':'SZ_RadiationResistance','psi':'SZ_PsiProtection',
      'tox':'ToxicResistance','shield':'SZ_ArtifactShielding','tend':'MedicalTendSpeed'}
BASES={'cold':'Insulation_Cold','heat':'Insulation_Heat'}

# ---------------- XML ----------------
o=['''<?xml version="1.0" encoding="utf-8"?>
<Defs>

  <!-- Файл сгенерирован Source/Tools/gen_packs.py.
       Рюкзаки и баллоны Зоны. Новый Belt/Shoulders путь отрисовки,
       но рюкзак/баллон можно надеть только один. Грузоподъёмность — стат SZ_InventoryCapacity
       (инвентарь и караваны, C#: ZoneHarmony). -->

  <ApparelLayerDef>
    <defName>SZ_BackLayer</defName>
    <label>back</label>
    <drawOrder>500</drawOrder>
  </ApparelLayerDef>

  <StatDef>
    <defName>SZ_ArtifactShielding</defName>
    <label>artifact shielding</label>
    <description>How many active artifacts have their radiation blocked by the gear, in addition to lead containers in the inventory.</description>
    <category>PawnCombat</category>
    <defaultBaseValue>0</defaultBaseValue>
    <minValue>0</minValue>
    <toStringStyle>Integer</toStringStyle>
  </StatDef>

  <ThingDef ParentName="ApparelBase" Name="SZ_PackBase" Abstract="True">
    <techLevel>Industrial</techLevel>
    <tradeability>All</tradeability>
    <thingCategories Inherit="False"><li>ApparelUtility</li></thingCategories>
    <apparel>
      <layers><li>Belt</li></layers>
      <bodyPartGroups><li>Shoulders</li></bodyPartGroups>
      <wornGraphicData>
        <renderUtilityAsPack>true</renderUtilityAsPack>
      </wornGraphicData>
      <careIfWornByCorpse>false</careIfWornByCorpse>
    </apparel>
  </ThingDef>
''']
tr=[]
for (k,en,ru,style,cols,st,val,mass,rec,tags,den,dru) in ITEMS:
    research,users,cost,skill,work=rec
    bases=''.join(f'      <{BASES[a]}>{v}</{BASES[a]}>\n' for a,v in st.items() if a in BASES)
    offs=''.join(f'      <{OFFS[a]}>{v}</{OFFS[a]}>\n' for a,v in st.items() if a in OFFS)
    us=''.join(f'<li>{u}</li>' for u in users); cs=''.join(f'<{m}>{c}</{m}>' for m,c in cost.items())
    tg=''.join(f'<li>SZ_Faction_{t}</li>' for t in tags)
    o.append(f'''
  <ThingDef ParentName="SZ_PackBase">
    <defName>SZ_Pack_{k}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den)}</description>
    <graphicData>
      <texPath>Things/Item/SZ_Packs/{k}</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
    <statBases>
      <MaxHitPoints>120</MaxHitPoints>
      <MarketValue>{val}</MarketValue>
      <Mass>{mass}</Mass>
      <WorkToMake>{work}</WorkToMake>
      <EquipDelay>2</EquipDelay>
      <Flammability>0.5</Flammability>
{bases}    </statBases>
    <equippedStatOffsets>
{offs}    </equippedStatOffsets>
    <apparel>
      <wornGraphicPath>{APP}/{k}/{k}</wornGraphicPath>
      <tags>{tg}</tags>
    </apparel>
    <costList>{cs}</costList>
    <recipeMaker>
      <researchPrerequisite>{research}</researchPrerequisite>
      <recipeUsers>{us}</recipeUsers>
      <workSpeedStat>GeneralLaborSpeed</workSpeedStat>
      <workSkill>Crafting</workSkill>
      <skillRequirements><Crafting>{skill}</Crafting></skillRequirements>
    </recipeMaker>
  </ThingDef>
''')
    tr.append((f'SZ_Pack_{k}',ru,dru))
o.append('\n</Defs>\n')
os.makedirs(f'{M}/Defs/Gear',exist_ok=True)
open(f'{M}/Defs/Gear/SZ_Packs.xml','w',encoding='utf-8').write(''.join(o))
for sub in ('ThingDef','ApparelLayerDef','StatDef'): os.makedirs(f'{L}/{sub}',exist_ok=True)
t=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']+[f'  <{d}.label>{esc(r)}</{d}.label>\n  <{d}.description>{esc(dr)}</{d}.description>\n' for d,r,dr in tr]+['</LanguageData>\n']
open(f'{L}/ThingDef/SZ_Packs.xml','w',encoding='utf-8').write(''.join(t))
open(f'{L}/ApparelLayerDef/SZ_Packs.xml','w',encoding='utf-8').write('<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n  <SZ_BackLayer.label>спина</SZ_BackLayer.label>\n</LanguageData>\n')
open(f'{L}/StatDef/SZ_Packs.xml','w',encoding='utf-8').write('<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n  <SZ_ArtifactShielding.label>экранирование артефактов</SZ_ArtifactShielding.label>\n  <SZ_ArtifactShielding.description>У скольких активных артефактов снаряжение гасит излучение — в добавление к свинцовым контейнерам в инвентаре.</SZ_ArtifactShielding.description>\n</LanguageData>\n')

# ---------------- ГРАФИКА ----------------
METAL=(0.62,0.63,0.62); HOSE=(0.16,0.16,0.16)
def grain(layer,seed):
    a=np.array(layer).astype(np.int16); rng=np.random.default_rng(seed)
    n=rng.normal(0,6,a.shape[:2]).astype(np.int16)
    for i in range(3): a[:,:,i]=np.clip(a[:,:,i]+n,0,255)
    return Image.fromarray(a.astype(np.uint8),'RGBA')

def tank(d,dm,x,y0,y1,r,col):
    d.rounded_rectangle([x-r,y0,x+r,y1],radius=r,fill=C(col)); dm.rounded_rectangle([x-r,y0,x+r,y1],radius=r,fill=255)
    d.line([(x-r*0.45,y0+r),(x-r*0.45,y1-r)],fill=(255,255,255,90),width=max(4,int(r*0.3)))     # блик
    d.line([(x+r*0.55,y0+r),(x+r*0.55,y1-r)],fill=(0,0,0,60),width=max(4,int(r*0.3)))
    d.rectangle([x-r*0.45,y0-18,x+r*0.45,y0+4],fill=C(METAL)); dm.rectangle([x-r*0.45,y0-18,x+r*0.45,y0+4],fill=255)
    d.ellipse([x-r*0.6,y0-30,x+r*0.6,y0-12],fill=C(METAL,0.8)); dm.ellipse([x-r*0.6,y0-30,x+r*0.6,y0-12],fill=255)

def body_pack(style,cols,d,dm,box,view):
    """Сам рюкзак/баллоны в рамке box (вид сзади или сбоку)."""
    base,sec=cols; x0,y0,x1,y1=box; w=x1-x0; h=y1-y0; cx=(x0+x1)/2
    def R(b,col,r=18,riv=False):
        bevel_rect(d,b,col,r=r,rivets=riv); dm.rounded_rectangle(b,radius=r,fill=255)
    if style=='sack':
        d.ellipse([x0,y0+h*0.15,x1,y1],fill=C(base)); dm.ellipse([x0,y0+h*0.15,x1,y1],fill=255)
        d.polygon([(cx-w*0.18,y0+h*0.2),(cx+w*0.18,y0+h*0.2),(cx+w*0.08,y0),(cx-w*0.08,y0)],fill=C(base,0.9))
        dm.polygon([(cx-w*0.18,y0+h*0.2),(cx+w*0.18,y0+h*0.2),(cx+w*0.08,y0),(cx-w*0.08,y0)],fill=255)
        d.line([(cx-w*0.16,y0+h*0.2),(cx+w*0.16,y0+h*0.2)],fill=C(sec,0.6),width=8)
        for i in range(4): d.arc([x0+20,y0+h*0.25+i*h*0.15,x1-20,y0+h*0.5+i*h*0.15],20,160,fill=C(base,0.75),width=3)
    elif style in ('tourist','raid','frame','medic'):
        if style=='frame':
            for x in (x0+8,x1-8): d.line([(x,y0-30),(x,y1+12)],fill=C(METAL,0.7),width=12); dm.line([(x,y0-30),(x,y1+12)],fill=255,width=12)
            d.line([(x0+8,y0-26),(x1-8,y0-26)],fill=C(METAL,0.7),width=10); dm.line([(x0+8,y0-26),(x1-8,y0-26)],fill=255,width=10)
        R((x0,y0,x1,y1),base,r=26)
        R((x0-6,y0-6,x1+6,y0+h*0.3),tuple(v*0.85 for v in base),r=24)                                   # клапан
        buckle(d,cx,y0+h*0.3)
        if style!='medic':
            pouch(d,cx-w*0.28,y0+h*0.52,w*0.56,h*0.32,sec)                                               # передний карман
            stitches(d,[(x0+16,y0+h*0.45),(x1-16,y0+h*0.45)],C(base,1.25))
        else:
            d.rectangle([cx-12,y0+h*0.45,cx+12,y0+h*0.85],fill=(235,235,230,255)); d.rectangle([cx-34,y0+h*0.57,cx+34,y0+h*0.73],fill=(235,235,230,255))
        if style in ('raid','frame'):                                                                    # скатка
            yb=y0-34 if style=='raid' else y1-10
            d.rounded_rectangle([x0-14,yb,x1+14,yb+40],radius=20,fill=C(sec,0.9)); dm.rounded_rectangle([x0-14,yb,x1+14,yb+40],radius=20,fill=255)
            for x in (x0+16,x1-16): d.line([(x,yb-2),(x,yb+42)],fill=C(sec,0.5),width=8)
            for i in range(3): d.line([(x0-6,yb+10+i*10),(x1+6,yb+10+i*10)],fill=C(sec,0.75),width=2)
        if style in ('tourist','raid','frame'):                                                          # боковые карманы
            for xx in (x0-18,x1-4):
                d.rounded_rectangle([xx,y0+h*0.4,xx+22,y0+h*0.85],radius=8,fill=C(base,0.8)); dm.rounded_rectangle([xx,y0+h*0.4,xx+22,y0+h*0.85],radius=8,fill=255)
    elif style=='lead':
        R((x0,y0,x1,y1),base,r=12,riv=True)
        for i in range(1,3): d.line([(x0+10,y0+i*h/3),(x1-10,y0+i*h/3)],fill=C(base,0.65),width=6)
        r=min(w,h)*0.18; d.ellipse([cx-r,y0+h*0.5-r,cx+r,y0+h*0.5+r],fill=(240,200,40,255))           # знак радиации
        for a in (90,210,330):
            d.pieslice([cx-r*0.9,y0+h*0.5-r*0.9,cx+r*0.9,y0+h*0.5+r*0.9],a-30,a+30,fill=(30,30,30,255))
        d.ellipse([cx-r*0.22,y0+h*0.5-r*0.22,cx+r*0.22,y0+h*0.5+r*0.22],fill=(30,30,30,255))
    elif style=='tank1':
        tank(d,dm,cx,y0+20,y1,w*0.26,base)
        d.line([(cx,y0),(cx+w*0.35,y0-24)],fill=C(HOSE),width=10); dm.line([(cx,y0),(cx+w*0.35,y0-24)],fill=255,width=10)
    elif style=='tank2':
        for dx in (-0.22,0.22): tank(d,dm,cx+dx*w,y0+20,y1,w*0.2,base)
        d.rectangle([cx-w*0.3,y0-6,cx+w*0.3,y0+10],fill=C(METAL)); dm.rectangle([cx-w*0.3,y0-6,cx+w*0.3,y0+10],fill=255)
        for dx in (-0.12,0.12): d.ellipse([cx+dx*w-10,y0-4,cx+dx*w+10,y0+16],fill=(200,60,40,255))
    elif style=='closed':
        R((x0,y0,x1,y1),base,r=20)
        for dx in (-0.2,0.2): tank(d,dm,cx+dx*w,y0+26,y1-14,w*0.15,sec)
        for i,colr in enumerate([(120,230,140),(240,200,60)]):                                          # манометры
            gx=cx-30+i*60; d.ellipse([gx-16,y0+6,gx+16,y0+38],fill=(235,235,230,255),outline=(60,60,60,255),width=4)
            d.line([(gx,y0+22),(gx+10,y0+12)],fill=(40,40,40,255),width=3)
    elif style=='cooling':
        R((x0,y0,x1,y1),base,r=14,riv=True)
        for i in range(8): d.line([(x0+18,y0+20+i*(h-40)/8),(x1-18,y0+20+i*(h-40)/8)],fill=C(base,0.6),width=6)   # рёбра радиатора
        for xx in (x0+10,x1-10): d.line([(xx,y0+10),(xx,y1-10)],fill=C(sec),width=10)
        d.ellipse([cx-18,y1-50,cx+18,y1-14],fill=C(sec,1.1))

def render_pack(k,style,cols,body,view,seed=0):
    fit=Fit(body,view)
    layer=Image.new('RGBA',(N,N),(0,0,0,0)); d=ImageDraw.Draw(layer,'RGBA')
    mask=Image.new('L',(N,N),0); dm=ImageDraw.Draw(mask)
    base,sec=cols
    big={'frame':1.25,'raid':1.1,'lead':1.0,'closed':1.05,'cooling':1.0,'tourist':1.0,'medic':0.85,'sack':0.9,'tank1':0.9,'tank2':1.0}[style]
    yA,lA,rA,cA,wA=fit.at(0.10); yB=fit.at(min(0.72,0.56*big+0.06))[0]
    strap_col=C(sec,0.55) if style not in ('tank1','tank2','closed','cooling') else C(HOSE,1.2)
    if view=='north':
        pw=wA*0.58*min(big,1.15)
        body_pack(style,cols,d,dm,(cA-pw/2,yA+12,cA+pw/2,yB),view)
    elif view=='east':
        depth=wA*0.42*big
        body_pack(style,cols,d,dm,(lA-depth*0.55,yA+12,lA+depth*0.45,yB),view)
        # лямка через плечо на грудь
        pts=[(lA+depth*0.2,yA+20),(cA,yA-4),(rA-wA*0.12,fit.at(0.4)[0])]
        d.line(pts,fill=strap_col,width=14,joint='curve'); dm.line(pts,fill=255,width=14,joint='curve')
    else:   # спереди видны только лямки (и шланг у баллонов)
        if style=='sack':
            pts=[(cA-wA*0.3,yA),(cA+wA*0.25,fit.at(0.5)[0])]
            d.line(pts,fill=strap_col,width=16); dm.line(pts,fill=255,width=16)
        else:
            for dx in (-0.24,0.24):
                pts=[(cA+dx*wA,yA-6),(cA+dx*wA*0.9,fit.at(0.42)[0])]
                d.line(pts,fill=strap_col,width=16); dm.line(pts,fill=255,width=16)
            yc=fit.at(0.30)[0]; d.line([(cA-wA*0.22,yc),(cA+wA*0.22,yc)],fill=strap_col,width=10); dm.line([(cA-wA*0.22,yc),(cA+wA*0.22,yc)],fill=255,width=10)
            buckle(d,cA,yc); dm.rectangle([cA-14,yc-11,cA+14,yc+11],fill=255)
            if style in ('tank1','tank2','closed'):                                                       # шланг и редуктор
                pts=[(cA+wA*0.3,yA-10),(cA+wA*0.2,fit.at(0.22)[0]),(cA+wA*0.05,fit.at(0.18)[0])]
                d.line(pts,fill=C(HOSE),width=10,joint='curve'); dm.line(pts,fill=255,width=10,joint='curve')
                gx,gy=cA+wA*0.05,fit.at(0.18)[0]; d.rounded_rectangle([gx-16,gy-12,gx+16,gy+12],radius=6,fill=C(METAL)); dm.rounded_rectangle([gx-16,gy-12,gx+16,gy+12],radius=6,fill=255)
            if style=='cooling':
                for dx in (-0.12,0.12):
                    pts=[(cA+dx*wA,yA),(cA+dx*wA*1.4,fit.at(0.45)[0])]
                    d.line(pts,fill=C(sec),width=8); dm.line(pts,fill=255,width=8)
    layer=grain(layer,seed)
    return finish(layer,mask,yA-40,(yB-yA)+80)

import suit_art4 as art
_WL=[(104,100,70),(72,80,52),(130,112,78),(52,48,36)]
PLOOK={'Bag':('woodland',_WL,(80,72,52),None),'Tourist':('solid',[(84,98,106)],(52,60,66),None),
       'Raid':('woodland',[(86,92,62),(62,70,46),(110,100,70),(46,46,34)],(70,76,52),None),
       'Frame':('solid',[(112,84,56)],(70,54,38),None),'Lead':('solid',[(120,124,126)],(80,84,86),None),
       'Medic':('solid',[(70,88,60)],(50,62,44),None),'Tank':('solid',[(150,154,156)],(60,60,60),None),
       'TwinTank':('solid',[(214,128,40)],(60,60,60),None),'ClosedCycle':('solid',[(220,220,214)],(80,140,190),None),
       'Cooling':('solid',[(70,76,82)],(60,130,180),None)}
for n,(k,en,ru,style,cols,*_r) in enumerate(ITEMS):
    path=f'{T}/{APP}/{k}/{k}'; os.makedirs(os.path.dirname(path),exist_ok=True)
    for body in ('Male','Female','Thin','Fat','Hulk'):
        for view in ('south','east','north'):
            art.render_pack(style,PLOOK[k],body,view,seed=n*17).save(f'{path}_{body}_{view}.png',optimize=True)
    c=art.render_pack(style,PLOOK[k],'Male','north',seed=n*17)
    bb=c.getchannel('A').getbbox(); side=max(bb[2]-bb[0],bb[3]-bb[1])+16; cx,cy=(bb[0]+bb[2])//2,(bb[1]+bb[3])//2
    box=(cx-side//2,cy-side//2,cx+side//2,cy+side//2); os.makedirs(f'{T}/Things/Item/SZ_Packs',exist_ok=True)
    c.crop(box).resize((128,128),Image.LANCZOS).save(f'{T}/Things/Item/SZ_Packs/{k}.png')
print('packs:',len(ITEMS))
