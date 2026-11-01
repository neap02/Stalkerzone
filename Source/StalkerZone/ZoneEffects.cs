using System;
using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.Sound;

namespace StalkerZone
{
    /// <summary>Общие эффекты Зоны: облучение, пси, разряды аномалий, перемещение пешек, звуки.</summary>
    public static class ZoneEffects
    {
        private const float PsiBreakMinSeverity = 0.45f;
        private const float PsiBreakMaxSeverity = 0.7f;
        private const float PsiBreakChancePerDose = 0.05f;
        private const float ChainDamageFactor = 0.6f;   // цепная молния слабее основного разряда

        private static readonly List<Pawn> tmpVictims = new List<Pawn>();
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

        public static void AddPsi(Pawn pawn, float dose)
        {
            if (pawn == null || pawn.Dead || !pawn.RaceProps.IsFlesh)
                return;
            dose *= Math.Max(0f, pawn.GetStatValue(StatDefOf.PsychicSensitivity));
            dose *= 1f - Math.Min(1f, Math.Max(0f, pawn.GetStatValue(SZ_DefOf.SZ_PsiProtection)));   // пси-защита костюма
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
        /// Срабатывание без взрыва: звук, эффект и урон своим типом всем в радиусе действия.
        /// Урон и пробитие — из DamageDef; броню учитывает ванильная система по категории урона.
        /// Возвращает задетых пешек (список переиспользуется, не хранить).
        /// </summary>
        public static List<Pawn> Discharge(Thing anomaly, AnomalyProfile p)
        {
            Map map = anomaly.Map;
            IntVec3 pos = anomaly.Position;
            PlaySound(p.Sound, pos, map);
            ShowDischargeFx(anomaly, p);

            PawnsAround(pos, map, p.effectRadius, tmpVictims);
            DamageDef damage = p.Damage;
            if (damage != null)
            {
                foreach (Pawn pawn in tmpVictims)
                    pawn.TakeDamage(new DamageInfo(damage, p.DamageAmount, p.ArmorPenetration, -1f, anomaly));
            }
            return tmpVictims;
        }

        private static void ShowDischargeFx(Thing anomaly, AnomalyProfile p)
        {
            Map map = anomaly.Map;
            IntVec3 pos = anomaly.Position;
            int cells = GenRadial.NumCellsInRadius(p.effectRadius);
            switch (p.fx)
            {
                case DischargeFx.Electric:
                    FleckMaker.ThrowLightningGlow(anomaly.DrawPos, map, 3f);
                    for (int i = 0; i < 8; i++)
                    {
                        IntVec3 c = pos + GenRadial.RadialPattern[Rand.Range(0, cells)];
                        if (c.InBounds(map)) FleckMaker.ThrowMicroSparks(c.ToVector3Shifted(), map);
                    }
                    break;
                case DischargeFx.Fire:
                    FleckMaker.ThrowFireGlow(anomaly.DrawPos, map, 2.5f);
                    FleckMaker.ThrowHeatGlow(pos, map, 2.5f);
                    for (int i = 0; i < 3; i++) FleckMaker.ThrowSmoke(anomaly.DrawPos, map, 1.5f);
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
                        IntVec3 c = pos + new IntVec3((int)Math.Round(Math.Cos(a) * p.effectRadius), 0, (int)Math.Round(Math.Sin(a) * p.effectRadius));
                        if (c.InBounds(map)) FleckMaker.ThrowDustPuff(c, map, 1.2f);
                    }
                    FleckMaker.ThrowDustPuff(pos, map, 2f);
                    break;
            }
        }

        /// <summary>Электра: разряд перескакивает на до count случайных пешек в радиусе (искры по линии).</summary>
        public static void ChainLightning(Thing anomaly, float radius, int count, AnomalyProfile p)
        {
            Map map = anomaly.Map;
            PawnsAround(anomaly.Position, map, radius, tmpChain);
            int hit = 0;
            foreach (Pawn target in tmpChain.InRandomOrder())
            {
                if (hit >= count)
                    break;
                IntVec3 a = anomaly.Position, b = target.Position;
                for (int k = 1; k <= 3; k++)
                {
                    IntVec3 c = new IntVec3(a.x + (b.x - a.x) * k / 4, 0, a.z + (b.z - a.z) * k / 4);
                    if (c.InBounds(map)) FleckMaker.ThrowMicroSparks(c.ToVector3Shifted(), map);
                }
                FleckMaker.ThrowLightningGlow(target.DrawPos, map, 1.5f);
                if (p.Damage != null)
                    target.TakeDamage(new DamageInfo(p.Damage, p.DamageAmount * ChainDamageFactor, p.ArmorPenetration, -1f, anomaly));
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

        /// <summary>
        /// Мгновенно переносит пешку. keepJob = true: пешка продолжает своё дело
        /// (например, уходит прочь по приказу), путь просто пересчитывается.
        /// </summary>
        public static void MovePawn(Pawn pawn, IntVec3 dest, bool keepJob)
        {
            pawn.pather?.StopDead();
            pawn.Position = dest;
            pawn.Notify_Teleported(!keepJob, true);
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

        /// <summary>Подсказка "видно вблизи": искры, марево, пыль.</summary>
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
