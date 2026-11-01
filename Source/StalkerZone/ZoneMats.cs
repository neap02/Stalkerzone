using UnityEngine;
using Verse;

namespace StalkerZone
{
    /// <summary>Материалы для меток детектора. Создаются один раз в главном потоке при старте.</summary>
    [StaticConstructorOnStartup]
    public static class ZoneMats
    {
        public static readonly Material AnomalyMarker = MaterialPool.MatFrom("SZ_Fx/AnomalyMarker", ShaderDatabase.MetaOverlay);
        public static readonly Material ArtifactMarker = MaterialPool.MatFrom("SZ_Fx/ArtifactMarker", ShaderDatabase.MetaOverlay);

        /// <summary>Рисует плоскую метку размером size в точке pos над всем остальным.</summary>
        public static void DrawMarker(Material mat, Vector3 pos, float size)
        {
            pos.y = AltitudeLayer.MetaOverlays.AltitudeFor();
            Matrix4x4 matrix = Matrix4x4.TRS(pos, Quaternion.identity, new Vector3(size, 1f, size));
            Graphics.DrawMesh(MeshPool.plane10, matrix, mat, 0);
        }

        /// <summary>Пульсация 0..1 по реальному времени (работает и на паузе).</summary>
        public static float Pulse(float speed)
        {
            return 0.5f + 0.5f * Mathf.Sin(Time.realtimeSinceStartup * speed);
        }
    }
}
