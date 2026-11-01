using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Поле аномалий карты.
    /// - Аномалии — записи в MapComponent_Zone (не вещи), стоят скоплениями одного типа.
    /// - Рядом с ними прячутся артефакты: на карте появляются, когда их найдёт детектор.
    /// - Выброс сносит старое поле, ненайденные и неподобранные артефакты и строит новое.
    /// - Пси-поля и радиоактивные пятна (со знаками) — тоже записи, один раз на карту.
    /// - Вокруг всего опасного лежит невидимая зона с высокой стоимостью пути.
    /// </summary>
    public static class AnomalyField
    {
        private const float FieldCenterSpacing = 14f;
        private const int FieldRadius = 6;
        private const float SpotSpacing = 8f;
        private const int MaxTries = 300;


        private static float expectedPer10k;
        private static readonly List<Thing> tmpThings = new List<Thing>();
        private static readonly List<IntVec3> tmpCells = new List<IntVec3>();

        public static void Init()
        {
            expectedPer10k = 0f;
            foreach (AnomalyDef def in ZoneDefs.Anomalies)
                expectedPer10k += def.per10k;
        }

        /// <summary>Сносит старое поле и строит новое. Возвращает число аномалий.</summary>
        public static int Rebuild(Map map)
        {
            MapComponent_Zone zone = map?.GetComponent<MapComponent_Zone>();
            if (zone == null || ZoneDefs.Anomalies.Count == 0)
                return 0;

            zone.ClearAnomalies();
            zone.RemoveUnclaimedArtifacts();
            zone.ClearLatentArtifacts();

            float expected = map.Area / 10000f * expectedPer10k;
            int spawned = 0, failures = 0;
            while (spawned < expected && failures < 10)
            {
                AnomalyDef def = ZoneDefs.Anomalies.RandomElementByWeight(d => d.per10k);
                int made = SpawnCluster(map, def, zone);
                if (made == 0) failures++;
                spawned += made;
            }
            MarkAllDanger(map);
            return spawned;
        }

        private static int SpawnCluster(Map map, AnomalyDef def, MapComponent_Zone zone)
        {
            if (!CellFinderLoose.TryGetRandomCellWith(c => CanPlaceAt(c, map, zone, FieldCenterSpacing), map, MaxTries, out IntVec3 center))
                return 0;
            int size = Rand.RangeInclusive(def.clusterMin, def.clusterMax);
            int made = 0;
            for (int i = 0; i < size; i++)
            {
                IntVec3 cell = center;
                if (i > 0 && !CellFinder.TryFindRandomCellNear(center, map, FieldRadius, c => CanPlaceAt(c, map, zone, def.memberSpacing), out cell))
                    continue;
                AnomalyInstance anomaly = zone.AddAnomaly(def, cell);
                made++;
                if (Rand.Chance(def.artifactChance))
                    HideArtifactNear(map, anomaly, zone);
            }
            return made;
        }

        /// <summary>Прячет артефакт рядом с аномалией: на карте он появится, когда его найдёт детектор.</summary>
        private static void HideArtifactNear(Map map, AnomalyInstance anomaly, MapComponent_Zone zone)
        {
            AnomalyDef def = anomaly.def;
            if (def.artifacts.NullOrEmpty())
                return;
            AnomalyArtifact pick = def.artifacts.RandomElementByWeight(a => a.weight);
            if (pick.artifact == null)
                return;
            float radius = System.Math.Max(2.5f, def.triggerRadius + 1f);
            tmpCells.Clear();
            foreach (IntVec3 c in GenRadial.RadialCellsAround(anomaly.pos, radius, false))
            {
                if (c.InBounds(map) && c.Standable(map) && c.GetEdifice(map) == null)
                    tmpCells.Add(c);
            }
            if (tmpCells.Count > 0)
                zone.AddLatentArtifact(tmpCells.RandomElement(), pick.artifact, pick.tier);
            tmpCells.Clear();
        }

        // ---------- Пси-поля и радиоактивные пятна ----------
        /// <summary>Ставит пятна каждого типа (записи, не вещи) и знаки по краю. Один раз на карту.</summary>
        public static void SpawnFields(Map map)
        {
            MapComponent_Zone zone = map.GetComponent<MapComponent_Zone>();
            if (zone == null)
                return;
            foreach (ZoneFieldDef def in ZoneDefs.Fields)
            {
                int count = GenMath.RoundRandom(map.Area / 10000f * def.per10k.RandomInRange);
                for (int i = 0; i < count; i++)
                {
                    if (!CellFinderLoose.TryGetRandomCellWith(c => CanPlaceAt(c, map, zone, SpotSpacing), map, MaxTries, out IntVec3 cell))
                        continue;
                    ZoneFieldInstance field = zone.AddField(def, cell);
                    if (!def.signTexPath.NullOrEmpty())
                        PlaceSigns(map, field);
                }
            }
            MarkAllDanger(map);
        }

        /// <summary>Клетки знаков по краю пятна (сами знаки рисует ZoneMats).</summary>
        private static void PlaceSigns(Map map, ZoneFieldInstance field)
        {
            field.signs.Clear();
            for (int k = 0; k < field.def.signCount; k++)
            {
                double a = System.Math.PI / 4 + k * 2 * System.Math.PI / field.def.signCount;
                IntVec3 target = field.pos + new IntVec3((int)System.Math.Round(System.Math.Cos(a) * field.def.signDistance), 0,
                                                         (int)System.Math.Round(System.Math.Sin(a) * field.def.signDistance));
                if (CellFinder.TryFindRandomCellNear(target, map, 1,
                        c => c.InBounds(map) && c.Standable(map) && c.GetEdifice(map) == null && !map.areaManager.Home[c], out IntVec3 cell))
                {
                    field.signs.Add(cell);
                }
            }
        }

        // ---------- Зоны обхода ----------
        /// <summary>Невидимая зона вокруг всех аномалий, пси-полей и пятен (заново).</summary>
        public static void MarkAllDanger(Map map)
        {
            ClearDanger(map);
            MapComponent_Zone zone = map.GetComponent<MapComponent_Zone>();
            if (zone != null)
            {
                foreach (AnomalyInstance a in zone.Anomalies)
                    MarkDanger(map, a.def.moves ? a.origin : a.pos, a.def.avoidRadius);
            }
            if (zone != null)
            {
                foreach (ZoneFieldInstance f in zone.Fields)
                    MarkDanger(map, f.pos, f.def.avoidRadius);
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

        /// <summary>Подходит ли клетка: вне колонии, не под крышей, не вода, пусто, далеко от других.</summary>
        public static bool CanPlaceAt(IntVec3 c, Map map, MapComponent_Zone zone, float spacing)
        {
            if (!c.InBounds(map) || c.Fogged(map) || !c.Standable(map))
                return false;
            if (map.areaManager.Home[c] || c.Roofed(map) || c.GetTerrain(map).IsWater)
                return false;
            if (c.GetEdifice(map) != null || c.GetFirstPawn(map) != null || c.GetFirstItem(map) != null)
                return false;
            if (zone != null && (zone.AnyAnomalyWithin(c, spacing) || zone.AnyFieldWithin(c, spacing)))
                return false;
            return true;
        }
    }
}
