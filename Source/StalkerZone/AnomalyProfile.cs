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
    /// Аномалия не взрывается: она бьёт своим типом урона тех, кто в радиусе действия,
    /// с собственным звуком и визуальным эффектом.
    /// </summary>
    public class AnomalyProfile
    {
        // --- срабатывание ---
        public float triggerRadius = 1.5f;     // срабатывает, если пешка ближе (0 = не срабатывает)
        public int cooldownTicks = 300;        // перезарядка (60 тиков = 1 сек. на x1)
        public float effectRadius = 1.9f;      // кого задевает срабатывание
        public string damageDefName;           // свой тип урона (DamageDef из XML)
        public float damageAmount = 10f;
        public float armorPenetration = 0.2f;
        public DischargeFx fx = DischargeFx.Gravity;
        public string soundDefName;            // звук срабатывания
        public string idleSoundDefName;        // звук рядом (гул, треск, бульканье)
        // --- особые повадки ---
        public float pullRadius;               // затягивание (0 = нет)
        public int pullInterval = 60;          // кратно 30
        public bool throwsInsteadOfDamage;     // трамплин: только отбрасывает
        public bool throwsAfterDischarge;      // карусель: удар, затем швыряет
        public int throwDistance = 4;
        public float throwDamage = 8f;
        public int stunTicks = 60;
        public bool chainLightning;            // электра: разряд по соседям
        public bool leavesPuddle;              // холодец: едкая лужа
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
            ["Springboard"] = new AnomalyProfile { cooldownTicks = 180, throwsInsteadOfDamage = true, throwDistance = 5, throwDamage = 8f, stunTicks = 90,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity },
            ["Vortex"] = new AnomalyProfile { cooldownTicks = 600, pullRadius = 4.9f, pullInterval = 60, effectRadius = 1.9f,
                damageDefName = "SZ_GravityCrushHeavy", damageAmount = 24f, armorPenetration = 0.3f,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity,
                clusterMin = 2, clusterMax = 3, memberSpacing = 6f, artifactChance = 0.5f },
            ["Whirligig"] = new AnomalyProfile { cooldownTicks = 360, pullRadius = 2.9f, pullInterval = 60, effectRadius = 1.9f,
                damageDefName = "SZ_GravityCrush", damageAmount = 18f, throwsAfterDischarge = true, throwDistance = 4, stunTicks = 60,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity, clusterMax = 5, memberSpacing = 4f },
            ["Meatgrinder"] = new AnomalyProfile { cooldownTicks = 900, pullRadius = 2.4f, pullInterval = 30, effectRadius = 1.5f,
                damageDefName = "SZ_GravityShred", damageAmount = 30f, armorPenetration = 0.35f,
                soundDefName = GravD, idleSoundDefName = GravI, fx = DischargeFx.Gravity, clusterMin = 2, clusterMax = 4, memberSpacing = 4f },
            ["Electro"] = new AnomalyProfile { triggerRadius = 1.9f, cooldownTicks = 240, effectRadius = 2.4f,
                damageDefName = "SZ_ElectricDischarge", damageAmount = 14f, armorPenetration = 0.3f, chainLightning = true,
                soundDefName = "SZ_Electro_Discharge", idleSoundDefName = "SZ_Electro_Idle", fx = DischargeFx.Electric, fleck = AnomalyFleck.Sparks },
            ["Burner"] = new AnomalyProfile { cooldownTicks = 360, effectRadius = 1.9f,
                damageDefName = "SZ_ThermalBurn", damageAmount = 16f, armorPenetration = 0.25f,
                soundDefName = "SZ_Fire_Discharge", idleSoundDefName = "SZ_Fire_Idle", fx = DischargeFx.Fire, fleck = AnomalyFleck.Heat },
            ["Comet"] = new AnomalyProfile { triggerRadius = 0f, damageDefName = "SZ_ThermalBurn", damageAmount = 8f,
                soundDefName = "SZ_Fire_Discharge", idleSoundDefName = "SZ_Fire_Idle", fx = DischargeFx.Fire,
                clusterMin = 1, clusterMax = 2, memberSpacing = 7f, artifactChance = 0.6f, fleck = AnomalyFleck.Heat },
            ["FruitPunch"] = new AnomalyProfile { cooldownTicks = 480, effectRadius = 1.9f, leavesPuddle = true,
                damageDefName = "SZ_ChemicalBurn", damageAmount = 12f,
                soundDefName = "SZ_Acid_Discharge", idleSoundDefName = "SZ_Acid_Idle", fx = DischargeFx.Acid, fleck = AnomalyFleck.Air },
            ["BurntFuzz"] = new AnomalyProfile { triggerRadius = 2.9f, cooldownTicks = 300, effectRadius = 2.9f,
                damageDefName = "SZ_FuzzSting", damageAmount = 7f, armorPenetration = 0.1f,
                soundDefName = "SZ_Fuzz_Discharge", fx = DischargeFx.Fuzz, clusterMax = 5, memberSpacing = 4f },
        };

        public static AnomalyProfile For(string type)
        {
            return type != null && profiles.TryGetValue(type, out AnomalyProfile p) ? p : Default;
        }
    }
}
