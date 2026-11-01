using System.Collections.Generic;
using System.Reflection;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>Отношение двух фракций (в обе стороны).</summary>
    public class ZoneFactionRelation
    {
        public FactionDef a;
        public FactionDef b;
        public FactionRelationKind kind = FactionRelationKind.Neutral;   // Hostile / Neutral / Ally
        public int goodwill;                                            // -100..100, для подсказок
    }

    /// <summary>Стартовое отношение фракции к игроку.</summary>
    public class ZonePlayerGoodwill
    {
        public FactionDef faction;
        public int goodwill;
    }

    /// <summary>Таблица отношений фракций Зоны (SZ_FactionRelations.xml).</summary>
    public class FactionRelationsDef : Def
    {
        public List<ZoneFactionRelation> relations = new List<ZoneFactionRelation>();
        public List<ZonePlayerGoodwill> playerGoodwill = new List<ZonePlayerGoodwill>();
    }

    /// <summary>
    /// Один раз на игру выставляет отношения между фракциями Зоны и их стартовое
    /// отношение к игроку. Дальше отношения живут своей жизнью (события, квесты).
    /// Игра сама добавляет этот компонент к каждой игре.
    /// </summary>
    public class GameComponent_ZoneFactions : GameComponent
    {
        private bool relationsApplied;

        // Имя поля доброжелательности менялось между версиями — ищем осторожно
        private static readonly FieldInfo goodwillField =
            typeof(FactionRelation).GetField("baseGoodwill", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)
            ?? typeof(FactionRelation).GetField("goodwill", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);

        public GameComponent_ZoneFactions(Game game)
        {
        }

        public override void FinalizeInit()
        {
            base.FinalizeInit();
            if (relationsApplied || Find.FactionManager == null)
                return;
            int pairs = ApplyRelations();
            if (pairs > 0)
            {
                ApplyPlayerGoodwill();
                relationsApplied = true;
                Log.Message("[StalkerZone] Отношения фракций Зоны выставлены: пар " + pairs + ".");
            }
        }

        private static int ApplyRelations()
        {
            int count = 0;
            foreach (FactionRelationsDef def in DefDatabase<FactionRelationsDef>.AllDefsListForReading)
            {
                foreach (ZoneFactionRelation r in def.relations)
                {
                    if (r.a == null || r.b == null)
                        continue;
                    Faction fa = Find.FactionManager.FirstFactionOfDef(r.a);
                    Faction fb = Find.FactionManager.FirstFactionOfDef(r.b);
                    if (fa == null || fb == null || fa == fb)
                        continue;
                    Set(fa, fb, r);
                    Set(fb, fa, r);
                    count++;
                }
            }
            return count;
        }

        private static void Set(Faction from, Faction to, ZoneFactionRelation r)
        {
            FactionRelation rel = from.RelationWith(to, true);
            if (rel == null)
                return;
            rel.kind = r.kind;
            if (goodwillField != null && goodwillField.FieldType == typeof(int))
                goodwillField.SetValue(rel, r.goodwill);
        }

        private static void ApplyPlayerGoodwill()
        {
            Faction player = Faction.OfPlayer;
            foreach (FactionRelationsDef def in DefDatabase<FactionRelationsDef>.AllDefsListForReading)
            {
                foreach (ZonePlayerGoodwill g in def.playerGoodwill)
                {
                    Faction f = g.faction != null ? Find.FactionManager.FirstFactionOfDef(g.faction) : null;
                    if (f == null || f.def.permanentEnemy)
                        continue;
                    int delta = g.goodwill - f.PlayerGoodwill;
                    if (delta != 0)
                        f.TryAffectGoodwillWith(player, delta, false, false);
                }
            }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref relationsApplied, "szRelationsApplied", false);
        }
    }
}
