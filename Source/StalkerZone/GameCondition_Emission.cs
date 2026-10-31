using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Выброс. Погоду из GameConditionDef.weatherDef держит родитель (GameCondition_ForceWeather),
    /// а этот класс добавляет облучение всех органических существ, стоящих не под крышей.
    /// Итоговая доза = доза * (1 - SZ_RadiationResistance).
    /// </summary>
    public class GameCondition_Emission : GameCondition_ForceWeather
    {
        private const float TicksPerHour = 2500f;

        // Копия списка пешек карты: обход безопасен, даже если кто-то умрёт во время обхода
        private static readonly List<Pawn> tmpPawns = new List<Pawn>();

        private EmissionExtension settings;

        private EmissionExtension Settings
        {
            get
            {
                if (settings == null)
                    settings = def.GetModExtension<EmissionExtension>() ?? new EmissionExtension();
                return settings;
            }
        }

        public override void GameConditionTick()
        {
            base.GameConditionTick();

            int interval = Math.Max(1, Settings.checkIntervalTicks);
            if (Find.TickManager.TicksGame % interval != 0)
                return;

            // Доза за один интервал проверки
            float dose = Settings.radiationPerHour * interval / TicksPerHour;

            var maps = AffectedMaps;
            for (int i = 0; i < maps.Count; i++)
                IrradiateMap(maps[i], dose);
        }

        private void IrradiateMap(Map map, float dose)
        {
            tmpPawns.Clear();
            tmpPawns.AddRange(map.mapPawns.AllPawnsSpawned);

            for (int i = 0; i < tmpPawns.Count; i++)
            {
                Pawn pawn = tmpPawns[i];
                if (!IsExposed(pawn, map))
                    continue;

                // 0 = без защиты, 1 = полная защита
                float resistance = pawn.GetStatValue(SZ_DefOf.SZ_RadiationResistance);
                float finalDose = dose * (1f - Math.Min(1f, Math.Max(0f, resistance)));
                if (finalDose > 0f)
                    HealthUtility.AdjustSeverity(pawn, SZ_DefOf.SZ_Radiation, finalDose);
            }

            tmpPawns.Clear();
        }

        private bool IsExposed(Pawn pawn, Map map)
        {
            if (pawn.Dead || !pawn.Spawned || pawn.Map != map)
                return false;

            // Механоиды и прочая неорганика не облучаются
            if (!pawn.RaceProps.IsFlesh)
                return false;

            if (!Settings.affectAnimals && pawn.RaceProps.Animal)
                return false;

            // Защищает любая крыша: тонкая, горная, крыша здания
            return !pawn.Position.Roofed(map);
        }
    }
}
