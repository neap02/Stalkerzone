using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Артефакт, который лежит в поле аномалий, но ещё не найден.
    /// На карте его нет, пока к нему не подойдёт колонист с подходящим детектором.
    /// </summary>
    public class LatentArtifact : IExposable
    {
        public IntVec3 cell;
        public ThingDef def;
        public int tier = 1;   // 1 — обычный, 2 — необычный, 3 — редкий

        public void ExposeData()
        {
            Scribe_Values.Look(ref cell, "cell");
            Scribe_Defs.Look(ref def, "def");
            Scribe_Values.Look(ref tier, "tier", 1);
        }
    }
}
