using System;
using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.Sound;

namespace StalkerZone
{
    /// <summary>Общие эффекты Зоны: облучение, пси, срабатывания аномалий, перемещение пешек, звуки.</summary>
    public static class ZoneEffects
    {
        private const float PsiBreakMinSeverity = 0.45f;
        private const float PsiBreakMaxSeverity = 0.7f;
        private const float PsiBreakChancePerDose = 0.05f;
        private const float ChainDamageFactor = 0.6f;

        private static readonly List<Pawn> tmpVictims = new List<Pawn>();
        private static readonly List<Pawn> tmpChain = new List<Pawn>();

        // ---------- Радиация и пси ----------
        public static void AddRadiation(Pawn pawn, float dose)
        {
            if (pawn == null || pawn.Dead || !pawn.RaceProps.IsFlesh)
                return;
            SuitBonuses.Of(pawn, out _, out float suitRad, out _);
            float resistance = pawn.GetStatValue(SZ_DefOf.SZ_RadiationResistance) + suitRad;
            dose *= 1f - Math.Min(1f, Math.Max(0f, resistance));
            if (dose > 0f)
                HealthUtility.AdjustSeverity(pawn, SZ_DefOf.SZ_Radiation, dose);
        }

        /// <summary>Пси-доза × пси-чувствительность × (1 − пси-защита).</summary>
        public static void AddPsi(Pawn pawn, float dose)
        {
            if (pawn == null || pawn.Dead || !pawn.RaceProps.IsFlesh)
                return;
            dose *= Math.Max(0f, pawn.GetStatValue(StatDefOf.PsychicSensitivity));
            SuitBonuses.Of(pawn, out _, out _, out float suitPsi);
            dose *= 1f - Math.Min(1f, Math.Max(0f, pawn.GetStatValue(SZ_DefOf.SZ_PsiProtection) + suitPsi));
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

        // ---------- Срабатывание аномалии ----------
        /// <summary>
        /// Звук, эффект и урон типа аномалии всем в радиусе действия.
        /// Урон, пробитие и категория защиты — из DamageDef аномалии.
        /// Возвращает задетых пешек (список переиспользуется, не хранить).
        /// </summary>
        public static List<Pawn> Discharge(Map map, IntVec3 pos, AnomalyDef def)
        {
            PlaySound(def.sound, pos, map);
            ShowDischargeFx(map, pos, def);
            PawnsAround(pos, map, def.effectRadius, tmpVictims);
            if (def.damage != null)
            {
                foreach (Pawn pawn in tmpVictims)
                    pawn.TakeDamage(new DamageInfo(def.damage, def.DamageAmount, def.ArmorPenetration));
            }
            return tmpVictims;
        }

        private static void ShowDischargeFx(Map map, IntVec3 pos, AnomalyDef def)
        {
            int cells = GenRadial.NumCellsInRadius(def.effectRadius);
            switch (def.fx)
            {
                case DischargeFx.Electric:
                    FleckMaker.ThrowLightningGlow(pos.ToVector3Shifted(), map, 3f);
                    for (int i = 0; i < 8; i++)
                    {
                        IntVec3 c = pos + GenRadial.RadialPattern[Rand.Range(0, cells)];
                        if (c.InBounds(map)) FleckMaker.ThrowMicroSparks(c.ToVector3Shifted(), map);
                    }
                    break;
                case DischargeFx.Fire:
                    FleckMaker.ThrowFireGlow(pos.ToVector3Shifted(), map, 2.5f);
                    FleckMaker.ThrowHeatGlow(pos, map, 2.5f);
                    for (int i = 0; i < 3; i++) FleckMaker.ThrowSmoke(pos.ToVector3Shifted(), map, 1.5f);
                    break;
                case DischargeFx.Acid:
                    for (int i = 0; i < 6; i++)
                    {
                        IntVec3 c = pos + GenRadial.RadialPattern[Rand.Range(0, cells)];
                        if (c.InBounds(map)) FleckMaker.ThrowAirPuffUp(c.ToVector3Shifted(), map);
                    }
                    break;
                case DischargeFx.Fuzz:
                    for (int i = 0; i < 10; i++)
                    {
                        IntVec3 c = pos + GenRadial.RadialPattern[Rand.Range(0, cells)];
                        if (c.InBounds(map)) FleckMaker.ThrowDustPuff(c, map, 0.6f);
                    }
                    break;
                default: // гравитация: кольцо пыли
                    for (int i = 0; i < 12; i++)
                    {
                        double a = i * Math.PI / 6;
                        IntVec3 c = pos + new IntVec3((int)Math.Round(Math.Cos(a) * def.effectRadius), 0, (int)Math.Round(Math.Sin(a) * def.effectRadius));
                        if (c.InBounds(map)) FleckMaker.ThrowDustPuff(c, map, 1.2f);
                    }
                    FleckMaker.ThrowDustPuff(pos, map, 2f);
                    break;
            }
        }

        /// <summary>Электра: разряд перескакивает на до count случайных пешек в радиусе.</summary>
        public static void ChainLightning(Map map, IntVec3 pos, AnomalyDef def, float radius, int count)
        {
            PawnsAround(pos, map, radius, tmpChain);
            int hit = 0;
            foreach (Pawn target in tmpChain.InRandomOrder())
            {
                if (hit >= count)
                    break;
                IntVec3 b = target.Position;
                for (int k = 1; k <= 3; k++)
                {
                    IntVec3 c = new IntVec3(pos.x + (b.x - pos.x) * k / 4, 0, pos.z + (b.z - pos.z) * k / 4);
                    if (c.InBounds(map)) FleckMaker.ThrowMicroSparks(c.ToVector3Shifted(), map);
                }
                FleckMaker.ThrowLightningGlow(target.DrawPos, map, 1.5f);
                if (def.damage != null)
                    target.TakeDamage(new DamageInfo(def.damage, def.DamageAmount * ChainDamageFactor, def.ArmorPenetration));
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
            {
                FleckMaker.ThrowDustPuff(pawn.Position, map, 1f);
                MovePawn(pawn, dest, false);
            }
        }

        /// <summary>Мгновенно переносит пешку. keepJob = true: пешка продолжает своё дело.</summary>
        public static void MovePawn(Pawn pawn, IntVec3 dest, bool keepJob)
        {
            pawn.pather?.StopDead();
            pawn.Position = dest;
            pawn.Notify_Teleported(!keepJob, true);
        }

        public static void Stun(Pawn pawn, int ticks)
        {
            if (!pawn.Dead)
                pawn.stances?.stunner?.StunFor(ticks, null, false);
        }

        public static void PawnsAround(IntVec3 center, Map map, float radius, List<Pawn> result)
        {
            result.Clear();
            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(center, map, radius, true))
            {
                if (thing is Pawn pawn && !pawn.Dead)
                    result.Add(pawn);
            }
        }

        public static void PlaySound(SoundDef sound, IntVec3 cell, Map map)
        {
            sound?.PlayOneShot(SoundInfo.InMap(new TargetInfo(cell, map)));
        }

        /// <summary>Признак "видно вблизи": искры, марево, пыль.</summary>
        public static void ThrowHint(Map map, IntVec3 pos, AnomalyFleck fleck)
        {
            switch (fleck)
            {
                case AnomalyFleck.Sparks: FleckMaker.ThrowMicroSparks(pos.ToVector3Shifted(), map); break;
                case AnomalyFleck.Heat: FleckMaker.ThrowHeatGlow(pos, map, 1f); break;
                case AnomalyFleck.Air: FleckMaker.ThrowAirPuffUp(pos.ToVector3Shifted(), map); break;
                default: FleckMaker.ThrowDustPuff(pos, map, 0.8f); break;
            }
        }
    }
}
