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
            ApparelLayerDef belt = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("Belt");
            ApparelLayerDef vest = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_ModularVestLayer");
            ApparelLayerDef exo = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_ExoLayer");
            ApparelLayerDef back = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_BackLayer");
            if (shell == null || back == null)
            {
                Log.Warning("[StalkerZone] Cannot initialize backpack layers: Shell or SZ_BackLayer missing.");
                return;
            }

            // RH2 Gruppa Krovi (1.6) uses a utility-as-pack worn graphic and
            // a backpack layer with drawOrder 500. Keep a distinct StalkerZone
            // layer so our backpacks do not change the vanilla Belt globally.
            // Draw order is only one part of RimWorld's apparel rendering.
            int shellOrder = shell.drawOrder;
            if (vest != null) vest.drawOrder = shellOrder + 1;
            if (exo != null) exo.drawOrder = shellOrder + 2;
            int minimumPackOrder = shellOrder + 3;
            if (belt != null && belt.drawOrder >= minimumPackOrder)
                minimumPackOrder = belt.drawOrder + 1;
            back.drawOrder = System.Math.Max(500, minimumPackOrder);

            Log.Message("[StalkerZone] V61 layers: Shell=" + shell.drawOrder
                + ", Belt=" + (belt != null ? belt.drawOrder.ToString() : "missing")
                + ", Vest=" + (vest != null ? vest.drawOrder.ToString() : "missing")
                + ", Exo=" + (exo != null ? exo.drawOrder.ToString() : "missing")
                + ", Backpack=" + back.drawOrder);

            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                if (def == null || def.apparel == null || def.defName == null
                    || !def.defName.StartsWith("SZ_Pack_"))
                    continue;
                if (def.apparel.layers == null || !def.apparel.layers.Contains(back))
                    Log.Warning("[StalkerZone] " + def.defName + " does not use SZ_BackLayer.");
            }
        }

    }
}
