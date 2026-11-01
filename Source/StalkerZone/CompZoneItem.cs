using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace StalkerZone
{
    public class CompProperties_ZoneItem : CompProperties
    {
        public CompProperties_ZoneItem()
        {
            compClass = typeof(CompZoneItem);
        }
    }

    /// <summary>
    /// Правая кнопка по предмету Зоны на земле (выбран колонист):
    /// - артефакт: "Надеть на пояс" — колонист подбирает его в инвентарь, там он и работает;
    /// - ремкомплект: "Починить костюм" — подбирает и сразу чинит надетый костюм Зоны.
    /// </summary>
    public class CompZoneItem : ThingComp
    {
        public override IEnumerable<FloatMenuOption> CompFloatMenuOptions(Pawn selPawn)
        {
            foreach (FloatMenuOption o in base.CompFloatMenuOptions(selPawn))
                yield return o;
            if (selPawn == null || !selPawn.IsColonistPlayerControlled || selPawn.inventory == null || !parent.Spawned)
                yield break;

            bool artifact = parent.def.GetModExtension<ArtifactExtension>() != null;
            bool kit = parent.def == SZ_DefOf.SZ_RepairKit;
            if (!artifact && !kit)
                yield break;

            bool repairNow = kit && SuitRepair.MostWornSuit(selPawn) != null
                             && SuitRepair.MostWornSuit(selPawn).HitPoints < SuitRepair.MostWornSuit(selPawn).MaxHitPoints;
            string label = artifact ? "SZ_PutOnBelt".Translate(parent.LabelShort).Resolve()
                         : repairNow ? "SZ_RepairWithKit".Translate().Resolve()
                         : "SZ_TakeKit".Translate(parent.LabelShort).Resolve();

            if (!selPawn.CanReach(parent, PathEndMode.ClosestTouch, Danger.Deadly))
            {
                yield return new FloatMenuOption(label + " (" + "NoPath".Translate().Resolve() + ")", null);
                yield break;
            }

            Thing item = parent;
            yield return new FloatMenuOption(label, () =>
            {
                item.SetForbidden(false, false);
                Job job = JobMaker.MakeJob(JobDefOf.TakeInventory, item);
                job.count = 1;
                selPawn.jobs.TryTakeOrderedJob(job);
                if (repairNow)
                    SuitRepair.Request(selPawn);
            });
        }
    }
}
