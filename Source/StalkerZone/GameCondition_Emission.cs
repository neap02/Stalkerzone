using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Выброс. Погоду из GameConditionDef.weatherDef держит родитель (GameCondition_ForceWeather).
    ///
    /// Фазы:
    /// 1. Приближение (первый игровой час): урона нет, колонисты уходят под крышу.
    /// 2. Пик: всех органических существ не под крышей бьёт пси-удар и радиация.
    ///    Без укрытия смерть примерно через 50 минут (пси), выжившие — с лучевой болезнью.
    /// 3. Конец: колонистам возвращаются прежние зоны, поле аномалий строится заново,
    ///    неподобранные артефакты исчезают, появляются новые.
    /// </summary>
    public class GameCondition_Emission : GameCondition_ForceWeather
    {
        // ===== Баланс =====
        private const int WarmupTicks = 2500;              // 1 игровой час на то, чтобы укрыться
        private const float RadiationPerHour = 0.2f;       // лучевая болезнь на пике
        private const float PsiPerHour = 1.2f;             // пси: ~35 мин до потери сознания, ~50 мин до смерти
        private const int CheckIntervalTicks = 250;        // ≈ 4 сек. на x1
        private const float TicksPerHour = 2500f;

        // ===== Укрытие (сохраняется) =====
        private bool shelterApplied;
        private List<Pawn> shelterPawns = new List<Pawn>();
        private List<Area> shelterPrevAreas = new List<Area>();
        private List<Area> shelterTempAreas = new List<Area>();

        private static readonly List<Pawn> tmpPawns = new List<Pawn>();

        private bool AtPeak => TicksPassed >= WarmupTicks;

        public override void GameConditionTick()
        {
            base.GameConditionTick();

            if (!shelterApplied)
            {
                shelterApplied = true;
                foreach (Map map in AffectedMaps)
                    ApplyShelter(map);
            }

            if (!AtPeak || Find.TickManager.TicksGame % CheckIntervalTicks != 0)
                return;

            float radDose = RadiationPerHour * CheckIntervalTicks / TicksPerHour;
            float psiDose = PsiPerHour * CheckIntervalTicks / TicksPerHour;
            foreach (Map map in AffectedMaps)
            {
                tmpPawns.Clear();
                tmpPawns.AddRange(map.mapPawns.AllPawnsSpawned);
                foreach (Pawn pawn in tmpPawns)
                {
                    if (pawn.Dead || !pawn.Spawned || !pawn.RaceProps.IsFlesh || pawn.Position.Roofed(map))
                        continue;
                    pawn.needs?.mood?.thoughts?.memories?.TryGainMemory(SZ_DefOf.SZ_ExposedToEmission);
                    ZoneEffects.AddPsi(pawn, psiDose);
                    ZoneEffects.AddRadiation(pawn, radDose);
                }
                tmpPawns.Clear();
            }
        }

        public override void End()
        {
            List<Map> maps = new List<Map>(AffectedMaps);
            RestoreShelter();
            base.End();

            int spawned = 0;
            foreach (Map map in maps)
                spawned += AnomalyField.Rebuild(map);   // новое поле и свежие артефакты

            if (spawned > 0)
            {
                Find.LetterStack.ReceiveLetter(
                    "SZ_AnomaliesShiftedLabel".Translate(),
                    "SZ_AnomaliesShiftedText".Translate(),
                    LetterDefOf.NeutralEvent);
            }
        }

        // ---------- Укрытие ----------
        /// <summary>
        /// Временная зона "только под крышей" для колонистов и ручных животных.
        /// Ванильный ИИ сам уводит пешек в разрешённую зону. Призванные (drafted) пешки
        /// подчиняются игроку и зону игнорируют.
        /// </summary>
        private void ApplyShelter(Map map)
        {
            if (!map.areaManager.TryMakeNewAllowed(out Area_Allowed shelter))
            {
                Log.Warning("[StalkerZone] Не удалось создать зону укрытия: слишком много зон.");
                return;
            }

            int roofedCells = 0;
            foreach (IntVec3 c in map.AllCells)
            {
                if (c.Roofed(map) && !c.Fogged(map) && c.Standable(map))
                {
                    shelter[c] = true;
                    roofedCells++;
                }
            }
            if (roofedCells == 0)
            {
                shelter.Delete();
                return;
            }
            shelterTempAreas.Add(shelter);

            foreach (Pawn pawn in map.mapPawns.PawnsInFaction(Faction.OfPlayer))
            {
                if (!pawn.Spawned || pawn.Dead || pawn.playerSettings == null || !pawn.RaceProps.IsFlesh)
                    continue;
                shelterPawns.Add(pawn);
                shelterPrevAreas.Add(pawn.playerSettings.AreaRestrictionInPawnCurrentMap);
                pawn.playerSettings.AreaRestrictionInPawnCurrentMap = shelter;
            }
            Messages.Message("SZ_ShelterOrdered".Translate(), MessageTypeDefOf.NeutralEvent);
        }

        /// <summary>Возвращает пешкам прежние зоны и удаляет временную.</summary>
        private void RestoreShelter()
        {
            for (int i = 0; i < shelterPawns.Count; i++)
            {
                Pawn pawn = shelterPawns[i];
                if (pawn == null || pawn.Destroyed || pawn.playerSettings == null)
                    continue;
                Area prev = i < shelterPrevAreas.Count ? shelterPrevAreas[i] : null;
                // Если игрок за это время удалил старую зону — снимаем ограничение
                if (prev != null && (pawn.MapHeld == null || !pawn.MapHeld.areaManager.AllAreas.Contains(prev)))
                    prev = null;
                pawn.playerSettings.AreaRestrictionInPawnCurrentMap = prev;
            }
            foreach (Area area in shelterTempAreas)
                area?.Delete();
            shelterPawns.Clear();
            shelterPrevAreas.Clear();
            shelterTempAreas.Clear();
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref shelterApplied, "shelterApplied", false);
            Scribe_Collections.Look(ref shelterPawns, "shelterPawns", LookMode.Reference);
            Scribe_Collections.Look(ref shelterPrevAreas, "shelterPrevAreas", LookMode.Reference);
            Scribe_Collections.Look(ref shelterTempAreas, "shelterTempAreas", LookMode.Reference);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (shelterPawns == null) shelterPawns = new List<Pawn>();
                if (shelterPrevAreas == null) shelterPrevAreas = new List<Area>();
                if (shelterTempAreas == null) shelterTempAreas = new List<Area>();
            }
        }
    }
}
