using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>Общие эффекты Зоны: облучение, пси, разряды аномалий, перемещение пешек.</summary>
    public static class ZoneEffects
    {
        private const float PsiBreakMinSeverity = 0.45f;
        private const float PsiBreakMaxSeverity = 0.7f;
        private const float PsiBreakChancePerDose = 0.05f;
        private const float ChainDamage = 10f;

        private static readonly List<Pawn> tmpChain = new List<Pawn>();

        // ---------- Радиация и пси ----------
        public static void AddRadiation(Pawn pawn, float dose)
        {
            if (pawn == null || pawn.Dead || !pawn.RaceProps.IsFlesh)
                return;
            float resistance = pawn.GetStatValue(SZ_DefOf.SZ_RadiationResistance);
            dose *= 1f - Math.Min(1f, Math.Max(0f, resistance));
            if (dose > 0f)
                HealthUtility.AdjustSeverity(pawn, SZ_DefOf.SZ_Radiation, dose);
        }

        /// <summary>Пси-доза × пси-чувствительность. Пси-глухие не страдают.</summary>
        public static void AddPsi(Pawn pawn, float dose)
        {
            if (pawn == null || pawn.Dead || !pawn.RaceProps.IsFlesh)
                return;
            dose *= Math.Max(0f, pawn.GetStatValue(StatDefOf.PsychicSensitivity));
            if (dose <= 0f)
                return;
            HealthUtility.AdjustSeverity(pawn, SZ_DefOf.SZ_PsiExposure, dose);
            TryPsiBreak(pawn);
        }

        private static void TryPsiBreak(Pawn pawn)
        {
            if (!pawn.RaceProps.Humanlike || pawn.InMentalState || pawn.Downed)
                return;
            Hediff psi = pawn.health.hediffSet.GetFirstHediffOfDef(SZ_DefOf.SZ_PsiExposure);
            if (psi == null || psi.Severity < PsiBreakMinSeverity || psi.Severity >= PsiBreakMaxSeverity)
                return;
            if (Rand.Chance(PsiBreakChancePerDose))
                pawn.mindState?.mentalStateHandler?.TryStartMentalState(MentalStateDefOf.Wander_Psychotic, "SZ_PsiBreakReason".Translate());
        }

        // ---------- Аномалии ----------
        /// <summary>
        /// Разряд аномалии: взрыв с уроном и радиусом из её CompProperties_Explosive (XML).
        /// Сама аномалия не страдает — она вечная.
        /// </summary>
        public static void Explode(Thing anomaly)
        {
            CompProperties_Explosive props = anomaly.def.GetCompProperties<CompProperties_Explosive>();
            if (props == null || props.explosiveDamageType == null || !anomaly.Spawned)
                return;
            GenExplosion.DoExplosion(anomaly.Position, anomaly.Map, props.explosiveRadius, props.explosiveDamageType, anomaly,
                ignoredThings: new List<Thing> { anomaly });
        }

        /// <summary>Электра: разряд перескакивает на до count случайных пешек в радиусе.</summary>
        public static void ChainLightning(Thing anomaly, float radius, int count)
        {
            Map map = anomaly.Map;
            PawnsAround(anomaly.Position, map, radius, tmpChain);
            int hit = 0;
            foreach (Pawn target in tmpChain.InRandomOrder())
            {
                if (hit >= count)
                    break;
                FleckMaker.ThrowLightningGlow(target.DrawPos, map, 1.5f);
                FleckMaker.ThrowMicroSparks(target.DrawPos, map);
                target.TakeDamage(new DamageInfo(SZ_DefOf.SZ_ElectricDischarge, ChainDamage, 0.3f, -1f, anomaly));
                hit++;
            }
            tmpChain.Clear();
        }

        /// <summary>Отбрасывает пешку от клетки (или в случайную сторону) до препятствия.</summary>
        public static void ThrowPawn(Pawn pawn, IntVec3 from, int distance, bool randomDirection)
        {
            Map map = pawn.Map;
            IntVec3 dir = randomDirection
                ? GenAdj.AdjacentCells[Rand.Range(0, 8)]
                : new IntVec3(Math.Sign(pawn.Position.x - from.x), 0, Math.Sign(pawn.Position.z - from.z));
            if (dir == IntVec3.Zero)
                dir = GenAdj.AdjacentCells[Rand.Range(0, 8)];

            IntVec3 cur = pawn.Position;
            IntVec3 dest = cur;
            for (int i = 0; i < distance; i++)
            {
                cur += dir;
                if (!cur.InBounds(map) || !cur.Walkable(map))
                    break;
                dest = cur;
            }
            if (dest != pawn.Position)
                MovePawn(pawn, dest);
        }

        /// <summary>Мгновенно переносит пешку в клетку.</summary>
        public static void MovePawn(Pawn pawn, IntVec3 dest)
        {
            pawn.pather?.StopDead();
            pawn.Position = dest;
            pawn.Notify_Teleported();
        }

        /// <summary>Живые пешки в радиусе вокруг клетки.</summary>
        public static void PawnsAround(IntVec3 center, Map map, float radius, List<Pawn> result)
        {
            result.Clear();
            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(center, map, radius, true))
            {
                if (thing is Pawn pawn && !pawn.Dead)
                    result.Add(pawn);
            }
        }

        /// <summary>Эффект "вблизи видно": искры, марево, пыль.</summary>
        public static void ThrowHint(Thing anomaly, AnomalyFleck fleck)
        {
            Map map = anomaly.Map;
            switch (fleck)
            {
                case AnomalyFleck.Sparks: FleckMaker.ThrowMicroSparks(anomaly.DrawPos, map); break;
                case AnomalyFleck.Heat: FleckMaker.ThrowHeatGlow(anomaly.Position, map, 1f); break;
                case AnomalyFleck.Air: FleckMaker.ThrowAirPuffUp(anomaly.DrawPos, map); break;
                default: FleckMaker.ThrowDustPuff(anomaly.Position, map, 0.8f); break;
            }
        }
    }
}
