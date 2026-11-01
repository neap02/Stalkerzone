using System;
using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Улучшение костюма (SZ_SuitUpgrades.xml). Ставится на станке рецептом SZ_Upgrade_*.
    /// armorOffsets — прибавка к броне самого костюма (любые ArmorRating_*),
    /// slots / radiation / psi — бонусы владельцу (учитываются кодом Зоны).
    /// </summary>
    public class SuitUpgradeDef : Def
    {
        public List<StatModifier> armorOffsets = new List<StatModifier>();
        public int slots;
        public float radiation;
        public float psi;
        public int maxPerSuit = 1;
    }

    /// <summary>Что делает рецепт с костюмом: ставит улучшение и/или чинит.</summary>
    public class SuitRecipeExtension : DefModExtension
    {
        public SuitUpgradeDef upgrade;
        public float repairFraction;
    }

    public class CompProperties_Suit : CompProperties
    {
        public int upgradeSlots = 2;          // сколько улучшений помещается
        public float minArmorFactor = 0.4f;   // защита при 0% прочности (при 100% — полная)

        public CompProperties_Suit()
        {
            compClass = typeof(CompSuit);
        }
    }

    /// <summary>
    /// Костюм Зоны:
    /// - износ: чем ниже прочность, тем слабее вся броня костюма (до minArmorFactor);
    /// - улучшения со станка (сохраняются в самом костюме);
    /// - ремонт ремкомплектом: из инвентаря сам (SuitRepair) или правой кнопкой по ремкомплекту.
    /// </summary>
    public class CompSuit : ThingComp
    {
        private List<SuitUpgradeDef> upgrades = new List<SuitUpgradeDef>();

        public CompProperties_Suit Props => (CompProperties_Suit)props;
        public int FreeSlots => Props.upgradeSlots - upgrades.Count;
        public int SlotBonus => upgrades.Sum(u => u.slots);
        public float RadiationBonus => upgrades.Sum(u => u.radiation);
        public float PsiBonus => upgrades.Sum(u => u.psi);

        public bool CanUpgrade(SuitUpgradeDef u)
        {
            return FreeSlots > 0 && upgrades.Count(x => x == u) < u.maxPerSuit;
        }

        public void AddUpgrade(SuitUpgradeDef u)
        {
            upgrades.Add(u);
        }

        /// <summary>Множитель брони от износа.</summary>
        public float WearFactor
        {
            get
            {
                if (!parent.def.useHitPoints || parent.MaxHitPoints <= 0)
                    return 1f;
                float hp = Math.Max(0f, Math.Min(1f, (float)parent.HitPoints / parent.MaxHitPoints));
                return Props.minArmorFactor + (1f - Props.minArmorFactor) * hp;
            }
        }

        public override float GetStatOffset(StatDef stat)
        {
            float sum = 0f;
            foreach (SuitUpgradeDef u in upgrades)
            {
                if (u.armorOffsets == null)
                    continue;
                foreach (StatModifier m in u.armorOffsets)
                {
                    if (m.stat == stat)
                        sum += m.value;
                }
            }
            return sum;
        }

        public override float GetStatFactor(StatDef stat)
        {
            return SuitBonuses.IsArmorStat(stat) ? WearFactor : 1f;
        }

        public override string TransformLabel(string label)
        {
            return upgrades.Count > 0 ? label + " +" + upgrades.Count : label;
        }

        public override string CompInspectStringExtra()
        {
            string list = upgrades.Count > 0 ? string.Join(", ", upgrades.Select(u => u.label)) : "—";
            return "SZ_SuitWear".Translate(WearFactor.ToStringPercent()).Resolve() + "\n"
                + "SZ_SuitUpgradesInspect".Translate(upgrades.Count, Props.upgradeSlots, list).Resolve();
        }

        public override void PostExposeData()
        {
            base.PostExposeData();
            Scribe_Collections.Look(ref upgrades, "szUpgrades", LookMode.Def);
            if (Scribe.mode == LoadSaveMode.PostLoadInit)
            {
                if (upgrades == null)
                    upgrades = new List<SuitUpgradeDef>();
                upgrades.RemoveAll(u => u == null);
            }
        }
    }

    /// <summary>
    /// Рецепт станка для костюма: костюм не расходуется, а получает улучшение или ремонт.
    /// Материалы расходуются как обычно.
    /// </summary>
    public class RecipeWorker_Suit : RecipeWorker
    {
        public override void ConsumeIngredient(Thing ingredient, RecipeDef recipe, Map map)
        {
            CompSuit suit = ingredient.TryGetComp<CompSuit>();
            SuitRecipeExtension ext = recipe.GetModExtension<SuitRecipeExtension>();
            if (suit == null || ext == null)
            {
                base.ConsumeIngredient(ingredient, recipe, map);
                return;
            }
            if (ext.upgrade != null)
            {
                if (suit.CanUpgrade(ext.upgrade))
                {
                    suit.AddUpgrade(ext.upgrade);
                    Messages.Message("SZ_SuitUpgraded".Translate(ingredient.LabelCap, ext.upgrade.label), ingredient, MessageTypeDefOf.PositiveEvent, false);
                }
                else
                {
                    Messages.Message("SZ_SuitNoRoom".Translate(ingredient.LabelCap, ext.upgrade.label), ingredient, MessageTypeDefOf.RejectInput, false);
                }
            }
            if (ext.repairFraction > 0f)
            {
                ingredient.HitPoints = Math.Min(ingredient.MaxHitPoints,
                    ingredient.HitPoints + (int)Math.Ceiling(ingredient.MaxHitPoints * ext.repairFraction));
                Messages.Message("SZ_SuitRepaired".Translate(ingredient.LabelCap), ingredient, MessageTypeDefOf.PositiveEvent, false);
            }
            // Костюм не уничтожается и остаётся у станка.
        }
    }

    /// <summary>Бонусы улучшений всех надетых костюмов пешки.</summary>
    public static class SuitBonuses
    {
        private static HashSet<StatDef> armorStats = new HashSet<StatDef>();

        public static void Init()
        {
            armorStats = new HashSet<StatDef>(DefDatabase<StatDef>.AllDefsListForReading
                .Where(s => s.defName.StartsWith("ArmorRating_") || s.defName.StartsWith("SZ_ArmorRating_")));
        }

        public static bool IsArmorStat(StatDef stat)
        {
            return stat != null && armorStats.Contains(stat);
        }

        public static void Of(Pawn pawn, out int slots, out float radiation, out float psi)
        {
            slots = 0; radiation = 0f; psi = 0f;
            if (pawn?.apparel == null)
                return;
            foreach (Apparel a in pawn.apparel.WornApparel)
            {
                CompSuit c = a.TryGetComp<CompSuit>();
                if (c == null)
                    continue;
                slots += c.SlotBonus;
                radiation += c.RadiationBonus;
                psi += c.PsiBonus;
            }
        }
    }

    /// <summary>
    /// Ремкомплекты. Лежат в инвентаре — используются сами, когда надетый костюм Зоны
    /// изношен ниже 70%. Правая кнопка по ремкомплекту на земле — взять и сразу починить.
    /// </summary>
    public static class SuitRepair
    {
        public const float AutoRepairBelow = 0.7f;
        public const float KitRepairFraction = 0.4f;
        private static readonly HashSet<int> requested = new HashSet<int>();

        /// <summary>Просьба починить при первой возможности, даже если износ меньше порога.</summary>
        public static void Request(Pawn pawn)
        {
            if (pawn != null) requested.Add(pawn.thingIDNumber);
        }

        public static Apparel MostWornSuit(Pawn pawn)
        {
            Apparel worst = null; float worstHp = 1f;
            if (pawn?.apparel == null) return null;
            foreach (Apparel a in pawn.apparel.WornApparel)
            {
                if (a.TryGetComp<CompSuit>() == null || a.MaxHitPoints <= 0) continue;
                float hp = (float)a.HitPoints / a.MaxHitPoints;
                if (hp < worstHp) { worstHp = hp; worst = a; }
            }
            return worst;
        }

        public static void TryAutoRepair(Pawn pawn)
        {
            if (pawn == null || pawn.Dead || pawn.inventory == null || pawn.Faction != Faction.OfPlayer)
                return;
            bool asked = requested.Contains(pawn.thingIDNumber);
            Apparel suit = MostWornSuit(pawn);
            if (suit == null) { requested.Remove(pawn.thingIDNumber); return; }
            float hp = (float)suit.HitPoints / suit.MaxHitPoints;
            if (hp >= (asked ? 0.999f : AutoRepairBelow))
                return;
            Thing kit = pawn.inventory.innerContainer.FirstOrDefault(t => t.def == SZ_DefOf.SZ_RepairKit);
            if (kit == null)
                return;
            kit.SplitOff(1).Destroy();
            suit.HitPoints = Math.Min(suit.MaxHitPoints, suit.HitPoints + (int)Math.Ceiling(suit.MaxHitPoints * KitRepairFraction));
            requested.Remove(pawn.thingIDNumber);
            if (pawn.Map != null)
                ZoneEffects.PlaySound(SZ_DefOf.SZ_Bolt_Clink, pawn.Position, pawn.Map);
            Messages.Message("SZ_SuitRepaired".Translate(suit.LabelCap), pawn, MessageTypeDefOf.PositiveEvent, false);
        }
    }
}
