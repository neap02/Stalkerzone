using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>Данные артефакта (в XML у ThingDef артефакта, modExtensions).</summary>
    public class ArtifactExtension : DefModExtension
    {
        public float radiationPerDay;      // облучение владельца в сутки (если не в свинцовом контейнере)
        public HediffDef effectHediff;     // эффект артефакта: стадии для 1..5 одинаковых артефактов
    }

    /// <summary>
    /// Артефакты работают из инвентаря:
    /// - число слотов = стат SZ_ArtifactSlots (1 "в кармане" + бонус костюма, максимум 5);
    /// - каждый свинцовый контейнер в инвентаре гасит излучение одного артефакта
    ///   (сначала самых "грязных"), эффект артефакта при этом сохраняется;
    /// - эффект — хедифф артефакта, его тяжесть = число одинаковых активных артефактов.
    /// </summary>
    public static class ZoneArtifacts
    {
        public const int MaxSlots = 5;
        public const int Interval = 250;

        private static readonly HashSet<HediffDef> effectHediffs = new HashSet<HediffDef>();
        private static readonly List<Thing> active = new List<Thing>();
        private static readonly Dictionary<HediffDef, int> counts = new Dictionary<HediffDef, int>();
        private static readonly List<Hediff> toRemove = new List<Hediff>();

        public static int ArtifactTypes => effectHediffs.Count;

        public static void Init()
        {
            effectHediffs.Clear();
            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                ArtifactExtension ext = def.GetModExtension<ArtifactExtension>();
                if (ext?.effectHediff != null)
                    effectHediffs.Add(ext.effectHediff);
            }
        }

        public static void TickPawn(Pawn pawn)
        {
            if (pawn.Dead || pawn.inventory == null || pawn.health == null || !pawn.RaceProps.Humanlike)
                return;

            SuitBonuses.Of(pawn, out int bonusSlots, out _, out _);   // улучшения костюма
            int slots = Math.Min(MaxSlots, (int)Math.Floor(pawn.GetStatValue(SZ_DefOf.SZ_ArtifactSlots) + 0.001f) + bonusSlots);
            active.Clear();
            int containers = 0;
            foreach (Thing t in pawn.inventory.innerContainer)
            {
                if (t.def == SZ_DefOf.SZ_LeadContainer)
                    containers += t.stackCount;
                else if (active.Count < slots && t.def.GetModExtension<ArtifactExtension>() != null)
                    active.Add(t);
            }

            // Излучение: контейнеры гасят самые сильные артефакты
            active.Sort((a, b) => Rate(b).CompareTo(Rate(a)));
            float dose = 0f;
            for (int i = containers; i < active.Count; i++)
                dose += Rate(active[i]);
            if (dose > 0f)
                ZoneEffects.AddRadiation(pawn, dose * Interval / 60000f);

            // Эффекты: по хедиффу на тип артефакта, тяжесть = сколько таких активно
            counts.Clear();
            foreach (Thing t in active)
            {
                HediffDef h = t.def.GetModExtension<ArtifactExtension>().effectHediff;
                if (h != null)
                    counts[h] = (counts.TryGetValue(h, out int c) ? c : 0) + 1;
            }
            toRemove.Clear();
            foreach (Hediff h in pawn.health.hediffSet.hediffs)
            {
                if (effectHediffs.Contains(h.def) && !counts.ContainsKey(h.def))
                    toRemove.Add(h);
            }
            foreach (Hediff h in toRemove)
                pawn.health.RemoveHediff(h);
            foreach (KeyValuePair<HediffDef, int> kv in counts)
            {
                Hediff h = pawn.health.hediffSet.GetFirstHediffOfDef(kv.Key);
                if (h == null)
                {
                    h = HediffMaker.MakeHediff(kv.Key, pawn);
                    h.Severity = kv.Value;
                    pawn.health.AddHediff(h);
                }
                else if (Math.Abs(h.Severity - kv.Value) > 0.01f)
                {
                    h.Severity = kv.Value;
                }
            }
            active.Clear();
        }

        private static float Rate(Thing t)
        {
            ArtifactExtension ext = t.def.GetModExtension<ArtifactExtension>();
            return ext != null ? ext.radiationPerDay : 0f;
        }
    }
}
