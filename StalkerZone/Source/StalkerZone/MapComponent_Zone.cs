using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Поведение Зоны на карте (только C#). Добавляется игрой к каждой карте сама.
    /// - Аномалии вечные: срабатывают на приближение и перезаряжаются (AnomalyProfile).
    /// - У каждого типа свои повадки: затягивание, отброс, цепной разряд, едкая лужа.
    /// - Комета ходит по кругу и обжигает.
    /// - Пси-поля и радиоактивные пятна действуют на всех в радиусе.
    /// - Аномалии еле заметны; рядом с колонистом их выдают искры, марево или пыль.
    /// </summary>
    public class MapComponent_Zone : MapComponent
    {
        private const int CometRouteRadius = 3;
        private const int CometMoveInterval = 60;
        private const float CometBurnDamage = 8f;

        private const float ChainRadius = 6.9f;
        private const int ChainTargets = 3;

        private const int PuddleDurationTicks = 3600;      // ≈ 1,5 игрового часа
        private const float PuddleRadius = 1.9f;
        private const float PuddleDamage = 3f;

        private const int FieldInterval = 120;
        private const float RadiationSpotRadius = 4.9f;
        private const float RadiationSpotPerHour = 0.15f;
        private const float PsiFieldRadius = 6.9f;
        private const float PsiFieldPerHour = 0.6f;
        private const float TicksPerHour = 2500f;

        private const int HintInterval = 90;
        private const float HintRadius = 8f;               // "видно вблизи": в 8 клетках от колониста

        // Сохраняется
        private bool fieldsSpawned;
        private bool anomaliesBuilt;
        private Dictionary<int, IntVec3> cometOrigins = new Dictionary<int, IntVec3>();
        private Dictionary<int, int> cometSteps = new Dictionary<int, int>();
        private List<Thing> fieldArtifacts = new List<Thing>();

        // Не сохраняется
        private readonly Dictionary<int, int> readyTick = new Dictionary<int, int>();
        private readonly List<Puddle> puddles = new List<Puddle>();
        private readonly List<Thing> tmpThings = new List<Thing>();
        private readonly List<Pawn> tmpPawns = new List<Pawn>();
        private static readonly List<IntVec3> cometRing = BuildRing(CometRouteRadius);

        private class Puddle { public IntVec3 cell; public int expireTick; }

        public MapComponent_Zone(Map map) : base(map)
        {
        }

        public override void FinalizeInit()
        {
            base.FinalizeInit();
            // Один раз на карту: поле аномалий скоплениями (заменяет разбросанные генерацией)
            // и пси-поля с радиоактивными пятнами.
            if (!anomaliesBuilt)
            {
                AnomalyField.Rebuild(map);
                anomaliesBuilt = true;
            }
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
                TickAnomalies(tick);
            if (tick % CometMoveInterval == 0)
                TickComets();
            if (tick % FieldInterval == 0)
            {
                TickFields();
                TickPuddles(tick);
            }
            if (tick % HintInterval == 45)
                TickHints();
        }

        // ---------- Аномалии: затягивание и срабатывание ----------
        private void TickAnomalies(int tick)
        {
            CollectThings(ZoneDefs.AllAnomalies);
            foreach (Thing anomaly in tmpThings)
            {
                if (!anomaly.Spawned)
                    continue;
                AnomalyProfile p = ZoneDefs.ProfileOf(anomaly.def);

                if (p.pullRadius > 0f && tick % p.pullInterval == 0)
                    Pull(anomaly, p);

                if (p.triggerRadius <= 0f)
                    continue;
                if (readyTick.TryGetValue(anomaly.thingIDNumber, out int ready) && tick < ready)
                    continue;

                ZoneEffects.PawnsAround(anomaly.Position, map, p.triggerRadius, tmpPawns);
                if (tmpPawns.Count == 0)
                    continue;

                Trigger(anomaly, p, tick);
                readyTick[anomaly.thingIDNumber] = tick + p.cooldownTicks;
            }
        }

        /// <summary>Тянет пешек на клетку к центру (воронка, карусель, мясорубка).</summary>
        private void Pull(Thing anomaly, AnomalyProfile p)
        {
            IntVec3 center = anomaly.Position;
            ZoneEffects.PawnsAround(center, map, p.pullRadius, tmpPawns);
            foreach (Pawn pawn in tmpPawns)
            {
                IntVec3 pos = pawn.Position;
                if (pos.DistanceTo(center) <= 1.5f)
                    continue;   // уже в зоне срабатывания
                IntVec3 next = pos + new IntVec3(Math.Sign(center.x - pos.x), 0, Math.Sign(center.z - pos.z));
                if (next.InBounds(map) && next.Walkable(map))
                    ZoneEffects.MovePawn(pawn, next);
            }
        }

        private void Trigger(Thing anomaly, AnomalyProfile p, int tick)
        {
            // Трамплин: без взрыва, отбрасывает и оглушает
            if (p.throwsInsteadOfExplosion)
            {
                foreach (Pawn pawn in tmpPawns)
                {
                    ZoneEffects.ThrowPawn(pawn, anomaly.Position, p.throwDistance, false);
                    pawn.TakeDamage(new DamageInfo(DamageDefOf.Blunt, p.throwDamage, 0f, -1f, anomaly));
                    if (!pawn.Dead)
                        pawn.stances?.stunner?.StunFor(p.stunTicks, anomaly);
                }
                return;
            }

            ZoneEffects.Explode(anomaly);

            if (p.chainLightning)
                ZoneEffects.ChainLightning(anomaly, ChainRadius, ChainTargets);

            if (p.throwsAfterExplosion)   // карусель швыряет в случайную сторону
            {
                foreach (Pawn pawn in tmpPawns)
                {
                    if (pawn.Dead || !pawn.Spawned)
                        continue;
                    ZoneEffects.ThrowPawn(pawn, anomaly.Position, p.throwDistance, true);
                    pawn.stances?.stunner?.StunFor(p.stunTicks, anomaly);
                }
            }

            if (p.leavesPuddle)
                AddPuddle(anomaly.Position, tick);
        }

        // ---------- Холодец: едкая лужа ----------
        private void AddPuddle(IntVec3 center, int tick)
        {
            puddles.Add(new Puddle { cell = center, expireTick = tick + PuddleDurationTicks });
            if (ZoneDefs.PuddleFilth == null)
                return;
            foreach (IntVec3 c in GenRadial.RadialCellsAround(center, PuddleRadius, true))
            {
                if (c.InBounds(map) && c.Standable(map))
                    FilthMaker.TryMakeFilth(c, map, ZoneDefs.PuddleFilth);
            }
        }

        private void TickPuddles(int tick)
        {
            puddles.RemoveAll(pd => tick >= pd.expireTick);
            foreach (Puddle puddle in puddles)
            {
                ZoneEffects.PawnsAround(puddle.cell, map, PuddleRadius, tmpPawns);
                foreach (Pawn pawn in tmpPawns)
                    pawn.TakeDamage(new DamageInfo(SZ_DefOf.SZ_ChemicalBurn, PuddleDamage, 0f, -1f));
            }
        }

        // ---------- Комета: ходит по кругу и обжигает ----------
        private void TickComets()
        {
            CollectThings(ZoneDefs.Comets);
            foreach (Thing comet in tmpThings)
            {
                if (!comet.Spawned)
                    continue;
                int id = comet.thingIDNumber;
                if (!cometOrigins.TryGetValue(id, out IntVec3 origin))
                {
                    origin = comet.Position;
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

        // ---------- "Еле заметны, видно вблизи" ----------
        private void TickHints()
        {
            var colonists = map.mapPawns.FreeColonistsSpawned;
            if (colonists.Count == 0)
                return;
            CollectThings(ZoneDefs.AllAnomalies);
            foreach (Thing anomaly in tmpThings)
            {
                if (!anomaly.Spawned)
                    continue;
                foreach (Pawn colonist in colonists)
                {
                    if (colonist.Position.DistanceTo(anomaly.Position) <= HintRadius)
                    {
                        ZoneEffects.ThrowHint(anomaly, ZoneDefs.ProfileOf(anomaly.def).fleck);
                        break;
                    }
                }
            }
        }

        // ---------- Артефакты поля ----------
        public void RegisterFieldArtifact(Thing item)
        {
            fieldArtifacts.Add(item);
        }

        /// <summary>
        /// Перед новым полем: убирает артефакты, которые игрок так и не забрал
        /// (лежат вне колонии и всё ещё запрещены). Остальные считаются найденными.
        /// </summary>
        public void RemoveUnclaimedArtifacts()
        {
            foreach (Thing item in fieldArtifacts)
            {
                if (item == null || item.Destroyed || !item.Spawned || item.Map != map)
                    continue;
                if (!map.areaManager.Home[item.Position] && item.IsForbidden(Faction.OfPlayer))
                    item.Destroy(DestroyMode.Vanish);
            }
            fieldArtifacts.Clear();
        }

        // ---------- Служебное ----------
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
            if (Scribe.mode == LoadSaveMode.Saving)
                fieldArtifacts.RemoveAll(t => t == null || t.Destroyed);
            Scribe_Values.Look(ref fieldsSpawned, "fieldsSpawned", false);
            Scribe_Values.Look(ref anomaliesBuilt, "anomaliesBuilt", false);
            Scribe_Collections.Look(ref cometOrigins, "cometOrigins", LookMode.Value, LookMode.Value);
            Scribe_Collections.Look(ref cometSteps, "cometSteps", LookMode.Value, LookMode.Value);
            Scribe_Collections.Look(ref fieldArtifacts, "fieldArtifacts", LookMode.Reference);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (cometOrigins == null) cometOrigins = new Dictionary<int, IntVec3>();
                if (cometSteps == null) cometSteps = new Dictionary<int, int>();
                if (fieldArtifacts == null) fieldArtifacts = new List<Thing>();
                fieldArtifacts.RemoveAll(t => t == null);
            }
        }
    }
}
