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
            ApparelLayerDef vest = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_ModularVestLayer");
            ApparelLayerDef exo = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_ExoLayer");
            ApparelLayerDef back = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_BackLayer");
            if (shell == null)
            {
                Log.Warning("[StalkerZone] Cannot set gear layers: Shell layer is missing.");
                return;
            }

            // Use an explicit ascending order; do not rely on Belt or on XML defaults.
            // These values control layer sorting, not the actual rear texture contents.
            int order = shell.drawOrder;
            if (vest != null) vest.drawOrder = ++order;
            if (exo != null) exo.drawOrder = ++order;
            if (back != null) back.drawOrder = ++order;

            Log.Message("[StalkerZone] Apparel layer order: Shell=" + shell.drawOrder
                + ", Vest=" + (vest != null ? vest.drawOrder.ToString() : "missing")
                + ", Exo=" + (exo != null ? exo.drawOrder.ToString() : "missing")
                + ", Pack=" + (back != null ? back.drawOrder.ToString() : "missing"));

            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                if (def == null || def.apparel == null || def.defName == null
                    || !def.defName.StartsWith("SZ_Pack_"))
                    continue;
                bool hasBack = def.apparel.layers != null && back != null
                    && def.apparel.layers.Contains(back);
                if (!hasBack)
                    Log.Warning("[StalkerZone] Backpack " + def.defName
                        + " does not use SZ_BackLayer; inspect its inherited apparel XML.");
            }
        }

    }
}
