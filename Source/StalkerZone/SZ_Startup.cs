using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Запускается один раз после загрузки всех Defs, но только если DLL загрузилась.
    /// В XML у Выброса стоит ванильный GameCondition_ForceWeather, чтобы мод работал
    /// и там, где C# недоступен. Здесь подменяем класс и готовим списки аномалий.
    /// </summary>
    [StaticConstructorOnStartup]
    public static class SZ_Startup
    {
        static SZ_Startup()
        {
            SZ_DefOf.SZ_Emission.conditionClass = typeof(GameCondition_Emission);
            ZoneDefs.Init();
            AnomalyField.Init();
            Log.Message("[StalkerZone] C#-часть загружена: " + ZoneDefs.AllAnomalies.Count + " аномалий ("
                + ZoneDefs.Vortices.Count + " воронок, " + ZoneDefs.Springboards.Count + " трамплинов, "
                + ZoneDefs.Comets.Count + " комет), пси-поле: " + (ZoneDefs.PsiField != null)
                + ", радиоактивное пятно: " + (ZoneDefs.RadiationSpot != null) + ".");
        }
    }
}
