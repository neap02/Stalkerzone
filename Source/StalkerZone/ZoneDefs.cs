using System.Collections.Generic;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Списки наших Defs. Тип аномалии берётся из defName (SZ_Anomaly_[Тип]_[Артефакт]),
    /// поэтому новые варианты из генератора подхватываются без правки кода.
    /// </summary>
    public static class ZoneDefs
    {
        public const string AnomalyPrefix = "SZ_Anomaly_";

        public static readonly List<ThingDef> AllAnomalies = new List<ThingDef>();
        public static readonly List<ThingDef> Comets = new List<ThingDef>();
        private static readonly Dictionary<ThingDef, string> typeOf = new Dictionary<ThingDef, string>();
        private static readonly Dictionary<ThingDef, ThingDef> artifactOf = new Dictionary<ThingDef, ThingDef>();

        public static ThingDef PsiField;
        public static ThingDef RadiationSpot;
        public static ThingDef PuddleFilth;
        public static ThingDef RadiationSign;

        public static void Init()
        {
            AllAnomalies.Clear(); Comets.Clear(); typeOf.Clear(); artifactOf.Clear();
            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                if (!def.defName.StartsWith(AnomalyPrefix))
                    continue;
                AllAnomalies.Add(def);
                string[] parts = def.defName.Split('_');
                string type = parts.Length > 2 ? parts[2] : "";
                typeOf[def] = type;
                if (type == "Comet")
                    Comets.Add(def);
                if (def.killedLeavings != null && def.killedLeavings.Count > 0)
                    artifactOf[def] = def.killedLeavings[0].thingDef;

                // С C# аномалии вечные: их нельзя разрушить или разобрать,
                // а срабатывание полностью ведёт MapComponent_Zone (не ванильная мина).
                def.useHitPoints = false;
                def.thingClass = typeof(Building);
                if (def.building != null)
                    def.building.isTrap = false;
            }
            PsiField = DefDatabase<ThingDef>.GetNamedSilentFail("SZ_Field_Psi");
            RadiationSpot = DefDatabase<ThingDef>.GetNamedSilentFail("SZ_Field_Radiation");
            RadiationSign = DefDatabase<ThingDef>.GetNamedSilentFail("SZ_RadiationSign");
            PuddleFilth = DefDatabase<ThingDef>.GetNamedSilentFail("Filth_Slime")
                          ?? DefDatabase<ThingDef>.GetNamedSilentFail("Filth_Vomit");
        }

        public static bool IsAnomaly(ThingDef def)
        {
            return def != null && def.defName.StartsWith(AnomalyPrefix);
        }

        public static string TypeOf(ThingDef def)
        {
            return def != null && typeOf.TryGetValue(def, out string t) ? t : null;
        }

        public static ThingDef ArtifactOf(ThingDef def)
        {
            return def != null && artifactOf.TryGetValue(def, out ThingDef a) ? a : null;
        }

        public static AnomalyProfile ProfileOf(ThingDef def)
        {
            return AnomalyProfile.For(TypeOf(def));
        }
    }
}
