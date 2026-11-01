using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Классы детекторов. Детектор — одежда на поясе (SZ_Detectors.xml).
    /// level: какие артефакты видит (1 — обычные, 2 — + необычные, 3 — все).
    /// anomalyRange: в каком радиусе пищит и подсвечивает аномалии.
    /// revealRange: с какого расстояния находит артефакт (артефакт появляется на земле).
    /// markRange: в каком радиусе показывает метку, где лежит ещё не найденный артефакт.
    /// </summary>
    public class DetectorTier
    {
        public int level;
        public float anomalyRange;
        public float revealRange;
        public float markRange;
    }

    public static class Detectors
    {
        private static readonly Dictionary<ThingDef, DetectorTier> tiers = new Dictionary<ThingDef, DetectorTier>();

        public static void Init()
        {
            tiers.Clear();
            Add("SZ_Detector_Basic", new DetectorTier { level = 1, anomalyRange = 10f, revealRange = 4f, markRange = 0f });
            Add("SZ_Detector_Advanced", new DetectorTier { level = 2, anomalyRange = 14f, revealRange = 7f, markRange = 14f });
            Add("SZ_Detector_Scanner", new DetectorTier { level = 3, anomalyRange = 18f, revealRange = 10f, markRange = 30f });
        }

        private static void Add(string defName, DetectorTier tier)
        {
            ThingDef def = DefDatabase<ThingDef>.GetNamedSilentFail(defName);
            if (def != null)
                tiers[def] = tier;
        }

        /// <summary>Лучший детектор, надетый на пешку, или null.</summary>
        public static DetectorTier BestOf(Pawn pawn)
        {
            if (pawn.apparel == null)
                return null;
            DetectorTier best = null;
            foreach (Apparel apparel in pawn.apparel.WornApparel)
            {
                if (tiers.TryGetValue(apparel.def, out DetectorTier t) && (best == null || t.level > best.level))
                    best = t;
            }
            return best;
        }
    }
}
