using Verse;

namespace StalkerZone
{
    /// <summary>Одна аномалия на карте: тип и клетка. Не вещь, а запись в MapComponent_Zone.</summary>
    public class AnomalyInstance : IExposable
    {
        public int id;
        public AnomalyDef def;
        public IntVec3 pos;
        public IntVec3 origin;     // центр маршрута (комета)
        public int step;           // шаг по маршруту
        public int readyTick;      // не сохраняется: после загрузки аномалия сразу заряжена

        public void ExposeData()
        {
            Scribe_Values.Look(ref id, "id");
            Scribe_Defs.Look(ref def, "def");
            Scribe_Values.Look(ref pos, "pos");
            Scribe_Values.Look(ref origin, "origin");
            Scribe_Values.Look(ref step, "step");
        }
    }
}
