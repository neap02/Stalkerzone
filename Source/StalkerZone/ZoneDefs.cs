using System.Collections.Generic;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Списки наших аномалий по типам. Тип определяется по префиксу defName
    /// (SZ_Anomaly_Vortex_..., SZ_Anomaly_Springboard_... и т.д.), поэтому
    /// новые варианты из генератора подхватываются без правки кода.
    /// </summary>
    public static class ZoneDefs
    {
        public const string AnomalyPrefix = "SZ_Anomaly_";

        public static readonly List<ThingDef> AllAnomalies = new List<ThingDef>();
        public static readonly List<ThingDef> Vortices = new List<ThingDef>();
        public static readonly List<ThingDef> Springboards = new List<ThingDef>();
        public static readonly List<ThingDef> Comets = new List<ThingDef>();

        public static ThingDef PsiField;
        public static ThingDef RadiationSpot;

        public static void Init()
        {
            AllAnomalies.Clear(); Vortices.Clear(); Springboards.Clear(); Comets.Clear();
            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                string name = def.defName;
                if (!name.StartsWith(AnomalyPrefix))
                    continue;
                AllAnomalies.Add(def);
                if (name.StartsWith("SZ_Anomaly_Vortex_")) Vortices.Add(def);
                else if (name.StartsWith("SZ_Anomaly_Springboard_")) Springboards.Add(def);
                else if (name.StartsWith("SZ_Anomaly_Comet_")) Comets.Add(def);
            }
            PsiField = DefDatabase<ThingDef>.GetNamedSilentFail("SZ_Field_Psi");
            RadiationSpot = DefDatabase<ThingDef>.GetNamedSilentFail("SZ_Field_Radiation");
        }

        public static bool IsAnomaly(ThingDef def)
        {
            return def != null && def.defName.StartsWith(AnomalyPrefix);
        }
    }
}
