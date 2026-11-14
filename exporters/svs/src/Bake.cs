using System;
using System.Collections.Generic;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using Character;
using UnityEngine;
using UnityEngine.Rendering;

namespace KKBP.Exporter
{
    /// <summary>
    /// Bakes each material's light and dark Texture Variants with the game's own shader and maker light:
    /// the material is drawn on a quad covering UV space, lit from the front and from behind, and for
    /// shaders whose look depends on the mesh (the skin shaders, overlay textures, specular height, xukmi, tessellation)
    /// the mesh flattened into UV space is drawn too and laid over it. While it runs, the Character's
    /// renderers and anything else near the origin are hidden; Dispose puts everything back.
    /// </summary>
    internal sealed class Bake : IDisposable
    {
        /// <summary>
        /// Normal and alpha maps, mat caps and highlights would bake lighting detail or holes into the colour.
        /// These are the slots the legacy SVS exporter cleared.
        /// </summary>
        private static readonly string[] ClearedTextures =
        {
            "_DetailNormal", "_Matcap_mask", "_Mat_cap_01", "_Mat_cap_02", "_Mat_cap_03", "unity_Lightmaps", "unity_LightmapsInd",
            "_Normal", "_Normal_map", "_Cloth_alpha", "_Cloth_alpha_bot", "_Highlight_texture",
        };

        private static readonly string[] ClearedFloats =
        {
            "_SpecularPower", "_SpecularPowerNail", "_nip_specular", "_Is_SpecularToHighColor", "_HighColor_Power",
        };

        private static readonly string[] Overlays = { "_overtex1", "_overtex2", "_overtex3" };

        /// <summary>
        /// The skin shaders, which place the under-hair, nipples, nose, lips and cheek blush by the mesh's
        /// own positions, so only the flattened mesh draws them in the right place (legacy SVS's
        /// multi-texture shaders).
        /// </summary>
        private static readonly HashSet<string> MeshPlacedShaders = new HashSet<string> { "LIF/lif_main_skin_head", "LIF/lif_main_skin_body" };

        /// <summary>
        /// Those layers, cleared after the mesh render so the quad render gives the bare skin under them.
        /// Legacy SVS cleared the first four; the cheek and lips land out of place on the quad too.
        /// </summary>
        private static readonly string[] MeshPlacedLayers =
        {
            "_Lip_line_texture", "_Nose_texture", "_Nip", "_Under_hair_texture", "_Cheek_texture", "_Lip_texture",
        };

        // The maker light's placements for the light and dark bakes, as the legacy SVS exporter used them.
        private static readonly Quaternion FrontLight = new Quaternion(-0.03940f, 0.95533f, -0.21508f, -0.19882f);
        private static readonly Quaternion BackLight = new Quaternion(0.16412f, -0.02926f, 0.00487f, 0.98600f);
        private static readonly Vector3 FrontLightPosition = new Vector3(0.70f, 4.46f, 2.69f);
        private static readonly Vector3 BackLightPosition = new Vector3(-0.17f, 4.40f, 2.84f);

        private readonly Light light;
        private readonly Camera camera;
        private readonly GameObject cameraObject;
        private readonly Quaternion lightRotation;
        private readonly Vector3 lightPosition;
        private readonly List<Renderer> disabled = new List<Renderer>();
        private readonly List<GameObject> hidden = new List<GameObject>();
        private readonly Mesh quad;
        public Bake(Human cha)
        {
            light = Svs.MakerLight();
            // A camera of its own, copied from the maker's: URP post-processing on the maker camera would
            // tint the bake and drop its alpha.
            cameraObject = new GameObject("KKBP bake camera");
            camera = cameraObject.AddComponent<Camera>();
            camera.CopyFrom(Camera.main);
            // Left enabled: URP doesn't render from a disabled camera. It only exists while the bake runs.
            camera.allowHDR = false;
            lightRotation = light.transform.rotation;
            lightPosition = light.transform.position;

            camera.orthographic = true;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = UnityEngine.Color.clear;
            camera.allowMSAA = false;
            // CopyFrom also copies the maker camera's viewport rect; a narrowed one would resample the
            // bake sideways and blur it (ADR 0036).
            camera.rect = new Rect(0, 0, 1, 1);

            foreach (var r in cha.objTop.GetComponentsInChildren<Renderer>(false))
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
                if (go.activeSelf && Mathf.Abs(go.transform.position.y) <= 3 && go.GetComponent<Renderer>() != null && !go.transform.IsChildOf(cha.objTop.transform) && go.layer == cha.objTop.layer)
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
        public void Add(Renderer renderer, Material source, int slot, MaterialData data, bool skin)
        {
            Add(renderer, source, slot, data, skin, TextureVariant.Light, TextureVariant.Dark);
        }

        /// <summary>Bakes one material slot lit and unlit, as it is drawn now, and adds the two as these Variants.</summary>
        public void Add(Renderer renderer, Material source, int slot, MaterialData data, bool skin, TextureVariant lightVariant, TextureVariant darkVariant)
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
                var main = material.mainTexture;
                int width, height;
                LightBake.Size(main != null ? main.width : 0, main != null ? main.height : 0, skin, out width, out height);
                var block = new MaterialPropertyBlock();
                renderer.GetPropertyBlock(block);
                int sub = Mathf.Min(slot, mesh.subMeshCount - 1);
                string shader = material.shader.name;
                bool tessellated = shader.ToLowerInvariant().Contains("tess");
                bool meshPlaced = MeshPlacedShaders.Contains(shader);
                bool meshDependent = meshPlaced || HasOverlay(material) || material.HasProperty("_SpeclarHeight") || shader.StartsWith("xukmi", StringComparison.Ordinal) || tessellated;

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
                        meshLight = LightBake.Fold(Render(FrontLight, flattened, sub, material, renderer, block, width * across, height * up), width, height, across, up);
                        meshDark = LightBake.Fold(Render(BackLight, flattened, sub, material, renderer, block, width * across, height * up), width, height, across, up);
                    }
                    foreach (string t in meshPlaced ? MeshPlacedLayers : Overlays)
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
                    lit = LightBake.Pad(meshLight, width, height, 2);
                    dark = LightBake.Pad(meshDark, width, height, 2);
                }
                else
                {
                    Aim(new Vector3(0.5f, 0.5f, 1f), 0.5f, 1f);
                    lit = Render(FrontLight, quad, 0, material, renderer, block, width, height);
                    dark = Render(BackLight, quad, 0, material, renderer, block, width, height);
                    if (meshLight != null)
                    {
                        LightBake.Overlay(lit, meshLight);
                        LightBake.Overlay(dark, meshDark);
                    }
                }
                if (DrawsEyeWhite(material, data.Role))
                {
                    bool white = data.Role == MaterialRole.EyeWhite;
                    lit = EyeLayer(FrontLight, lit, material, renderer, block, width, height, white);
                    dark = EyeLayer(BackLight, dark, material, renderer, block, width, height, white);
                }
                data.Textures.Add(new TextureData { Role = TextureRole.Main, Raw = "_MainTex", Variant = lightVariant, Png = Png(lit, width, height) });
                data.Textures.Add(new TextureData { Role = TextureRole.Main, Raw = "_MainTex", Variant = darkVariant, Png = Png(dark, width, height) });
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

        /// <summary>
        /// The textures SVS's eye shader draws the iris, pupil and highlights from. The eye white copies
        /// leave them out (ADR 0034).
        /// </summary>
        internal static readonly string[] IrisTextures =
        {
            "_Eye_mask", "_Pipil_texture", "_Grade_texture", "_Highlight_texture_01", "_Highlight_texture_02", "_Highlight_texture_03",
        };

        /// <summary>The eye white's two colours, which its shadow mask blends between.</summary>
        private static readonly string[] EyeWhiteColors = { "_Eye_white_color_01", "_Eye_white_color_02" };

        /// <summary>An eye or eye white material whose shader draws the eye white and the pupil together (ADR 0034).</summary>
        private static bool DrawsEyeWhite(Material material, MaterialRole? role)
        {
            return (role == MaterialRole.EyeWhite || role == MaterialRole.EyeL || role == MaterialRole.EyeR)
                && material.HasProperty(EyeWhiteColors[0]) && material.HasProperty(IrisTextures[0]);
        }

        /// <summary>
        /// One layer of such an eye, with one light: the eye white alone, drawn with the iris textures
        /// cleared, or the pupil over a transparent background, worked out from <paramref name="full"/>,
        /// the eye as the game draws it, and two more renders with the eye white black and white
        /// (<see cref="LightBake.Pupil"/>).
        /// </summary>
        private byte[] EyeLayer(Quaternion light, byte[] full, Material material, Renderer renderer, MaterialPropertyBlock block, int width, int height, bool eyeWhite)
        {
            Aim(new Vector3(0.5f, 0.5f, 1f), 0.5f, 1f);
            var white = RenderWith(light, material, renderer, block, width, height, m =>
            {
                foreach (string t in IrisTextures)
                {
                    if (m.HasProperty(t))
                    {
                        m.SetTexture(t, Texture2D.blackTexture);
                    }
                }
            });
            if (eyeWhite)
            {
                return white;
            }
            var onBlack = RenderWith(light, material, renderer, block, width, height, m => SetEyeWhite(m, UnityEngine.Color.black));
            var onWhite = RenderWith(light, material, renderer, block, width, height, m => SetEyeWhite(m, UnityEngine.Color.white));
            return LightBake.Pupil(full, white, onBlack, onWhite);
        }

        private static void SetEyeWhite(Material material, UnityEngine.Color color)
        {
            foreach (string c in EyeWhiteColors)
            {
                material.SetColor(c, color);
            }
        }

        /// <summary>Renders a copy of the material on the UV quad, changed by <paramref name="change"/>.</summary>
        private byte[] RenderWith(Quaternion light, Material material, Renderer renderer, MaterialPropertyBlock block, int width, int height, Action<Material> change)
        {
            var copy = new Material(material);
            try
            {
                change(copy);
                return Render(light, quad, 0, copy, renderer, block, width, height);
            }
            finally
            {
                UnityEngine.Object.Destroy(copy);
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
            var smr = renderer.TryCast<SkinnedMeshRenderer>();
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
            light.transform.position = rotation == FrontLight ? FrontLightPosition : BackLightPosition;
            var rt = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32);
            rt.antiAliasing = 1;
            rt.filterMode = FilterMode.Point;
            camera.targetTexture = rt;
            camera.cullingMask = 1 << renderer.gameObject.layer;
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

        private static byte[] Png(byte[] rgba, int width, int height)
        {
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
            var pixels = new Color32[width * height];
            for (int i = 0; i < pixels.Length; i++)
            {
                pixels[i] = new Color32(rgba[i * 4], rgba[i * 4 + 1], rgba[i * 4 + 2], rgba[i * 4 + 3]);
            }
            texture.SetPixels32(pixels);
            texture.Apply();
            var png = Svs.EncodePng(texture);
            UnityEngine.Object.Destroy(texture);
            return png;
        }

        public void Dispose()
        {
            light.transform.rotation = lightRotation;
            light.transform.position = lightPosition;
            UnityEngine.Object.Destroy(cameraObject);
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
