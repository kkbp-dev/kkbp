using System;
using System.Collections.Generic;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;
using UnityEngine.Rendering;

namespace KKBP.Exporter
{
    /// <summary>
    /// Bakes each material's light and dark Texture Variants with the game's own shader and maker light:
    /// the material is drawn on a quad covering UV space, lit from the front and from behind, and for
    /// shaders whose look depends on the mesh (overlay textures, specular height, xukmi, tessellation)
    /// the mesh flattened into UV space is drawn too and laid over it. While it runs, the Character's
    /// renderers and anything else near the origin are hidden; Dispose puts everything back.
    /// </summary>
    internal sealed class Bake : IDisposable
    {
        /// <summary>Normal and alpha maps and specular highlights would bake lighting detail into the colour.</summary>
        private static readonly string[] ClearedTextures = { "_AlphaMask", "_NormalMap", "_NormalMapDetail", "_NormalMask" };

        private static readonly string[] ClearedFloats =
        {
            "_SpecularPower", "_SpecularPowerNail", "_nip_specular", "_Is_SpecularToHighColor", "_HighColor_Power",
        };

        private static readonly string[] Overlays = { "_overtex1", "_overtex2", "_overtex3" };

        private static readonly Quaternion FrontLight = new Quaternion(0, 1, 0, 0);
        private static readonly Quaternion BackLight = new Quaternion(0, 0, 0, -1);

        private readonly Light light;
        private readonly Camera camera;
        private readonly Quaternion lightRotation;
        private readonly bool orthographic;
        private readonly float aspect;
        private readonly float orthographicSize;
        private readonly Vector3 cameraPosition;
        private readonly Quaternion cameraRotation;
        private readonly CameraClearFlags clearFlags;
        private readonly UnityEngine.Color background;
        private readonly bool msaa;
        private readonly Rect rect;
        private readonly RenderTexture target;
        private readonly List<Renderer> disabled = new List<Renderer>();
        private readonly List<GameObject> hidden = new List<GameObject>();
        private readonly Mesh quad;
        private readonly Kks.CameraEffects effects;

        public Bake(ChaControl cha)
        {
            light = Kks.MakerLight();
            camera = Camera.main;
            lightRotation = light.transform.rotation;
            orthographic = camera.orthographic;
            aspect = camera.aspect;
            orthographicSize = camera.orthographicSize;
            cameraPosition = camera.transform.position;
            cameraRotation = camera.transform.rotation;
            clearFlags = camera.clearFlags;
            background = camera.backgroundColor;
            msaa = camera.allowMSAA;
            rect = camera.rect;
            target = camera.targetTexture;
            effects = Kks.QuietCameraEffects(camera);

            camera.orthographic = true;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = UnityEngine.Color.clear;
            camera.allowMSAA = false;
            // The maker narrows the camera's viewport to leave room for its menus (x 0.33). Rendering
            // into a texture keeps that rect, which resampled every bake sideways and blurred it (ADR 0036).
            camera.rect = new Rect(0, 0, 1, 1);

            foreach (var r in cha.objTop.GetComponentsInChildren<Renderer>())
            {
                if (r.enabled)
                {
                    r.enabled = false;
                    disabled.Add(r);
                }
            }
            // The maker's own props sit around the origin, where the bake draws.
            foreach (var go in UnityEngine.Object.FindObjectsOfType<GameObject>())
            {
                if (go.activeSelf && Mathf.Abs(go.transform.position.y) <= 3 && go.GetComponent<Renderer>() != null && !go.transform.IsChildOf(cha.objTop.transform))
                {
                    go.SetActive(false);
                    hidden.Add(go);
                }
            }

            quad = new Mesh
            {
                vertices = new[] { new Vector3(1.001f, -0.001f, 0), new Vector3(1.001f, 1.001f, 0), new Vector3(-0.001f, 1.001f, 0), new Vector3(-0.001f, -0.001f, 0) },
                uv = new[] { new Vector2(-0.001f, -0.001f), new Vector2(-0.001f, 1.001f), new Vector2(1.001f, 1.001f), new Vector2(1.001f, -0.001f) },
                triangles = new[] { 1, 3, 0, 2, 3, 1 },
            };
            quad.RecalculateBounds();
            quad.RecalculateNormals();
            quad.RecalculateTangents();
        }

        /// <summary>Adds the light and dark Variants of one material slot to its captured material.</summary>
        public void Add(Renderer renderer, Material source, int slot, MaterialData data, bool face)
        {
            var mesh = Meshes.SourceMesh(renderer);
            var material = new Material(source);
            Mesh flattened = null;
            try
            {
                material.SetShaderPassEnabled("OUTLINE", false);
                material.SetShaderPassEnabled("SHADOWCASTER", false);
                foreach (string t in ClearedTextures)
                {
                    if (material.HasProperty(t))
                    {
                        material.SetTexture(t, null);
                    }
                }
                foreach (string f in ClearedFloats)
                {
                    if (material.HasProperty(f))
                    {
                        material.SetFloat(f, 0);
                    }
                }
                int size = face ? 4096 : material.mainTexture != null ? Mathf.Max(material.mainTexture.width, material.mainTexture.height) : 2048;
                var block = new MaterialPropertyBlock();
                renderer.GetPropertyBlock(block);
                int sub = Mathf.Min(slot, mesh.subMeshCount - 1);
                string shader = material.shader.name;
                bool tessellated = shader.ToLowerInvariant().Contains("tess");
                bool meshDependent = HasOverlay(material) || material.HasProperty("_SpeclarHeight") || shader.StartsWith("xukmi", StringComparison.Ordinal) || tessellated;

                byte[] meshLight = null;
                byte[] meshDark = null;
                if (meshDependent)
                {
                    int across, up;
                    Vector3 front;
                    flattened = Flatten(renderer, mesh, out across, out up, out front);
                    if (flattened != null)
                    {
                        Aim(front, up / 2f, (float)across / up);
                        meshLight = LightBake.Fold(Render(FrontLight, flattened, sub, material, renderer, block, size * across, size * up), size, across, up);
                        meshDark = LightBake.Fold(Render(BackLight, flattened, sub, material, renderer, block, size * across, size * up), size, across, up);
                    }
                    foreach (string t in Overlays)
                    {
                        if (material.HasProperty(t))
                        {
                            material.SetTexture(t, null);
                        }
                    }
                }

                byte[] lit;
                byte[] dark;
                if (tessellated && meshLight != null)
                {
                    lit = LightBake.Pad(meshLight, size, size, 2);
                    dark = LightBake.Pad(meshDark, size, size, 2);
                }
                else
                {
                    Aim(new Vector3(0.5f, 0.5f, 1f), 0.5f, 1f);
                    lit = Render(FrontLight, quad, 0, material, renderer, block, size, size);
                    dark = Render(BackLight, quad, 0, material, renderer, block, size, size);
                    if (meshLight != null)
                    {
                        LightBake.Overlay(lit, meshLight);
                        LightBake.Overlay(dark, meshDark);
                    }
                }
                data.Textures.Add(new TextureData { Role = TextureRole.Main, Raw = "_MainTex", Variant = TextureVariant.Light, Png = Png(lit, size) });
                data.Textures.Add(new TextureData { Role = TextureRole.Main, Raw = "_MainTex", Variant = TextureVariant.Dark, Png = Png(dark, size) });
            }
            finally
            {
                UnityEngine.Object.Destroy(material);
                if (flattened != null)
                {
                    UnityEngine.Object.Destroy(flattened);
                }
            }
        }

        private static bool HasOverlay(Material m)
        {
            foreach (string t in Overlays)
            {
                if (m.HasProperty(t) && m.GetTexture(t) != null)
                {
                    return true;
                }
            }
            return false;
        }

        /// <summary>
        /// A copy of the mesh with each vertex moved to its UV position, overlapping UV islands layered
        /// apart. Returns null for a mesh without UVs, or one whose data can't be copied.
        /// </summary>
        private static Mesh Flatten(Renderer renderer, Mesh source, out int across, out int up, out Vector3 front)
        {
            across = up = 1;
            front = Vector3.zero;
            Mesh mesh;
            var smr = renderer as SkinnedMeshRenderer;
            if (smr != null)
            {
                mesh = new Mesh();
                smr.BakeMesh(mesh);
            }
            else if (source.isReadable)
            {
                mesh = UnityEngine.Object.Instantiate(source);
            }
            else
            {
                return null;
            }
            var uvs = mesh.uv;
            if (uvs.Length == 0)
            {
                UnityEngine.Object.Destroy(mesh);
                return null;
            }
            float minX = float.PositiveInfinity, minY = float.PositiveInfinity, maxX = float.NegativeInfinity, maxY = float.NegativeInfinity;
            var flat = new Vec2[uvs.Length];
            for (int i = 0; i < uvs.Length; i++)
            {
                flat[i] = new Vec2(uvs[i].x, uvs[i].y);
                minX = Mathf.Min(minX, uvs[i].x);
                maxX = Mathf.Max(maxX, uvs[i].x);
                minY = Mathf.Min(minY, uvs[i].y);
                maxY = Mathf.Max(maxY, uvs[i].y);
            }
            int xOffset = Mathf.FloorToInt(minX);
            int yOffset = Mathf.FloorToInt(minY);
            across = Mathf.Max(1, Mathf.CeilToInt(maxX) - xOffset);
            up = Mathf.Max(1, Mathf.CeilToInt(maxY) - yOffset);

            // The camera looks down -Z, so U runs along -X to come out left to right.
            var triangles = mesh.triangles;
            var depths = LightBake.IslandDepths(triangles, flat);
            var vertices = new Vector3[uvs.Length];
            for (int i = 0; i < uvs.Length; i++)
            {
                vertices[i] = new Vector3(-uvs[i].x, uvs[i].y, depths[i]);
            }
            for (int t = 0; t + 2 < triangles.Length; t += 3)
            {
                var a = vertices[triangles[t]];
                if (Vector3.Cross(vertices[triangles[t + 1]] - a, vertices[triangles[t + 2]] - a).z < 0)
                {
                    int swap = triangles[t + 1];
                    triangles[t + 1] = triangles[t + 2];
                    triangles[t + 2] = swap;
                }
            }
            mesh.vertices = vertices;
            mesh.triangles = triangles;
            mesh.RecalculateBounds();
            mesh.RecalculateNormals();
            mesh.RecalculateTangents();
            front = new Vector3(-xOffset - across / 2f, yOffset + up / 2f, 10f);
            return mesh;
        }

        private void Aim(Vector3 position, float size, float aspectRatio)
        {
            camera.orthographicSize = size;
            camera.aspect = aspectRatio;
            camera.transform.position = position;
            camera.transform.LookAt(new Vector3(position.x, position.y, 0));
        }

        private byte[] Render(Quaternion rotation, Mesh mesh, int sub, Material material, Renderer renderer, MaterialPropertyBlock block, int width, int height)
        {
            light.transform.rotation = rotation;
            var rt = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32);
            rt.antiAliasing = 1;
            rt.filterMode = FilterMode.Point;
            camera.targetTexture = rt;
            Graphics.DrawMesh(mesh, Matrix4x4.identity, material, renderer.gameObject.layer, camera, sub, block,
                renderer.shadowCastingMode, renderer.receiveShadows, renderer.probeAnchor, renderer.lightProbeUsage != LightProbeUsage.Off);
            camera.Render();
            var previous = RenderTexture.active;
            RenderTexture.active = rt;
            var read = new Texture2D(width, height, TextureFormat.RGBA32, false);
            read.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            RenderTexture.active = previous;
            camera.targetTexture = null;
            RenderTexture.ReleaseTemporary(rt);
            var pixels = read.GetPixels32();
            UnityEngine.Object.Destroy(read);
            var bytes = new byte[pixels.Length * 4];
            for (int i = 0; i < pixels.Length; i++)
            {
                bytes[i * 4] = pixels[i].r;
                bytes[i * 4 + 1] = pixels[i].g;
                bytes[i * 4 + 2] = pixels[i].b;
                bytes[i * 4 + 3] = pixels[i].a;
            }
            return bytes;
        }

        private static byte[] Png(byte[] rgba, int size)
        {
            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            var pixels = new Color32[size * size];
            for (int i = 0; i < pixels.Length; i++)
            {
                pixels[i] = new Color32(rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2], rgba[i * 4 + 3]);
            }
            texture.SetPixels32(pixels);
            texture.Apply();
            var png = Kks.EncodePng(texture);
            UnityEngine.Object.Destroy(texture);
            return png;
        }

        public void Dispose()
        {
            light.transform.rotation = lightRotation;
            camera.orthographic = orthographic;
            camera.aspect = aspect;
            camera.orthographicSize = orthographicSize;
            camera.transform.position = cameraPosition;
            camera.transform.rotation = cameraRotation;
            camera.clearFlags = clearFlags;
            camera.backgroundColor = background;
            camera.allowMSAA = msaa;
            camera.rect = rect;
            camera.targetTexture = target;
            effects.Restore();
            foreach (var r in disabled)
            {
                if (r != null)
                {
                    r.enabled = true;
                }
            }
            foreach (var go in hidden)
            {
                if (go != null)
                {
                    go.SetActive(true);
                }
            }
            UnityEngine.Object.Destroy(quad);
        }
    }
}
