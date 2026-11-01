using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>Подсказка "видно вблизи" (без детектора).</summary>
    public enum AnomalyFleck { Dust, Sparks, Heat, Air }

    /// <summary>Как выглядит срабатывание аномалии (вместо взрыва).</summary>
    public enum DischargeFx { Gravity, Electric, Fire, Acid, Fuzz }

    /// <summary>
    /// Повадки каждого типа аномалии (только C#). Тип = часть defName: SZ_Anomaly_[Тип]_[Артефакт].
    /// Урон и пробитие брони берутся из DamageDef (XML, генератор gen_zone.py),
    /// категория урона определяет, какая защита костюма от него спасает (SZ_Protection.xml).
    /// </summary>
    public class AnomalyProfile
    {
        // --- срабатывание ---
        public float triggerRadius = 1.5f;     // срабатывает, если пешка ближе (0 = не срабатывает)
        public int cooldownTicks = 300;        // перезарядка (60 тиков = 1 сек. на x1); затягивание в это время стоит
        public float effectRadius = 1.9f;      // кого задевает срабатывание
        public string damageDefName;           // DamageDef аномалии: урон, пробитие, категория защиты
        public DischargeFx fx = DischargeFx.Gravity;
        public string soundDefName;
        public string idleSoundDefName;
        // --- обход ---
        public float avoidRadius = 2.5f;       // зона, которую пешки стараются обходить
        // --- затягивание ---
        public float pullRadius;               // 0 = не тянет
        public int pullInterval = 60;          // кратно 30
        public float pullStrength = 0.7f;      // шанс рывка у самого центра; к краю падает до 0
        // --- особые повадки ---
        public bool throwsInsteadOfDamage;     // трамплин
        public bool throwsAfterDischarge;      // карусель
        public int throwDistance = 4;
        public int stunTicks = 60;
        public bool chainLightning;            // электра
        public bool leavesPuddle;              // холодец
        // --- поле ---
        public int clusterMin = 3;
        public int clusterMax = 6;
        public float memberSpacing = 3f;
        public float artifactChance = 0.4f;
        public AnomalyFleck fleck = AnomalyFleck.Dust;

        private bool resolved;
        private DamageDef damageDef;
        private SoundDef sound, idleSound;

        public DamageDef Damage { get { Resolve(); return damageDef; } }
        public SoundDef Sound { get { Resolve(); return sound; } }
        public SoundDef IdleSound { get { Resolve(); return idleSound; } }
        public float DamageAmount => Damage != null ? Damage.defaultDamage : 0f;
        public float ArmorPenetration => Damage != null && Damage.defaultArmorPenetration >= 0f ? Damage.defaultArmorPenetration : 0f;

        private void Resolve()
        {
            if (resolved) return;
            resolved = true;
            if (damageDefName != null) damageDef = DefDatabase<DamageDef>.GetNamedSilentFail(damageDefName);
            if (soundDefName != null) sound = DefDatabase<SoundDef>.GetNamedSilentFail(soundDefName);
            if (idleSoundDefName != null) idleSound = DefDatabase<SoundDef>.GetNamedSilentFail(idleSoundDefName);
        }

        private const string GravD = "SZ_Gravity_Discharge", GravI = "SZ_Gravity_Idle";

        private static readonly AnomalyProfile Default = new AnomalyProfile();
        private static readonly Dictionary<string, AnomalyProfile> profiles = new Dictionary<string, AnomalyProfile>
        {
            // Трамплин: отбрасывает и оглушает (урон: удар, 12)
            ["Springboard"] = new AnomalyProfile { cooldownTicks = 180, throwsInsteadOfDamage = true, throwDistance = 5, stunTicks = 90,
                damageDefName = "SZ_GravityCrushLight", avoidRadius = 2.5f,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity },
            // Воронка: тянет с 5 клеток, в центре — удар 35. После разряда 10 сек. не тянет: время уйти.
            ["Vortex"] = new AnomalyProfile { cooldownTicks = 600, pullRadius = 4.9f, pullInterval = 60, pullStrength = 0.8f, effectRadius = 1.9f,
                damageDefName = "SZ_GravityCrushHeavy", avoidRadius = 5.5f,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity,
                clusterMin = 2, clusterMax = 3, memberSpacing = 7f, artifactChance = 0.5f },
            // Карусель: подтягивает с 3 клеток, удар 22 и отшвыривает
            ["Whirligig"] = new AnomalyProfile { cooldownTicks = 360, pullRadius = 2.9f, pullInterval = 60, pullStrength = 0.6f, effectRadius = 1.9f,
                damageDefName = "SZ_GravityCrush", throwsAfterDischarge = true, throwDistance = 4, stunTicks = 60, avoidRadius = 3.5f,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity, clusterMax = 5, memberSpacing = 4f },
            // Мясорубка: самая опасная. Тянет сильно и часто, разрыв 40. Уйти можно только сразу после разряда.
            ["Meatgrinder"] = new AnomalyProfile { cooldownTicks = 900, pullRadius = 2.9f, pullInterval = 30, pullStrength = 0.9f, effectRadius = 1.5f,
                damageDefName = "SZ_GravityShred", avoidRadius = 3.5f,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity, clusterMin = 2, clusterMax = 4, memberSpacing = 4f },
            // Электра: разряд 18 и цепная молния ещё на троих
            ["Electro"] = new AnomalyProfile { triggerRadius = 2.2f, cooldownTicks = 240, effectRadius = 2.4f, chainLightning = true,
                damageDefName = "SZ_ElectricDischarge", avoidRadius = 3f,
                soundDefName = "SZ_Electro_Discharge", idleSoundDefName = "SZ_Electro_Idle", fx = DischargeFx.Electric, fleck = AnomalyFleck.Sparks },
            // Жарка: выброс пламени 22
            ["Burner"] = new AnomalyProfile { cooldownTicks = 300, effectRadius = 1.9f, damageDefName = "SZ_ThermalBurn", avoidRadius = 2.5f,
                soundDefName = "SZ_Fire_Discharge", idleSoundDefName = "SZ_Fire_Idle", fx = DischargeFx.Fire, fleck = AnomalyFleck.Heat },
            // Комета: ходит по кругу радиусом 3, обжигает 14
            ["Comet"] = new AnomalyProfile { triggerRadius = 0f, damageDefName = "SZ_CometBurn", avoidRadius = 4.9f,
                soundDefName = "SZ_Fire_Discharge", idleSoundDefName = "SZ_Fire_Idle", fx = DischargeFx.Fire,
                clusterMin = 1, clusterMax = 2, memberSpacing = 8f, artifactChance = 0.6f, fleck = AnomalyFleck.Heat },
            // Холодец: всплеск 16 и едкая лужа
            ["FruitPunch"] = new AnomalyProfile { cooldownTicks = 480, effectRadius = 1.9f, leavesPuddle = true,
                damageDefName = "SZ_ChemicalBurn", avoidRadius = 2.5f,
                soundDefName = "SZ_Acid_Discharge", idleSoundDefName = "SZ_Acid_Idle", fx = DischargeFx.Acid, fleck = AnomalyFleck.Air },
            // Жгучий пух: слабо (9), но широко и часто
            ["BurntFuzz"] = new AnomalyProfile { triggerRadius = 2.9f, cooldownTicks = 240, effectRadius = 2.9f,
                damageDefName = "SZ_FuzzSting", avoidRadius = 3.5f,
                soundDefName = "SZ_Fuzz_Discharge", fx = DischargeFx.Fuzz, clusterMax = 5, memberSpacing = 4f },
        };

        public static AnomalyProfile For(string type)
        {
            return type != null && profiles.TryGetValue(type, out AnomalyProfile p) ? p : Default;
        }
    }
}
