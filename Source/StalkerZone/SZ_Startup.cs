using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Запускается один раз после загрузки всех Defs, но только если DLL загрузилась.
    /// Без DLL мод работает в XML-режиме: разовые аномалии, артефакт выпадает при уничтожении.
    /// С DLL: вечные аномалии со своими повадками, скопления, артефакты внутри, фазы Выброса.
    /// </summary>
    [StaticConstructorOnStartup]
    public static class SZ_Startup
    {
        static SZ_Startup()
        {
            SZ_DefOf.SZ_Emission.conditionClass = typeof(GameCondition_Emission);
            ZoneDefs.Init();
            AnomalyField.Init();
            Log.Message("[StalkerZone] C#-часть загружена: " + ZoneDefs.AllAnomalies.Count + " вариантов аномалий, "
                + AnomalyField.VariantCount + " в генерации, комет: " + ZoneDefs.Comets.Count
                + ", пси-поле: " + (ZoneDefs.PsiField != null) + ", радиоактивное пятно: " + (ZoneDefs.RadiationSpot != null) + ".");
        }
    }
}
