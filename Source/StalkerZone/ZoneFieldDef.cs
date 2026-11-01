using System.Collections.Generic;
using Verse;

namespace StalkerZone
{
    public enum FieldKind { Radiation, Psi }

    /// <summary>
    /// Пятно Зоны (радиоактивное пятно, пси-поле). Как и аномалия, это НЕ вещь:
    /// записи хранит MapComponent_Zone, рисует ZoneMats, при наведении — подсказка.
    /// Знаки радиационной опасности — часть пятна, тоже просто рисуются.
    /// </summary>
    public class ZoneFieldDef : Def
    {
        public FieldKind kind = FieldKind.Radiation;
        public float radius = 4.9f;              // радиус действия
        public float dosePerHour = 0.15f;        // радиация или пси за игровой час внутри
        public string texPath;                   // папка с кадрами анимации
        public float drawSize = 10f;
        public float fps = 4f;
        public float avoidRadius = 5.4f;         // зона обхода
        public FloatRange per10k = new FloatRange(0.25f, 0.5f);
        public bool geiger;                      // детектор щёлкает дозиметром
        // знаки по краю
        public string signTexPath;               // пусто = без знаков
        public int signCount = 4;
        public float signDistance = 5.5f;
    }

    /// <summary>Одно пятно на карте: тип, центр и клетки знаков.</summary>
    public class ZoneFieldInstance : IExposable
    {
        public int id;
        public ZoneFieldDef def;
        public IntVec3 pos;
        public List<IntVec3> signs = new List<IntVec3>();

        public void ExposeData()
        {
            Scribe_Values.Look(ref id, "id");
            Scribe_Defs.Look(ref def, "def");
            Scribe_Values.Look(ref pos, "pos");
            Scribe_Collections.Look(ref signs, "signs", LookMode.Value);
            if (Scribe.mode == LoadSaveMode.PostLoadInit && signs == null)
                signs = new List<IntVec3>();
        }
    }
}
