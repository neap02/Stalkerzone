using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Запускается один раз после загрузки всех Defs, но только если DLL загрузилась.
    /// Без DLL мод работает в XML-режиме: аномалии — разовые мины, артефакт выпадает при уничтожении.
    /// С DLL: вечные аномалии без взрывов, свои повадки, скопления, детекторы, фазы Выброса.
    /// </summary>
    [StaticConstructorOnStartup]
    public static class SZ_Startup
    {
        static SZ_Startup()
        {
            SZ_DefOf.SZ_Emission.conditionClass = typeof(GameCondition_Emission);
            ZoneDefs.Init();
            AnomalyField.Init();
            Detectors.Init();
            Log.Message("[StalkerZone] C#-часть загружена: " + ZoneDefs.AllAnomalies.Count + " вариантов аномалий, "
                + AnomalyField.VariantCount + " в генерации, комет: " + ZoneDefs.Comets.Count
                + ", пси-поле: " + (ZoneDefs.PsiField != null) + ", радиоактивное пятно: " + (ZoneDefs.RadiationSpot != null)
                + ", знак: " + (ZoneDefs.RadiationSign != null) + ".");
        }
    }
}
