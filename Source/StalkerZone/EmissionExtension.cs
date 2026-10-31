using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Настройки Выброса. Задаются в XML через modExtensions у GameConditionDef,
    /// поэтому баланс правится без перекомпиляции.
    /// Значения ниже используются, если поле в XML не указано.
    /// </summary>
    public class EmissionExtension : DefModExtension
    {
        /// <summary>Прирост тяжести SZ_Radiation за игровой час под открытым небом (1 час = 2500 тиков).</summary>
        public float radiationPerHour = 0.2f;

        /// <summary>Как часто проверять пешек, в тиках. 250 тиков ≈ 4 сек. на скорости x1.</summary>
        public int checkIntervalTicks = 250;

        /// <summary>Облучать ли животных.</summary>
        public bool affectAnimals = true;
    }
}
