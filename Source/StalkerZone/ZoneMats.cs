using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Verse;

namespace StalkerZone
{
    /// <summary>
    /// Всё, что Зона рисует сама: аномалии, пятна, знаки, метки детектора, подсказки.
    /// Материалы создаются один раз при старте (в главном потоке).
    /// </summary>
    [StaticConstructorOnStartup]
    public static class ZoneMats
    {
        public static readonly Material AnomalyMarker = MaterialPool.MatFrom("SZ_Fx/AnomalyMarker", ShaderDatabase.MetaOverlay);
        public static readonly Material ArtifactMarker = MaterialPool.MatFrom("SZ_Fx/ArtifactMarker", ShaderDatabase.MetaOverlay);

        private static readonly Dictionary<string, Material[]> frames = new Dictionary<string, Material[]>();
        private static readonly Dictionary<Def, Material> glows = new Dictionary<Def, Material>();
        private static readonly Dictionary<string, Material> singles = new Dictionary<string, Material>();

        static ZoneMats()
        {
            foreach (AnomalyDef def in DefDatabase<AnomalyDef>.AllDefsListForReading)
            {
                LoadFrames(def.texPath, def.defName);
                glows[def] = MaterialPool.MatFrom("SZ_Fx/Glow", ShaderDatabase.MoteGlow, def.glowColor);
            }
            foreach (ZoneFieldDef def in DefDatabase<ZoneFieldDef>.AllDefsListForReading)
            {
                LoadFrames(def.texPath, def.defName);
                if (!def.signTexPath.NullOrEmpty())
                    singles[def.signTexPath] = MaterialPool.MatFrom(def.signTexPath, ShaderDatabase.Cutout);
            }
        }

        private static void LoadFrames(string texPath, string owner)
        {
            if (texPath.NullOrEmpty() || frames.ContainsKey(texPath))
                return;
            var list = new List<Material>();
            foreach (Texture2D tex in ContentFinder<Texture2D>.GetAllInFolder(texPath).OrderBy(t => t.name))
                list.Add(MaterialPool.MatFrom(new MaterialRequest(tex, ShaderDatabase.Transparent)));
            if (list.Count == 0)
                Log.Warning("[StalkerZone] Нет кадров анимации для " + owner + " в " + texPath);
            frames[texPath] = list.ToArray();
        }

        /// <summary>Аномалия: свечение под ней и кадр анимации (по порядку, и на паузе тоже).</summary>
        public static void DrawAnomaly(AnomalyDef def, IntVec3 cell, int seed)
        {
            Vector3 pos = cell.ToVector3Shifted();
            if (glows.TryGetValue(def, out Material glow))
                DrawPlane(glow, pos, def.glowSize, AltitudeLayer.FloorEmplacement);
            DrawAnimated(def.texPath, pos, def.drawSize, def.fps, seed, AltitudeLayer.Building);
        }

        /// <summary>Пятно: анимированная заливка на земле и знаки по краю.</summary>
        public static void DrawField(ZoneFieldInstance field)
        {
            ZoneFieldDef def = field.def;
            DrawAnimated(def.texPath, field.pos.ToVector3Shifted(), def.drawSize, def.fps, field.id, AltitudeLayer.FloorEmplacement);
            if (!def.signTexPath.NullOrEmpty() && singles.TryGetValue(def.signTexPath, out Material sign))
            {
                foreach (IntVec3 c in field.signs)
                    DrawPlane(sign, c.ToVector3Shifted(), 1f, AltitudeLayer.Building);
            }
        }

        private static void DrawAnimated(string texPath, Vector3 pos, float size, float fps, int seed, AltitudeLayer layer)
        {
            if (texPath == null || !frames.TryGetValue(texPath, out Material[] f) || f.Length == 0)
                return;
            int i = (int)(Time.realtimeSinceStartup * fps + seed) % f.Length;
            DrawPlane(f[i], pos, size, layer);
        }

        public static void DrawMarker(Material mat, Vector3 pos, float size)
        {
            DrawPlane(mat, pos, size, AltitudeLayer.MetaOverlays);
        }

        private static void DrawPlane(Material mat, Vector3 pos, float size, AltitudeLayer layer)
        {
            pos.y = layer.AltitudeFor();
            Matrix4x4 matrix = Matrix4x4.TRS(pos, Quaternion.identity, new Vector3(size, 1f, size));
            Graphics.DrawMesh(MeshPool.plane10, matrix, mat, 0);
        }

        public static float Pulse(float speed)
        {
            return 0.5f + 0.5f * Mathf.Sin(Time.realtimeSinceStartup * speed);
        }

        /// <summary>Подсказка рядом с курсором.</summary>
        public static void DrawHoverTip(string text)
        {
            if (Event.current.type != EventType.Repaint)
                return;
            Text.Font = GameFont.Small;
            const float width = 300f;
            float height = Text.CalcHeight(text, width - 16f) + 16f;
            Vector2 m = Event.current.mousePosition;
            Rect rect = new Rect(m.x + 20f, m.y + 20f, width, height);
            if (rect.xMax > UI.screenWidth) rect.x = m.x - width - 20f;
            if (rect.yMax > UI.screenHeight) rect.y = m.y - height - 20f;
            Widgets.DrawWindowBackground(rect);
            Widgets.Label(rect.ContractedBy(8f), text);
        }
    }
}
