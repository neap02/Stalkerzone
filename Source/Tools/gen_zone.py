# Генератор XML для аномалий и артефактов: одна таблица -> Defs, патч, перевод.
import os
from xml.sax.saxutils import escape as esc
M='/mnt/user-data/outputs/StalkerZone/Common'
TEX='/mnt/user-data/outputs/StalkerZone/Common/Textures/Things'

# ---------------- Урон ----------------
# key, en label, ru label, hediff, armor, dmg, ap, fleck, sound, colorCenter, colorEdge, en death, ru death
DAMAGE=[
 ('SZ_ElectricDischarge','electric discharge','электрический разряд','Burn','Heat',14,0.3,'BlastEMP','SZ_Electro_Discharge','(0.6, 0.8, 1.0)','(0.3, 0.5, 1.0)',
  '{0} was killed by an anomalous electric discharge.','{0} погибает от разряда аномалии.'),
 ('SZ_GravityCrushLight','gravitational blow','гравитационный удар','Crush','Blunt',10,0.15,'BlastDry','SZ_Gravity_Discharge','(0.7, 0.5, 1.0)','(0.4, 0.2, 0.7)',
  '{0} was killed by a gravitational anomaly.','{0} погибает в гравитационной аномалии.'),
 ('SZ_GravityCrush','gravitational crush','гравитационное сдавливание','Crush','Blunt',18,0.2,'BlastDry','SZ_Gravity_Discharge','(0.7, 0.5, 1.0)','(0.4, 0.2, 0.7)',
  '{0} was crushed by a gravitational anomaly.','{0} раздавлен гравитационной аномалией.'),
 ('SZ_GravityCrushHeavy','gravitational collapse','гравитационный коллапс','Crush','Blunt',24,0.3,'BlastDry','SZ_Gravity_Discharge','(0.6, 0.4, 0.9)','(0.3, 0.15, 0.6)',
  '{0} was crushed by a gravitational collapse.','{0} раздавлен гравитационным коллапсом.'),
 ('SZ_GravityShred','gravitational shredding','гравитационный разрыв','Cut','Sharp',30,0.35,'BlastDry','SZ_Gravity_Discharge','(0.9, 0.2, 0.2)','(0.5, 0.05, 0.1)',
  '{0} was torn apart by an anomaly.','{0} разорван аномалией.'),
 ('SZ_ThermalBurn','anomalous heat','аномальный жар','Burn','Heat',16,0.25,'BlastFlame','SZ_Fire_Discharge','(1.0, 0.6, 0.2)','(0.8, 0.3, 0.1)',
  '{0} was burned alive by a thermal anomaly.','{0} сгорает в термической аномалии.'),
 ('SZ_ChemicalBurn','caustic splash','едкий всплеск','Burn','Heat',12,0.2,'BlastDry','SZ_Acid_Discharge','(0.4, 1.0, 0.4)','(0.2, 0.6, 0.2)',
  '{0} was dissolved by a chemical anomaly.','{0} погибает в химической аномалии.'),
 ('SZ_FuzzSting','stinging fibers','жгучие волокна','Scratch','Sharp',7,0.1,'BlastDry','SZ_Fuzz_Discharge','(1.0, 0.95, 0.7)','(0.8, 0.75, 0.5)',
  '{0} was killed by stinging fibers.','{0} погибает от жгучих волокон.'),
]

# ---------------- Аномалии ----------------
# key, en, ru, texture, damage, radius, glow(r,g,b), drawSize, en desc, ru desc, group comment
SUF_EN=' Artifacts are sometimes found in or near it.'
SUF_RU=' В ней или рядом с ней иногда находят артефакты.'
ANOM=[
 ('Springboard','springboard','трамплин','Springboard','SZ_GravityCrushLight',1.5,(160,110,255),1.6,
  'A patch of air where dust hangs strangely still. Whatever steps into it is slammed by a short burst of gravity.',
  'Пятно воздуха, в котором пыль странно застыла на месте. Того, кто в него шагнёт, бьёт коротким всплеском гравитации.','гравитационная: слабый удар, маленький радиус'),
 ('Vortex','vortex','воронка','Vortex','SZ_GravityCrushHeavy',2.9,(150,120,220),2.2,
  'A wide swirl of leaves and debris circling a single point. When disturbed, it crushes everything in a large radius.',
  'Широкий вихрь из листьев и мусора, кружащий вокруг одной точки. Если его потревожить, он сминает всё в большом радиусе.','гравитационная: сильный урон, большой радиус'),
 ('Whirligig','whirligig','карусель','Whirligig','SZ_GravityCrush',2.2,(120,140,255),2.0,
  'A spinning column of distorted air. It batters anything that comes too close.',
  'Вращающийся столб искажённого воздуха. Бьёт всё, что подойдёт слишком близко.','гравитационная: средний урон и радиус'),
 ('Meatgrinder','meatgrinder','мясорубка','Meatgrinder','SZ_GravityShred',1.9,(220,60,60),1.8,
  'A small knot of twisted space, deadly to anything alive. It tears apart whatever touches it.',
  'Небольшой узел искривлённого пространства, смертельный для всего живого. Разрывает всё, что его коснётся.','гравитационная: резаные раны, очень опасна'),
 ('Electro','electro','электра','Electro','SZ_ElectricDischarge',2.9,(90,140,255),1.8,
  'A knot of crackling energy hanging just above the ground. Anything that touches it is hit by a powerful discharge.',
  'Сгусток потрескивающей энергии над самой землёй. Всё, что его касается, бьёт мощным разрядом.','электрическая: ожоги, большой радиус'),
 ('Burner','burner','жарка','Burner','SZ_ThermalBurn',2.4,(255,140,60),1.8,
  'A patch of shimmering, scorching air. When disturbed, it erupts in a column of fire.',
  'Пятно дрожащего раскалённого воздуха. Если его потревожить, оно взрывается столбом огня.','термическая: ванильный огонь, поджигает'),
 ('Comet','comet','комета','Comet','SZ_ThermalBurn',1.9,(255,150,70),1.6,
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
an_keys={a[0] for a in ANOM}; dmg_keys={d[0] for d in DAMAGE}|{'Flame'}
for a in ANOM: assert a[4] in dmg_keys, a; assert os.path.isdir(f'{TEX}/Building/SZ_Anomalies/{a[3]}'), a[3]  # папка с кадрами
for r in ART:
    assert r[3] in an_keys, r; assert os.path.exists(f'{TEX}/Item/SZ_Artifacts/{r[0]}.png'), r[0]
for a in an_keys: assert any(r[3]==a for r in ART), a

# =============== SZ_Anomalies.xml ===============
o=[]; w=o.append
w('<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n')
w('''  <!-- Файл сгенерирован из одной таблицы. Аномалии и артефакты "по мотивам" Зоны:
       названия узнаваемые, описания, баланс и текстуры свои. -->

  <!-- ================= УРОН АНОМАЛИЙ =================
       Общий абстрактный родитель: всё, что одинаково у всех разрядов.
       Жарка использует ванильный Flame (поджигает), ему своё описание не нужно. -->
  <DamageDef Name="SZ_AnomalyDamageBase" Abstract="True">
    <workerClass>DamageWorker_AddInjury</workerClass>
    <externalViolence>true</externalViolence>
    <isExplosive>true</isExplosive>
    <combatLogRules>Damage_Bomb</combatLogRules>
  </DamageDef>
''')
for d in DAMAGE:
    k,en,ru,hed,arm,dmg,ap,fl,snd,cc,ce,den,dru=d
    w(f'''
  <DamageDef ParentName="SZ_AnomalyDamageBase">
    <defName>{k}</defName>
    <label>{esc(en)}</label>
    <deathMessage>{esc(den)}</deathMessage>
    <hediff>{hed}</hediff>
    <armorCategory>{arm}</armorCategory>
    <defaultDamage>{dmg}</defaultDamage>
    <defaultArmorPenetration>{ap}</defaultArmorPenetration>
    <explosionCellFleck>{fl}</explosionCellFleck>
    <explosionColorCenter>{cc}</explosionColorCenter>
    <explosionColorEdge>{ce}</explosionColorEdge>
    <soundExplosion>{snd}</soundExplosion>
  </DamageDef>
''')
w('''
  <!-- ================= БАЗА АНОМАЛИИ =================
       XML-режим (без DLL): Building_TrapExplosive — ванильная мина (как IED).
       Срабатывает от шага или когда HP падает ниже startWickHitPointsPercent
       (можно разрядить выстрелами). При уничтожении оставляет артефакт (killedLeavings).
       C#-режим: при старте аномалия становится вечной (без HP, не мина), срабатывание
       и повадки ведёт MapComponent_Zone, а killedLeavings — просто "какой артефакт рядом".
       pathCost: колонисты обходят клетку аномалии в обоих режимах.
       Звук разряда в XML-режиме задаёт soundExplosion у DamageDef (свои SoundDef). -->
  <ThingDef ParentName="BuildingBase" Name="SZ_AnomalyBase" Abstract="True">
    <thingClass>Building_TrapExplosive</thingClass>
    <altitudeLayer>Building</altitudeLayer>
    <drawerType>RealtimeOnly</drawerType>   <!-- рисуется каждый кадр: нужно для анимации -->
    <passability>Standable</passability>
    <rotatable>false</rotatable>
    <tickerType>Normal</tickerType>   <!-- ловушке нужен тик, чтобы замечать пешек -->
    <stealable>false</stealable>
    <pathCost>300</pathCost>          <!-- пешки обходят, если есть другой путь -->
    <useHitPoints>true</useHitPoints>
    <statBases>
      <MaxHitPoints>60</MaxHitPoints>
      <Flammability>0</Flammability>
      <Beauty>-10</Beauty>
    </statBases>
    <building>
      <isTrap>true</isTrap>
      <claimable>false</claimable>
      <deconstructible>false</deconstructible>
    </building>
  </ThingDef>

  <!-- ================= ТИПЫ АНОМАЛИЙ =================
       Каждый тип — абстрактный родитель: внешний вид, урон, радиус, свечение.
       Конкретные аномалии ниже — варианты типа, которые различаются только
       артефактом (killedLeavings). Снаружи варианты не отличить: так в чистом XML
       получается случайный артефакт с разной редкостью. -->
''')
for a in ANOM:
    k,en,ru,tex,dmg,rad,glow,ds,den,dru,note=a
    w(f'''
  <!-- {ru.capitalize()}: {note} -->
  <ThingDef ParentName="SZ_AnomalyBase" Name="SZ_AnomalyType_{k}" Abstract="True">
    <label>{esc(en)}</label>
    <description>{esc(den+SUF_EN)}</description>
    <graphicData>
      <texPath>Things/Building/SZ_Anomalies/{tex}</texPath>  <!-- папка с 8 кадрами -->
      <graphicClass>Graphic_Flicker</graphicClass>        <!-- ванильная анимация (как у огня) -->
      <shaderType>Transparent</shaderType>                <!-- мягкое свечение с прозрачностью -->
      <drawSize>({ds},{ds})</drawSize>
    </graphicData>
    <comps>
      <li Class="CompProperties_Explosive">
        <explosiveRadius>{rad}</explosiveRadius>
        <explosiveDamageType>{dmg}</explosiveDamageType>
        <startWickHitPointsPercent>0.5</startWickHitPointsPercent>
        <wickTicks>10~20</wickTicks>         <!-- почти мгновенный разряд -->
      </li>
      <li Class="CompProperties_Glower">
        <glowRadius>2.5</glowRadius>
        <glowColor>({glow[0]*3//4},{glow[1]*3//4},{glow[2]*3//4},0)</glowColor>
      </li>
    </comps>
  </ThingDef>
''')
    for r in ART:
        if r[3]!=k: continue
        w(f'''  <ThingDef ParentName="SZ_AnomalyType_{k}">   <!-- {RARITY[r[4]][1]}: {r[2]} -->
    <defName>SZ_Anomaly_{k}_{r[0]}</defName>
    <killedLeavings>
      <SZ_Artifact_{r[0]}>1</SZ_Artifact_{r[0]}>
    </killedLeavings>
  </ThingDef>
''')
w('''
  <!-- ================= ГЕНЕРАЦИЯ НА КАРТЕ =================
       Один шаг на вариант. countPer10kCellsRange — штук на 10 000 клеток
       (карта 250x250 ≈ 6 таких блоков). Частота задаёт редкость артефакта:
       обычный 0.12~0.25, необычный 0.06~0.12, редкий 0.02~0.06.
       Подключаются к карте колонии патчем Patches/SZ_MapGen.xml. -->
''')
order=650
for r in ART:
    w(f'''  <GenStepDef>
    <defName>SZ_Scatter_{r[3]}_{r[0]}</defName>
    <order>{order}</order>
    <genStep Class="GenStep_ScatterThings">
      <thingDef>SZ_Anomaly_{r[3]}_{r[0]}</thingDef>
      <countPer10kCellsRange>{RARITY[r[4]][0]}</countPer10kCellsRange>
      <minSpacing>8</minSpacing>
    </genStep>
  </GenStepDef>
''')
    order+=1
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
lis=''.join(f'        <li>SZ_Scatter_{r[3]}_{r[0]}</li>\n' for r in ART)
open(f'{M}/Patches/SZ_MapGen.xml','w',encoding='utf-8').write(f'''<?xml version="1.0" encoding="utf-8"?>
<Patch>

  <!-- Добавляем аномалии в генерацию карты колонии (Base_Player).
       PatchOperationConditional: если такого узла нет, патч молча пропускается.
       Работает только для НОВЫХ карт. На текущую ставьте через режим разработчика. -->
  <Operation Class="PatchOperationConditional">
    <xpath>Defs/MapGeneratorDef[defName="Base_Player"]/genSteps</xpath>
    <match Class="PatchOperationAdd">
      <xpath>Defs/MapGeneratorDef[defName="Base_Player"]/genSteps</xpath>
      <value>
{lis}      </value>
    </match>
  </Operation>

</Patch>
''')

# =============== Перевод ===============
L=f'{M}/Languages/Russian/DefInjected'
o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for d in DAMAGE:
    o.append(f'  <{d[0]}.label>{esc(d[2])}</{d[0]}.label>\n  <{d[0]}.deathMessage>{esc(d[12])}</{d[0]}.deathMessage>\n')
o.append('</LanguageData>\n'); open(f'{L}/DamageDef/SZ_Anomalies.xml','w',encoding='utf-8').write(''.join(o))

o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for a in ANOM:
    o.append(f'\n  <!-- {a[2]} -->\n')
    for r in ART:
        if r[3]!=a[0]: continue
        dn=f'SZ_Anomaly_{a[0]}_{r[0]}'
        o.append(f'  <{dn}.label>{esc(a[2])}</{dn}.label>\n  <{dn}.description>{esc(a[9]+SUF_RU)}</{dn}.description>\n')
o.append('</LanguageData>\n'); open(f'{L}/ThingDef/SZ_Anomalies.xml','w',encoding='utf-8').write(''.join(o))

o=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
for r in ART:
    dn=f'SZ_Artifact_{r[0]}'
    o.append(f'  <{dn}.label>{esc(r[2])}</{dn}.label>\n  <{dn}.description>{esc(r[10]+RAD_RU[r[8]])}</{dn}.description>\n')
o.append('</LanguageData>\n'); open(f'{L}/ThingDef/SZ_Artifacts.xml','w',encoding='utf-8').write(''.join(o))

print(f'anomaly types: {len(ANOM)}, variants/artifacts: {len(ART)}, damage defs: {len(DAMAGE)}')
