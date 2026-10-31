using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Поведение Зоны на карте (только с C#):
    /// - любая пешка, ступившая в аномалию, вызывает разряд (без ванильного шанса "знал о ловушке");
    /// - воронка затягивает, трамплин отбрасывает;
    /// - комета движется по кругу и обжигает тех, кто рядом;
    /// - пси-поля и радиоактивные пятна действуют на всех в радиусе.
    /// Компонент добавляется игрой к каждой карте автоматически.
    /// </summary>
    public class MapComponent_Zone : MapComponent
    {
        // ===== Воронка =====
        private const float VortexPullRadius = 4.9f;   // радиус затягивания
        private const int VortexPullInterval = 60;     // раз в 1 сек. (x1) тянет на клетку
        // ===== Трамплин =====
        private const float SpringboardRadius = 1.5f;  // соседние клетки
        private const int SpringboardThrowDistance = 5;
        private const float SpringboardDamage = 8f;
        private const int SpringboardStunTicks = 90;
        private const int SpringboardCooldown = 180;   // перезарядка между отбросами
        // ===== Комета =====
        private const int CometRouteRadius = 3;        // радиус круга, по которому она ходит
        private const int CometMoveInterval = 60;
        private const float CometBurnDamage = 8f;
        // ===== Пятна =====
        private const int FieldInterval = 120;
        private const float RadiationSpotRadius = 4.9f;
        private const float RadiationSpotPerHour = 0.15f;  // ~6.5 ч в пятне до смерти без защиты
        private const float PsiFieldRadius = 6.9f;
        private const float PsiFieldPerHour = 0.6f;        // ~70 мин до потери сознания
        private const float TicksPerHour = 2500f;

        // Сохраняется
        private bool fieldsSpawned;
        private Dictionary<int, IntVec3> cometOrigins = new Dictionary<int, IntVec3>();
        private Dictionary<int, int> cometSteps = new Dictionary<int, int>();

        // Не сохраняется
        private readonly Dictionary<int, int> springboardReadyTick = new Dictionary<int, int>();
        private readonly List<Thing> tmpThings = new List<Thing>();
        private readonly List<Pawn> tmpPawns = new List<Pawn>();
        private static readonly List<IntVec3> cometRing = BuildRing(CometRouteRadius);

        public MapComponent_Zone(Map map) : base(map)
        {
        }

        public override void FinalizeInit()
        {
            base.FinalizeInit();
            // Пси-поля и радиоактивные пятна — один раз на карту
            if (!fieldsSpawned)
            {
                AnomalyField.SpawnFields(map);
                fieldsSpawned = true;
            }
        }

        public override void MapComponentTick()
        {
            base.MapComponentTick();
            int tick = Find.TickManager.TicksGame;

            if (tick % 30 == 0)
                CheckContacts();
            if (tick % VortexPullInterval == 0)
                TickVortices();
            if (tick % 30 == 15)
                TickSpringboards(tick);
            if (tick % CometMoveInterval == 0)
                TickComets();
            if (tick % FieldInterval == 0)
                TickFields();
        }

        // ---------- Разряд при контакте ----------
        private void CheckContacts()
        {
            CollectThings(ZoneDefs.AllAnomalies);
            foreach (Thing anomaly in tmpThings)
            {
                if (ZoneDefs.Springboards.Contains(anomaly.def))
                    continue; // трамплин не взрывается от шага, он отбрасывает
                foreach (Thing thing in anomaly.Position.GetThingList(map))
                {
                    if (thing is Pawn pawn && !pawn.Dead)
                    {
                        ZoneEffects.Discharge(anomaly);
                        break;
                    }
                }
            }
        }

        // ---------- Воронка: затягивает к центру ----------
        private void TickVortices()
        {
            CollectThings(ZoneDefs.Vortices);
            foreach (Thing vortex in tmpThings)
            {
                IntVec3 center = vortex.Position;
                ZoneEffects.PawnsAround(center, map, VortexPullRadius, tmpPawns);
                foreach (Pawn pawn in tmpPawns)
                {
                    IntVec3 pos = pawn.Position;
                    if (pos.DistanceTo(center) <= 1.5f)
                    {
                        ZoneEffects.Discharge(vortex);   // втянуло — разряд
                        continue;
                    }
                    IntVec3 step = new IntVec3(Math.Sign(center.x - pos.x), 0, Math.Sign(center.z - pos.z));
                    IntVec3 next = pos + step;
                    if (next.InBounds(map) && next.Walkable(map))
                        ZoneEffects.MovePawn(pawn, next);
                }
            }
        }

        // ---------- Трамплин: отбрасывает и оглушает ----------
        private void TickSpringboards(int tick)
        {
            CollectThings(ZoneDefs.Springboards);
            foreach (Thing board in tmpThings)
            {
                if (springboardReadyTick.TryGetValue(board.thingIDNumber, out int ready) && tick < ready)
                    continue;
                ZoneEffects.PawnsAround(board.Position, map, SpringboardRadius, tmpPawns);
                if (tmpPawns.Count == 0)
                    continue;

                foreach (Pawn pawn in tmpPawns)
                {
                    IntVec3 from = board.Position;
                    IntVec3 dir = new IntVec3(Math.Sign(pawn.Position.x - from.x), 0, Math.Sign(pawn.Position.z - from.z));
                    if (dir == IntVec3.Zero)
                        dir = GenAdj.AdjacentCells[Rand.Range(0, 8)];

                    // Летим по направлению, пока не упрёмся в препятствие
                    IntVec3 dest = pawn.Position;
                    for (int i = 1; i <= SpringboardThrowDistance; i++)
                    {
                        IntVec3 c = from + new IntVec3(dir.x * (i + 1), 0, dir.z * (i + 1));
                        if (!c.InBounds(map) || !c.Walkable(map))
                            break;
                        dest = c;
                    }
                    if (dest != pawn.Position)
                        ZoneEffects.MovePawn(pawn, dest);
                    pawn.TakeDamage(new DamageInfo(DamageDefOf.Blunt, SpringboardDamage, 0f, -1f, board));
                    if (!pawn.Dead)
                        pawn.stances?.stunner?.StunFor(SpringboardStunTicks, board);
                }
                springboardReadyTick[board.thingIDNumber] = tick + SpringboardCooldown;
            }
        }

        // ---------- Комета: ходит по кругу и обжигает ----------
        private void TickComets()
        {
            CollectThings(ZoneDefs.Comets);
            foreach (Thing comet in tmpThings)
            {
                int id = comet.thingIDNumber;
                if (!cometOrigins.TryGetValue(id, out IntVec3 origin))
                {
                    origin = comet.Position;   // центр маршрута — место появления
                    cometOrigins[id] = origin;
                    cometSteps[id] = 0;
                }
                int stepIndex = (cometSteps.TryGetValue(id, out int s) ? s : 0) + 1;
                cometSteps[id] = stepIndex;
                IntVec3 dest = origin + cometRing[stepIndex % cometRing.Count];

                if (dest.InBounds(map) && dest.Standable(map) && dest.GetEdifice(map) == null && !map.areaManager.Home[dest])
                {
                    comet.DeSpawn();
                    GenSpawn.Spawn(comet, dest, map);
                }

                ZoneEffects.PawnsAround(comet.Position, map, 1.5f, tmpPawns);
                foreach (Pawn pawn in tmpPawns)
                    pawn.TakeDamage(new DamageInfo(DamageDefOf.Flame, CometBurnDamage, 0f, -1f, comet));
            }
        }

        // ---------- Пси-поля и радиоактивные пятна ----------
        private void TickFields()
        {
            if (ZoneDefs.RadiationSpot != null)
            {
                float dose = RadiationSpotPerHour * FieldInterval / TicksPerHour;
                foreach (Thing spot in map.listerThings.ThingsOfDef(ZoneDefs.RadiationSpot))
                {
                    ZoneEffects.PawnsAround(spot.Position, map, RadiationSpotRadius, tmpPawns);
                    foreach (Pawn pawn in tmpPawns)
                        ZoneEffects.AddRadiation(pawn, dose);
                }
            }
            if (ZoneDefs.PsiField != null)
            {
                float dose = PsiFieldPerHour * FieldInterval / TicksPerHour;
                foreach (Thing field in map.listerThings.ThingsOfDef(ZoneDefs.PsiField))
                {
                    ZoneEffects.PawnsAround(field.Position, map, PsiFieldRadius, tmpPawns);
                    foreach (Pawn pawn in tmpPawns)
                        ZoneEffects.AddPsi(pawn, dose);
                }
            }
        }

        // ---------- Служебное ----------
        /// <summary>Копия всех вещей нужных Def в tmpThings (обход безопасен при изменениях).</summary>
        private void CollectThings(List<ThingDef> defs)
        {
            tmpThings.Clear();
            foreach (ThingDef def in defs)
                tmpThings.AddRange(map.listerThings.ThingsOfDef(def));
        }

        private static List<IntVec3> BuildRing(int radius)
        {
            var ring = new List<IntVec3>();
            const int steps = 32;
            for (int i = 0; i < steps; i++)
            {
                double a = i * 2 * Math.PI / steps;
                var offset = new IntVec3((int)Math.Round(Math.Cos(a) * radius), 0, (int)Math.Round(Math.Sin(a) * radius));
                if (ring.Count == 0 || ring[ring.Count - 1] != offset)
                    ring.Add(offset);
            }
            if (ring.Count > 1 && ring[0] == ring[ring.Count - 1])
                ring.RemoveAt(ring.Count - 1);
            return ring;
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref fieldsSpawned, "fieldsSpawned", false);
            Scribe_Collections.Look(ref cometOrigins, "cometOrigins", LookMode.Value, LookMode.Value);
            Scribe_Collections.Look(ref cometSteps, "cometSteps", LookMode.Value, LookMode.Value);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (cometOrigins == null) cometOrigins = new Dictionary<int, IntVec3>();
                if (cometSteps == null) cometSteps = new Dictionary<int, int>();
            }
        }
    }
}
