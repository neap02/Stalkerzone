using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Поле аномалий карты (только C#).
    /// - Аномалии стоят скоплениями одного типа (размер — в AnomalyProfile).
    /// - Рядом с аномалиями прячутся артефакты: их нет на карте, пока их не найдёт детектор.
    /// - Выброс сносит старое поле, ненайденные и неподобранные артефакты и строит новое.
    /// - Пси-поля и радиоактивные пятна (со знаками опасности) — один раз на карту.
    /// - Вокруг всего опасного лежит невидимая зона с высокой стоимостью пути: пешки обходят.
    /// </summary>
    public static class AnomalyField
    {
        private const float FieldCenterSpacing = 14f;
        private const int FieldRadius = 6;
        private const float SpotSpacing = 8f;
        private const float SignDistance = 5.5f;     // знаки по краю радиоактивного пятна (радиус 4.9)
        private const float RadiationAvoidRadius = 5.4f;
        private const float PsiAvoidRadius = 7.4f;
        private const int MaxTries = 300;

        private static readonly FloatRange PsiFieldsPer10k = new FloatRange(0.05f, 0.12f);
        private static readonly FloatRange RadiationSpotsPer10k = new FloatRange(0.25f, 0.5f);

        private class Variant { public ThingDef def; public float weight; }
        private class AnomalyType { public string name; public float weight; public List<Variant> variants = new List<Variant>(); }

        private static readonly List<AnomalyType> types = new List<AnomalyType>();
        private static readonly Dictionary<ThingDef, int> artifactTier = new Dictionary<ThingDef, int>();
        private static float expectedPer10k;
        private static readonly List<Thing> tmpThings = new List<Thing>();
        private static readonly List<IntVec3> tmpCells = new List<IntVec3>();

        public static int VariantCount { get; private set; }

        /// <summary>Таблица типов и вариантов из GenStepDef. Редкость варианта = редкость артефакта.</summary>
        public static void Init()
        {
            types.Clear(); artifactTier.Clear();
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

                // обычный (частый вариант) — 1, необычный — 2, редкий — 3
                ThingDef artifact = ZoneDefs.ArtifactOf(scatter.thingDef);
                if (artifact != null)
                    artifactTier[artifact] = weight >= 0.15f ? 1 : weight >= 0.07f ? 2 : 3;
            }
        }

        public static int TierOf(ThingDef artifact)
        {
            return artifact != null && artifactTier.TryGetValue(artifact, out int t) ? t : 1;
        }

        /// <summary>Сносит старое поле аномалий и строит новое. Возвращает число аномалий.</summary>
        public static int Rebuild(Map map)
        {
            if (map == null || types.Count == 0)
                return 0;
            MapComponent_Zone zone = map.GetComponent<MapComponent_Zone>();

            tmpThings.Clear();
            foreach (ThingDef def in ZoneDefs.AllAnomalies)
                tmpThings.AddRange(map.listerThings.ThingsOfDef(def));
            foreach (Thing thing in tmpThings)
            {
                if (!thing.Destroyed)
                    thing.Destroy(DestroyMode.Vanish);
            }
            tmpThings.Clear();
            ClearDanger(map);
            zone?.RemoveUnclaimedArtifacts();
            zone?.ClearLatentArtifacts();

            float expected = map.Area / 10000f * expectedPer10k;
            int spawned = 0, failures = 0;
            while (spawned < expected && failures < 10)
            {
                AnomalyType type = types.RandomElementByWeight(t => t.weight);
                int made = SpawnCluster(map, type, zone);
                if (made == 0) failures++;
                spawned += made;
            }
            MarkAllDanger(map);
            return spawned;
        }

        // ---------- Зоны опасности ----------
        /// <summary>Невидимая зона вокруг всех аномалий, пси-полей и пятен (заново).</summary>
        public static void MarkAllDanger(Map map)
        {
            ClearDanger(map);
            foreach (ThingDef def in ZoneDefs.AllAnomalies)
            {
                foreach (Thing anomaly in map.listerThings.ThingsOfDef(def))
                    MarkDanger(map, anomaly.Position, ZoneDefs.ProfileOf(def).avoidRadius);
            }
            if (ZoneDefs.RadiationSpot != null)
            {
                foreach (Thing spot in map.listerThings.ThingsOfDef(ZoneDefs.RadiationSpot))
                    MarkDanger(map, spot.Position, RadiationAvoidRadius);
            }
            if (ZoneDefs.PsiField != null)
            {
                foreach (Thing field in map.listerThings.ThingsOfDef(ZoneDefs.PsiField))
                    MarkDanger(map, field.Position, PsiAvoidRadius);
            }
        }

        private static void MarkDanger(Map map, IntVec3 center, float radius)
        {
            ThingDef marker = ZoneDefs.DangerMarker;
            if (marker == null)
                return;
            foreach (IntVec3 c in GenRadial.RadialCellsAround(center, radius, true))
            {
                if (c.InBounds(map) && !c.Impassable(map) && c.GetFirstThing(map, marker) == null)
                    GenSpawn.Spawn(ThingMaker.MakeThing(marker), c, map);
            }
        }

        private static void ClearDanger(Map map)
        {
            if (ZoneDefs.DangerMarker == null)
                return;
            tmpThings.Clear();
            tmpThings.AddRange(map.listerThings.ThingsOfDef(ZoneDefs.DangerMarker));
            foreach (Thing thing in tmpThings)
            {
                if (!thing.Destroyed)
                    thing.Destroy(DestroyMode.Vanish);
            }
            tmpThings.Clear();
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
                if (zone != null && Rand.Chance(profile.artifactChance))
                    HideArtifactNear(anomaly, profile, zone);
            }
            return made;
        }

        /// <summary>Прячет артефакт рядом с аномалией: на карте он появится, когда его найдёт детектор.</summary>
        private static void HideArtifactNear(Thing anomaly, AnomalyProfile profile, MapComponent_Zone zone)
        {
            ThingDef artifact = ZoneDefs.ArtifactOf(anomaly.def);
            if (artifact == null)
                return;
            Map map = anomaly.Map;
            float radius = Math.Max(2.5f, profile.triggerRadius + 1f);
            tmpCells.Clear();
            foreach (IntVec3 c in GenRadial.RadialCellsAround(anomaly.Position, radius, false))
            {
                if (c.InBounds(map) && c.Standable(map) && c.GetEdifice(map) == null)
                    tmpCells.Add(c);
            }
            if (tmpCells.Count > 0)
                zone.AddLatentArtifact(tmpCells.RandomElement(), artifact, TierOf(artifact));
            tmpCells.Clear();
        }

        /// <summary>Пси-поля и радиоактивные пятна со знаками. Один раз на карту.</summary>
        public static void SpawnFields(Map map)
        {
            if (ZoneDefs.PsiField != null)
                SpawnScattered(map, ZoneDefs.PsiField, PsiFieldsPer10k);
            if (ZoneDefs.RadiationSpot != null)
            {
                foreach (Thing spot in SpawnScattered(map, ZoneDefs.RadiationSpot, RadiationSpotsPer10k))
                    PlaceSigns(spot);
            }
            MarkAllDanger(map);
        }

        /// <summary>Четыре знака радиационной опасности по краю пятна.</summary>
        public static void PlaceSigns(Thing spot)
        {
            if (ZoneDefs.RadiationSign == null || !spot.Spawned)
                return;
            Map map = spot.Map;
            for (int k = 0; k < 4; k++)
            {
                double a = Math.PI / 4 + k * Math.PI / 2;
                IntVec3 target = spot.Position + new IntVec3((int)Math.Round(Math.Cos(a) * SignDistance), 0, (int)Math.Round(Math.Sin(a) * SignDistance));
                if (CellFinder.TryFindRandomCellNear(target, map, 1,
                        c => c.InBounds(map) && c.Standable(map) && c.GetEdifice(map) == null && !map.areaManager.Home[c], out IntVec3 cell))
                {
                    GenSpawn.Spawn(ThingMaker.MakeThing(ZoneDefs.RadiationSign), cell, map);
                }
            }
        }

        private static List<Thing> SpawnScattered(Map map, ThingDef def, FloatRange per10k)
        {
            var result = new List<Thing>();
            int count = GenMath.RoundRandom(map.Area / 10000f * per10k.RandomInRange);
            for (int i = 0; i < count; i++)
            {
                if (CellFinderLoose.TryGetRandomCellWith(c => CanPlaceAt(c, map, def, SpotSpacing), map, MaxTries, out IntVec3 cell))
                    result.Add(GenSpawn.Spawn(ThingMaker.MakeThing(def), cell, map));
            }
            return result;
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
