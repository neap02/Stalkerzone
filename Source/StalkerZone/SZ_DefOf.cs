using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Прямые ссылки на наши Defs из XML.
    /// Игра сама заполняет поля по совпадению имени поля и defName.
    /// </summary>
    [DefOf]
    public static class SZ_DefOf
    {
        public static HediffDef SZ_Radiation;
        public static StatDef SZ_RadiationResistance;

        static SZ_DefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(SZ_DefOf));
        }
    }
}
