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
            ApparelLayerDef legacyBack = DefDatabase<ApparelLayerDef>.GetNamedSilentFail("SZ_BackLayer");
            BodyPartGroupDef shoulders = DefDatabase<BodyPartGroupDef>.GetNamedSilentFail("Shoulders");

            if (shell == null || belt == null || shoulders == null)
            {
                Log.Error("[StalkerZone] V62: Missing Shell, Belt or Shoulders definition; backpack render routing cannot be verified.");
                return;
            }

            // V62: same pack route as the 1.6 RH2 definitions: Belt + Shoulders
            // with wornGraphicData.renderUtilityAsPack. In contrast to V61, a
            // high drawOrder on a separate custom layer is not sufficient.
            // RH2 also raises Belt to 500; doing so affects other Belt apparel.
            int shellOrder = shell.drawOrder;
            if (vest != null) vest.drawOrder = shellOrder + 1;
            if (exo != null) exo.drawOrder = shellOrder + 2;
            int requiredBeltOrder = System.Math.Max(500, shellOrder + 3);
            if (belt.drawOrder < requiredBeltOrder)
                belt.drawOrder = requiredBeltOrder;
            if (legacyBack != null)
                legacyBack.drawOrder = belt.drawOrder;

            Log.Message("[StalkerZone] V62 layers: Shell=" + shell.drawOrder
                + ", Vest=" + (vest != null ? vest.drawOrder.ToString() : "missing")
                + ", Exo=" + (exo != null ? exo.drawOrder.ToString() : "missing")
                + ", Belt=" + belt.drawOrder + ", LegacyBack="
                + (legacyBack != null ? legacyBack.drawOrder.ToString() : "missing"));

            int checkedPacks = 0;
            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                if (def == null || def.apparel == null || def.defName == null
                    || !def.defName.StartsWith("SZ_Pack_"))
                    continue;
                checkedPacks++;
                bool beltOk = def.apparel.layers != null && def.apparel.layers.Contains(belt);
                bool shouldersOk = def.apparel.bodyPartGroups != null
                    && def.apparel.bodyPartGroups.Contains(shoulders);
                if (!beltOk || !shouldersOk)
                    Log.Warning("[StalkerZone] V62: " + def.defName
                        + " is not set up for Belt/Shoulders (belt=" + beltOk
                        + ", shoulders=" + shouldersOk + ").");
            }
            Log.Message("[StalkerZone] V62: inspected " + checkedPacks
                + " backpack/tank defs; expected 10, all should use Belt and Shoulders.");
        }

    }
}
