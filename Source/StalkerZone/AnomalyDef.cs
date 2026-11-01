using System.Collections.Generic;
using UnityEngine;
using Verse;

namespace StalkerZone
{
    /// <summary>Подсказка "видно вблизи" (без детектора).</summary>
    public enum AnomalyFleck { Dust, Sparks, Heat, Air }

    /// <summary>Как выглядит срабатывание аномалии.</summary>
    public enum DischargeFx { Gravity, Electric, Fire, Acid, Fuzz }

    /// <summary>Какой артефакт прячется рядом с аномалией этого типа и как часто.</summary>
    public class AnomalyArtifact
    {
        public ThingDef artifact;
        public float weight = 1f;   // относительная частота среди артефактов этого типа
        public int tier = 1;        // 1 — обычный, 2 — необычный, 3 — редкий (какой детектор найдёт)
    }

    /// <summary>
    /// Тип аномалии. Это НЕ ThingDef: аномалия — явление на карте, а не предмет.
    /// Её нельзя выбрать, атаковать, перенести, купить или заспавнить как вещь.
    /// Экземпляры хранит MapComponent_Zone, рисует ZoneMats.
    /// Все значения задаются в XML (генератор Source/Tools/gen_zone.py).
    /// </summary>
    public class AnomalyDef : Def
    {
        // --- вид ---
        public string texPath;                     // папка с кадрами анимации
        public float drawSize = 1.8f;
        public float fps = 8f;                     // кадров в секунду
        public Color glowColor = new Color(1f, 1f, 1f, 0.4f);
        public float glowSize = 3f;
        public AnomalyFleck fleck = AnomalyFleck.Dust;

        // --- срабатывание ---
        public float triggerRadius = 1.5f;         // 0 = не срабатывает на приближение
        public int cooldownTicks = 300;            // перезарядка; затягивание в это время стоит
        public float effectRadius = 1.9f;
        public DamageDef damage;                   // урон, пробитие и категория защиты
        public DischargeFx fx = DischargeFx.Gravity;
        public SoundDef sound;
        public SoundDef idleSound;

        // --- обход ---
        public float avoidRadius = 2.5f;

        // --- затягивание ---
        public float pullRadius;
        public int pullInterval = 60;
        public float pullStrength = 0.7f;

        // --- особые повадки ---
        public bool throwsInsteadOfDamage;
        public bool throwsAfterDischarge;
        public int throwDistance = 4;
        public int stunTicks = 60;
        public bool chainLightning;
        public bool leavesPuddle;
        public bool moves;                         // комета
        public int routeRadius = 3;

        // --- поле ---
        public float per10k = 0.3f;                // сколько таких аномалий на 10 000 клеток
        public int clusterMin = 3;
        public int clusterMax = 6;
        public float memberSpacing = 3f;
        public float artifactChance = 0.4f;
        public List<AnomalyArtifact> artifacts = new List<AnomalyArtifact>();

        public float DamageAmount => damage != null ? damage.defaultDamage : 0f;
        public float ArmorPenetration => damage != null && damage.defaultArmorPenetration >= 0f ? damage.defaultArmorPenetration : 0f;
    }
}
