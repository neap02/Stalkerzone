using System.Collections.Generic;

namespace StalkerZone
{
    /// <summary>Какой эффект показывать у аномалии, когда рядом колонист.</summary>
    public enum AnomalyFleck { Dust, Sparks, Heat, Air }

    /// <summary>
    /// Повадки каждого типа аномалии (только C#). Урон и радиус взрыва
    /// берутся из XML (CompProperties_Explosive), здесь — поведение.
    /// Тип = часть defName: SZ_Anomaly_[Тип]_[Артефакт].
    /// </summary>
    public class AnomalyProfile
    {
        public float triggerRadius = 1.5f;     // срабатывает, если пешка ближе (0 = не срабатывает)
        public int cooldownTicks = 300;        // перезарядка после срабатывания (60 тиков = 1 сек. на x1)
        public float pullRadius;               // затягивание (0 = нет)
        public int pullInterval = 60;          // как часто тянет на клетку (кратно 30)
        public bool throwsInsteadOfExplosion;  // трамплин: только отбрасывает
        public bool throwsAfterExplosion;      // карусель: взрыв, затем швыряет
        public int throwDistance = 4;
        public float throwDamage = 8f;
        public int stunTicks = 60;
        public bool chainLightning;            // электра: разряд по соседям
        public bool leavesPuddle;              // холодец: едкая лужа
        public int clusterMin = 3;             // размер скопления
        public int clusterMax = 6;
        public float memberSpacing = 3f;       // расстояние между аномалиями в скоплении
        public float artifactChance = 0.4f;    // шанс артефакта рядом с каждой аномалией
        public AnomalyFleck fleck = AnomalyFleck.Dust;

        private static readonly AnomalyProfile Default = new AnomalyProfile();
        private static readonly Dictionary<string, AnomalyProfile> profiles = new Dictionary<string, AnomalyProfile>
        {
            ["Springboard"] = new AnomalyProfile { cooldownTicks = 180, throwsInsteadOfExplosion = true, throwDistance = 5, throwDamage = 8f, stunTicks = 90 },
            ["Vortex"] = new AnomalyProfile { cooldownTicks = 600, pullRadius = 4.9f, pullInterval = 60, clusterMin = 2, clusterMax = 3, memberSpacing = 6f, artifactChance = 0.5f },
            ["Whirligig"] = new AnomalyProfile { cooldownTicks = 360, pullRadius = 2.9f, pullInterval = 60, throwsAfterExplosion = true, throwDistance = 4, stunTicks = 60, clusterMax = 5, memberSpacing = 4f },
            ["Meatgrinder"] = new AnomalyProfile { cooldownTicks = 900, pullRadius = 2.4f, pullInterval = 30, clusterMin = 2, clusterMax = 4, memberSpacing = 4f },
            ["Electro"] = new AnomalyProfile { triggerRadius = 1.9f, cooldownTicks = 240, chainLightning = true, fleck = AnomalyFleck.Sparks },
            ["Burner"] = new AnomalyProfile { cooldownTicks = 360, fleck = AnomalyFleck.Heat },
            ["Comet"] = new AnomalyProfile { triggerRadius = 0f, clusterMin = 1, clusterMax = 2, memberSpacing = 7f, artifactChance = 0.6f, fleck = AnomalyFleck.Heat },
            ["FruitPunch"] = new AnomalyProfile { cooldownTicks = 480, leavesPuddle = true, fleck = AnomalyFleck.Air },
            ["BurntFuzz"] = new AnomalyProfile { triggerRadius = 2.9f, cooldownTicks = 300, clusterMax = 5, memberSpacing = 4f },
        };

        public static AnomalyProfile For(string type)
        {
            return type != null && profiles.TryGetValue(type, out AnomalyProfile p) ? p : Default;
        }
    }
}
