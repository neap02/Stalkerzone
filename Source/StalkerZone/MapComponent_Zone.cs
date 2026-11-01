using System;
using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace StalkerZone
{
    /// <summary>
    /// Зона на карте (только C#). Добавляется игрой к каждой карте сама.
    /// - Хранит аномалии и пятна как записи (не вещи): их нельзя выбрать, атаковать, перенести или купить.
    /// - Рисует их сама (анимация + свечение) и показывает подсказку при наведении курсора.
    /// - Срабатывание на приближение, свой урон, перезарядка, повадки каждого типа.
    /// - Из затягивания можно вырваться; пойманные пешки сами бегут прочь.
    /// - Детекторы: писк, метки, поиск артефактов, дозиметр.
    /// - Пси-поля и радиоактивные пятна действуют на всех в радиусе.
    /// </summary>
    public class MapComponent_Zone : MapComponent
    {
        private const float ChainRadius = 6.9f;
        private const int ChainTargets = 3;

        private const int PuddleDurationTicks = 3600;
        private const float PuddleRadius = 1.9f;
        private const float PuddleDamageFactor = 0.25f;

        private const int FieldInterval = 120;
        private const float TicksPerHour = 2500f;

        private const int HintInterval = 90;
        private const float HintRadius = 8f;
        private const float IdleSoundChance = 0.3f;

        private const float DraftedPullFactor = 0.5f;
        private const float DownedPullFactor = 0.5f;
        private const int FleeCooldownTicks = 300;
        private const int CometMoveInterval = 60;

        // ---------- сохраняется ----------
        private List<AnomalyInstance> anomalies = new List<AnomalyInstance>();
        private int nextAnomalyId = 1;
        private bool phenomenaBuilt;
        private List<ZoneFieldInstance> fields = new List<ZoneFieldInstance>();
        private int nextFieldId = 1;
        private bool fieldsBuilt;
        private List<Thing> fieldArtifacts = new List<Thing>();
        private List<LatentArtifact> latentArtifacts = new List<LatentArtifact>();

        // ---------- не сохраняется ----------
        private readonly Dictionary<int, int> nextBeep = new Dictionary<int, int>();
        private readonly Dictionary<int, int> nextGeiger = new Dictionary<int, int>();
        private readonly Dictionary<int, int> fleeUntil = new Dictionary<int, int>();
        private readonly HashSet<AnomalyInstance> detected = new HashSet<AnomalyInstance>();
        private readonly HashSet<IntVec3> markedArtifacts = new HashSet<IntVec3>();
        private readonly List<Puddle> puddles = new List<Puddle>();
        private readonly List<Pawn> tmpPawns = new List<Pawn>();
        private static readonly Dictionary<int, List<IntVec3>> rings = new Dictionary<int, List<IntVec3>>();

        private class Puddle { public IntVec3 cell; public int expireTick; }

        public MapComponent_Zone(Map map) : base(map)
        {
        }

        public List<AnomalyInstance> Anomalies => anomalies;

        public AnomalyInstance AddAnomaly(AnomalyDef def, IntVec3 cell)
        {
            var a = new AnomalyInstance { id = nextAnomalyId++, def = def, pos = cell, origin = cell };
            anomalies.Add(a);
            return a;
        }

        public void ClearAnomalies()
        {
            anomalies.Clear();
            detected.Clear();
        }

        public List<ZoneFieldInstance> Fields => fields;

        public ZoneFieldInstance AddField(ZoneFieldDef def, IntVec3 cell)
        {
            var f = new ZoneFieldInstance { id = nextFieldId++, def = def, pos = cell };
            fields.Add(f);
            return f;
        }

        public bool AnyFieldWithin(IntVec3 c, float radius)
        {
            float r2 = radius * radius;
            foreach (ZoneFieldInstance f in fields)
            {
                if ((f.pos - c).LengthHorizontalSquared <= r2)
                    return true;
            }
            return false;
        }

        public bool AnyAnomalyWithin(IntVec3 c, float radius)
        {
            float r2 = radius * radius;
            foreach (AnomalyInstance a in anomalies)
            {
                if ((a.pos - c).LengthHorizontalSquared <= r2)
                    return true;
            }
            return false;
        }

        public override void FinalizeInit()
        {
            base.FinalizeInit();
            if (!phenomenaBuilt)
            {
                // Новая карта или сохранение до этой версии: строим поле аномалий-явлений
                AnomalyField.Rebuild(map);
                phenomenaBuilt = true;
            }
            if (!fieldsBuilt)
            {
                // Новая карта или сохранение, где пятна ещё были вещами
                AnomalyField.SpawnFields(map);
                fieldsBuilt = true;
            }
        }

        public override void MapComponentTick()
        {
            base.MapComponentTick();
            int tick = Find.TickManager.TicksGame;
            if (tick % 15 == 0) TickDetectors(tick);
            if (tick % 30 == 0) TickAnomalies(tick);
            if (tick % 60 == 20) TickNearEffects();
            if (tick % 250 == 75) ZoneAmbience.Tick(map, tick);
            if (tick % CometMoveInterval == 0) TickComets();
            if (tick % FieldInterval == 0) { TickFields(); TickPuddles(tick); }
            if (tick % HintInterval == 45) TickHints();
            if (tick % ZoneArtifacts.Interval == 100) TickArtifacts();
        }

        // ---------- Отрисовка ----------
        public override void MapComponentUpdate()
        {
            base.MapComponentUpdate();
            if (Find.CurrentMap != map)
                return;
            CellRect view = Find.CameraDriver.CurrentViewRect.ExpandedBy(3);
            CellRect wide = view.ExpandedBy(8);
            foreach (ZoneFieldInstance f in fields)
            {
                if (f.def != null && wide.Contains(f.pos) && !f.pos.Fogged(map))
                    ZoneMats.DrawField(f);
            }
            foreach (AnomalyInstance a in anomalies)
            {
                if (a.def != null && view.Contains(a.pos) && !a.pos.Fogged(map))
                    ZoneMats.DrawAnomaly(a.def, a.pos, a.id);
            }
            if (detected.Count == 0 && markedArtifacts.Count == 0)
                return;
            float pulse = ZoneMats.Pulse(4f);
            foreach (AnomalyInstance a in detected)
                ZoneMats.DrawMarker(ZoneMats.AnomalyMarker, a.pos.ToVector3Shifted(), 2.3f + 0.3f * pulse);
            foreach (IntVec3 cell in markedArtifacts)
                ZoneMats.DrawMarker(ZoneMats.ArtifactMarker, cell.ToVector3Shifted(), 1.0f + 0.4f * pulse);
        }

        /// <summary>Подсказка при наведении на аномалию: название, описание, урон.</summary>
        public override void MapComponentOnGUI()
        {
            base.MapComponentOnGUI();
            if (Find.CurrentMap != map || Find.WindowStack.GetWindowAt(UI.MousePositionOnUIInverted) != null)
                return;
            IntVec3 mouse = UI.MouseCell();
            if (!mouse.InBounds(map) || mouse.Fogged(map))
                return;
            foreach (AnomalyInstance a in anomalies)
            {
                if (a.def != null && (a.pos - mouse).LengthHorizontalSquared <= 1)
                {
                    ZoneMats.DrawHoverTip(a.def.LabelCap.Resolve() + "\n\n" + a.def.description);
                    return;
                }
            }
            foreach (ZoneFieldInstance f in fields)
            {
                if (f.def == null)
                    continue;
                if (f.signs.Contains(mouse))
                {
                    ZoneMats.DrawHoverTip("SZ_RadiationSignTip".Translate().Resolve());
                    return;
                }
                if ((f.pos - mouse).LengthHorizontalSquared <= 2)
                {
                    ZoneMats.DrawHoverTip(f.def.LabelCap.Resolve() + "\n\n" + f.def.description);
                    return;
                }
            }
        }

        // ---------- Детекторы ----------
        private void TickDetectors(int tick)
        {
            detected.Clear();
            markedArtifacts.Clear();
            var colonists = map.mapPawns.FreeColonistsSpawned;
            for (int ci = 0; ci < colonists.Count; ci++)
            {
                Pawn pawn = colonists[ci];
                DetectorTier tier = Detectors.BestOf(pawn);
                if (tier == null)
                    continue;
                IntVec3 pos = pawn.Position;
                int id = pawn.thingIDNumber;

                float nearest = float.MaxValue;
                foreach (AnomalyInstance a in anomalies)
                {
                    float d = a.pos.DistanceTo(pos);
                    if (d <= tier.anomalyRange)
                    {
                        detected.Add(a);
                        if (d < nearest) nearest = d;
                    }
                }
                if (nearest < float.MaxValue && (!nextBeep.TryGetValue(id, out int nb) || tick >= nb))
                {
                    ZoneEffects.PlaySound(SZ_DefOf.SZ_Detector_Beep, pos, map);
                    nextBeep[id] = tick + 15 + (int)(nearest * 10f);
                }

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

                if (!nextGeiger.TryGetValue(id, out int ng) || tick >= ng)
                {
                    float best = float.MaxValue;
                    float edge = 0f;
                    foreach (ZoneFieldInstance f in fields)
                    {
                        if (f.def == null || !f.def.geiger)
                            continue;
                        float d = f.pos.DistanceTo(pos);
                        if (d < best) { best = d; edge = f.def.radius; }
                    }
                    if (best <= edge + 1f)
                    {
                        ZoneEffects.PlaySound(SZ_DefOf.SZ_Geiger_Click, pos, map);
                        nextGeiger[id] = tick + (int)(best * 4f) + Rand.Range(0, 12);
                    }
                }
            }
        }

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


        // ---------- Артефакты из инвентаря ----------
        private void TickArtifacts()
        {
            tmpPawns.Clear();
            tmpPawns.AddRange(map.mapPawns.AllPawnsSpawned);
            foreach (Pawn pawn in tmpPawns)
            {
                ZoneArtifacts.TickPawn(pawn);
                SuitRepair.TryAutoRepair(pawn);   // ремкомплекты из инвентаря
            }
            tmpPawns.Clear();
        }

        // ---------- Воздействие вблизи ----------
        /// <summary>
        /// Рядом с аномалией (до срабатывания) пешка чувствует её: жар, статику, тяжесть,
        /// едкие пары или жжение. Эффект держится, пока пешка рядом, и проходит за ~20 сек.
        /// </summary>
        private void TickNearEffects()
        {
            foreach (AnomalyInstance a in anomalies)
            {
                AnomalyDef def = a.def;
                if (def == null || def.nearHediff == null || def.nearRadius <= 0f)
                    continue;
                ZoneEffects.PawnsAround(a.pos, map, def.nearRadius, tmpPawns);
                foreach (Pawn pawn in tmpPawns)
                {
                    if (!pawn.RaceProps.IsFlesh)
                        continue;
                    Hediff h = pawn.health.hediffSet.GetFirstHediffOfDef(def.nearHediff);
                    if (h == null)
                    {
                        h = HediffMaker.MakeHediff(def.nearHediff, pawn);
                        h.Severity = 1f;
                        pawn.health.AddHediff(h);
                    }
                    else
                    {
                        h.Severity = 1f;
                    }
                    if (Rand.Chance(0.3f))
                        ZoneEffects.ThrowHint(map, pawn.Position, def.fleck);
                }
            }
        }

        // ---------- Срабатывание и затягивание ----------
        private void TickAnomalies(int tick)
        {
            foreach (AnomalyInstance a in anomalies)
            {
                AnomalyDef def = a.def;
                if (def == null || def.moves)
                    continue;
                bool charged = tick >= a.readyTick;

                if (charged && def.pullRadius > 0f && tick % def.pullInterval == 0)
                    Pull(a, tick);

                if (def.triggerRadius <= 0f || !charged)
                    continue;
                ZoneEffects.PawnsAround(a.pos, map, def.triggerRadius, tmpPawns);
                if (tmpPawns.Count == 0)
                    continue;
                Trigger(a, tick);
                a.readyTick = tick + def.cooldownTicks;
            }
        }

        /// <summary>
        /// Шанс рывка = сила × (1 − расстояние/радиус): у края почти не тянет, у центра сильно.
        /// Пешка не теряет своё дело: уходящая прочь продолжает уходить.
        /// </summary>
        private void Pull(AnomalyInstance a, int tick)
        {
            AnomalyDef def = a.def;
            IntVec3 center = a.pos;
            ZoneEffects.PawnsAround(center, map, def.pullRadius, tmpPawns);
            foreach (Pawn pawn in tmpPawns)
            {
                IntVec3 pos = pawn.Position;
                float dist = pos.DistanceTo(center);
                if (dist <= 1.5f)
                    continue;
                float chance = def.pullStrength * (1f - dist / def.pullRadius);
                if (pawn.Drafted) chance *= DraftedPullFactor;
                if (pawn.Downed) chance *= DownedPullFactor;
                if (Rand.Chance(chance))
                {
                    IntVec3 next = pos + new IntVec3(Math.Sign(center.x - pos.x), 0, Math.Sign(center.z - pos.z));
                    if (next.InBounds(map) && next.Walkable(map))
                    {
                        FleckMaker.ThrowDustPuff(pos, map, 0.6f);
                        ZoneEffects.MovePawn(pawn, next, true);
                    }
                }
                TryFlee(pawn, center, def.pullRadius, tick);
            }
        }

        /// <summary>Пойманная пешка (не призванная) сама бежит прочь.</summary>
        private void TryFlee(Pawn pawn, IntVec3 center, float radius, int tick)
        {
            if (pawn.Drafted || pawn.Downed || pawn.Dead || !pawn.Spawned || pawn.jobs == null || pawn.InMentalState)
                return;
            if (fleeUntil.TryGetValue(pawn.thingIDNumber, out int until) && tick < until)
                return;
            IntVec3 pos = pawn.Position;
            IntVec3 dir = new IntVec3(Math.Sign(pos.x - center.x), 0, Math.Sign(pos.z - center.z));
            if (dir == IntVec3.Zero)
                dir = GenAdj.AdjacentCells[Rand.Range(0, 8)];
            int steps = (int)(radius - pos.DistanceTo(center)) + 3;
            IntVec3 target = pos + new IntVec3(dir.x * steps, 0, dir.z * steps);
            if (CellFinder.TryFindRandomCellNear(target, map, 2,
                    c => c.InBounds(map) && c.Standable(map) && c.DistanceTo(center) > radius + 1f, out IntVec3 dest))
            {
                Job job = JobMaker.MakeJob(JobDefOf.Goto, dest);
                job.locomotionUrgency = LocomotionUrgency.Sprint;
                pawn.jobs.StartJob(job, JobCondition.InterruptForced);
                fleeUntil[pawn.thingIDNumber] = tick + FleeCooldownTicks;
            }
        }

        private void Trigger(AnomalyInstance a, int tick)
        {
            AnomalyDef def = a.def;
            if (def.throwsInsteadOfDamage)
            {
                ZoneEffects.PlaySound(def.sound, a.pos, map);
                FleckMaker.ThrowDustPuff(a.pos, map, 2f);
                foreach (Pawn pawn in tmpPawns)
                {
                    ZoneEffects.ThrowPawn(pawn, a.pos, def.throwDistance, false);
                    if (def.damage != null)
                        pawn.TakeDamage(new DamageInfo(def.damage, def.DamageAmount, def.ArmorPenetration));
                    ZoneEffects.Stun(pawn, def.stunTicks);
                }
                return;
            }

            List<Pawn> victims = ZoneEffects.Discharge(map, a.pos, def);
            if (def.chainLightning)
                ZoneEffects.ChainLightning(map, a.pos, def, ChainRadius, ChainTargets);
            if (def.throwsAfterDischarge)
            {
                foreach (Pawn pawn in victims)
                {
                    if (pawn.Dead || !pawn.Spawned)
                        continue;
                    ZoneEffects.ThrowPawn(pawn, a.pos, def.throwDistance, true);
                    ZoneEffects.Stun(pawn, def.stunTicks);
                }
            }
            if (def.leavesPuddle)
                AddPuddle(a.pos, tick);
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
            DamageDef acid = SZ_DefOf.SZ_ChemicalBurn;
            foreach (Puddle puddle in puddles)
            {
                ZoneEffects.PawnsAround(puddle.cell, map, PuddleRadius, tmpPawns);
                foreach (Pawn pawn in tmpPawns)
                    pawn.TakeDamage(new DamageInfo(acid, acid.defaultDamage * PuddleDamageFactor));
            }
        }

        // ---------- Комета ----------
        private void TickComets()
        {
            foreach (AnomalyInstance a in anomalies)
            {
                AnomalyDef def = a.def;
                if (def == null || !def.moves)
                    continue;
                List<IntVec3> ring = RingOf(def.routeRadius);
                a.step++;
                IntVec3 dest = a.origin + ring[a.step % ring.Count];
                if (dest.InBounds(map) && dest.Standable(map) && dest.GetEdifice(map) == null && !map.areaManager.Home[dest])
                {
                    a.pos = dest;
                    FleckMaker.ThrowHeatGlow(dest, map, 1.5f);
                }
                ZoneEffects.PawnsAround(a.pos, map, 1.5f, tmpPawns);
                if (tmpPawns.Count > 0)
                {
                    ZoneEffects.PlaySound(def.sound, a.pos, map);
                    FleckMaker.ThrowFireGlow(a.pos.ToVector3Shifted(), map, 2f);
                    if (def.damage != null)
                    {
                        foreach (Pawn pawn in tmpPawns)
                            pawn.TakeDamage(new DamageInfo(def.damage, def.DamageAmount, def.ArmorPenetration));
                    }
                }
            }
        }

        private static List<IntVec3> RingOf(int radius)
        {
            if (rings.TryGetValue(radius, out List<IntVec3> ring))
                return ring;
            ring = new List<IntVec3>();
            const int steps = 32;
            for (int i = 0; i < steps; i++)
            {
                double ang = i * 2 * Math.PI / steps;
                var offset = new IntVec3((int)Math.Round(Math.Cos(ang) * radius), 0, (int)Math.Round(Math.Sin(ang) * radius));
                if (ring.Count == 0 || ring[ring.Count - 1] != offset)
                    ring.Add(offset);
            }
            if (ring.Count > 1 && ring[0] == ring[ring.Count - 1])
                ring.RemoveAt(ring.Count - 1);
            rings[radius] = ring;
            return ring;
        }

        // ---------- Пси-поля и радиоактивные пятна ----------
        private void TickFields()
        {
            foreach (ZoneFieldInstance f in fields)
            {
                if (f.def == null)
                    continue;
                float dose = f.def.dosePerHour * FieldInterval / TicksPerHour;
                ZoneEffects.PawnsAround(f.pos, map, f.def.radius, tmpPawns);
                foreach (Pawn pawn in tmpPawns)
                {
                    if (f.def.kind == FieldKind.Psi)
                        ZoneEffects.AddPsi(pawn, dose);
                    else
                        ZoneEffects.AddRadiation(pawn, dose);
                }
            }
        }

        // ---------- Признаки и звуки вблизи ----------
        private void TickHints()
        {
            var colonists = map.mapPawns.FreeColonistsSpawned;
            if (colonists.Count == 0)
                return;
            foreach (AnomalyInstance a in anomalies)
            {
                if (a.def == null)
                    continue;
                foreach (Pawn colonist in colonists)
                {
                    if (colonist.Position.DistanceTo(a.pos) <= HintRadius)
                    {
                        ZoneEffects.ThrowHint(map, a.pos, a.def.fleck);
                        if (Rand.Chance(IdleSoundChance))
                            ZoneEffects.PlaySound(a.def.idleSound, a.pos, map);
                        break;
                    }
                }
            }
        }

        // ---------- Артефакты поля ----------
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

        public override void ExposeData()
        {
            base.ExposeData();
            if (Scribe.mode == LoadSaveMode.Saving)
                fieldArtifacts.RemoveAll(t => t == null || t.Destroyed);
            Scribe_Collections.Look(ref anomalies, "anomalies", LookMode.Deep);
            Scribe_Values.Look(ref nextAnomalyId, "nextAnomalyId", 1);
            Scribe_Values.Look(ref phenomenaBuilt, "phenomenaBuilt", false);
            Scribe_Collections.Look(ref fields, "zoneFields", LookMode.Deep);
            Scribe_Values.Look(ref nextFieldId, "nextFieldId", 1);
            Scribe_Values.Look(ref fieldsBuilt, "zoneFieldsBuilt", false);
            Scribe_Collections.Look(ref fieldArtifacts, "fieldArtifacts", LookMode.Reference);
            Scribe_Collections.Look(ref latentArtifacts, "latentArtifacts", LookMode.Deep);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (anomalies == null) anomalies = new List<AnomalyInstance>();
                if (fields == null) fields = new List<ZoneFieldInstance>();
                fields.RemoveAll(f => f == null || f.def == null);
                if (fieldArtifacts == null) fieldArtifacts = new List<Thing>();
                if (latentArtifacts == null) latentArtifacts = new List<LatentArtifact>();
                anomalies.RemoveAll(a => a == null || a.def == null);
                fieldArtifacts.RemoveAll(t => t == null);
                latentArtifacts.RemoveAll(la => la == null || la.def == null);
            }
        }
    }
}
