# Генератор фракций Зоны: одна таблица -> FactionDef, PawnKindDef, перевод, эмблемы.
# Названия узнаваемые, описания, звания, баланс и эмблемы свои (эмблемы игр не копируются).
import math, os
from xml.sax.saxutils import escape as esc
from PIL import Image, ImageDraw, ImageFilter

M = '/mnt/user-data/outputs/StalkerZone/Common'
L = f'{M}/Languages/Russian/DefInjected'

# ---------- Звания: (ключ, вес в бою, сила, оружие $, одежда $, теги оружия, теги одежды, лидер) ----------
RANKS = {
 'Rookie':  dict(power=45,  weapon='150~300', apparel='150~400',  wtags=['SimpleGun','Gun'],
                 atags=['IndustrialBasic'], heal='0.4~1.2', resist=(8,14), will=(0,1)),
 'Fighter': dict(power=75,  weapon='250~500', apparel='400~900',  wtags=['Gun'],
                 atags=['IndustrialBasic','IndustrialMilitaryBasic'], heal='0.6~1.5', resist=(13,20), will=(1,2)),
 'Veteran': dict(power=120, weapon='500~900', apparel='900~1800', wtags=['IndustrialGunAdvanced','SniperRifle'],
                 atags=['IndustrialMilitaryBasic','IndustrialMilitaryAdvanced'], heal='0.8~1.8', bionics=True, resist=(18,28), will=(2,4)),
 'Leader':  dict(power=140, weapon='600~1000', apparel='1200~2200', wtags=['IndustrialGunAdvanced'],
                 atags=['IndustrialMilitaryAdvanced','IndustrialAdvanced'], heal='1~2', bionics=True, leader=True, resist=(25,35), will=(3,5)),
}

# ---------- Фракции ----------
# key, en/ru название, en/ru описание, en/ru бойцы (ед./мн.), en/ru звания (4), en/ru лидер,
# цвета, отношение, торговля, доп. теги оружия ветеранов, веса (новичок, боец, ветеран), эмблема
F = [
 dict(key='Loners', en='Loners', ru='Одиночки',
  den='Unaffiliated stalkers who come to the Zone alone or in small groups, chasing artifacts and a living. They trade with anyone who does not shoot first.',
  dru='Сталкеры без группировки: приходят в Зону поодиночке или малыми группами за артефактами и заработком. Торгуют со всеми, кто не стреляет первым.',
  pawn=('stalker','stalkers','сталкер','сталкеры'),
  ranks=(('rookie stalker','новичок'),('stalker','сталкер'),('veteran stalker','бывалый сталкер'),('old-timer','старожил')),
  leader=('old-timer','старожил'),
  colors=[(0.62,0.48,0.25),(0.75,0.62,0.30)], relation='neutral', trade=True, vtags=[], weights=(6,8,3), icon='compass'),
 dict(key='Duty', en='Duty', ru='Долг',
  den='A disciplined paramilitary order that sees the Zone as a threat to be contained and destroyed. Strict ranks, heavy weapons and little patience for anarchists.',
  dru='Дисциплинированный военизированный орден: Зона для него — угроза, которую нужно сдержать и уничтожить. Строгая иерархия, тяжёлое оружие и никакого терпения к анархистам.',
  pawn=('Duty fighter','Duty fighters','боец Долга','бойцы Долга'),
  ranks=(('Duty recruit','новобранец Долга'),('Duty fighter','боец Долга'),('Duty veteran','ветеран Долга'),('Duty general','генерал Долга')),
  leader=('general','генерал'),
  colors=[(0.45,0.08,0.08),(0.30,0.05,0.05)], relation='neutral', trade=True, vtags=['GunHeavy'], weights=(3,8,5), icon='shield'),
 dict(key='Freedom', en='Freedom', ru='Свобода',
  den='Free-spirited anarchists who believe the Zone belongs to everyone. Relaxed in camp, dangerous in a fight, and sworn rivals of Duty.',
  dru='Вольные анархисты, уверенные, что Зона принадлежит всем. Расслаблены в лагере, опасны в бою и давние соперники Долга.',
  pawn=('Freedom fighter','Freedom fighters','боец Свободы','бойцы Свободы'),
  ranks=(('Freedom newcomer','новичок Свободы'),('Freedom fighter','боец Свободы'),('Freedom veteran','ветеран Свободы'),('Freedom leader','лидер Свободы')),
  leader=('leader','лидер'),
  colors=[(0.20,0.45,0.18),(0.30,0.60,0.25)], relation='neutral', trade=True, vtags=[], weights=(4,8,4), icon='wing'),
 dict(key='Bandits', en='Bandits', ru='Бандиты',
  den='Gangs of thugs who prey on stalkers: ambushes, robbery and protection rackets. You can buy their goods, if you can stomach the prices.',
  dru='Шайки головорезов, промышляющие за счёт сталкеров: засады, грабежи и поборы. У них можно купить товар, если выдержите цены.',
  pawn=('bandit','bandits','бандит','бандиты'),
  ranks=(('thug','шестёрка'),('bandit','бандит'),('gang enforcer','громила'),('gang boss','главарь')),
  leader=('boss','главарь'),
  colors=[(0.15,0.15,0.15),(0.30,0.28,0.25)], relation='hostile', trade=True, vtags=[], weights=(8,6,2), icon='blades'),
 dict(key='Military', en='Military', ru='Военные',
  den='Government troops guarding the cordon around the Zone. Well armed and organised, they shoot trespassers on sight.',
  dru='Правительственные войска, охраняющие кордон вокруг Зоны. Хорошо вооружены и организованы, нарушителей расстреливают без предупреждения.',
  pawn=('soldier','soldiers','солдат','солдаты'),
  ranks=(('private','рядовой'),('soldier','солдат'),('sergeant','сержант'),('officer','офицер')),
  leader=('commander','командир'),
  colors=[(0.30,0.34,0.18),(0.40,0.42,0.25)], relation='hostile', trade=False, vtags=['GunHeavy'], weights=(4,8,5), icon='star'),
 dict(key='Monolith', en='Monolith', ru='Монолит',
  den='Fanatics from the heart of the Zone who serve something they call the Monolith. They do not negotiate, do not retreat and attack everyone.',
  dru='Фанатики из сердца Зоны, служащие тому, что они называют Монолитом. Не ведут переговоров, не отступают и нападают на всех.',
  pawn=('Monolith fanatic','Monolith fanatics','фанатик Монолита','фанатики Монолита'),
  ranks=(('Monolith acolyte','послушник Монолита'),('Monolith fighter','боец Монолита'),('Monolith zealot','ревнитель Монолита'),('Monolith preacher','проповедник Монолита')),
  leader=('preacher','проповедник'),
  colors=[(0.75,0.75,0.72),(0.55,0.58,0.60)], fanatic=1.5, relation='enemy', trade=False, vtags=['GunHeavy'], weights=(2,8,6), icon='shard'),
 dict(key='Mercenaries', en='Mercenaries', ru='Наёмники',
  den='Professional soldiers of fortune working for whoever pays. Excellent equipment, cold calculation, no questions asked.',
  dru='Профессиональные солдаты удачи, работающие на того, кто платит. Отличное снаряжение, холодный расчёт и никаких лишних вопросов.',
  pawn=('mercenary','mercenaries','наёмник','наёмники'),
  ranks=(('hired gun','стрелок'),('mercenary','наёмник'),('mercenary specialist','специалист'),('mercenary commander','командир наёмников')),
  leader=('commander','командир'),
  colors=[(0.15,0.25,0.45),(0.25,0.35,0.55)], relation='neutral', trade=True, vtags=[], weights=(2,6,6), icon='crosshair'),
 dict(key='Scientists', en='Scientists', ru='Учёные',
  den='Researchers studying anomalies and artifacts from fortified camps. Poorly armed, but pay well for samples and sell rare equipment.',
  dru='Исследователи, изучающие аномалии и артефакты из укреплённых лагерей. Вооружены слабо, но хорошо платят за образцы и продают редкое снаряжение.',
  pawn=('scientist','scientists','учёный','учёные'),
  ranks=(('lab assistant','лаборант'),('scientist','научный сотрудник'),('expedition guard','охранник экспедиции'),('chief researcher','руководитель исследований')),
  leader=('chief researcher','руководитель исследований'),
  colors=[(0.85,0.50,0.15),(0.95,0.95,0.92)], relation='neutral', trade=True, vtags=[], weights=(8,4,3), icon='atom'),
]
RANK_KEYS = ['Rookie','Fighter','Veteran','Leader']

# ---------- XML ----------
o=[]; w=o.append
w('''<?xml version="1.0" encoding="utf-8"?>
<Defs>

  <!-- Файл сгенерирован Source/Tools/gen_factions.py.
       Фракции Зоны. Наследуют ванильную основу фракций-поселенцев (OutlanderFactionBase):
       культура, предыстории, поселения и прочее берутся из неё, а отряды, отношение,
       торговля, цвета и эмблема — свои.

       ЗАДЕЛ ПОД КОСТЮМЫ: у каждой фракции свой тег одежды SZ_Faction_[Фракция]
       (в apparelTags её бойцов). Достаточно дать будущему костюму этот тег:
         <apparel><tags><li>SZ_Faction_Duty</li></tags></apparel>
       и бойцы фракции начнут в нём появляться. -->

  <!-- ===== Общая основа бойца Зоны ===== -->
  <PawnKindDef Name="SZ_StalkerBase" Abstract="True">
    <race>Human</race>
    <isFighter>true</isFighter>
    <itemQuality>Normal</itemQuality>
    <apparelAllowHeadgearChance>0.7</apparelAllowHeadgearChance>
    <chemicalAddictionChance>0.05</chemicalAddictionChance>
    <invNutrition>2.55</invNutrition>
    <!-- В карманах: серебро, лекарство или антирад -->
    <inventoryOptions>
      <skipChance>0.5</skipChance>
      <subOptionsChooseOne>
        <li><thingDef>Silver</thingDef><countRange>30~150</countRange></li>
        <li><thingDef>MedicineIndustrial</thingDef><countRange>1~2</countRange></li>
        <li><thingDef>SZ_Antirad</thingDef><countRange>1~3</countRange></li>
      </subOptionsChooseOne>
    </inventoryOptions>
  </PawnKindDef>
''')

def li(items): return ''.join(f'<li>{x}</li>' for x in items)

for f in F:
    k=f['key']; fd=f'SZ_Faction_{k}'
    w(f'\n  <!-- ================= {f["ru"].upper()} ================= -->\n')
    for i,rk in enumerate(RANK_KEYS):
        R=RANKS[rk]; en,ru=f['ranks'][i]
        wt=R['wtags']+(f['vtags'] if rk in ('Veteran','Leader') else [])
        at=R['atags']+[f'SZ_Faction_{k}']
        bion='' if not R.get('bionics') else '''    <techHediffsChance>0.15</techHediffsChance>
    <techHediffsMoney>300~900</techHediffsMoney>
    <techHediffsTags><li>Simple</li><li>Advanced</li></techHediffsTags>
'''
        lead='    <factionLeader>true</factionLeader>\n' if R.get('leader') else ''
        k_f=f.get('fanatic',1.0)
        res=f"{R['resist'][0]*k_f:g}~{R['resist'][1]*k_f:g}"; wil=f"{R['will'][0]*k_f:g}~{R['will'][1]*k_f:g}"
        w(f'''  <PawnKindDef ParentName="SZ_StalkerBase">
    <defName>SZ_{k}_{rk}</defName>
    <label>{esc(en)}</label>
    <defaultFactionType>{fd}</defaultFactionType>
{lead}    <combatPower>{R["power"]}</combatPower>
    <gearHealthRange>{R["heal"]}</gearHealthRange>
    <weaponMoney>{R["weapon"]}</weaponMoney>
    <weaponTags>{li(wt)}</weaponTags>
    <apparelMoney>{R["apparel"]}</apparelMoney>
    <apparelTags>{li(at)}</apparelTags>
    <initialResistanceRange>{res}</initialResistanceRange>   <!-- сопротивление вербовке -->
    <initialWillRange>{wil}</initialWillRange>               <!-- воля (обращение в рабство) -->
{bion}  </PawnKindDef>
''')
    rel={'neutral':'','hostile':'    <naturalEnemy>true</naturalEnemy>          <!-- враждебны с начала, но можно помириться -->\n',
         'enemy':'    <permanentEnemy>true</permanentEnemy>      <!-- вечные враги -->\n'}[f['relation']]
    colors=''.join(f'<li>({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f})</li>' for c in f['colors'])
    wr,wf,wv=f['weights']
    combat=f'<SZ_{k}_Rookie>{wr}</SZ_{k}_Rookie><SZ_{k}_Fighter>{wf}</SZ_{k}_Fighter><SZ_{k}_Veteran>{wv}</SZ_{k}_Veteran><SZ_{k}_Leader>1</SZ_{k}_Leader>'
    trade_group='' if not f['trade'] else f'''      <li>
        <kindDef>Trader</kindDef>
        <traders><Town_Trader>1</Town_Trader></traders>
        <carriers><Muffalo>6</Muffalo><Dromedary>5</Dromedary></carriers>
        <guards><SZ_{k}_Fighter>8</SZ_{k}_Fighter><SZ_{k}_Veteran>3</SZ_{k}_Veteran></guards>
      </li>
'''
    no_trade='' if f['trade'] else '''    <caravanTraderKinds Inherit="False" />     <!-- не торгуют -->
    <visitorTraderKinds Inherit="False" />
    <baseTraderKinds Inherit="False" />
'''
    w(f'''
  <FactionDef ParentName="OutlanderFactionBase">
    <defName>{fd}</defName>
    <label>{esc(f["en"].lower())}</label>
    <fixedName>{esc(f["en"])}</fixedName>
    <description>{esc(f["den"])}</description>
    <pawnSingular>{esc(f["pawn"][0])}</pawnSingular>
    <pawnsPlural>{esc(f["pawn"][1])}</pawnsPlural>
    <leaderTitle>{esc(f["leader"][0])}</leaderTitle>
    <factionIconPath>World/SZ_Factions/{k}</factionIconPath>
    <colorSpectrum Inherit="False">{colors}</colorSpectrum>
    <requiredCountAtGameStart>0</requiredCountAtGameStart>   <!-- можно убрать при создании мира -->
    <maxCountAtGameStart>1</maxCountAtGameStart>
    <canMakeRandomly>false</canMakeRandomly>                <!-- одна такая фракция на мир -->
    <basicMemberKind>SZ_{k}_Fighter</basicMemberKind>
{rel}{no_trade}    <pawnGroupMakers Inherit="False">
      <!-- Набеги и бои -->
      <li>
        <kindDef>Combat</kindDef>
        <options>{combat}</options>
      </li>
      <!-- Гости -->
      <li>
        <kindDef>Peaceful</kindDef>
        <options><SZ_{k}_Rookie>6</SZ_{k}_Rookie><SZ_{k}_Fighter>4</SZ_{k}_Fighter></options>
      </li>
{trade_group}      <!-- Защитники поселения -->
      <li>
        <kindDef>Settlement</kindDef>
        <options><SZ_{k}_Rookie>{wr}</SZ_{k}_Rookie><SZ_{k}_Fighter>{wf}</SZ_{k}_Fighter><SZ_{k}_Veteran>{wv}</SZ_{k}_Veteran><SZ_{k}_Leader>1</SZ_{k}_Leader></options>
      </li>
    </pawnGroupMakers>
  </FactionDef>
''')
w('\n</Defs>\n')
open(f'{M}/Defs/Factions/SZ_Factions.xml','w',encoding='utf-8').write(''.join(o))

# ---------- Перевод ----------
os.makedirs(f'{L}/FactionDef', exist_ok=True); os.makedirs(f'{L}/PawnKindDef', exist_ok=True)
o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for f in F:
    d=f'SZ_Faction_{f["key"]}'
    o.append(f'''
  <{d}.label>{esc(f["ru"].lower())}</{d}.label>
  <{d}.fixedName>{esc(f["ru"])}</{d}.fixedName>
  <{d}.description>{esc(f["dru"])}</{d}.description>
  <{d}.pawnSingular>{esc(f["pawn"][2])}</{d}.pawnSingular>
  <{d}.pawnsPlural>{esc(f["pawn"][3])}</{d}.pawnsPlural>
  <{d}.leaderTitle>{esc(f["leader"][1])}</{d}.leaderTitle>
''')
o.append('</LanguageData>\n'); open(f'{L}/FactionDef/SZ_Factions.xml','w',encoding='utf-8').write(''.join(o))
o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for f in F:
    for i,rk in enumerate(RANK_KEYS):
        o.append(f'  <SZ_{f["key"]}_{rk}.label>{esc(f["ranks"][i][1])}</SZ_{f["key"]}_{rk}.label>\n')
o.append('</LanguageData>\n'); open(f'{L}/PawnKindDef/SZ_Factions.xml','w',encoding='utf-8').write(''.join(o))

# ---------- Эмблемы: белые силуэты (игра красит их в цвет фракции) ----------
N=128; C=N/2; WH=(255,255,255,255)
def icon(kind):
    img=Image.new('RGBA',(N,N),(0,0,0,0)); d=ImageDraw.Draw(img)
    if kind=='compass':      # путник: кольцо и стрелка
        d.ellipse([12,12,116,116],outline=WH,width=10)
        d.polygon([(C,20),(C+14,C),(C,C-6),(C-14,C)],fill=WH); d.polygon([(C,108),(C+10,C),(C-10,C)],fill=(255,255,255,140))
    elif kind=='shield':     # щит с тремя полосами
        d.polygon([(20,16),(108,16),(108,64),(C,116),(20,64)],fill=WH)
        for y in (34,52,70): d.rectangle([34,y,94,y+8],fill=(0,0,0,0))
    elif kind=='wing':       # птица в полёте: два изогнутых крыла и тело
        d.polygon([(C,70),(14,30),(26,58),(C-8,86)],fill=WH)
        d.polygon([(C,70),(114,30),(102,58),(C+8,86)],fill=WH)
        d.ellipse([C-9,60,C+9,100],fill=WH)
        d.ellipse([10,10,118,118],outline=WH,width=6)
    elif kind=='blades':     # два скрещённых клинка
        for s in (1,-1):
            pts=[(C-s*42,20),(C-s*30,20),(C+s*44,104),(C+s*34,108)]
            d.polygon(pts,fill=WH)
        d.ellipse([C-10,C-10,C+10,C+10],fill=WH)
    elif kind=='star':       # звезда в круге
        d.ellipse([10,10,118,118],outline=WH,width=8); pts=[]
        for i in range(10):
            a=-math.pi/2+i*math.pi/5; r=44 if i%2==0 else 18; pts.append((C+math.cos(a)*r,C+math.sin(a)*r))
        d.polygon(pts,fill=WH)
    elif kind=='shard':      # высокий кристалл с лучами
        d.polygon([(C,8),(C+18,40),(C+12,120),(C-12,120),(C-18,40)],fill=WH)
        for a in (-0.6,-0.3,0.3,0.6):
            d.line([(C,40),(C+math.sin(a)*60,40-math.cos(a)*30)],fill=WH,width=4)
    elif kind=='crosshair':  # прицел в ромбе
        d.polygon([(C,8),(120,C),(C,120),(8,C)],outline=WH,width=8)
        d.ellipse([C-24,C-24,C+24,C+24],outline=WH,width=6)
        for (x1,y1,x2,y2) in ((C,28,C,50),(C,78,C,100),(28,C,50,C),(78,C,100,C)): d.line([(x1,y1),(x2,y2)],fill=WH,width=6)
    elif kind=='atom':       # орбиты и ядро
        for ang in (0,60,120):
            e=Image.new('RGBA',(N,N),(0,0,0,0)); ed=ImageDraw.Draw(e); ed.ellipse([8,C-20,120,C+20],outline=WH,width=6)
            img.alpha_composite(e.rotate(ang,resample=Image.BICUBIC,center=(C,C)))
        d.ellipse([C-12,C-12,C+12,C+12],fill=WH)
    return img
for f in F:
    icon(f['icon']).save(f'{M}/Textures/World/SZ_Factions/{f["key"]}.png')
print('factions:', len(F), 'pawnkinds:', len(F)*4)
