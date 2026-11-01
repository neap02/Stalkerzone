using Verse;

namespace StalkerZone
{
    /// <summary>Запускается один раз после загрузки всех Defs.</summary>
    [StaticConstructorOnStartup]
    public static class SZ_Startup
    {
        static SZ_Startup()
        {
            SZ_DefOf.SZ_Emission.conditionClass = typeof(GameCondition_Emission);
            ZoneDefs.Init();
            AnomalyField.Init();
            Detectors.Init();
            ZoneArtifacts.Init();
            SuitBonuses.Init();
            ZoneHarmony.TryPatch();
            ZoneAtmosphere.Apply();
            FactionSetup.RemoveVanillaFactionsFromNewWorlds();
            Log.Message("[StalkerZone] Загружено: типов аномалий " + ZoneDefs.Anomalies.Count
                + ", типов пятен " + ZoneDefs.Fields.Count + ", зона обхода: " + (ZoneDefs.DangerMarker != null) + ".");
        }
    }
}
