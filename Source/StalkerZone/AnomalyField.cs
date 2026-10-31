using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Поле аномалий карты.
    /// - После Выброса старые аномалии исчезают, новые появляются в других местах.
    ///   Сколько и каких — берём из тех же GenStepDef, что и при генерации карты.
    /// - Пси-поля и радиоактивные пятна ставятся один раз на карту (только с C#)
    ///   и Выбросом не переставляются.
    /// </summary>
    public static class AnomalyField
    {
        /// <summary>Минимальное расстояние между аномалиями, в клетках.</summary>
        private const float MinSpacing = 8f;
        private const int MaxTriesPerThing = 500;

        // Сколько пятен ставить на 10 000 клеток (карта 250x250 ≈ 6 блоков)
        private static readonly FloatRange PsiFieldsPer10k = new FloatRange(0.05f, 0.12f);     // 0–1 на карту
        private static readonly FloatRange RadiationSpotsPer10k = new FloatRange(0.25f, 0.5f); // 1–3 на карту

        private class SpawnEntry
        {
            public ThingDef def;
            public FloatRange per10kCells;
        }

        private static readonly List<SpawnEntry> spawnTable = new List<SpawnEntry>();
        private static readonly List<Thing> tmpThings = new List<Thing>();

        public static int VariantCount => spawnTable.Count;

        /// <summary>Собирает таблицу появления из GenStepDef. Вызывается один раз при старте.</summary>
        public static void Init()
        {
            spawnTable.Clear();
            foreach (GenStepDef stepDef in DefDatabase<GenStepDef>.AllDefsListForReading)
            {
                if (stepDef.genStep is GenStep_ScatterThings scatter && ZoneDefs.IsAnomaly(scatter.thingDef))
                {
                    spawnTable.Add(new SpawnEntry { def = scatter.thingDef, per10kCells = scatter.countPer10kCellsRange });
                }
            }
        }

        /// <summary>Убирает все аномалии (без артефактов) и расставляет новые. Возвращает число новых.</summary>
        public static int Reshuffle(Map map)
        {
            if (map == null || spawnTable.Count == 0)
                return 0;

            tmpThings.Clear();
            foreach (SpawnEntry entry in spawnTable)
                tmpThings.AddRange(map.listerThings.ThingsOfDef(entry.def));
            foreach (Thing thing in tmpThings)
            {
                if (!thing.Destroyed)
                    thing.Destroy(DestroyMode.Vanish);   // Vanish: без взрыва и без артефакта
            }
            tmpThings.Clear();

            int spawned = 0;
            foreach (SpawnEntry entry in spawnTable)
                spawned += SpawnSome(map, entry.def, entry.per10kCells);
            return spawned;
        }

        /// <summary>Ставит пси-поля и радиоактивные пятна. Вызывается один раз на карту.</summary>
        public static void SpawnFields(Map map)
        {
            if (ZoneDefs.PsiField != null)
                SpawnSome(map, ZoneDefs.PsiField, PsiFieldsPer10k);
            if (ZoneDefs.RadiationSpot != null)
                SpawnSome(map, ZoneDefs.RadiationSpot, RadiationSpotsPer10k);
        }

        private static int SpawnSome(Map map, ThingDef def, FloatRange per10k)
        {
            int count = GenMath.RoundRandom(map.Area / 10000f * per10k.RandomInRange);
            int spawned = 0;
            for (int i = 0; i < count; i++)
            {
                if (CellFinderLoose.TryGetRandomCellWith(c => CanPlaceAt(c, map, def), map, MaxTriesPerThing, out IntVec3 cell))
                {
                    GenSpawn.Spawn(ThingMaker.MakeThing(def), cell, map);
                    spawned++;
                }
            }
            return spawned;
        }

        /// <summary>Подходит ли клетка для аномалии или пятна.</summary>
        public static bool CanPlaceAt(IntVec3 c, Map map, ThingDef def)
        {
            if (!c.InBounds(map) || c.Fogged(map) || !c.Standable(map))
                return false;
            if (map.areaManager.Home[c] || c.Roofed(map))          // не в колонии и не под крышей
                return false;
            if (c.GetEdifice(map) != null || c.GetFirstPawn(map) != null || c.GetFirstItem(map) != null)
                return false;

            TerrainDef terrain = c.GetTerrain(map);
            if (def.terrainAffordanceNeeded != null && !terrain.affordances.Contains(def.terrainAffordanceNeeded))
                return false;

            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(c, map, MinSpacing, true))
            {
                if (ZoneDefs.IsAnomaly(thing.def) || thing.def == ZoneDefs.PsiField || thing.def == ZoneDefs.RadiationSpot)
                    return false;
            }
            return true;
        }
    }
}
