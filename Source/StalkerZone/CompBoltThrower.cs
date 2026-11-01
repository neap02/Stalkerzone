using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace StalkerZone
{
    /// <summary>Иконки кнопок. Загружаются один раз при старте.</summary>
    [StaticConstructorOnStartup]
    public static class ZoneTex
    {
        public static readonly Texture2D Bolt = ContentFinder<Texture2D>.Get("UI/SZ/Bolt");
        public static readonly Texture2D Belt = ContentFinder<Texture2D>.Get("UI/SZ/Belt");
        public static readonly Texture2D Repair = ContentFinder<Texture2D>.Get("UI/SZ/Repair");
    }

    /// <summary>
    /// Снаряжение Зоны (костюмы и детекторы) даёт владельцу кнопки
    /// "Бросить болт" и "Артефакт на пояс".
    /// </summary>
    public class CompProperties_BoltThrower : CompProperties
    {
        public float range = 10f;   // дальность броска, клеток

        public CompProperties_BoltThrower()
        {
            compClass = typeof(CompBoltThrower);
        }
    }

    public class CompBoltThrower : ThingComp
    {
        public CompProperties_BoltThrower Props => (CompProperties_BoltThrower)props;

        public override IEnumerable<Gizmo> CompGetWornGizmosExtra()
        {
            Pawn wearer = (parent as Apparel)?.Wearer;
            if (wearer == null || !wearer.Spawned || !wearer.IsColonistPlayerControlled || wearer.apparel == null)
                yield break;

            // Кнопка одна, даже если болты есть и в костюме, и в детекторе
            foreach (Apparel a in wearer.apparel.WornApparel)
            {
                if (a.GetComp<CompBoltThrower>() != null)
                {
                    if (a != parent)
                        yield break;
                    break;
                }
            }

            float range = Props.range;
            yield return new Command_Target
            {
                defaultLabel = "SZ_ThrowBolt".Translate(),
                defaultDesc = "SZ_ThrowBoltDesc".Translate(),
                icon = ZoneTex.Bolt,
                targetingParams = new TargetingParameters
                {
                    canTargetLocations = true,
                    canTargetPawns = false,
                    canTargetBuildings = false,
                    canTargetItems = false
                },
                action = target => wearer.Map?.GetComponent<MapComponent_Zone>()?.ThrowBolt(wearer, target.Cell, range)
            };

            // Подобрать артефакт с земли в инвентарь (пояс)
            yield return new Command_Target
            {
                defaultLabel = "SZ_BeltLabel".Translate(),
                defaultDesc = "SZ_BeltDesc".Translate(),
                icon = ZoneTex.Belt,
                targetingParams = new TargetingParameters
                {
                    canTargetItems = true,
                    canTargetPawns = false,
                    canTargetBuildings = false,
                    validator = t => t.HasThing && t.Thing.def.GetModExtension<ArtifactExtension>() != null
                },
                action = target => TakeArtifact(wearer, target.Thing)
            };
        }

        private static void TakeArtifact(Pawn pawn, Thing thing)
        {
            if (thing == null || !thing.Spawned || pawn.jobs == null)
                return;
            thing.SetForbidden(false, false);
            Job job = JobMaker.MakeJob(JobDefOf.TakeInventory, thing);
            job.count = 1;
            pawn.jobs.TryTakeOrderedJob(job);
        }
    }
}
