using System.Collections.Generic;
using System.Reflection;
using RimWorld;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Настройка фракций нового мира: по умолчанию в нём только фракции Зоны.
    /// Ванильные фракции людей (поселенцы, племена, пираты, Империя и фракции DLC)
    /// не удаляются из игры: им просто ставится "0 в новом мире". Вернуть любую можно
    /// вручную в списке фракций на экране создания мира.
    /// Служебные фракции (механоиды, насекомые, древние, сущности и т.п.) не трогаем:
    /// на них завязаны события и квесты.
    /// Уже созданные миры и сохранения не меняются.
    /// </summary>
    public static class FactionSetup
    {
        public static void RemoveVanillaFactionsFromNewWorlds()
        {
            // Поле списка фракций при создании мира ищем осторожно (через отражение),
            // чтобы сборка не зависела от его точного имени в конкретной версии игры.
            FieldInfo startingCount = typeof(FactionDef).GetField("startingCountAtWorldCreation",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);

            var removed = new List<string>();
            foreach (FactionDef def in DefDatabase<FactionDef>.AllDefsListForReading)
            {
                if (def.isPlayer || def.hidden || !def.humanlikeFaction || def.defName.StartsWith("SZ_"))
                    continue;
                def.requiredCountAtGameStart = 0;
                if (startingCount != null && startingCount.FieldType == typeof(int))
                    startingCount.SetValue(def, 0);
                removed.Add(def.defName);
            }

            if (removed.Count > 0)
                Log.Message("[StalkerZone] В новом мире по умолчанию только фракции Зоны. Убраны: "
                    + string.Join(", ", removed) + ". Вернуть можно на экране создания мира.");
            if (startingCount == null)
                Log.Warning("[StalkerZone] Не найдено поле списка фракций при создании мира: ванильные фракции могут остаться в списке, удалите их вручную.");
        }
    }
}
