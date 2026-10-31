using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Поле аномалий карты (только C#).
    /// - Аномалии стоят скоплениями по 1–6 штук одного типа (размер — в AnomalyProfile).
    /// - Рядом с аномалиями лежат артефакты (запрещённые для подбора: решение за игроком).
    /// - Выброс сносит старое поле и неподобранные артефакты и строит новое.
    /// Сколько аномалий и какие варианты — из тех же GenStepDef, что и генерация карты.
    /// Пси-поля и радиоактивные пятна ставятся один раз на карту.
    /// </summary>
    public static class AnomalyField
    {
        private const float FieldCenterSpacing = 14f;   // между центрами скоплений
        private const int FieldRadius = 6;              // разброс аномалий вокруг центра
        private const float SpotSpacing = 8f;           // для пси-полей и пятен
        private const int MaxTries = 300;

        private static readonly FloatRange PsiFieldsPer10k = new FloatRange(0.05f, 0.12f);     // 0–1 на карту
        private static readonly FloatRange RadiationSpotsPer10k = new FloatRange(0.25f, 0.5f); // 1–3 на карту

        private class Variant { public ThingDef def; public float weight; }
        private class AnomalyType { public string name; public float weight; public List<Variant> variants = new List<Variant>(); }

        private static readonly List<AnomalyType> types = new List<AnomalyType>();
        private static float expectedPer10k;
        private static readonly List<Thing> tmpThings = new List<Thing>();
        private static readonly List<IntVec3> tmpCells = new List<IntVec3>();

        public static int VariantCount { get; private set; }

        /// <summary>Таблица типов и вариантов из GenStepDef. Вызывается один раз при старте.</summary>
        public static void Init()
        {
            types.Clear();
            expectedPer10k = 0f;
            VariantCount = 0;
            foreach (GenStepDef stepDef in DefDatabase<GenStepDef>.AllDefsListForReading)
            {
                if (!(stepDef.genStep is GenStep_ScatterThings scatter) || !ZoneDefs.IsAnomaly(scatter.thingDef))
                    continue;
                float weight = scatter.countPer10kCellsRange.Average;
                string typeName = ZoneDefs.TypeOf(scatter.thingDef);
                AnomalyType type = types.Find(t => t.name == typeName);
                if (type == null)
                {
                    type = new AnomalyType { name = typeName };
                    types.Add(type);
                }
                type.variants.Add(new Variant { def = scatter.thingDef, weight = weight });
                type.weight += weight;
                expectedPer10k += weight;
                VariantCount++;
            }
        }

        /// <summary>Сносит старое поле аномалий и строит новое. Возвращает число аномалий.</summary>
        public static int Rebuild(Map map)
        {
            if (map == null || types.Count == 0)
                return 0;
            MapComponent_Zone zone = map.GetComponent<MapComponent_Zone>();

            // Старые аномалии исчезают (Vanish: без взрыва), неподобранные артефакты — тоже
            tmpThings.Clear();
            foreach (ThingDef def in ZoneDefs.AllAnomalies)
                tmpThings.AddRange(map.listerThings.ThingsOfDef(def));
            foreach (Thing thing in tmpThings)
            {
                if (!thing.Destroyed)
                    thing.Destroy(DestroyMode.Vanish);
            }
            tmpThings.Clear();
            zone?.RemoveUnclaimedArtifacts();

            // Новые скопления, пока не наберём ожидаемое число аномалий
            float expected = map.Area / 10000f * expectedPer10k;
            int spawned = 0, failures = 0;
            while (spawned < expected && failures < 10)
            {
                AnomalyType type = types.RandomElementByWeight(t => t.weight);
                int made = SpawnCluster(map, type, zone);
                if (made == 0) failures++;
                spawned += made;
            }
            return spawned;
        }

        private static int SpawnCluster(Map map, AnomalyType type, MapComponent_Zone zone)
        {
            AnomalyProfile profile = AnomalyProfile.For(type.name);
            ThingDef probe = type.variants[0].def;
            if (!CellFinderLoose.TryGetRandomCellWith(c => CanPlaceAt(c, map, probe, FieldCenterSpacing), map, MaxTries, out IntVec3 center))
                return 0;

            int size = Rand.RangeInclusive(profile.clusterMin, profile.clusterMax);
            int made = 0;
            for (int i = 0; i < size; i++)
            {
                ThingDef def = type.variants.RandomElementByWeight(v => v.weight).def;
                IntVec3 cell = center;
                if (i > 0 && !CellFinder.TryFindRandomCellNear(center, map, FieldRadius, c => CanPlaceAt(c, map, def, profile.memberSpacing), out cell))
                    continue;
                Thing anomaly = GenSpawn.Spawn(ThingMaker.MakeThing(def), cell, map);
                made++;
                if (Rand.Chance(profile.artifactChance))
                    SpawnArtifactNear(anomaly, profile, zone);
            }
            return made;
        }

        /// <summary>Кладёт артефакт этой аномалии в клетку рядом с ней (в зоне срабатывания).</summary>
        private static void SpawnArtifactNear(Thing anomaly, AnomalyProfile profile, MapComponent_Zone zone)
        {
            ThingDef artifact = ZoneDefs.ArtifactOf(anomaly.def);
            if (artifact == null)
                return;
            Map map = anomaly.Map;
            float radius = Math.Max(1.5f, Math.Max(profile.triggerRadius, 3f));
            tmpCells.Clear();
            foreach (IntVec3 c in GenRadial.RadialCellsAround(anomaly.Position, radius, false))
            {
                if (c.InBounds(map) && c.Standable(map) && c.GetEdifice(map) == null && c.GetFirstItem(map) == null)
                    tmpCells.Add(c);
            }
            if (tmpCells.Count == 0)
                return;
            Thing item = GenSpawn.Spawn(ThingMaker.MakeThing(artifact), tmpCells.RandomElement(), map);
            item.SetForbidden(true, false);   // колонисты не полезут за ним сами
            zone?.RegisterFieldArtifact(item);
            tmpCells.Clear();
        }

        /// <summary>Пси-поля и радиоактивные пятна. Один раз на карту.</summary>
        public static void SpawnFields(Map map)
        {
            if (ZoneDefs.PsiField != null)
                SpawnScattered(map, ZoneDefs.PsiField, PsiFieldsPer10k);
            if (ZoneDefs.RadiationSpot != null)
                SpawnScattered(map, ZoneDefs.RadiationSpot, RadiationSpotsPer10k);
        }

        private static void SpawnScattered(Map map, ThingDef def, FloatRange per10k)
        {
            int count = GenMath.RoundRandom(map.Area / 10000f * per10k.RandomInRange);
            for (int i = 0; i < count; i++)
            {
                if (CellFinderLoose.TryGetRandomCellWith(c => CanPlaceAt(c, map, def, SpotSpacing), map, MaxTries, out IntVec3 cell))
                    GenSpawn.Spawn(ThingMaker.MakeThing(def), cell, map);
            }
        }

        /// <summary>Подходит ли клетка: вне колонии, не под крышей, пусто, грунт держит, далеко от других.</summary>
        public static bool CanPlaceAt(IntVec3 c, Map map, ThingDef def, float spacing)
        {
            if (!c.InBounds(map) || c.Fogged(map) || !c.Standable(map))
                return false;
            if (map.areaManager.Home[c] || c.Roofed(map))
                return false;
            if (c.GetEdifice(map) != null || c.GetFirstPawn(map) != null || c.GetFirstItem(map) != null)
                return false;

            TerrainDef terrain = c.GetTerrain(map);
            if (def.terrainAffordanceNeeded != null && !terrain.affordances.Contains(def.terrainAffordanceNeeded))
                return false;

            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(c, map, spacing, true))
            {
                if (ZoneDefs.IsAnomaly(thing.def) || thing.def == ZoneDefs.PsiField || thing.def == ZoneDefs.RadiationSpot)
                    return false;
            }
            return true;
        }
    }
}
