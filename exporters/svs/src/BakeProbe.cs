using System;
using System.IO;
using System.Text;
using KKBP.Exporter.Core;
using UnityEngine;
using UnityEngine.Rendering;

namespace KKBP.Exporter
{
    /// <summary>
    /// Records the scene values SVS's shaders read during each light and dark bake, which the bundle
    /// doesn't carry, for modelling the shaders as edit templates (issue 62): the maker light, the
    /// pipeline's globals and keywords, the ambient light and probe, the camera, and the material's
    /// keywords and the defaults of the textures the bake clears. The export runs as usual; the
    /// request's "probe_bake" names the file. Each read that fails records its error instead.
    /// </summary>
    internal sealed class BakeProbe
    {
        /// <summary>The URP globals the LIF shaders read, set while the camera renders.</summary>
        private static readonly string[] Globals =
        {
            "_MainLightPosition", "_MainLightColor", "_MainLightShadowParams", "_AdditionalLightsCount",
            "_WorldSpaceCameraPos", "unity_SpecCube0_HDR", "_TimeParameters", "_ScreenParams", "_ProjectionParams",
            "glstate_lightmodel_ambient", "unity_AmbientSky", "unity_AmbientEquator", "unity_AmbientGround",
            "_GlossyEnvironmentColor", "_SubtractiveShadowColor",
        };

        /// <summary>The pipeline keywords the LIF shaders' Forward pass has variants for.</summary>
        private static readonly string[] PipelineKeywords =
        {
            "_MAIN_LIGHT_SHADOWS", "_MAIN_LIGHT_SHADOWS_CASCADE", "_MAIN_LIGHT_SHADOWS_SCREEN", "_ADDITIONAL_LIGHTS_VERTEX",
            "_ADDITIONAL_LIGHTS", "_ADDITIONAL_LIGHT_SHADOWS", "_SHADOWS_SOFT", "_MIXED_LIGHTING_SUBTRACTIVE",
            "LIGHTMAP_ON", "DIRLIGHTMAP_COMBINED", "_SAMPLE_GI", "FOG_LINEAR", "FOG_EXP", "FOG_EXP2", "LOD_FADE_CROSSFADE",
            "_DBUFFER_MRT1", "_DBUFFER_MRT2", "_DBUFFER_MRT3", "DEBUG_DISPLAY",
        };

        private readonly JsonArray renders = new JsonArray();
        private JsonObject scene;

        /// <summary>One render of the bake, read just after the camera rendered it.</summary>
        public void Record(Material material, string[] cleared, Light light, bool quad, Camera camera, Renderer renderer, int width, int height)
        {
            if (scene == null)
            {
                scene = Try(() => Scene());
            }
            var keywords = new JsonArray();
            foreach (string k in material.shaderKeywords)
            {
                keywords.Add(k);
            }
            var globals = new JsonObject();
            foreach (string g in Globals)
            {
                globals.Add(g, Try(() => (object)V4(Shader.GetGlobalVector(g))));
            }
            var pipeline = new JsonArray();
            foreach (string k in PipelineKeywords)
            {
                if (Shader.IsKeywordEnabled(k))
                {
                    pipeline.Add(k);
                }
            }
            var defaults = new JsonObject();
            foreach (string t in cleared)
            {
                string name = t;
                defaults.Add(name, Try(() =>
                {
                    int i = material.shader.FindPropertyIndex(name);
                    return i < 0 ? null : (object)material.shader.GetPropertyTextureDefaultName(i);
                }));
            }
            renders.Add(new JsonObject()
                .Add("material", material.name)
                .Add("shader", material.shader.name)
                .Add("light", light.transform.forward.z < 0 ? "front" : "back")  // the quad faces +z
                .Add("mesh", quad ? "quad" : "flattened")
                .Add("size", new JsonArray { (double)width, (double)height })
                .Add("keywords", keywords)
                .Add("pipeline_keywords", pipeline)
                .Add("globals", globals)
                .Add("cleared_texture_defaults", defaults)
                .Add("light_forward", V3(light.transform.forward))
                .Add("light_color", V4(light.color))
                .Add("light_intensity", (double)light.intensity)
                .Add("camera_position", V3(camera.transform.position))
                .Add("camera_forward", V3(camera.transform.forward))
                .Add("camera_size", (double)camera.orthographicSize)
                .Add("light_probe_usage", renderer.lightProbeUsage.ToString())
                .Add("probe_anchor", renderer.probeAnchor != null ? renderer.probeAnchor.name : null)
                .Add("interpolated_probe", Try(() =>
                {
                    SphericalHarmonicsL2 sh;
                    LightProbes.GetInterpolatedProbe(new Vector3(0.5f, 0.5f, 0f), null, out sh);
                    return (object)Sh(sh);
                })));
        }

        public void Write(string path)
        {
            var root = new JsonObject().Add("scene", scene).Add("renders", renders);
            File.WriteAllText(path, JsonWriter.Write(root, true), new UTF8Encoding(false));
        }

        private static JsonObject Scene()
        {
            return new JsonObject()
                .Add("color_space", QualitySettings.activeColorSpace.ToString())
                .Add("ambient_mode", RenderSettings.ambientMode.ToString())
                .Add("ambient_light", V4(RenderSettings.ambientLight))
                .Add("ambient_sky", V4(RenderSettings.ambientSkyColor))
                .Add("ambient_equator", V4(RenderSettings.ambientEquatorColor))
                .Add("ambient_ground", V4(RenderSettings.ambientGroundColor))
                .Add("ambient_intensity", (double)RenderSettings.ambientIntensity)
                .Add("ambient_probe", Try(() => (object)Sh(RenderSettings.ambientProbe)))
                .Add("reflection_intensity", (double)RenderSettings.reflectionIntensity)
                .Add("default_reflection_mode", RenderSettings.defaultReflectionMode.ToString())
                .Add("fog", RenderSettings.fog)
                .Add("light_probes", Try(() => LightmapSettings.lightProbes != null ? (object)(double)LightmapSettings.lightProbes.count : null));
        }

        /// <summary>A probe's 27 coefficients, by colour (r, g, b) then coefficient (0..8), as Unity indexes them.</summary>
        private static JsonArray Sh(SphericalHarmonicsL2 sh)
        {
            var a = new JsonArray();
            for (int c = 0; c < 3; c++)
            {
                for (int i = 0; i < 9; i++)
                {
                    a.Add((double)sh[c, i]);
                }
            }
            return a;
        }

        private static object Try(Func<object> read)
        {
            try
            {
                return read();
            }
            catch (Exception e)
            {
                return "error: " + e.GetType().Name + ": " + e.Message;
            }
        }

        private static JsonObject Try(Func<JsonObject> read)
        {
            try
            {
                return read();
            }
            catch (Exception e)
            {
                return new JsonObject().Add("error", e.GetType().Name + ": " + e.Message);
            }
        }

        private static JsonArray V3(Vector3 v)
        {
            return new JsonArray { (double)v.x, (double)v.y, (double)v.z };
        }

        private static JsonArray V4(Vector4 v)
        {
            return new JsonArray { (double)v.x, (double)v.y, (double)v.z, (double)v.w };
        }

        private static JsonArray V4(UnityEngine.Color c)
        {
            return new JsonArray { (double)c.r, (double)c.g, (double)c.b, (double)c.a };
        }
    }
}
