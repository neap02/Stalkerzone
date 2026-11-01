using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.Sound;

namespace StalkerZone
{
    /// <summary>
    /// Мрачная палитра Зоны: при старте небо и тени всех погод становятся темнее,
    /// холоднее и менее насыщенными. Погоды мода (SZ_*) не трогаем — у них своя палитра.
    /// </summary>
    public static class ZoneAtmosphere
    {
        private const float Darken = 0.84f;          // общее затемнение
        private const float GrayMix = 0.35f;         // доля серого (обесцвечивание)
        private const float TintMix = 0.15f;         // доля холодного оттенка
        private const float SaturationFactor = 0.7f;
        private static readonly Color Tint = new Color(0.55f, 0.60f, 0.63f);

        public static void Apply()
        {
            int n = 0;
            foreach (WeatherDef w in DefDatabase<WeatherDef>.AllDefsListForReading)
            {
                if (w.defName.StartsWith("SZ_"))
                    continue;
                w.skyColorsDay = Gloom(w.skyColorsDay);
                w.skyColorsDusk = Gloom(w.skyColorsDusk);
                w.skyColorsNightEdge = Gloom(w.skyColorsNightEdge);
                w.skyColorsNightMid = Gloom(w.skyColorsNightMid);
                n++;
            }
            Log.Message("[StalkerZone] Палитра Зоны применена к погодам: " + n + ".");
            AddZoneWeathers();
        }

        /// <summary>
        /// Погоды Зоны во всех биомах с погодой. Делается кодом, а не XML-патчем:
        /// список погод биома ищется по типу поля, а не по имени узла в XML.
        /// </summary>
        private static void AddZoneWeathers()
        {
            var weights = new Dictionary<string, float>
            {
                { "SZ_Weather_Overcast", 8f },
                { "SZ_Weather_Drizzle", 4f },
                { "SZ_Weather_ZoneFog", 3f },
            };
            const BindingFlags all = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
            FieldInfo field = typeof(BiomeDef).GetFields(all).FirstOrDefault(f => f.FieldType == typeof(List<WeatherCommonalityRecord>));
            if (field == null)
            {
                Log.Warning("[StalkerZone] Не найден список погод биома: погоды Зоны не добавлены.");
                return;
            }
            int biomes = 0;
            foreach (BiomeDef b in DefDatabase<BiomeDef>.AllDefsListForReading)
            {
                var list = field.GetValue(b) as List<WeatherCommonalityRecord>;
                if (list == null || list.Count == 0)
                    continue;                      // биомы без погоды (космос и т.п.) не трогаем
                foreach (KeyValuePair<string, float> kv in weights)
                {
                    WeatherDef w = DefDatabase<WeatherDef>.GetNamedSilentFail(kv.Key);
                    if (w == null || list.Any(r => r.weather == w))
                        continue;
                    list.Add(new WeatherCommonalityRecord { weather = w, commonality = kv.Value });
                }
                // сбросить кеш вероятностей погоды, если игра его уже построила
                foreach (FieldInfo f in typeof(BiomeDef).GetFields(all))
                {
                    if (f.Name.IndexOf("cached", System.StringComparison.OrdinalIgnoreCase) >= 0
                        && f.Name.IndexOf("weather", System.StringComparison.OrdinalIgnoreCase) >= 0
                        && !f.FieldType.IsValueType)
                        f.SetValue(b, null);
                }
                biomes++;
            }
            Log.Message("[StalkerZone] Погоды Зоны добавлены в биомы: " + biomes + ".");
        }

        private static SkyColorSet Gloom(SkyColorSet s)
        {
            s.sky = Mix(s.sky);
            s.shadow = Mix(s.shadow);
            s.overlay = Mix(s.overlay);
            s.saturation *= SaturationFactor;
            return s;
        }

        private static Color Mix(Color c)
        {
            float g = c.grayscale;
            Color d = Color.Lerp(c, new Color(g, g, g, c.a), GrayMix);
            d = Color.Lerp(d, Tint, TintMix) * Darken;
            d.a = c.a;
            return d;
        }
    }

    /// <summary>
    /// Звуки Зоны и эфир. Время от времени на карте колонии слышны ветер, гул,
    /// далёкие выстрелы и вой (ночью чаще), а по рации приходят сообщения сталкеров.
    /// </summary>
    public static class ZoneAmbience
    {
        private const int RadioLines = 12;
        private static readonly Dictionary<int, int> nextSound = new Dictionary<int, int>();
        private static readonly Dictionary<int, int> nextRadio = new Dictionary<int, int>();

        public static void Tick(Map map, int tick)
        {
            if (map == null || !map.IsPlayerHome)
                return;
            int id = map.uniqueID;
            if (!nextSound.TryGetValue(id, out int ns))
                nextSound[id] = ns = tick + Rand.Range(1200, 3000);
            if (!nextRadio.TryGetValue(id, out int nr))
                nextRadio[id] = nr = tick + Rand.Range(15000, 40000);

            if (tick >= ns)
            {
                nextSound[id] = tick + Rand.Range(2500, 6000);
                if (Find.CurrentMap == map)
                    PlayAmbient(map);
            }
            if (tick >= nr)
            {
                nextRadio[id] = tick + Rand.Range(24000, 60000);
                int line = Rand.Range(0, RadioLines);
                Messages.Message("SZ_RadioPrefix".Translate().Resolve() + ": " + ("SZ_Radio_" + line).Translate().Resolve(),
                    MessageTypeDefOf.NeutralEvent, false);
            }
        }

        private static void PlayAmbient(Map map)
        {
            int hour = GenLocalDate.HourOfDay(map);
            bool night = hour < 5 || hour >= 21;
            var options = new List<KeyValuePair<string, float>>
            {
                new KeyValuePair<string, float>("SZ_Ambient_Wind", 3f),
                new KeyValuePair<string, float>("SZ_Ambient_Drone", 1f),
                new KeyValuePair<string, float>("SZ_Ambient_Shots", night ? 0.5f : 1.2f),
                new KeyValuePair<string, float>("SZ_Ambient_Howl", night ? 3f : 0.4f),
            };
            string pick = options.RandomElementByWeight(o => o.Value).Key;
            DefDatabase<SoundDef>.GetNamedSilentFail(pick)?.PlayOneShotOnCamera(map);
        }
    }
}
