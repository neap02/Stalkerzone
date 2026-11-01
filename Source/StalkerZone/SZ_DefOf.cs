using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Прямые ссылки на наши Defs из XML.
    /// Игра сама заполняет поля по совпадению имени поля и defName (и типа Def).
    /// </summary>
    [DefOf]
    public static class SZ_DefOf
    {
        public static HediffDef SZ_Radiation;
        public static HediffDef SZ_PsiExposure;
        public static StatDef SZ_RadiationResistance;
        public static GameConditionDef SZ_Emission;
        public static ThoughtDef SZ_ExposedToEmission;
        public static DamageDef SZ_ElectricDischarge;
        public static DamageDef SZ_ChemicalBurn;
        public static SoundDef SZ_Detector_Beep;
        public static SoundDef SZ_Detector_Artifact;
        public static SoundDef SZ_Geiger_Click;

        static SZ_DefOf()
        {
            DefOfHelper.EnsureInitializedInCtor(typeof(SZ_DefOf));
        }
    }
}
