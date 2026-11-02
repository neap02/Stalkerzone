using RimWorld;
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
            FixLayerOrder();
            FactionSetup.RemoveVanillaFactionsFromNewWorlds();
            Log.Message("[StalkerZone] Загружено: типов аномалий " + ZoneDefs.Anomalies.Count
                + ", типов пятен " + ZoneDefs.Fields.Count + ", зона обхода: " + (ZoneDefs.DangerMarker != null) + ".");
        }
    
        /// <summary>
        /// Слои мода рисуются над бронёй: каркас экзоскелета — сразу над верхним слоем (Shell),
        /// рюкзак/баллоны — ещё выше. Числа берём у ванильных слоёв, какими бы они ни были в этой версии.
        /// </summary>
        private static void FixLayerOrder()
        {
            ApparelLayerDef shell = ApparelLayerDefOf.Shell;
            ApparelLayerDef exo = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_ExoLayer");
            ApparelLayerDef back = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_BackLayer");
            if (shell == null)
                return;
            int baseOrder = shell.drawOrder;
            int beltOrder = ApparelLayerDefOf.Belt != null ? ApparelLayerDefOf.Belt.drawOrder : baseOrder + 2;
            if (exo != null) exo.drawOrder = baseOrder + 1;
            if (back != null) back.drawOrder = System.Math.Max(beltOrder, baseOrder + 2);
            Log.Message("[StalkerZone] Порядок слоёв: броня " + baseOrder + ", экзоскелет " + (exo?.drawOrder ?? -1) + ", спина " + (back?.drawOrder ?? -1) + ".");
        }
    }
}
