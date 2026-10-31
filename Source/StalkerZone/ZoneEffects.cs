using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>Общие эффекты Зоны: облучение, пси-удар, перемещение пешек, разряд аномалии.</summary>
    public static class ZoneEffects
    {
        // ===== Пси =====
        /// <summary>С этой тяжести пси-воздействия возможен психоз.</summary>
        private const float PsiBreakMinSeverity = 0.45f;
        /// <summary>С этой тяжести пешка без сознания, психоз уже не нужен.</summary>
        private const float PsiBreakMaxSeverity = 0.7f;
        /// <summary>Шанс психоза за одну дозу в опасном диапазоне.</summary>
        private const float PsiBreakChancePerDose = 0.05f;

        /// <summary>Облучение с учётом стата защиты от радиации.</summary>
        public static void AddRadiation(Pawn pawn, float dose)
        {
            if (pawn == null || pawn.Dead || !pawn.RaceProps.IsFlesh)
                return;
            float resistance = pawn.GetStatValue(SZ_DefOf.SZ_RadiationResistance);
            dose *= 1f - Math.Min(1f, Math.Max(0f, resistance));
            if (dose > 0f)
                HealthUtility.AdjustSeverity(pawn, SZ_DefOf.SZ_Radiation, dose);
        }

        /// <summary>
        /// Пси-воздействие с учётом пси-чувствительности.
        /// Пси-глухие (чувствительность 0) не страдают. Артефакт "лунный свет" её снижает.
        /// </summary>
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

        /// <summary>Мгновенно переносит пешку в клетку (затягивание, отброс).</summary>
        public static void MovePawn(Pawn pawn, IntVec3 dest)
        {
            pawn.pather?.StopDead();
            pawn.Position = dest;
            pawn.Notify_Teleported();
        }

        /// <summary>Заставляет аномалию разрядиться, если она ещё не разряжается.</summary>
        public static void Discharge(Thing anomaly)
        {
            CompExplosive comp = anomaly.TryGetComp<CompExplosive>();
            if (comp != null && !comp.wickStarted)
                comp.StartWick();
        }

        /// <summary>Живые пешки в радиусе вокруг клетки. Результат — в переданный список.</summary>
        public static void PawnsAround(IntVec3 center, Map map, float radius, List<Pawn> result)
        {
            result.Clear();
            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(center, map, radius, true))
            {
                if (thing is Pawn pawn && !pawn.Dead)
                    result.Add(pawn);
            }
        }
    }
}
