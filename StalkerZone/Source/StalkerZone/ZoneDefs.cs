using System.Collections.Generic;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Наши описания. Аномалии и пятна — свои Def (не вещи).
    /// Вещью осталась только невидимая зона обхода: игра строит пути только по вещам и грунту.
    /// </summary>
    public static class ZoneDefs
    {
        public static ThingDef DangerMarker;
        public static ThingDef PuddleFilth;

        public static List<AnomalyDef> Anomalies => DefDatabase<AnomalyDef>.AllDefsListForReading;
        public static List<ZoneFieldDef> Fields => DefDatabase<ZoneFieldDef>.AllDefsListForReading;

        public static void Init()
        {
            DangerMarker = DefDatabase<ThingDef>.GetNamedSilentFail("SZ_AnomalyDanger");
            PuddleFilth = DefDatabase<ThingDef>.GetNamedSilentFail("Filth_Slime")
                          ?? DefDatabase<ThingDef>.GetNamedSilentFail("Filth_Vomit");
        }
    }
}
