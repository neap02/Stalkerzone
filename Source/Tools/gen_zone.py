# Генератор XML для аномалий и артефактов: одна таблица -> Defs, патч, перевод.
import os
from xml.sax.saxutils import escape as esc
M='/mnt/user-data/outputs/StalkerZone/Common'
TEX='/mnt/user-data/outputs/StalkerZone/Common/Textures/Things'

# ---------------- Урон ----------------
# key, en label, ru label, hediff, armor, dmg, ap, fleck, sound, colorCenter, colorEdge, en death, ru death
DAMAGE=[
 # key, en, ru, ранение, категория защиты, урон, пробитие брони, эффект (XML-режим), звук, цвета, сообщения о смерти
 ('SZ_GravityCrushLight','gravitational blow','гравитационный удар','Crush','SZ_Strike',12,0.15,'BlastDry','SZ_Gravity_Discharge','(0.7, 0.5, 1.0)','(0.4, 0.2, 0.7)',
  '{0} was killed by a gravitational anomaly.','{0} погибает в гравитационной аномалии.'),
 ('SZ_GravityCrushHeavy','gravitational collapse','гравитационный коллапс','Crush','SZ_Strike',35,0.35,'BlastDry','SZ_Gravity_Discharge','(0.6, 0.4, 0.9)','(0.3, 0.15, 0.6)',
  '{0} was crushed by a gravitational collapse.','{0} раздавлен гравитационным коллапсом.'),
 ('SZ_GravityCrush','gravitational crush','гравитационное сдавливание','Crush','SZ_Strike',22,0.25,'BlastDry','SZ_Gravity_Discharge','(0.7, 0.5, 1.0)','(0.4, 0.2, 0.7)',
  '{0} was crushed by a gravitational anomaly.','{0} раздавлен гравитационной аномалией.'),
 ('SZ_GravityShred','gravitational shredding','гравитационный разрыв','Cut','SZ_Rupture',40,0.4,'BlastDry','SZ_Gravity_Discharge','(0.9, 0.2, 0.2)','(0.5, 0.05, 0.1)',
  '{0} was torn apart by an anomaly.','{0} разорван аномалией.'),
 ('SZ_ElectricDischarge','electric discharge','электрический разряд','Burn','SZ_Shock',18,0.3,'BlastEMP','SZ_Electro_Discharge','(0.6, 0.8, 1.0)','(0.3, 0.5, 1.0)',
  '{0} was killed by an anomalous electric discharge.','{0} погибает от разряда аномалии.'),
 ('SZ_ThermalBurn','anomalous heat','аномальный жар','Burn','SZ_Burn',22,0.3,'BlastFlame','SZ_Fire_Discharge','(1.0, 0.6, 0.2)','(0.8, 0.3, 0.1)',
  '{0} was burned alive by a thermal anomaly.','{0} сгорает в термической аномалии.'),
 ('SZ_CometBurn','fiery touch','огненное касание','Burn','SZ_Burn',14,0.25,'BlastFlame','SZ_Fire_Discharge','(1.0, 0.6, 0.2)','(0.8, 0.3, 0.1)',
  '{0} was burned by a comet.','{0} сгорает от кометы.'),
 ('SZ_ChemicalBurn','caustic splash','едкий всплеск','Burn','SZ_Chemical',16,0.2,'BlastDry','SZ_Acid_Discharge','(0.4, 1.0, 0.4)','(0.2, 0.6, 0.2)',
  '{0} was dissolved by a chemical anomaly.','{0} погибает в химической аномалии.'),
 ('SZ_FuzzSting','stinging fibers','жгучие волокна','Scratch','SZ_Chemical',9,0.1,'BlastDry','SZ_Fuzz_Discharge','(1.0, 0.95, 0.7)','(0.8, 0.75, 0.5)',
  '{0} was killed by stinging fibers.','{0} погибает от жгучих волокон.'),
]
# Категории защиты (DamageArmorCategoryDef в SZ_Protection.xml): подпись для описаний
CAT={'SZ_Strike':('strike','удар'),'SZ_Rupture':('rupture','разрыв'),'SZ_Shock':('electric shock','электрошок'),
     'SZ_Burn':('burn','ожог'),'SZ_Chemical':('chemical burn','химический ожог')}
DMG={d[0]:d for d in DAMAGE}
def dmg_line(key, ru=False):
    d=DMG[key]; cat=CAT[d[4]]
    if ru: return f' Урон: {d[5]} ({cat[1]}), пробитие брони {int(round(d[6]*100))}%.'
    return f' Damage: {d[5]} ({cat[0]}), armor penetration {int(round(d[6]*100))}%.'

# ---------------- Аномалии ----------------
# key, en, ru, texture, damage, radius, glow(r,g,b), drawSize, en desc, ru desc, group comment
SUF_EN=' Artifacts are sometimes found in or near it.'
SUF_RU=' В ней или рядом с ней иногда находят артефакты.'
ANOM=[
 ('Springboard','springboard','трамплин','Springboard','SZ_GravityCrushLight',1.5,(160,110,255),1.6,
  'A patch of air where dust hangs strangely still. Whatever steps into it is slammed by a short burst of gravity.',
  'Пятно воздуха, в котором пыль странно застыла на месте. Того, кто в него шагнёт, бьёт коротким всплеском гравитации.','гравитационная: слабый удар, маленький радиус'),
 ('Vortex','vortex','воронка','Vortex','SZ_GravityCrushHeavy',2.9,(150,120,220),2.2,
  'A wide swirl of leaves and debris circling a single point. It drags in anything within about five cells and crushes it at the center. A creature moving away can break free, especially right after a discharge.',
  'Широкий вихрь из листьев и мусора, кружащий вокруг одной точки. Затягивает всё в радиусе пяти клеток и сминает в центре. Тот, кто уходит прочь, может вырваться, особенно сразу после разряда.','гравитационная: сильный урон, большой радиус'),
 ('Whirligig','whirligig','карусель','Whirligig','SZ_GravityCrush',2.2,(120,140,255),2.0,
  'A spinning column of distorted air. It pulls in anything that comes too close, batters it and flings it aside. Moving away helps to break free.',
  'Вращающийся столб искажённого воздуха. Подтягивает всё, что подойдёт слишком близко, бьёт и отшвыривает. Чтобы вырваться, нужно уходить прочь.','гравитационная: средний урон и радиус'),
 ('Meatgrinder','meatgrinder','мясорубка','Meatgrinder','SZ_GravityShred',1.9,(220,60,60),1.8,
  'A small knot of twisted space, deadly to anything alive. It sucks in whatever comes near and tears it apart. Only quick retreat right after a discharge gives a chance to escape.',
  'Небольшой узел искривлённого пространства, смертельный для всего живого. Втягивает всё, что подойдёт близко, и разрывает. Шанс вырваться даёт только быстрый отход сразу после разряда.','гравитационная: резаные раны, очень опасна'),
 ('Electro','electro','электра','Electro','SZ_ElectricDischarge',2.9,(90,140,255),1.8,
  'A knot of crackling energy hanging just above the ground. Anything that touches it is hit by a powerful discharge.',
  'Сгусток потрескивающей энергии над самой землёй. Всё, что его касается, бьёт мощным разрядом.','электрическая: ожоги, большой радиус'),
 ('Burner','burner','жарка','Burner','SZ_ThermalBurn',2.4,(255,140,60),1.8,
  'A patch of shimmering, scorching air. When disturbed, it erupts in a column of fire.',
  'Пятно дрожащего раскалённого воздуха. Если его потревожить, оно взрывается столбом огня.','термическая: ванильный огонь, поджигает'),
 ('Comet','comet','комета','Comet','SZ_CometBurn',1.9,(255,150,70),1.6,
  'A fiery clot that drifts in a slow circle, scorching everything in its path.',
  'Огненный сгусток, медленно кружащий по одному и тому же маршруту и обжигающий всё на пути.','термическая: движется по кругу (только с C#)'),
 ('FruitPunch','fruit punch','холодец','FruitPunch','SZ_ChemicalBurn',2.2,(90,230,90),1.8,
  'A pool of glowing green ooze. It splashes caustic liquid on anyone nearby.',
  'Лужа светящейся зелёной жижи. Обдаёт едкой жидкостью всех, кто рядом.','химическая: ожоги'),
 ('BurntFuzz','burnt fuzz','жгучий пух','BurntFuzz','SZ_FuzzSting',3.5,(240,230,170),2.0,
  'Pale, hair-like strands hanging in the air. Touching them sends stinging fibers in every direction.',
  'Бледные волосовидные нити, свисающие в воздухе. Если их задеть, во все стороны летят жгучие волокна.','биологическая: слабые царапины, очень большой радиус'),
]

# ---------------- Артефакты ----------------

# Повадки типов аномалий -> поля StalkerZone.AnomalyDef (значения по умолчанию — в AnomalyDef.cs)
GD, GI = 'SZ_Gravity_Discharge', 'SZ_Gravity_Idle'
PROFILE={
 'Springboard': dict(triggerRadius=1.5, cooldownTicks=180, effectRadius=1.5, throwsInsteadOfDamage='true', throwDistance=5, stunTicks=90,
                     avoidRadius=2.5, fx='Gravity', sound=GD, idleSound=GI, fleck='Dust', fps=8),
 'Vortex':      dict(triggerRadius=1.5, cooldownTicks=600, effectRadius=1.9, pullRadius=4.9, pullInterval=60, pullStrength=0.8, avoidRadius=5.5,
                     fx='Gravity', sound=GD, idleSound=GI, fleck='Dust', clusterMin=2, clusterMax=3, memberSpacing=7, artifactChance=0.5, fps=8),
 'Whirligig':   dict(triggerRadius=1.5, cooldownTicks=360, effectRadius=1.9, pullRadius=2.9, pullInterval=60, pullStrength=0.6,
                     throwsAfterDischarge='true', throwDistance=4, stunTicks=60, avoidRadius=3.5,
                     fx='Gravity', sound=GD, idleSound=GI, fleck='Dust', clusterMax=5, memberSpacing=4, fps=12),
 'Meatgrinder': dict(triggerRadius=1.5, cooldownTicks=900, effectRadius=1.5, pullRadius=2.9, pullInterval=30, pullStrength=0.9, avoidRadius=3.5,
                     fx='Gravity', sound=GD, idleSound=GI, fleck='Dust', clusterMin=2, clusterMax=4, memberSpacing=4, fps=12),
 'Electro':     dict(triggerRadius=2.2, cooldownTicks=240, effectRadius=2.4, chainLightning='true', avoidRadius=3,
                     fx='Electric', sound='SZ_Electro_Discharge', idleSound='SZ_Electro_Idle', fleck='Sparks', fps=10),
 'Burner':      dict(triggerRadius=1.5, cooldownTicks=300, effectRadius=1.9, avoidRadius=2.5,
                     fx='Fire', sound='SZ_Fire_Discharge', idleSound='SZ_Fire_Idle', fleck='Heat', fps=10),
 'Comet':       dict(triggerRadius=0, moves='true', routeRadius=3, avoidRadius=4.9,
                     fx='Fire', sound='SZ_Fire_Discharge', idleSound='SZ_Fire_Idle', fleck='Heat',
                     clusterMin=1, clusterMax=2, memberSpacing=8, artifactChance=0.6, fps=10),
 'FruitPunch':  dict(triggerRadius=1.5, cooldownTicks=480, effectRadius=1.9, leavesPuddle='true', avoidRadius=2.5,
                     fx='Acid', sound='SZ_Acid_Discharge', idleSound='SZ_Acid_Idle', fleck='Air', fps=6),
 'BurntFuzz':   dict(triggerRadius=2.9, cooldownTicks=240, effectRadius=2.9, avoidRadius=3.5,
                     fx='Fuzz', sound='SZ_Fuzz_Discharge', fleck='Dust', clusterMax=5, memberSpacing=4, fps=6),
}
RARITY_W={'common':(0.185,1),'uncommon':(0.09,2),'rare':(0.04,3)}   # вес и класс детектора
RARITY={'common':('0.12~0.25','обычный'),'uncommon':('0.06~0.12','необычный'),'rare':('0.02~0.06','редкий')}
EXPO={'mild':'SZ_ArtifactExposure','strong':'SZ_ArtifactExposureStrong','none':None}
RAD_EN={'mild':' Emits weak radiation.','strong':' Emits strong radiation.','none':' Does not emit radiation.'}
RAD_RU={'mild':' Слабо излучает.','strong':' Сильно излучает.','none':' Не излучает.'}
# key, en, ru, anomaly, rarity, value, mass, offsets, exposure, en desc, ru desc
ART=[
 ('Jellyfish','jellyfish','медуза','Springboard','common',500,0.5,{'CarryingCapacity':25},'mild',
  'A translucent, gently pulsing mass that is lighter than it looks. Loads feel lighter to its wearer.',
  'Полупрозрачный, мягко пульсирующий комок, легче, чем кажется. Груз владельцу кажется легче.'),
 ('StoneFlower','stone flower','каменный цветок','Springboard','uncommon',900,0.5,{'PainShockThreshold':0.1,'MentalBreakThreshold':-0.03},'mild',
  'A stone growth shaped like an open flower. It steadies the nerves and dulls pain.',
  'Каменный нарост в форме раскрытого цветка. Успокаивает нервы и притупляет боль.'),
 ('Gravi','gravi','грави','Vortex','common',700,1,{'CarryingCapacity':40},'mild',
  'A dense, perfectly smooth sphere that seems to pull at the hand. It noticeably eases heavy loads.',
  'Плотный, идеально гладкий шар, будто тянущий руку вниз. Заметно облегчает тяжёлую ношу.'),
 ('NightStar','night star','ночная звезда','Vortex','uncommon',1300,0.5,{'CarryingCapacity':50,'MoveSpeed':0.1},'strong',
  'A star-shaped artifact that glimmers faintly in the dark. Its wearer is lighter on their feet and can carry far more.',
  'Артефакт в форме звезды, слабо мерцающий в темноте. Владелец легче на ногу и уносит куда больше.'),
 ('MamasBeads',"mama's beads",'мамины бусы','Whirligig','uncommon',1100,0.5,{'AimingDelayFactor':-0.15},'mild',
  "A string of hardened, bead-like growths. Its wearer's hands stay steady and aiming comes quicker.",
  'Нить затвердевших наростов, похожих на бусины. Руки владельца не дрожат, и целится он быстрее.'),
 ('Goldfish','goldfish','золотая рыбка','Whirligig','rare',2500,0.5,{'CarryingCapacity':80},'strong',
  'A rare golden artifact shaped like a small fish. Its wearer can carry enormous loads.',
  'Редкий золотистый артефакт в форме маленькой рыбки. Владелец может нести огромный груз.'),
 ('MeatChunk','meat chunk','ломоть мяса','Meatgrinder','common',500,0.5,{'InjuryHealingFactor':0.3,'MentalBreakThreshold':0.02},'mild',
  'An unpleasant, fleshy growth. It speeds up the healing of wounds, though its wearer feels uneasy.',
  'Неприятный мясистый нарост. Ускоряет заживление ран, хотя владельцу с ним не по себе.'),
 ('Soul','soul','душа','Meatgrinder','rare',3000,0.5,{'InjuryHealingFactor':1.0,'ImmunityGainSpeed':0.2},'strong',
  'A rare, warm artifact that seems almost alive. Wounds and illness fade from its wearer at an astonishing rate.',
  'Редкий тёплый артефакт, кажущийся почти живым. Раны и болезни отступают от владельца поразительно быстро.'),
 ('Flash','flash','вспышка','Electro','common',600,0.5,{'MoveSpeed':0.3},'mild',
  'A crackling cluster of blue crystals. Its wearer moves faster.',
  'Потрескивающая друза голубых кристаллов. Владелец двигается быстрее.'),
 ('Sparkler','sparkler','бенгальский огонь','Electro','common',600,0.5,{'WorkSpeedGlobal':0.08},'mild',
  'A brittle artifact that now and then throws off sparks. Work goes faster with it.',
  'Хрупкий артефакт, время от времени рассыпающий искры. С ним работа идёт быстрее.'),
 ('Battery','battery','батарейка','Electro','uncommon',1000,1,{'RestRateMultiplier':0.3,'MoveSpeed':0.15},'mild',
  'A heavy artifact that holds a constant faint charge. Sleep restores its wearer faster, and they move a little quicker.',
  'Тяжёлый артефакт с постоянным слабым зарядом. Владелец быстрее высыпается и двигается чуть быстрее.'),
 ('Moonlight','moonlight','лунный свет','Electro','rare',2200,0.5,{'PsychicSensitivity':-0.3,'MentalBreakThreshold':-0.05},'mild',
  'A rare, pale sphere with a soft glow. It dulls psychic influence and steadies the mind.',
  'Редкая бледная сфера с мягким свечением. Ослабляет психическое воздействие и успокаивает разум.'),
 ('Droplet','droplet','капля','Burner','common',700,0.5,{'SZ_RadiationResistance':0.3,'ComfyTemperatureMax':5},'none',
  'A glassy, teardrop-shaped artifact formed in intense heat. It seems to draw radiation away from its wearer.',
  'Стеклянистый артефакт в форме капли, рождённый в сильном жаре. Словно оттягивает радиацию от владельца.'),
 ('Fireball','fireball','огненный шар','Burner','uncommon',900,0.5,{'ComfyTemperatureMin':-25},'mild',
  'A stone that radiates steady warmth. Its wearer barely feels the cold.',
  'Камень, от которого идёт ровное тепло. Владелец почти не чувствует холода.'),
 ('Crystal','crystal','кристалл','Burner','rare',2200,0.5,{'ComfyTemperatureMin':-20,'ComfyTemperatureMax':20},'strong',
  'A rare faceted crystal born in fire. It shields its wearer from both heat and cold.',
  'Редкий гранёный кристалл, рождённый в огне. Защищает владельца и от жары, и от холода.'),
 ('Flame','flame','пламя','Comet','uncommon',1300,0.5,{'InjuryHealingFactor':0.5,'ComfyTemperatureMin':-10},'strong',
  'A flickering artifact that is warm to the touch. Wounds close faster on its wearer, and the cold bothers them less.',
  'Мерцающий артефакт, тёплый на ощупь. Раны владельца затягиваются быстрее, и холод его меньше беспокоит.'),
 ('Slime','slime','слизь','FruitPunch','common',500,0.5,{'ToxicResistance':0.3},'mild',
  'A slick, jelly-like artifact. It helps the body resist toxins.',
  'Скользкий, желеобразный артефакт. Помогает организму сопротивляться токсинам.'),
 ('Slug','slug','слизняк','FruitPunch','uncommon',900,0.5,{'ToxicResistance':0.5,'ImmunityGainSpeed':0.15},'mild',
  'A rubbery, slowly shifting lump. It strengthens resistance to toxins and disease.',
  'Упругий, медленно шевелящийся комок. Повышает устойчивость к токсинам и болезням.'),
 ('StoneBlood','stone blood','кровь камня','FruitPunch','uncommon',1000,1,{'InjuryHealingFactor':0.4,'ImmunityGainSpeed':0.1},'mild',
  'A dark red, porous stone. It speeds up the healing of wounds and helps fight disease.',
  'Тёмно-красный пористый камень. Ускоряет заживление ран и помогает бороться с болезнями.'),
 ('Thorn','thorn','колючка','BurntFuzz','common',500,0.5,{'PainShockThreshold':0.15,'MentalBreakThreshold':0.03},'mild',
  'A cluster of hard, needle-like spines. Its wearer shrugs off pain but grows irritable.',
  'Пучок твёрдых игловидных шипов. Владелец легко терпит боль, но становится раздражительным.'),
 ('Urchin','urchin','морской ёж','BurntFuzz','uncommon',1200,0.5,{'PainShockThreshold':0.25,'AimingDelayFactor':-0.1},'strong',
  'A round artifact covered in spines. Its wearer ignores pain and aims faster.',
  'Круглый артефакт, покрытый шипами. Владелец не замечает боли и целится быстрее.'),
]
STAT_RU={'CarryingCapacity':'грузоподъёмность','PainShockThreshold':'болевой порог','MentalBreakThreshold':'порог срыва (минус = лучше)',
 'MoveSpeed':'скорость','AimingDelayFactor':'время прицеливания (минус = быстрее)','InjuryHealingFactor':'заживление ран',
 'ImmunityGainSpeed':'иммунитет','WorkSpeedGlobal':'скорость работы','RestRateMultiplier':'восстановление сна',
 'PsychicSensitivity':'пси-чувствительность','SZ_RadiationResistance':'защита от радиации','ComfyTemperatureMax':'комфортная макс. t°',
 'ComfyTemperatureMin':'комфортная мин. t° (минус = теплее)','ToxicResistance':'сопротивление токсинам'}

# ---------- проверки целостности ----------
an_keys={a[0] for a in ANOM}; dmg_keys={d[0] for d in DAMAGE}
for a in ANOM: assert a[4] in dmg_keys, a; assert os.path.isdir(f'{TEX}/Building/SZ_Anomalies/{a[3]}'), a[3]; assert a[0] in PROFILE, a[0]
for r in ART:
    assert r[3] in an_keys, r; assert os.path.exists(f'{TEX}/Item/SZ_Artifacts/{r[0]}.png'), r[0]
for a in an_keys: assert any(r[3]==a for r in ART), a

# =============== SZ_Anomalies.xml ===============
o=[]; w=o.append
w('<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n')
w("""  <!-- Файл сгенерирован Source/Tools/gen_zone.py из одной таблицы.
       Аномалии по мотивам Зоны: названия узнаваемые, описания, баланс, текстуры и звуки свои. -->

  <!-- ================= УРОН АНОМАЛИЙ =================
       По одному DamageDef на тип аномалии. defaultDamage и defaultArmorPenetration —
       характеристики удара; armorCategory — какая защита от него спасает (SZ_Protection.xml). -->
  <DamageDef Name="SZ_AnomalyDamageBase" Abstract="True">
    <workerClass>DamageWorker_AddInjury</workerClass>
    <externalViolence>true</externalViolence>
    <combatLogRules>Damage_Bomb</combatLogRules>
  </DamageDef>
""")
for d in DAMAGE:
    k,en,ru,hed,arm,dmg,ap,fl,snd,cc,ce,den,dru=d
    w(f"""
  <DamageDef ParentName="SZ_AnomalyDamageBase">
    <defName>{k}</defName>
    <label>{esc(en)}</label>
    <deathMessage>{esc(den)}</deathMessage>
    <hediff>{hed}</hediff>
    <armorCategory>{arm}</armorCategory>       <!-- категория защиты -->
    <defaultDamage>{dmg}</defaultDamage>
    <defaultArmorPenetration>{ap}</defaultArmorPenetration>
  </DamageDef>
""")
w("""
  <!-- ================= ТИПЫ АНОМАЛИЙ =================
       StalkerZone.AnomalyDef — не вещь, а описание явления (C#: AnomalyDef.cs).
       Аномалии на карте — записи MapComponent_Zone: их нельзя выбрать, атаковать,
       перенести, купить или заспавнить как предмет. Рисует их сама Зона,
       при наведении курсора показывается подсказка с описанием и уроном.
       artifacts: какие артефакты прячутся рядом (weight — частота, tier — какой детектор найдёт). -->
""")
for a in ANOM:
    k,en,ru,tex,dmg,rad,glow,ds,den,dru,note=a
    P=PROFILE[k]
    arts=[r for r in ART if r[3]==k]
    per10k=round(sum(RARITY_W[r[4]][0] for r in arts),3)
    gc=f'({glow[0]/255:.2f}, {glow[1]/255:.2f}, {glow[2]/255:.2f}, 0.45)'
    w(f"""
  <!-- {ru.capitalize()}: {note} -->
  <StalkerZone.AnomalyDef>
    <defName>SZ_Anomaly_{k}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den+dmg_line(dmg)+SUF_EN)}</description>
    <texPath>Things/Building/SZ_Anomalies/{tex}</texPath>
    <drawSize>{ds}</drawSize>
    <glowColor>{gc}</glowColor>
    <glowSize>{round(ds*1.8,1)}</glowSize>
    <damage>{dmg}</damage>
    <per10k>{per10k}</per10k>
""")
    for key,val in P.items():
        w(f'    <{key}>{val}</{key}>\n')
    w('    <artifacts>\n')
    for r in arts:
        wt,tier=RARITY_W[r[4]]
        w(f'      <li><artifact>SZ_Artifact_{r[0]}</artifact><weight>{wt}</weight><tier>{tier}</tier></li>   <!-- {r[2]}, {RARITY[r[4]][1]} -->\n')
    w('    </artifacts>\n  </StalkerZone.AnomalyDef>\n')
w('\n</Defs>\n')
open(f'{M}/Defs/Anomalies/SZ_Anomalies.xml','w',encoding='utf-8').write(''.join(o))

# =============== SZ_Artifacts.xml ===============
o=[]; w=o.append
w('''<?xml version="1.0" encoding="utf-8"?>
<Defs>

  <!-- Своя категория в складах: внутри "Одежды", т.к. артефакт носится на поясе -->
  <ThingCategoryDef>
    <defName>SZ_Artifacts</defName>
    <label>artifacts</label>
    <parent>Apparel</parent>
  </ThingCategoryDef>

  <!-- Свой слой одежды для артефакта: занимает пояс, но не конфликтует
       с поясными вещами (детектор, щит-пояс). Один артефакт за раз. -->
  <ApparelLayerDef>
    <defName>SZ_ArtifactLayer</defName>
    <label>artifact</label>
    <drawOrder>350</drawOrder>
  </ApparelLayerDef>

  <!-- ================= ОБЛУЧЕНИЕ ОТ АРТЕФАКТА =================
       Появляется, пока артефакт на поясе (CompProperties_CauseHediff_Apparel),
       и исчезает, когда его снимают (HediffCompProperties_RemoveIfApparelDropped).
       Растёт, пока артефакт надет. Антирад снижает (makeImmuneTo в SZ_AntiradEffect).
       Не смертельно: максимум 1.0, но на высоких стадиях сильные штрафы и риск рака. -->
  <HediffDef Name="SZ_ArtifactExposureBase" Abstract="True">
    <hediffClass>HediffWithComps</hediffClass>
    <defaultLabelColor>(0.95, 0.75, 0.3)</defaultLabelColor>
    <isBad>true</isBad>
    <initialSeverity>0.01</initialSeverity>
    <maxSeverity>1</maxSeverity>
    <comps>
      <li Class="HediffCompProperties_RemoveIfApparelDropped"/>
    </comps>
    <stages>
      <li>
        <label>faint</label>
      </li>
      <li>
        <label>minor</label>
        <minSeverity>0.25</minSeverity>
        <capMods>
          <li><capacity>Consciousness</capacity><offset>-0.05</offset></li>
        </capMods>
      </li>
      <li>
        <label>moderate</label>
        <minSeverity>0.5</minSeverity>
        <vomitMtbDays>4</vomitMtbDays>
        <capMods>
          <li><capacity>Consciousness</capacity><offset>-0.1</offset></li>
          <li><capacity>BloodFiltration</capacity><offset>-0.1</offset></li>
        </capMods>
      </li>
      <li>
        <label>serious</label>
        <minSeverity>0.8</minSeverity>
        <vomitMtbDays>1</vomitMtbDays>
        <painOffset>0.1</painOffset>
        <capMods>
          <li><capacity>Consciousness</capacity><offset>-0.2</offset></li>
          <li><capacity>BloodFiltration</capacity><offset>-0.2</offset></li>
          <li><capacity>Moving</capacity><offset>-0.1</offset></li>
        </capMods>
        <hediffGivers>
          <li Class="HediffGiver_Random">
            <hediff>Carcinoma</hediff>
            <mtbDays>150</mtbDays>
            <canAffectAnyLivePart>true</canAffectAnyLivePart>
          </li>
        </hediffGivers>
      </li>
    </stages>
  </HediffDef>

  <!-- Слабое излучение: до тяжёлой стадии ~16 дней -->
  <HediffDef ParentName="SZ_ArtifactExposureBase">
    <defName>SZ_ArtifactExposure</defName>
    <label>artifact exposure</label>
    <description>Radiation from an artifact worn on the body. Grows while the artifact is worn and disappears once it is taken off. Anti-rad reduces it.</description>
    <comps>
      <li Class="HediffCompProperties_Immunizable">
        <severityPerDayNotImmune>0.05</severityPerDayNotImmune>
        <severityPerDayImmune>-0.3</severityPerDayImmune>
      </li>
    </comps>
  </HediffDef>

  <!-- Сильное излучение: до тяжёлой стадии ~5 дней -->
  <HediffDef ParentName="SZ_ArtifactExposureBase">
    <defName>SZ_ArtifactExposureStrong</defName>
    <label>strong artifact exposure</label>
    <description>Intense radiation from a powerful artifact worn on the body. Grows quickly while the artifact is worn and disappears once it is taken off. Anti-rad reduces it.</description>
    <comps>
      <li Class="HediffCompProperties_Immunizable">
        <severityPerDayNotImmune>0.15</severityPerDayNotImmune>
        <severityPerDayImmune>-0.3</severityPerDayImmune>
      </li>
    </comps>
  </HediffDef>

  <!-- ================= БАЗА АРТЕФАКТА =================
       Артефакт = предмет одежды на поясе в своём слое SZ_ArtifactLayer, один за раз.
       Бонусы даёт equippedStatOffsets, облучение — CompProperties_CauseHediff_Apparel. -->
  <ThingDef ParentName="ApparelBase" Name="SZ_ArtifactBase" Abstract="True">
    <thingCategories Inherit="False">
      <li>SZ_Artifacts</li>
    </thingCategories>
    <techLevel>Ultra</techLevel>
    <tradeability>All</tradeability>
    <smeltable>false</smeltable>
    <statBases>
      <MaxHitPoints>200</MaxHitPoints>
      <Flammability>0</Flammability>
      <DeteriorationRate>0</DeteriorationRate>  <!-- не портится на улице -->
      <EquipDelay>1</EquipDelay>
    </statBases>
    <thingSetMakerTags>
      <li>RewardStandardLowFreq</li>             <!-- могут выпадать наградой за квесты -->
    </thingSetMakerTags>
    <apparel>
      <layers>
        <li>SZ_ArtifactLayer</li>
      </layers>
      <bodyPartGroups>
        <li>Waist</li>
      </bodyPartGroups>
      <countsAsClothingForNudity>false</countsAsClothingForNudity>
      <careIfWornByCorpse>false</careIfWornByCorpse>
      <careIfDamaged>false</careIfDamaged>
      <wearPerDay>0</wearPerDay>                 <!-- не изнашивается -->
    </apparel>
  </ThingDef>
''')
for a in ANOM:
    w(f'\n  <!-- ============ Из аномалии «{a[2]}» ============ -->\n')
    for r in ART:
        if r[3]!=a[0]: continue
        k,en,ru,an,rar,val,mass,offs,exp,den,dru=r
        offs_xml=''.join(f'      <{s}>{v}</{s}>{"  <!-- "+STAT_RU[s]+" -->"}\n' for s,v in offs.items())
        comp='' if EXPO[exp] is None else f'''    <comps>
      <li Class="CompProperties_CauseHediff_Apparel">
        <hediff>{EXPO[exp]}</hediff>
      </li>
    </comps>
'''
        w(f'''  <ThingDef ParentName="SZ_ArtifactBase">   <!-- {ru}, {RARITY[rar][1]} -->
    <defName>SZ_Artifact_{k}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den+RAD_EN[exp])}</description>
    <graphicData>
      <texPath>Things/Item/SZ_Artifacts/{k}</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
    <statBases>
      <MarketValue>{val}</MarketValue>
      <Mass>{mass}</Mass>
    </statBases>
    <equippedStatOffsets>
{offs_xml}    </equippedStatOffsets>
{comp}  </ThingDef>
''')
w('\n</Defs>\n')
open(f'{M}/Defs/Artifacts/SZ_Artifacts.xml','w',encoding='utf-8').write(''.join(o))

# =============== Патч генерации карты ===============
# Не нужен: аномалии ставит C# (MapComponent_Zone), а не генерация карты.
_p=f'{M}/Patches/SZ_MapGen.xml'
if os.path.exists(_p): os.remove(_p)

# =============== Перевод ===============
L=f'{M}/Languages/Russian/DefInjected'
o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for d in DAMAGE:
    o.append(f'  <{d[0]}.label>{esc(d[2])}</{d[0]}.label>\n  <{d[0]}.deathMessage>{esc(d[12])}</{d[0]}.deathMessage>\n')
o.append('</LanguageData>\n'); open(f'{L}/DamageDef/SZ_Anomalies.xml','w',encoding='utf-8').write(''.join(o))

o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for a in ANOM:
    dn=f'SZ_Anomaly_{a[0]}'
    o.append(f'  <{dn}.label>{esc(a[2])}</{dn}.label>\n  <{dn}.description>{esc(a[9]+dmg_line(a[4],True)+SUF_RU)}</{dn}.description>\n')
o.append('</LanguageData>\n')
os.makedirs(f'{L}/StalkerZone.AnomalyDef', exist_ok=True)
open(f'{L}/StalkerZone.AnomalyDef/SZ_Anomalies.xml','w',encoding='utf-8').write(''.join(o))
_old=f'{L}/ThingDef/SZ_Anomalies.xml'
if os.path.exists(_old): os.remove(_old)

o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for r in ART:
    dn=f'SZ_Artifact_{r[0]}'
    o.append(f'  <{dn}.label>{esc(r[2])}</{dn}.label>\n  <{dn}.description>{esc(r[10]+RAD_RU[r[8]])}</{dn}.description>\n')
o.append('</LanguageData>\n'); open(f'{L}/ThingDef/SZ_Artifacts.xml','w',encoding='utf-8').write(''.join(o))

print(f'anomaly types: {len(ANOM)}, variants/artifacts: {len(ART)}, damage defs: {len(DAMAGE)}')
