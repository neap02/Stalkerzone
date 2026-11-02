# Генератор снаряжения Зоны (одна таблица -> XML, перевод, графика, звуки):
# - 24 костюма: по 2–3 на фракцию + особые; своя графика для всех типов тела;
# - шлемы и противогаз; свинцовый контейнер; ремкомплект;
# - улучшения костюмов на станке и ремонт; стат ячеек пояса; звук болта; иконки кнопок.
# Названия, характеристики и рисунки — свои.
import math, os, random, struct, wave
from xml.sax.saxutils import escape as esc
from PIL import Image, ImageDraw, ImageFilter, ImageChops

M='/mnt/user-data/outputs/StalkerZone/Common'
L=f'{M}/Languages/Russian/DefInjected'
T=f'{M}/Textures'
VAN='Things/Pawn/Humanlike/Apparel'

def P(sharp,blunt,heat,strike,rupture,shock,burn,chem,rad,psi,slots=0,move=0,carry=0,cold=10,heatins=0):
    return dict(sharp=sharp,blunt=blunt,heat=heat,strike=strike,rupture=rupture,shock=shock,burn=burn,chem=chem,
                rad=rad,psi=psi,slots=slots,move=move,carry=carry,cold=cold,heatins=heatins)

# класс -> (исследование, верстаки, материалы, навык, работа, ячеек улучшений)
CLS={
 'light':  ('ComplexClothing', ['HandTailoringBench','ElectricTailoringBench'], {'Cloth':80}, 4, 8000, 1),
 'cloak':  ('ComplexClothing', ['HandTailoringBench','ElectricTailoringBench'], {'Cloth':90}, 4, 8000, 1),
 'medium': ('FlakArmor', ['TableMachining'], {'Steel':60,'Cloth':60,'ComponentIndustrial':2}, 6, 14000, 2),
 'heavy':  ('FlakArmor', ['TableMachining'], {'Steel':100,'Plasteel':30,'Cloth':40,'ComponentIndustrial':3}, 8, 20000, 3),
 'science':('AdvancedFabrication', ['FabricationBench'], {'Synthread':60,'Plasteel':30,'ComponentSpacer':1}, 8, 20000, 3),
 'exo':    ('PoweredArmor', ['FabricationBench'], {'Plasteel':120,'ComponentIndustrial':4,'ComponentSpacer':4}, 10, 32000, 3),
}

# key, en, ru, класс, (основной, второй, акцент), защита, цена, масса, теги фракций, описание en, ru
SUITS=[
 # ---- Одиночки ----
 ('ScoutCloak','scout cloak','маскхалат разведчика','cloak',((0.36,0.40,0.28),(0.25,0.30,0.18),(0.50,0.45,0.30)),
   P(0.15,0.05,0.10, 0.05,0.03,0.05,0.10,0.05, 0.05,0.00, move=0.10, cold=12),350,2.5,['Loners'],
   'A light camouflage cloak with a hood. Barely protects, but does not slow its wearer down.',
   'Лёгкий маскировочный халат с капюшоном. Почти не защищает, зато не сковывает движений.'),
 ('LonerJacket','stalker jacket','куртка сталкера','light',((0.45,0.36,0.24),(0.30,0.24,0.16),(0.85,0.70,0.30)),
   P(0.25,0.10,0.15, 0.10,0.05,0.10,0.15,0.10, 0.10,0.00, cold=14),300,3,['Loners'],
   'A worn leather jacket with sewn-in protective panels. Cheap, light and better than nothing.',
   'Потёртая кожаная куртка со вшитыми защитными вставками. Дешёвая, лёгкая и лучше, чем ничего.'),
 ('Stalker','stalker suit','комбинезон сталкера','medium',((0.42,0.45,0.32),(0.30,0.32,0.24),(0.85,0.70,0.30)),
   P(0.45,0.20,0.25, 0.20,0.10,0.25,0.25,0.25, 0.25,0.05, slots=1),700,6,['Loners'],
   'A reliable all-round suit for trips into the Zone: armored panels, sealed seams and a rack for two artifacts.',
   'Надёжный универсальный комбинезон для походов в Зону: бронепанели, проклеенные швы и крепление под два артефакта.'),
 ('StalkerReinforced','reinforced stalker suit','усиленный комбинезон сталкера','heavy',((0.38,0.40,0.30),(0.26,0.28,0.22),(0.85,0.70,0.30)),
   P(0.60,0.28,0.30, 0.30,0.18,0.30,0.30,0.30, 0.30,0.05, slots=1, move=-0.1),1100,8,['Loners'],
   'A veteran\'s suit with extra plates and a sealed hood. Heavier, but holds up against both bullets and anomalies.',
   'Комбинезон бывалого сталкера с дополнительными пластинами и герметичным капюшоном. Тяжелее, зато держит и пули, и аномалии.'),
 # ---- Долг ----
 ('DutyUniform','Duty field uniform','полевая форма Долга','medium',((0.20,0.20,0.20),(0.45,0.08,0.08),(0.80,0.15,0.15)),
   P(0.45,0.20,0.20, 0.20,0.10,0.15,0.20,0.15, 0.20,0.05),600,5,['Duty'],
   'Everyday uniform of Duty patrols with a light armored vest.',
   'Повседневная форма патрулей Долга с лёгким бронежилетом.'),
 ('Duty','Duty armored suit','бронекостюм Долга','heavy',((0.42,0.08,0.08),(0.18,0.18,0.18),(0.85,0.20,0.20)),
   P(0.80,0.35,0.30, 0.35,0.20,0.20,0.30,0.20, 0.30,0.10, slots=1, move=-0.2),1300,10,['Duty'],
   'Heavy armor issued to Duty fighters. Stops bullets and blows well, but weighs its wearer down.',
   'Тяжёлая броня бойцов Долга. Хорошо держит пули и удары, но тяжела для владельца.'),
 ('DutyAssault','Duty assault armor','штурмовая броня Долга','heavy',((0.25,0.25,0.25),(0.45,0.08,0.08),(0.85,0.20,0.20)),
   P(0.95,0.45,0.35, 0.45,0.30,0.25,0.35,0.25, 0.35,0.10, slots=1, move=-0.35),1700,13,['Duty'],
   'Assault armor for storming mutant lairs. Nearly bulletproof and very heavy.',
   'Штурмовая броня для зачистки логов мутантов. Почти не пробивается и очень тяжела.'),
 # ---- Свобода ----
 ('FreedomLight','Freedom light suit','лёгкий костюм Свободы','light',((0.30,0.50,0.25),(0.20,0.32,0.15),(0.95,0.90,0.40)),
   P(0.30,0.12,0.20, 0.15,0.08,0.25,0.20,0.20, 0.20,0.05, slots=1, move=0.05),500,3,['Freedom'],
   'A light suit for fast raids, with a rack for two artifacts.',
   'Лёгкий костюм для быстрых вылазок, с креплением под два артефакта.'),
 ('Freedom','Freedom combat suit','комбинезон Свободы','medium',((0.24,0.42,0.20),(0.16,0.28,0.13),(0.95,0.90,0.40)),
   P(0.50,0.20,0.30, 0.25,0.15,0.35,0.30,0.30, 0.30,0.10, slots=2),900,6,['Freedom'],
   'A light combat suit favored by Freedom: good anomaly protection and room for three artifacts.',
   'Лёгкий боевой комбинезон, любимый Свободой: хорошая защита от аномалий и место под три артефакта.'),
 ('FreedomGuardian','Freedom guardian armor','броня стража Свободы','heavy',((0.20,0.36,0.18),(0.32,0.34,0.30),(0.95,0.90,0.40)),
   P(0.80,0.35,0.35, 0.35,0.22,0.35,0.35,0.30, 0.35,0.10, slots=2, move=-0.2),1600,11,['Freedom'],
   'Heavy armor of Freedom\'s best fighters, balanced between firefights and the Zone.',
   'Тяжёлая броня лучших бойцов Свободы, одинаково годная для перестрелок и для Зоны.'),
 # ---- Бандиты ----
 ('Bandit','bandit jacket','бандитская куртка','light',((0.16,0.16,0.16),(0.25,0.22,0.20),(0.55,0.55,0.55)),
   P(0.30,0.12,0.10, 0.10,0.05,0.05,0.10,0.05, 0.05,0.00, cold=12),250,4,['Bandits'],
   'A long black coat with a few steel plates sewn into the lining.',
   'Длинное чёрное пальто с несколькими стальными пластинами в подкладке.'),
 ('BanditCoat','reinforced leather coat','укреплённый кожаный плащ','medium',((0.30,0.22,0.15),(0.15,0.12,0.10),(0.55,0.55,0.55)),
   P(0.40,0.18,0.15, 0.15,0.08,0.10,0.15,0.10, 0.10,0.00, slots=1),550,5,['Bandits'],
   'A heavy leather coat over a stolen armored vest.',
   'Тяжёлый кожаный плащ поверх краденого бронежилета.'),
 # ---- Военные ----
 ('MilitaryUniform','army field uniform','армейская полевая форма','light',((0.40,0.43,0.26),(0.30,0.33,0.20),(0.75,0.70,0.30)),
   P(0.35,0.12,0.15, 0.10,0.05,0.10,0.15,0.10, 0.15,0.00, cold=15),400,3,['Military'],
   'Standard field uniform of the cordon troops with a light vest.',
   'Стандартная полевая форма войск кордона с лёгким жилетом.'),
 ('Military','army body armor','армейский бронекостюм','heavy',((0.33,0.36,0.20),(0.24,0.26,0.15),(0.75,0.70,0.30)),
   P(0.70,0.30,0.25, 0.30,0.15,0.15,0.20,0.15, 0.20,0.05, move=-0.1),1000,9,['Military'],
   'Standard body armor of the cordon troops. Built for firefights, not for anomalies.',
   'Штатная броня войск кордона. Сделана для перестрелок, а не для аномалий.'),
 ('MilitaryAssault','army assault armor','армейская штурмовая броня','heavy',((0.30,0.32,0.20),(0.20,0.22,0.15),(0.75,0.70,0.30)),
   P(0.95,0.45,0.35, 0.40,0.25,0.20,0.30,0.25, 0.30,0.05, move=-0.3),1600,13,['Military'],
   'Assault armor of the special units. Excellent against bullets, poor against the Zone.',
   'Штурмовая броня спецподразделений. Отлично держит пули, но слаба против Зоны.'),
 # ---- Монолит ----
 ('MonolithSuit','Monolith suit','костюм Монолита','medium',((0.70,0.70,0.66),(0.50,0.52,0.55),(0.40,0.70,0.90)),
   P(0.50,0.22,0.30, 0.25,0.15,0.30,0.30,0.25, 0.40,0.40, slots=1),1000,6,['Monolith'],
   'A pale suit of Monolith acolytes. Protects the mind better than the body.',
   'Бледный костюм послушников Монолита. Разум защищает лучше, чем тело.'),
 ('Monolith','Monolith armor','броня Монолита','heavy',((0.68,0.68,0.65),(0.45,0.47,0.50),(0.40,0.70,0.90)),
   P(0.75,0.35,0.35, 0.35,0.25,0.35,0.35,0.30, 0.50,0.60, slots=2, move=-0.15),1500,10,['Monolith'],
   'Pale armor of the Monolith fanatics. Strongly shields the mind and the body from the Zone.',
   'Бледная броня фанатиков Монолита. Надёжно защищает разум и тело от Зоны.'),
 # ---- Наёмники ----
 ('MercLight','mercenary light suit','лёгкий костюм наёмника','light',((0.25,0.32,0.45),(0.18,0.22,0.30),(0.85,0.85,0.85)),
   P(0.35,0.15,0.20, 0.15,0.08,0.20,0.20,0.15, 0.15,0.00, slots=1, move=0.05),600,3,['Mercenaries'],
   'A light tactical suit for quick contracts.',
   'Лёгкий тактический костюм для быстрых заказов.'),
 ('Mercenary','mercenary suit','костюм наёмника','medium',((0.20,0.27,0.40),(0.14,0.18,0.26),(0.85,0.85,0.85)),
   P(0.60,0.25,0.30, 0.25,0.15,0.30,0.30,0.25, 0.25,0.05, slots=1),1100,7,['Mercenaries'],
   'A professional combat suit: well-balanced protection from bullets and anomalies.',
   'Профессиональный боевой костюм: сбалансированная защита и от пуль, и от аномалий.'),
 ('MercHeavy','mercenary heavy armor','тяжёлая броня наёмника','heavy',((0.18,0.22,0.32),(0.30,0.33,0.38),(0.85,0.85,0.85)),
   P(0.85,0.40,0.35, 0.35,0.22,0.30,0.30,0.25, 0.30,0.05, slots=2, move=-0.25),1700,12,['Mercenaries'],
   'Heavy armor for well-paid jobs deep in the Zone.',
   'Тяжёлая броня для хорошо оплаченной работы в глубине Зоны.'),
 # ---- Учёные ----
 ('Scientist','scientific suit','научный комбинезон','science',((0.90,0.52,0.15),(0.95,0.95,0.92),(0.20,0.20,0.20)),
   P(0.20,0.10,0.40, 0.20,0.15,0.50,0.60,0.70, 0.70,0.30, slots=2, move=-0.05, cold=20, heatins=10),1400,7,['Scientists'],
   'A sealed research suit. Weak against bullets, but the best protection from radiation, chemicals and fire.',
   'Герметичный научный комбинезон. Слаб против пуль, зато лучше всего защищает от радиации, химии и огня.'),
 ('ClosedCycle','closed-cycle suit','костюм замкнутого цикла','science',((0.92,0.92,0.88),(0.95,0.55,0.15),(0.25,0.60,0.85)),
   P(0.40,0.20,0.50, 0.40,0.30,0.65,0.70,0.80, 0.85,0.40, slots=3, move=-0.1, cold=25, heatins=15),2200,9,['Scientists'],
   'A top-class research suit with its own air supply. The best protection against anomalies the Zone has seen.',
   'Научный костюм высшего класса с собственной системой дыхания. Лучшая защита от аномалий, какую знала Зона.'),
 # ---- Особые ----
 ('Exo','exoskeleton armor','броня экзоскелета','exo',((0.22,0.24,0.26),(0.35,0.37,0.40),(0.90,0.55,0.15)),
   P(1.00,0.50,0.45, 0.50,0.35,0.30,0.40,0.30, 0.35,0.15, slots=4, move=-0.3),2000,22,['Duty','Freedom','Monolith','Mercenaries'],
   'Heavy armor plating made to be worn with an exoskeleton frame. Holds five artifacts. Without the frame it is very heavy.',
   'Тяжёлая бронезащита для ношения вместе с каркасом экзоскелета. Держит пять артефактов. Без каркаса очень тяжела.'),
 ('ExoAssault','assault exoskeleton armor','штурмовая броня экзоскелета','exo',((0.18,0.19,0.20),(0.40,0.40,0.38),(0.85,0.20,0.20)),
   P(1.25,0.65,0.55, 0.60,0.45,0.35,0.45,0.35, 0.40,0.20, slots=3, move=-0.4),2200,27,['Duty','Monolith','Mercenaries'],
   'Assault plating for an exoskeleton. The strongest armor in the Zone, and the heaviest.',
   'Штурмовая бронезащита для экзоскелета. Самая прочная броня в Зоне и самая тяжёлая.'),
]

HEAD=[
 ('Helmet_Stalker','stalker helmet','шлем сталкера',f'{VAN}/SZ_Helmets/Helmet_Stalker/Helmet_Stalker','Overhead',['UpperHead'],(0.40,0.42,0.35),
   dict(sharp=0.40,blunt=0.20,heat=0.10,strike=0.20,rupture=0.10,shock=0.10,burn=0.10,chem=0.05),dict(psi=0.10),
   250,1.5,('Smithing',['TableMachining'],{'Steel':40},3,4000),['Loners','Duty','Military','Mercenaries'],
   'A steel helmet with a padded liner. Also slightly dulls psychic pressure.',
   'Стальной шлем с мягким подшлемником. Немного ослабляет и пси-давление.'),
 ('Helmet_Psi','psi helmet','пси-шлем',f'{VAN}/SZ_Helmets/Helmet_Psi/Helmet_Psi','Overhead',['UpperHead'],(0.75,0.78,0.85),
   dict(sharp=0.30,blunt=0.15,heat=0.15,strike=0.15,rupture=0.10,shock=0.20,burn=0.15,chem=0.10),dict(psi=0.50),
   900,1.2,('MicroelectronicsBasics',['FabricationBench'],{'Plasteel':25,'ComponentIndustrial':3},7,9000),['Monolith','Scientists'],
   'A helmet with a built-in psi shield circuit. Protects the mind from psychic fields and the emission.',
   'Шлем со встроенной схемой пси-экрана. Защищает разум от пси-полей и Выброса.'),
 ('GasMask','gas mask','противогаз','Things/Pawn/Humanlike/Apparel/SZ_GasMask/SZ_GasMask','EyeCover',['Eyes'],(1,1,1),
   dict(chem=0.30),dict(rad=0.15,tox=0.50),
   200,0.8,('ComplexClothing',['TableMachining'],{'Cloth':20,'Steel':15,'ComponentIndustrial':1},4,3000),['Freedom','Military','Scientists','Bandits'],
   'A rubber gas mask with a filter. Keeps out radioactive dust and toxic fumes. Can be worn under a helmet.',
   'Резиновый противогаз с фильтром. Защищает от радиоактивной пыли и ядовитых испарений. Надевается под шлем.'),
]

# key, en, ru, прибавки к броне костюма, ячейки, радиация, пси, максимум на костюм, исследование, материалы, навык, описание en/ru
UPG=[
 ('Plates','reinforced plates','усиленные бронепластины',{'ArmorRating_Sharp':0.15,'ArmorRating_Blunt':0.08,'SZ_ArmorRating_Strike':0.05},0,0,0,2,
   'FlakArmor',{'Plasteel':20,'Steel':20},6,'Extra armor plates: better protection from bullets and blows.','Дополнительные бронепластины: лучше защита от пуль и ударов.'),
 ('AntiRupture','anti-rupture mesh','противоразрывная сетка',{'SZ_ArmorRating_Rupture':0.15,'SZ_ArmorRating_Strike':0.05},0,0,0,2,
   'FlakArmor',{'Plasteel':15,'Cloth':20},6,'A woven mesh layer against tearing gravitational anomalies.','Сетчатый слой против разрывающих гравитационных аномалий.'),
 ('Thermal','thermal lining','термоизоляционный слой',{'SZ_ArmorRating_Burn':0.15,'ArmorRating_Heat':0.08},0,0,0,2,
   'ComplexClothing',{'Cloth':30,'ComponentIndustrial':1},4,'A heat-resistant lining against thermal anomalies and fire.','Термостойкая подкладка против термических аномалий и огня.'),
 ('Dielectric','dielectric lining','диэлектрическая подкладка',{'SZ_ArmorRating_Shock':0.15},0,0,0,2,
   'ComplexClothing',{'Cloth':20,'ComponentIndustrial':1},4,'An insulating lining against electric anomalies.','Изолирующая подкладка против электрических аномалий.'),
 ('Chemical','chemical impregnation','химзащитная пропитка',{'SZ_ArmorRating_Chemical':0.15},0,0,0,2,
   'DrugProduction',{'Cloth':20,'Neutroamine':4},4,'An impregnation that protects against caustic and toxic anomalies.','Пропитка, защищающая от едких и токсичных аномалий.'),
 ('Lead','lead inserts','свинцовые вставки',{},0,0.15,0,2,
   'Smithing',{'Steel':30},4,'Lead inserts in the lining: +15% radiation protection.','Свинцовые вставки в подкладке: +15% к защите от радиации.'),
 ('PsiMesh','psi shielding mesh','пси-экранирующая сетка',{},0,0,0.15,1,
   'MicroelectronicsBasics',{'ComponentIndustrial':3,'Plasteel':10},7,'A shielding mesh in the collar: +15% psi protection.','Экранирующая сетка в воротнике: +15% к пси-защите.'),
 ('ArtifactMount','artifact mount','крепление для артефакта',{},1,0,0,1,
   'MicroelectronicsBasics',{'Steel':15,'ComponentIndustrial':2},6,'An extra artifact container: +1 belt slot.','Дополнительный контейнер для артефакта: +1 ячейка пояса.'),
]

# Стиль шлема по классу костюма (и особые случаи)

# Внешний вид: (камуфляж, палитра RGB, цвет снаряжения, цвет нашивки). Камуфляжи свои, обобщённые.
_WL=[(104,100,70),(72,80,52),(130,112,78),(52,48,36)]
_WD=[(84,84,60),(60,66,46),(110,96,68),(44,42,32)]
_FR=[(78,104,58),(56,80,42),(108,120,74),(40,52,30)]
_DG=[(66,66,68),(42,42,44),(92,92,94)]
_FL=[(96,104,70),(64,74,48),(122,110,78)]
_MN=[(176,178,176),(140,142,142),(112,114,116)]
_MR=[(62,72,92),(44,52,70),(84,94,112)]
LOOK={
 'ScoutCloak':('woodland',[(86,96,60),(60,72,44),(112,108,72),(46,50,34)],(70,78,58),(200,170,60)),
 'LonerJacket':('solid',[(98,80,58)],(70,66,50),(210,170,60)),
 'Stalker':('woodland',_WL,(98,92,64),(210,170,60)),
 'StalkerReinforced':('woodland',_WD,(132,112,80),(210,170,60)),
 'DutyUniform':('digital',_DG,(40,40,42),(170,40,40)),
 'Duty':('digital',[(58,58,60),(38,38,40),(80,80,82)],(92,32,30),(190,46,40)),
 'DutyAssault':('digital',[(46,46,48),(30,30,32),(66,66,68)],(84,30,28),(190,46,40)),
 'FreedomLight':('woodland',_FR,(66,82,50),(230,210,90)),
 'Freedom':('woodland',_FR,(66,82,50),(230,210,90)),
 'FreedomGuardian':('woodland',_FR,(58,72,44),(230,210,90)),
 'Bandit':('solid',[(40,38,36)],(52,46,40),(150,150,150)),
 'BanditCoat':('solid',[(70,52,38)],(48,40,32),(150,150,150)),
 'MilitaryUniform':('flora',_FL,(88,92,62),(200,180,80)),
 'Military':('flora',_FL,(80,86,58),(200,180,80)),
 'MilitaryAssault':('flora',_FL,(70,76,52),(200,180,80)),
 'MonolithSuit':('urban',_MN,(120,122,124),(100,170,220)),
 'Monolith':('urban',_MN,(108,110,112),(100,170,220)),
 'MercLight':('urban',_MR,(40,42,46),(220,220,220)),
 'Mercenary':('urban',_MR,(40,42,46),(220,220,220)),
 'MercHeavy':('urban',_MR,(36,38,42),(220,220,220)),
 'Scientist':('solid',[(214,128,40)],(90,90,90),(60,60,60)),
 'ClosedCycle':('solid',[(222,222,214)],(110,110,110),(214,128,40)),
 'Exo':('solid',[(62,64,66)],(70,72,74),(220,130,40)),
 'ExoAssault':('solid',[(50,52,54)],(62,64,66),(200,50,40)),
 'Helmet_Stalker':('woodland',_WL,(98,92,64),(210,170,60)),
 'Helmet_Psi':('urban',_MN,(120,122,124),(100,170,220)),
}
HEADCOL={'Helmet_Stalker':((0.40,0.42,0.35),(0.30,0.32,0.26)),'Helmet_Psi':((0.62,0.64,0.70),(0.45,0.47,0.52))}
HSTYLE={'light':'cap','cloak':'hood','medium':'combat','heavy':'visor','science':'sealed','exo':'exo'}
HSTYLE_BY_SUIT={'MonolithSuit':'psi','Bandit':'hood','BanditCoat':'hood'}
HNOUN={'cap':('cap','шапка'),'hood':('hood','капюшон'),'combat':('helmet','шлем'),'psi':('psi helmet','пси-шлем'),
       'visor':('visor helmet','шлем с забралом'),'sealed':('sealed helmet','гермошлем'),'exo':('exo helmet','шлем экзоскелета')}
HFULL={'visor','sealed','exo'}                   # закрывают всю голову
HBONUS={'psi':{'psi':0.40},'sealed':{'psi':0.15,'rad':0.15},'exo':{'psi':0.10,'rad':0.05},'visor':{'psi':0.05},'combat':{'psi':0.05},'cap':{},'hood':{'rad':0.03}}

ARMOR={'sharp':'ArmorRating_Sharp','blunt':'ArmorRating_Blunt','heat':'ArmorRating_Heat',
       'strike':'SZ_ArmorRating_Strike','rupture':'SZ_ArmorRating_Rupture','shock':'SZ_ArmorRating_Shock',
       'burn':'SZ_ArmorRating_Burn','chem':'SZ_ArmorRating_Chemical'}
OFFS={'rad':'SZ_RadiationResistance','psi':'SZ_PsiProtection','slots':'SZ_ArtifactSlots','move':'MoveSpeed',
      'carry':'SZ_InventoryCapacity','tox':'ToxicResistance'}

def recipe_block(research,users,cost,skill):
    us=''.join(f'<li>{u}</li>' for u in users); cs=''.join(f'<{k}>{v}</{k}>' for k,v in cost.items())
    return f"""    <costList>{cs}</costList>
    <recipeMaker>
      <researchPrerequisite>{research}</researchPrerequisite>
      <recipeUsers>{us}</recipeUsers>
      <workSpeedStat>GeneralLaborSpeed</workSpeedStat>
      <workSkill>Crafting</workSkill>
      <skillRequirements><Crafting>{skill}</Crafting></skillRequirements>
    </recipeMaker>
"""

o=[]; w=o.append
w("""<?xml version="1.0" encoding="utf-8"?>
<Defs>

  <!-- Файл сгенерирован Source/Tools/gen_gear.py.
       Снаряжение Зоны. Броня от аномалий — статы категорий (SZ_Protection.xml), работают как
       обычная броня по закрытым частям тела. Радиация, пси и ячейки пояса — статы владельца.
       Комплект = комбинезон (SZ_Suit_*: всё тело) + шлем (SZ_Helm_*) + по желанию
       каркас экзоскелета (SZ_ExoFrame*: отдельный слой поверх брони). Костюмы: свой рисунок для всех типов тела, износ (CompSuit: ниже прочность — слабее броня),
       улучшения на станке (SZ_SuitUpgrades.xml), ремонт на станке и ремкомплектом в поле. -->

  <StatDef>
    <defName>SZ_ArtifactSlots</defName>
    <label>artifact slots</label>
    <description>How many artifacts carried in the inventory are active at once. One by default; suits add more.</description>
    <category>PawnCombat</category>
    <defaultBaseValue>1</defaultBaseValue>
    <minValue>0</minValue>
    <maxValue>5</maxValue>
    <toStringStyle>Integer</toStringStyle>
  </StatDef>

  <!-- ===== Грузоподъёмность снаряжения, кг: прибавляется к инвентарю и каравану (C#: ZoneHarmony) ===== -->
  <StatDef>
    <defName>SZ_InventoryCapacity</defName>
    <label>gear carrying capacity</label>
    <description>Extra mass this creature can carry in its inventory and in caravans thanks to its gear (exoskeletons, backpacks).</description>
    <category>BasicsPawn</category>
    <defaultBaseValue>0</defaultBaseValue>
    <toStringStyle>FloatOne</toStringStyle>
    <formatString>{0} kg</formatString>
  </StatDef>

  <SoundDef>
    <defName>SZ_Bolt_Clink</defName>
    <context>MapOnly</context>
    <maxSimultaneous>3</maxSimultaneous>
    <subSounds>
      <li>
        <grains><li Class="AudioGrain_Folder"><clipFolderPath>SZ/Bolt</clipFolderPath></li></grains>
        <volumeRange>30~36</volumeRange>
        <pitchRange>0.9~1.15</pitchRange>
        <distRange>5~40</distRange>
      </li>
    </subSounds>
  </SoundDef>

  <ThingDef ParentName="ApparelBase" Name="SZ_SuitBase" Abstract="True">
    <techLevel>Industrial</techLevel>
    <tradeability>All</tradeability>
    <thingCategories Inherit="False"><li>ApparelArmor</li></thingCategories>
    <apparel>
      <layers><li>Middle</li><li>Shell</li></layers>
      <bodyPartGroups><li>Torso</li><li>Neck</li><li>Shoulders</li><li>Arms</li><li>Legs</li></bodyPartGroups>
      <careIfWornByCorpse>false</careIfWornByCorpse>
    </apparel>
  </ThingDef>

  <ThingDef ParentName="ApparelBase" Name="SZ_HeadgearBase" Abstract="True">
    <techLevel>Industrial</techLevel>
    <tradeability>All</tradeability>
    <thingCategories Inherit="False"><li>Headgear</li></thingCategories>
    <apparel><careIfWornByCorpse>false</careIfWornByCorpse></apparel>
  </ThingDef>
""")
def stat_lines(prot, keys, table):
    return ''.join(f'      <{table[k]}>{prot[k]}</{table[k]}>\n' for k in keys if prot.get(k))

tr_t=[]
for (k,en,ru,cls,cols,prot,val,mass,tags,den,dru) in SUITS:
    research,users,cost,skill,work,upslots=CLS[cls]
    armor=stat_lines(prot,['sharp','blunt','heat','strike','rupture','shock','burn','chem'],ARMOR)
    offs=stat_lines(prot,['rad','psi','slots','move','carry'],OFFS)
    ins=f'      <Insulation_Cold>{prot["cold"]}</Insulation_Cold>\n'+(f'      <Insulation_Heat>{prot["heatins"]}</Insulation_Heat>\n' if prot['heatins'] else '')
    tg=''.join(f'<li>SZ_Faction_{t}</li>' for t in tags)
    w(f"""
  <!-- {ru}: ячеек пояса {1+prot['slots']}, мест под улучшения {upslots} -->
  <ThingDef ParentName="SZ_SuitBase">
    <defName>SZ_Suit_{k}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den)}</description>
    <graphicData>
      <texPath>Things/Item/SZ_Suits/{k}</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
    <statBases>
      <MaxHitPoints>{int(150+prot['sharp']*250)}</MaxHitPoints>
      <MarketValue>{val}</MarketValue>
      <Mass>{mass}</Mass>
      <WorkToMake>{work}</WorkToMake>
      <EquipDelay>4</EquipDelay>
      <Flammability>0.3</Flammability>
{armor}{ins}    </statBases>
    <equippedStatOffsets>
{offs}    </equippedStatOffsets>
    <apparel>
      <wornGraphicPath>{VAN}/SZ_Suits/{k}/{k}</wornGraphicPath>
      <tags>{tg}</tags>
    </apparel>
    <comps>
      <li Class="StalkerZone.CompProperties_Suit"><upgradeSlots>{upslots}</upgradeSlots></li>
    </comps>
{recipe_block(research,users,cost,skill)}  </ThingDef>
""")
    tr_t.append((f'SZ_Suit_{k}',ru,dru))

    def scaled(keys,f): return ''.join(f'      <{ARMOR[a]}>{round(prot[a]*f,3)}</{ARMOR[a]}>\n' for a in keys if prot.get(a))
    tg=''.join(f'<li>SZ_Faction_{t}</li>' for t in tags)
    # ---- шлем комплекта ----
    st=HSTYLE_BY_SUIT.get(k,HSTYLE[cls]); hen,hru=HNOUN[st]
    hcost={m:max(1,int(math.ceil(v*0.3))) for m,v in cost.items()}
    hb=''.join(f'      <{OFFS[a]}>{v}</{OFFS[a]}>\n' for a,v in HBONUS[st].items())
    grp='<li>FullHead</li>' if st in HFULL else '<li>UpperHead</li>'
    w(f"""
  <ThingDef ParentName="SZ_HeadgearBase">
    <defName>SZ_Helm_{k}</defName>
    <label>{esc(en)} {hen}</label>
    <description>The {hen} from the {esc(en)} set.{' Covers the whole head.' if st in HFULL else ''}</description>
    <graphicData>
      <texPath>Things/Item/SZ_Helmets/{k}</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
    <statBases>
      <MaxHitPoints>{int(90+prot['sharp']*150)}</MaxHitPoints>
      <MarketValue>{int(val*0.3)}</MarketValue>
      <Mass>{round(max(0.4,mass*0.12),1)}</Mass>
      <WorkToMake>{int(work*0.3)}</WorkToMake>
      <EquipDelay>1.5</EquipDelay>
{scaled(['sharp','blunt','heat','strike','rupture','shock','burn','chem'],0.85)}    </statBases>
    <equippedStatOffsets>
{hb}    </equippedStatOffsets>
    <apparel>
      <layers><li>Overhead</li></layers>
      <bodyPartGroups>{grp}</bodyPartGroups>
      <wornGraphicPath>{VAN}/SZ_Helmets/{k}/{k}</wornGraphicPath>
      <tags>{tg}</tags>
    </apparel>
{recipe_block(research,users,hcost,max(1,skill-1))}  </ThingDef>
""")
    tr_t.append((f'SZ_Helm_{k}',f'{ru} ({hru})',f'{hru.capitalize()} из комплекта «{ru}».'+(' Закрывает всю голову.' if st in HFULL else '')))

def head_gfx(k):
    return ''
    if k=='GasMask': return ''
    a,b=HEADCOL[k]
    return (f"\n      <shaderType>CutoutComplex</shaderType>\n      <color>({a[0]:.2f}, {a[1]:.2f}, {a[2]:.2f})</color>"
            f"\n      <colorTwo>({b[0]:.2f}, {b[1]:.2f}, {b[2]:.2f})</colorTwo>")
for (k,en,ru,tex,layer,groups,col,armor_d,offs_d,val,mass,rec,tags,den,dru) in HEAD:
    research,users,cost,skill,work=rec
    armor=''.join(f'      <{ARMOR[a]}>{v}</{ARMOR[a]}>\n' for a,v in armor_d.items())
    offs=''.join(f'      <{OFFS[a]}>{v}</{OFFS[a]}>\n' for a,v in offs_d.items())
    gr=''.join(f'<li>{g}</li>' for g in groups); tg=''.join(f'<li>SZ_Faction_{t}</li>' for t in tags)
    color=''
    w(f"""
  <ThingDef ParentName="SZ_HeadgearBase">
    <defName>SZ_{k}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den)}</description>
    <graphicData>
      <texPath>{tex if k=='GasMask' else 'Things/Item/SZ_Helmets/'+k}</texPath>
      <graphicClass>Graphic_Single</graphicClass>{head_gfx(k)}
    </graphicData>
    <statBases>
      <MaxHitPoints>120</MaxHitPoints>
      <MarketValue>{val}</MarketValue>
      <Mass>{mass}</Mass>
      <WorkToMake>{work}</WorkToMake>
      <EquipDelay>1.5</EquipDelay>
{armor}    </statBases>
    <equippedStatOffsets>
{offs}    </equippedStatOffsets>
    <apparel>
      <layers><li>{layer}</li></layers>
      <bodyPartGroups>{gr}</bodyPartGroups>
      <wornGraphicPath>{tex}</wornGraphicPath>
      <tags>{tg}</tags>
    </apparel>
{recipe_block(research,users,cost,skill)}  </ThingDef>
""")
    tr_t.append((f'SZ_{k}',ru,dru))

def item_def(dn,en,den,tex,mass,val,stack,cost,research,skill,work,note,extra_comp=''):
    cs=''.join(f'<{k}>{v}</{k}>' for k,v in cost.items())
    return f"""
  <!-- {note} -->
  <ThingDef>
    <defName>{dn}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den)}</description>
    <thingClass>ThingWithComps</thingClass>
    <category>Item</category>
    <drawerType>MapMeshOnly</drawerType>
    <altitudeLayer>Item</altitudeLayer>
    <selectable>true</selectable>
    <alwaysHaulable>true</alwaysHaulable>
    <drawGUIOverlay>true</drawGUIOverlay>
    <rotatable>false</rotatable>
    <pathCost>14</pathCost>
    <useHitPoints>true</useHitPoints>
    <stackLimit>{stack}</stackLimit>
    <tradeability>All</tradeability>
    <techLevel>Industrial</techLevel>
    <thingCategories><li>SZ_Artifacts</li></thingCategories>
    <graphicData>
      <texPath>{tex}</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
    <statBases>
      <MaxHitPoints>100</MaxHitPoints>
      <MarketValue>{val}</MarketValue>
      <Mass>{mass}</Mass>
      <Flammability>0.2</Flammability>
      <WorkToMake>{work}</WorkToMake>
    </statBases>
    <comps><li Class="CompProperties_Forbiddable"/>{extra_comp}</comps>
    <costList>{cs}</costList>
    <recipeMaker>
      <researchPrerequisite>{research}</researchPrerequisite>
      <recipeUsers><li>TableMachining</li></recipeUsers>
      <workSpeedStat>GeneralLaborSpeed</workSpeedStat>
      <workSkill>Crafting</workSkill>
      <skillRequirements><Crafting>{skill}</Crafting></skillRequirements>
    </recipeMaker>
  </ThingDef>
"""
w(item_def('SZ_LeadContainer','lead container',
  'A heavy lead-lined box for an artifact. Each container carried in the inventory blocks the radiation of one active artifact (the strongest first), while the artifact keeps working.',
  'Things/Item/SZ_Gear/LeadContainer',3,120,1,{'Steel':50},'Smithing',3,2500,
  'Свинцовый контейнер: каждый в инвентаре гасит излучение одного активного артефакта (C#: ZoneArtifacts.cs)'))
w(item_def('SZ_RepairKit','repair kit',
  'Patches, sealant and spare plates. Restores 40% of a worn Zone suit. In the inventory it is used automatically when the suit drops below 70%; right-click it on the ground to pick it up and repair right away.',
  'Things/Item/SZ_Gear/RepairKit',1,80,10,{'Steel':15,'Cloth':15,'ComponentIndustrial':1},'Smithing',4,2000,
  'Ремкомплект: +40% прочности костюма; из инвентаря сам при износе ниже 70%, правой кнопкой с земли — сразу (C#: SuitRepair)',
  '<li Class="StalkerZone.CompProperties_ZoneItem"/>'))

# ---------- Каркасы экзоскелета: отдельный слой поверх любой брони ----------
EXO=[
 ('ExoFrame','standard','exoskeleton frame','каркас экзоскелета',dict(carry=100,move=-0.25),1800,18,
  {'Plasteel':80,'ComponentIndustrial':4,'ComponentSpacer':2},['Duty','Freedom','Monolith','Mercenaries'],
  'A powered frame for the legs, hips and shoulders with a power unit on the back. Worn over any armor: carries a huge load, but slows its owner.',
  'Силовой каркас ног, таза и плеч с блоком питания на спине. Надевается поверх любой брони: несёт огромный груз, но замедляет владельца.'),
 ('ExoFrameAssault','assault','assault exoskeleton frame','штурмовой каркас экзоскелета',dict(carry=130,move=-0.3,melee=0.25),2400,24,
  {'Plasteel':110,'ComponentIndustrial':5,'ComponentSpacer':3},['Duty','Monolith','Mercenaries'],
  'A reinforced frame with heavy hydraulics. Carries even more and hits harder in melee.',
  'Усиленный каркас с тяжёлой гидравликой. Несёт ещё больше и сильнее бьёт в ближнем бою.'),
]
EXOCOL=((0.30,0.31,0.33),(0.44,0.46,0.48))
w("""
  <!-- ===== Каркас экзоскелета: свой слой, совместим с любым костюмом, шлемом, рюкзаком ===== -->
  <ApparelLayerDef>
    <defName>SZ_ExoLayer</defName>
    <label>exoskeleton</label>
    <drawOrder>3</drawOrder>
  </ApparelLayerDef>
""")
for (k,kind,en,ru,st,val,mass,cost,tags,den,dru) in EXO:
    offs=''.join(f'      <{n}>{v}</{n}>\n' for n,v in (('SZ_InventoryCapacity',st.get('carry')),('MoveSpeed',st.get('move')),('MeleeDamageFactor',st.get('melee'))) if v)
    cs=''.join(f'<{m}>{c}</{m}>' for m,c in cost.items()); tg=''.join(f'<li>SZ_Faction_{t}</li>' for t in tags)
    a,b=EXOCOL
    w(f"""
  <ThingDef ParentName="ApparelBase">
    <defName>SZ_{k}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den)}</description>
    <techLevel>Spacer</techLevel>
    <tradeability>All</tradeability>
    <thingCategories Inherit="False"><li>ApparelUtility</li></thingCategories>
    <graphicData>
      <texPath>Things/Item/SZ_Exo/{k}</texPath>
      <graphicClass>Graphic_Single</graphicClass>
    </graphicData>
    <statBases>
      <MaxHitPoints>260</MaxHitPoints>
      <MarketValue>{val}</MarketValue>
      <Mass>{mass}</Mass>
      <WorkToMake>24000</WorkToMake>
      <EquipDelay>6</EquipDelay>
      <Flammability>0</Flammability>
    </statBases>
    <equippedStatOffsets>
{offs}    </equippedStatOffsets>
    <apparel>
      <layers><li>SZ_ExoLayer</li></layers>
      <bodyPartGroups><li>Legs</li></bodyPartGroups>
      <wornGraphicPath>{VAN}/SZ_Exo/{k}/{k}</wornGraphicPath>
      <tags>{tg}</tags>
      <careIfWornByCorpse>false</careIfWornByCorpse>
    </apparel>
{recipe_block('PoweredArmor',['FabricationBench'],cost,8)}  </ThingDef>
""")
    tr_t.append((f'SZ_{k}',ru,dru))
w('\n</Defs>\n')
open(f'{M}/Defs/Gear/SZ_Gear.xml','w',encoding='utf-8').write(''.join(o))
tr_t.append(('SZ_LeadContainer','свинцовый контейнер','Тяжёлый ящик со свинцовой обшивкой для артефакта. Каждый контейнер в инвентаре гасит излучение одного активного артефакта (сначала самого сильного), а сам артефакт продолжает действовать.'))
tr_t.append(('SZ_RepairKit','ремкомплект','Заплаты, герметик и запасные пластины. Восстанавливает 40% прочности надетого костюма Зоны. Из инвентаря используется сам, когда костюм изношен ниже 70%; правой кнопкой по ремкомплекту на земле — подобрать и сразу починить.'))

# ---------- Улучшения и ремонт ----------
suit_list=''.join(f'<li>SZ_Suit_{s[0]}</li>' for s in SUITS)
o=[]; w=o.append
w("""<?xml version="1.0" encoding="utf-8"?>
<Defs>

  <!-- Файл сгенерирован Source/Tools/gen_gear.py.
       Улучшения костюмов Зоны. Ставятся на механическом станке рецептом: костюм не
       расходуется, материалы расходуются (C#: RecipeWorker_Suit). Мест под улучшения:
       лёгкий костюм 1, средний 2, тяжёлый/научный/экзо 3. Если места нет, материалы пропадут. -->
""")
tr_u=[]; tr_r=[]
for (k,en,ru,armor_d,slots,rad,psi,mx,research,cost,skill,den,dru) in UPG:
    ao=''.join(f'<{s}>{v}</{s}>' for s,v in armor_d.items())
    extra=(f'\n    <slots>{slots}</slots>' if slots else '')+(f'\n    <radiation>{rad}</radiation>' if rad else '')+(f'\n    <psi>{psi}</psi>' if psi else '')
    mats=''.join(f'\n      <li><filter><thingDefs><li>{m}</li></thingDefs></filter><count>{c}</count></li>' for m,c in cost.items())
    fix=''.join(f'<li>{m}</li>' for m in cost)
    w(f"""
  <StalkerZone.SuitUpgradeDef>
    <defName>SZ_Up_{k}</defName>
    <label>{esc(en)}</label>
    <description>{esc(den)}</description>
    <armorOffsets>{ao}</armorOffsets>{extra}
    <maxPerSuit>{mx}</maxPerSuit>
  </StalkerZone.SuitUpgradeDef>

  <RecipeDef>
    <defName>SZ_Upgrade_{k}</defName>
    <label>upgrade suit: {esc(en)}</label>
    <description>{esc(den)} Uses one free upgrade place of a Zone suit.</description>
    <jobString>Upgrading suit.</jobString>
    <workerClass>StalkerZone.RecipeWorker_Suit</workerClass>
    <workAmount>3000</workAmount>
    <workSpeedStat>GeneralLaborSpeed</workSpeedStat>
    <workSkill>Crafting</workSkill>
    <effectWorking>Smith</effectWorking>
    <soundWorking>Recipe_Smith</soundWorking>
    <recipeUsers><li>TableMachining</li></recipeUsers>
    <researchPrerequisite>{research}</researchPrerequisite>
    <skillRequirements><Crafting>{skill}</Crafting></skillRequirements>
    <ingredients>
      <li><filter><thingDefs>{suit_list}</thingDefs></filter><count>1</count></li>{mats}
    </ingredients>
    <fixedIngredientFilter><thingDefs>{suit_list}{fix}</thingDefs></fixedIngredientFilter>
    <modExtensions>
      <li Class="StalkerZone.SuitRecipeExtension"><upgrade>SZ_Up_{k}</upgrade></li>
    </modExtensions>
  </RecipeDef>
""")
    tr_u.append((f'SZ_Up_{k}',ru,dru))
    tr_r.append((f'SZ_Upgrade_{k}',f'улучшить костюм: {ru}',dru+' Занимает одно свободное место для улучшений костюма Зоны.','Улучшает костюм.'))
w(f"""
  <!-- Ремонт костюма на станке: +60% прочности -->
  <RecipeDef>
    <defName>SZ_RepairSuit</defName>
    <label>repair Zone suit</label>
    <description>Repair a damaged Zone suit: restores 60% of its durability. A worn suit protects worse.</description>
    <jobString>Repairing suit.</jobString>
    <workerClass>StalkerZone.RecipeWorker_Suit</workerClass>
    <workAmount>2000</workAmount>
    <workSpeedStat>GeneralLaborSpeed</workSpeedStat>
    <workSkill>Crafting</workSkill>
    <effectWorking>Smith</effectWorking>
    <soundWorking>Recipe_Smith</soundWorking>
    <recipeUsers><li>TableMachining</li></recipeUsers>
    <researchPrerequisite>Smithing</researchPrerequisite>
    <ingredients>
      <li><filter><thingDefs>{suit_list}</thingDefs><allowedHitPointsPercents>0~0.99</allowedHitPointsPercents></filter><count>1</count></li>
      <li><filter><thingDefs><li>Steel</li></thingDefs></filter><count>20</count></li>
      <li><filter><thingDefs><li>Cloth</li></thingDefs></filter><count>20</count></li>
    </ingredients>
    <fixedIngredientFilter><thingDefs>{suit_list}<li>Steel</li><li>Cloth</li></thingDefs></fixedIngredientFilter>
    <modExtensions>
      <li Class="StalkerZone.SuitRecipeExtension"><repairFraction>0.6</repairFraction></li>
    </modExtensions>
  </RecipeDef>

</Defs>
""")
tr_r.append(('SZ_RepairSuit','отремонтировать костюм Зоны','Починить повреждённый костюм Зоны: восстанавливает 60% прочности. Изношенный костюм защищает хуже.','Ремонтирует костюм.'))
open(f'{M}/Defs/Gear/SZ_SuitUpgrades.xml','w',encoding='utf-8').write(''.join(o))

# ---------- Перевод ----------
for sub in ('ThingDef','StatDef','RecipeDef','StalkerZone.SuitUpgradeDef'):
    os.makedirs(f'{L}/{sub}',exist_ok=True)
def tr_file(path,rows,keys):
    t=['<?xml version="1.0" encoding="utf-8"?>\n<LanguageData>\n']
    for row in rows:
        d=row[0]
        for key,val in zip(keys,row[1:]): t.append(f'  <{d}.{key}>{esc(val)}</{d}.{key}>\n')
    t.append('</LanguageData>\n'); open(path,'w',encoding='utf-8').write(''.join(t))
tr_file(f'{L}/ThingDef/SZ_Gear.xml',tr_t,['label','description'])
tr_file(f'{L}/StalkerZone.SuitUpgradeDef/SZ_SuitUpgrades.xml',tr_u,['label','description'])
tr_file(f'{L}/RecipeDef/SZ_SuitUpgrades.xml',tr_r,['label','description','jobString'])
open(f'{L}/StatDef/SZ_Gear.xml','w',encoding='utf-8').write('''<?xml version="1.0" encoding="utf-8"?>
<LanguageData>
  <SZ_InventoryCapacity.label>грузоподъёмность снаряжения</SZ_InventoryCapacity.label>
  <SZ_InventoryCapacity.description>Сколько дополнительной массы существо может нести в инвентаре и в караване благодаря снаряжению (экзоскелеты, рюкзаки).</SZ_InventoryCapacity.description>
  <SZ_ArtifactSlots.label>ячейки пояса</SZ_ArtifactSlots.label>
  <SZ_ArtifactSlots.description>Сколько артефактов из инвентаря действуют одновременно. По умолчанию одна ячейка, костюм добавляет ещё.</SZ_ArtifactSlots.description>
</LanguageData>
''')

# =====================================================================
# ГРАФИКА: Source/Tools/suit_art4.py — реалистичный стиль: цвет и камуфляж запечены
# в текстуру, тональные линии, тени под деталями, стропа и пряжки, стройные шлемы.
# =====================================================================
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suit_art4 as art
BODIES=['Male','Female','Thin','Fat','Hulk']
def save_icon(im,folder,name):
    bb=im.getchannel('A').getbbox(); side=max(bb[2]-bb[0],bb[3]-bb[1])+16
    cx,cy=(bb[0]+bb[2])//2,(bb[1]+bb[3])//2
    os.makedirs(f'{T}/Things/Item/{folder}',exist_ok=True)
    im.crop((cx-side//2,cy-side//2,cx+side//2,cy+side//2)).resize((128,128),Image.LANCZOS).save(f'{T}/Things/Item/{folder}/{name}.png')
ONLY=set(x for x in os.environ.get('SZ_ONLY','').split(',') if x)   # частями: SZ_ONLY=Duty,Freedom или EXTRA
if os.environ.get('SZ_SKIP_SUIT_ART')!='1':
    for n,(k,en,ru,cls,cols,*_rest) in enumerate(SUITS):
        if ONLY and k not in ONLY: continue
        look=LOOK[k]; st=HSTYLE_BY_SUIT.get(k,HSTYLE[cls]); c_cls='bandit' if k in ('Bandit','BanditCoat') and cls=='light' else cls
        for folder in ('SZ_Suits','SZ_Helmets'): os.makedirs(f'{T}/{VAN}/{folder}/{k}',exist_ok=True)
        for body in BODIES:
            for view in ('south','east','north'):
                art.render_coverall(c_cls,look,body,view,seed=n*31).save(f'{T}/{VAN}/SZ_Suits/{k}/{k}_{body}_{view}.png',optimize=True)
        for view in ('south','east','north'):
            art.render_helmet(st,look,view,seed=n*31).save(f'{T}/{VAN}/SZ_Helmets/{k}/{k}_{view}.png',optimize=True)
        save_icon(art.render_coverall(c_cls,look,'Male','south',seed=n*31),'SZ_Suits',k)
        save_icon(art.render_helmet(st,look,'south',seed=n*31),'SZ_Helmets',k)
        print('suit',k,flush=True)
    if not ONLY or 'EXTRA' in ONLY:
        for k,st in (('Helmet_Stalker','combat'),('Helmet_Psi','psi')):
            os.makedirs(f'{T}/{VAN}/SZ_Helmets/{k}',exist_ok=True)
            for view in ('south','east','north'):
                art.render_helmet(st,LOOK[k],view).save(f'{T}/{VAN}/SZ_Helmets/{k}/{k}_{view}.png',optimize=True)
            save_icon(art.render_helmet(st,LOOK[k],'south'),'SZ_Helmets',k)
        for (k,kind,*_r) in EXO:
            os.makedirs(f'{T}/{VAN}/SZ_Exo/{k}',exist_ok=True)
            for body in BODIES:
                for view in ('south','east','north'):
                    art.render_exo(kind,body,view).save(f'{T}/{VAN}/SZ_Exo/{k}/{k}_{body}_{view}.png',optimize=True)
            save_icon(art.render_exo(kind,'Male','north'),'SZ_Exo',k)
        print('helmets+exo done',flush=True)

# ---------- Остальная графика ----------
def save(path,img): os.makedirs(os.path.dirname(path),exist_ok=True); img.save(path)
def blank(n): return Image.new('RGBA',(n,n),(0,0,0,0))
RUB=(70,78,66,255); RUBD=(40,45,38,255); GLASS=(150,185,190,255); FIL=(95,100,90,255)
def mask_south():
    img=blank(128); d=ImageDraw.Draw(img)
    d.ellipse([42,44,86,98],fill=RUB,outline=RUBD,width=2)
    for x in (52,76):
        d.ellipse([x-9,56,x+9,74],fill=GLASS,outline=RUBD,width=3); d.ellipse([x-4,60,x,64],fill=(210,230,235,255))
    d.ellipse([54,82,74,104],fill=FIL,outline=RUBD,width=2)
    for y in (88,93,98): d.line([(58,y),(70,y)],fill=RUBD,width=1)
    return img
def mask_east():
    img=blank(128); d=ImageDraw.Draw(img)
    d.polygon([(62,46),(84,52),(88,92),(70,98),(60,90)],fill=RUB,outline=RUBD)
    d.ellipse([72,56,88,74],fill=GLASS,outline=RUBD,width=3); d.rectangle([82,84,96,98],fill=FIL,outline=RUBD)
    d.line([(60,60),(44,58)],fill=RUBD,width=3); return img
def mask_north():
    img=blank(128); d=ImageDraw.Draw(img)
    for y in (58,72,86): d.line([(44,y),(84,y)],fill=RUBD,width=3)
    d.line([(64,52),(64,92)],fill=RUBD,width=3); return img
G=f'{T}/Things/Pawn/Humanlike/Apparel/SZ_GasMask/SZ_GasMask'
for view in ('south','east','north'): save(f'{G}_{view}.png',art.render_gasmask(view))
gm=art.render_gasmask('south'); bb=gm.getchannel('A').getbbox(); side=max(bb[2]-bb[0],bb[3]-bb[1])+16
gcx,gcy=(bb[0]+bb[2])//2,(bb[1]+bb[3])//2
save(f'{G}.png',gm.crop((gcx-side//2,gcy-side//2,gcx+side//2,gcy+side//2)).resize((128,128),Image.LANCZOS))
img=blank(64); d=ImageDraw.Draw(img)
d.rounded_rectangle([10,16,54,54],radius=5,fill=(120,124,128,255),outline=(50,52,55,255),width=2)
d.rectangle([10,24,54,30],fill=(90,92,96,255)); d.rectangle([28,10,36,18],fill=(80,82,85,255)); d.ellipse([24,34,40,50],fill=(240,200,40,255))
save(f'{T}/Things/Item/SZ_Gear/LeadContainer.png',img)
img=blank(64); d=ImageDraw.Draw(img)                                   # ремкомплект
d.rounded_rectangle([8,20,56,52],radius=5,fill=(170,60,45,255),outline=(80,25,20,255),width=2)
d.rectangle([24,14,40,22],fill=(90,90,90,255)); d.rectangle([28,30,36,46],fill=(240,240,235,255)); d.rectangle([20,34,44,42],fill=(240,240,235,255))
save(f'{T}/Things/Item/SZ_Gear/RepairKit.png',img)
img=blank(64); d=ImageDraw.Draw(img)                                   # иконка: болт
pts=[(32+20*math.cos(a),32+20*math.sin(a)) for a in [i*math.pi/3 for i in range(6)]]
d.polygon(pts,fill=(170,170,165,255),outline=(70,70,68,255)); d.ellipse([24,24,40,40],fill=(40,40,40,255))
d.line([(8,58),(22,44)],fill=(200,200,195,255),width=4); save(f'{T}/UI/SZ/Bolt.png',img)
img=blank(64); d=ImageDraw.Draw(img)                                   # иконка: пояс
d.rounded_rectangle([8,26,56,46],radius=6,fill=(120,90,55,255),outline=(60,40,20,255),width=2)
for x in (16,32,48): d.ellipse([x-6,30,x+6,42],fill=(90,200,240,255),outline=(20,70,110,255))
save(f'{T}/UI/SZ/Belt.png',img)
img=blank(64); d=ImageDraw.Draw(img)                                   # иконка: ремонт
d.line([(14,50),(42,22)],fill=(190,190,185,255),width=8); d.ellipse([36,10,56,30],fill=(190,190,185,255)); d.ellipse([42,16,50,24],fill=(0,0,0,0))
d.rounded_rectangle([8,40,30,58],radius=4,fill=(170,60,45,255)); save(f'{T}/UI/SZ/Repair.png',img)

# ---------- Звук болта ----------
SR=22050
def clink(seed):
    rnd=random.Random(seed); n=int(.35*SR); out=[]
    fs=[rnd.uniform(1900,2300),rnd.uniform(3100,3500),rnd.uniform(5000,5600)]
    for i in range(n):
        t=i/SR; s=sum(math.sin(2*math.pi*f*t)*math.exp(-t*(12+j*6)) for j,f in enumerate(fs))
        if i<200: s+=rnd.uniform(-1,1)*(1-i/200)
        out.append(s)
    pk=max(abs(x) for x in out); return [x/pk*0.85 for x in out]
os.makedirs(f'{M}/Sounds/SZ/Bolt',exist_ok=True)
for i in range(2):
    with wave.open(f'{M}/Sounds/SZ/Bolt/bolt_{i}.wav','wb') as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR)
        wv.writeframes(b''.join(struct.pack('<h',int(x*32767)) for x in clink(300+i)))
print('suits:',len(SUITS),'headgear:',len(HEAD),'upgrades:',len(UPG))
