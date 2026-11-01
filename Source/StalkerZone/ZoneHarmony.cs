using System;
using System.Runtime.CompilerServices;
using System.Text;
using HarmonyLib;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Единственный патч мода: стат SZ_InventoryCapacity (кг) от снаряжения добавляется
    /// к грузоподъёмности пешки, которую игра использует для инвентаря и караванов.
    /// Если Harmony недоступен, мод работает дальше, просто без этого бонуса.
    /// </summary>
    public static class ZoneHarmony
    {
        public static bool Active { get; private set; }

        public static void TryPatch()
        {
            try
            {
                DoPatch();
                Active = true;
                Log.Message("[StalkerZone] Harmony: грузоподъёмность снаряжения учитывается в инвентаре и караванах.");
            }
            catch (Exception e)
            {
                Log.Warning("[StalkerZone] Harmony недоступен, грузоподъёмность снаряжения не учитывается: " + e.Message);
            }
        }

        [MethodImpl(MethodImplOptions.NoInlining)]
        private static void DoPatch()
        {
            var harmony = new Harmony("stalkerzone.core");
            var original = AccessTools.Method(typeof(MassUtility), nameof(MassUtility.Capacity), new[] { typeof(Pawn), typeof(StringBuilder) });
            if (original == null)
                throw new Exception("MassUtility.Capacity(Pawn, StringBuilder) не найден");
            harmony.Patch(original, postfix: new HarmonyMethod(typeof(ZoneHarmony), nameof(CapacityPostfix)));
        }

        public static void CapacityPostfix(Pawn __0, StringBuilder __1, ref float __result)
        {
            if (__0 == null || __result <= 0f)
                return;
            float bonus = __0.GetStatValue(SZ_DefOf.SZ_InventoryCapacity);
            if (bonus == 0f)
                return;
            __result = Math.Max(0f, __result + bonus);
            __1?.AppendLine("  " + "SZ_GearCapacity".Translate() + ": " + bonus.ToString("+0;-0") + " kg");
        }
    }
}
