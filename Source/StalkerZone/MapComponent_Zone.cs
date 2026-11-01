using System;
using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace StalkerZone
{
    /// <summary>
    /// Поведение Зоны на карте (только C#). Добавляется игрой к каждой карте сама.
    /// - Аномалии вечные: срабатывают на приближение, бьют своим уроном (без взрыва), перезаряжаются.
    /// - Повадки: затягивание, отброс, цепной разряд, едкая лужа; комета ходит по кругу.
    /// - Атаковать аномалию нельзя: приказ отменяется.
    /// - Детекторы: писк, метки аномалий, поиск артефактов, дозиметр.
    /// - Пси-поля и радиоактивные пятна действуют на всех в радиусе.
    /// </summary>
    public class MapComponent_Zone : MapComponent
    {
        private const int CometRouteRadius = 3;
        private const int CometMoveInterval = 60;

        private const float ChainRadius = 6.9f;
        private const int ChainTargets = 3;

        private const int PuddleDurationTicks = 3600;
        private const float PuddleRadius = 1.9f;
        private const float PuddleDamage = 3f;

        private const int FieldInterval = 120;
        private const float RadiationSpotRadius = 4.9f;
        private const float RadiationSpotPerHour = 0.15f;
        private const float PsiFieldRadius = 6.9f;
        private const float PsiFieldPerHour = 0.6f;
        private const float TicksPerHour = 2500f;

        private const int HintInterval = 90;
        private const float HintRadius = 8f;
        private const float IdleSoundChance = 0.3f;

        // ---------- сохраняется ----------
        private bool fieldsSpawned;
        private bool anomaliesBuilt;
        private bool signsPlaced;
        private Dictionary<int, IntVec3> cometOrigins = new Dictionary<int, IntVec3>();
        private Dictionary<int, int> cometSteps = new Dictionary<int, int>();
        private List<Thing> fieldArtifacts = new List<Thing>();
        private List<LatentArtifact> latentArtifacts = new List<LatentArtifact>();

        // ---------- не сохраняется ----------
        private readonly Dictionary<int, int> readyTick = new Dictionary<int, int>();
        private readonly Dictionary<int, int> nextBeep = new Dictionary<int, int>();
        private readonly Dictionary<int, int> nextGeiger = new Dictionary<int, int>();
        private readonly HashSet<Thing> detectedAnomalies = new HashSet<Thing>();
        private readonly HashSet<IntVec3> markedArtifacts = new HashSet<IntVec3>();
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
            if (!anomaliesBuilt)
            {
                AnomalyField.Rebuild(map);
                anomaliesBuilt = true;
            }
            if (!fieldsSpawned)
            {
                AnomalyField.SpawnFields(map);   // ставит и знаки
                fieldsSpawned = true;
                signsPlaced = true;
            }
            if (!signsPlaced && ZoneDefs.RadiationSpot != null)
            {
                // карта из прошлой версии: пятна уже есть, знаков нет
                foreach (Thing spot in map.listerThings.ThingsOfDef(ZoneDefs.RadiationSpot))
                    AnomalyField.PlaceSigns(spot);
                signsPlaced = true;
            }
        }

        public override void MapComponentTick()
        {
            base.MapComponentTick();
            int tick = Find.TickManager.TicksGame;

            if (tick % 10 == 0)
                TickAttackGuard();
            if (tick % 15 == 0)
                TickDetectors(tick);
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

        /// <summary>Метки детектора рисуются каждый кадр поверх карты.</summary>
        public override void MapComponentUpdate()
        {
            base.MapComponentUpdate();
            if (Find.CurrentMap != map || (detectedAnomalies.Count == 0 && markedArtifacts.Count == 0))
                return;
            float pulse = ZoneMats.Pulse(4f);
            foreach (Thing anomaly in detectedAnomalies)
            {
                if (anomaly.Spawned)
                    ZoneMats.DrawMarker(ZoneMats.AnomalyMarker, anomaly.DrawPos, 2.3f + 0.3f * pulse);
            }
            foreach (IntVec3 cell in markedArtifacts)
                ZoneMats.DrawMarker(ZoneMats.ArtifactMarker, cell.ToVector3Shifted(), 1.0f + 0.4f * pulse);
        }

        // ---------- Запрет атаки ----------
        private void TickAttackGuard()
        {
            var colonists = map.mapPawns.FreeColonistsSpawned;
            for (int i = 0; i < colonists.Count; i++)
            {
                Pawn pawn = colonists[i];
                Job job = pawn.CurJob;
                if (job == null || (job.def != JobDefOf.AttackMelee && job.def != JobDefOf.AttackStatic))
                    continue;
                Thing target = job.targetA.Thing;
                if (target == null || !ZoneDefs.IsAnomaly(target.def))
                    continue;
                pawn.jobs.EndCurrentJob(JobCondition.InterruptForced);
                Messages.Message("SZ_CannotAttackAnomaly".Translate(), pawn, MessageTypeDefOf.RejectInput, false);
            }
        }

        // ---------- Детекторы ----------
        private void TickDetectors(int tick)
        {
            detectedAnomalies.Clear();
            markedArtifacts.Clear();
            var colonists = map.mapPawns.FreeColonistsSpawned;
            if (colonists.Count == 0)
                return;
            CollectThings(ZoneDefs.AllAnomalies);

            for (int ci = 0; ci < colonists.Count; ci++)
            {
                Pawn pawn = colonists[ci];
                DetectorTier tier = Detectors.BestOf(pawn);
                if (tier == null)
                    continue;
                IntVec3 pos = pawn.Position;
                int id = pawn.thingIDNumber;

                // Аномалии: метки и писк (чем ближе, тем чаще)
                float nearest = float.MaxValue;
                foreach (Thing anomaly in tmpThings)
                {
                    if (!anomaly.Spawned)
                        continue;
                    float d = anomaly.Position.DistanceTo(pos);
                    if (d <= tier.anomalyRange)
                    {
                        detectedAnomalies.Add(anomaly);
                        if (d < nearest) nearest = d;
                    }
                }
                if (nearest < float.MaxValue && (!nextBeep.TryGetValue(id, out int nb) || tick >= nb))
                {
                    ZoneEffects.PlaySound(SZ_DefOf.SZ_Detector_Beep, pos, map);
                    nextBeep[id] = tick + 15 + (int)(nearest * 10f);   // вплотную ~4 раза в сек., на краю раз в 2 сек.
                }

                // Артефакты: находим вблизи, метим издалека
                for (int i = latentArtifacts.Count - 1; i >= 0; i--)
                {
                    LatentArtifact la = latentArtifacts[i];
                    if (la.def == null || la.tier > tier.level)
                        continue;
                    float d = la.cell.DistanceTo(pos);
                    if (d <= tier.revealRange)
                    {
                        Reveal(la);
                        latentArtifacts.RemoveAt(i);
                    }
                    else if (d <= tier.markRange)
                    {
                        markedArtifacts.Add(la.cell);
                    }
                }

                // Дозиметр: щелчки в радиоактивном пятне, чаще ближе к центру
                if (ZoneDefs.RadiationSpot != null && (!nextGeiger.TryGetValue(id, out int ng) || tick >= ng))
                {
                    float best = float.MaxValue;
                    foreach (Thing spot in map.listerThings.ThingsOfDef(ZoneDefs.RadiationSpot))
                        best = Math.Min(best, spot.Position.DistanceTo(pos));
                    if (best <= RadiationSpotRadius + 1f)
                    {
                        ZoneEffects.PlaySound(SZ_DefOf.SZ_Geiger_Click, pos, map);
                        nextGeiger[id] = tick + (int)(best * 4f) + Rand.Range(0, 12);
                    }
                }
            }
        }

        /// <summary>Артефакт найден: появляется на земле (запрещён для подбора — решение за игроком).</summary>
        private void Reveal(LatentArtifact la)
        {
            IntVec3 cell = la.cell;
            if (!cell.InBounds(map) || !cell.Standable(map) || cell.GetEdifice(map) != null)
            {
                if (!CellFinder.TryFindRandomCellNear(la.cell, map, 2, c => c.Standable(map) && c.GetEdifice(map) == null, out cell))
                    return;
            }
            Thing item = GenSpawn.Spawn(ThingMaker.MakeThing(la.def), cell, map);
            item.SetForbidden(true, false);
            fieldArtifacts.Add(item);
            ZoneEffects.PlaySound(SZ_DefOf.SZ_Detector_Artifact, cell, map);
            Messages.Message("SZ_ArtifactDetected".Translate(item.LabelCap), item, MessageTypeDefOf.PositiveEvent, false);
        }

        public void AddLatentArtifact(IntVec3 cell, ThingDef def, int tier)
        {
            latentArtifacts.Add(new LatentArtifact { cell = cell, def = def, tier = tier });
        }

        public void ClearLatentArtifacts()
        {
            latentArtifacts.Clear();
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

        private void Pull(Thing anomaly, AnomalyProfile p)
        {
            IntVec3 center = anomaly.Position;
            ZoneEffects.PawnsAround(center, map, p.pullRadius, tmpPawns);
            foreach (Pawn pawn in tmpPawns)
            {
                IntVec3 pos = pawn.Position;
                if (pos.DistanceTo(center) <= 1.5f)
                    continue;
                IntVec3 next = pos + new IntVec3(Math.Sign(center.x - pos.x), 0, Math.Sign(center.z - pos.z));
                if (next.InBounds(map) && next.Walkable(map))
                {
                    FleckMaker.ThrowDustPuff(pos, map, 0.6f);
                    ZoneEffects.MovePawn(pawn, next);
                }
            }
        }

        private void Trigger(Thing anomaly, AnomalyProfile p, int tick)
        {
            // Трамплин: удар и отброс, без урона по площади
            if (p.throwsInsteadOfDamage)
            {
                ZoneEffects.PlaySound(p.Sound, anomaly.Position, map);
                FleckMaker.ThrowDustPuff(anomaly.Position, map, 2f);
                foreach (Pawn pawn in tmpPawns)
                {
                    ZoneEffects.ThrowPawn(pawn, anomaly.Position, p.throwDistance, false);
                    pawn.TakeDamage(new DamageInfo(DamageDefOf.Blunt, p.throwDamage, 0f, -1f, anomaly));
                    if (!pawn.Dead)
                        pawn.stances?.stunner?.StunFor(p.stunTicks, anomaly);
                }
                return;
            }

            List<Pawn> victims = ZoneEffects.Discharge(anomaly, p);

            if (p.chainLightning)
                ZoneEffects.ChainLightning(anomaly, ChainRadius, ChainTargets, p.Damage);

            if (p.throwsAfterDischarge)
            {
                foreach (Pawn pawn in victims)
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

        // ---------- Комета ----------
        private void TickComets()
        {
            CollectThings(ZoneDefs.Comets);
            foreach (Thing comet in tmpThings)
            {
                if (!comet.Spawned)
                    continue;
                AnomalyProfile p = ZoneDefs.ProfileOf(comet.def);
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
                    FleckMaker.ThrowHeatGlow(dest, map, 1.5f);
                }

                ZoneEffects.PawnsAround(comet.Position, map, 1.5f, tmpPawns);
                if (tmpPawns.Count > 0)
                {
                    ZoneEffects.PlaySound(p.Sound, comet.Position, map);
                    FleckMaker.ThrowFireGlow(comet.DrawPos, map, 2f);
                    DamageDef damage = p.Damage ?? DamageDefOf.Flame;
                    foreach (Pawn pawn in tmpPawns)
                        pawn.TakeDamage(new DamageInfo(damage, p.damageAmount, 0.2f, -1f, comet));
                }
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

        // ---------- Признаки и звуки вблизи (без детектора) ----------
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
                        AnomalyProfile p = ZoneDefs.ProfileOf(anomaly.def);
                        ZoneEffects.ThrowHint(anomaly, p.fleck);
                        if (Rand.Chance(IdleSoundChance))
                            ZoneEffects.PlaySound(p.IdleSound, anomaly.Position, map);
                        break;
                    }
                }
            }
        }

        // ---------- Артефакты поля ----------
        /// <summary>
        /// Перед новым полем: убирает найденные, но не подобранные артефакты
        /// (лежат вне колонии и всё ещё запрещены).
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
            Scribe_Values.Look(ref signsPlaced, "signsPlaced", false);
            Scribe_Collections.Look(ref cometOrigins, "cometOrigins", LookMode.Value, LookMode.Value);
            Scribe_Collections.Look(ref cometSteps, "cometSteps", LookMode.Value, LookMode.Value);
            Scribe_Collections.Look(ref fieldArtifacts, "fieldArtifacts", LookMode.Reference);
            Scribe_Collections.Look(ref latentArtifacts, "latentArtifacts", LookMode.Deep);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (cometOrigins == null) cometOrigins = new Dictionary<int, IntVec3>();
                if (cometSteps == null) cometSteps = new Dictionary<int, int>();
                if (fieldArtifacts == null) fieldArtifacts = new List<Thing>();
                if (latentArtifacts == null) latentArtifacts = new List<LatentArtifact>();
                fieldArtifacts.RemoveAll(t => t == null);
                latentArtifacts.RemoveAll(la => la == null || la.def == null);
            }
        }
    }
}
