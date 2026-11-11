using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using BepInEx;
using ChaCustom;
using KKAPI.Maker;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Runs one export from a request file, then quits the game (ADR 0012). The request is
    /// BepInEx/config/kkbp-autoexport.json:
    /// <code>
    /// { "card": "/path/card.png", "outfit": 0, "output": "/path/folder",
    ///   "options": { "all_outfits": false, ... }, "dump_shaders": "/path/shaders.json",
    ///   "dump_bundles": [ "/path/kk/abdata/chara/mm_base.unity3d" ],
    ///   "probe_corrections": "/path/out.json", "probe_poses": "/path/poses.json" }
    /// </code>
    /// "probe_corrections" records the game's joint corrections for the poses in "probe_poses"
    /// instead of exporting (CorrectionProbe).
    /// "dump_bundles" (KKS only) names asset bundles, such as KK's, whose shaders the dump also lists.
    /// Every field but "card" and "output" is optional. The result goes to kkbp-autoexport.result.json
    /// next to the request: { "state": "succeeded" | "failed", "bundle": …, "error": …, "warnings": […] }.
    /// With "folder" instead of "card", it runs the window's batch export on every card in that folder;
    /// the result then has "cards", "bundles" and "failures", and succeeds only if every card exported.
    /// </summary>
    internal sealed class AutoExport
    {
        private static readonly string RequestPath = Path.Combine(Paths.ConfigPath, "kkbp-autoexport.json");
        private static readonly string ResultPath = Path.Combine(Paths.ConfigPath, "kkbp-autoexport.result.json");

        private readonly Plugin plugin;
        private JsonObject request;
        private readonly JsonObject result = new JsonObject();

        public AutoExport(Plugin plugin)
        {
            this.plugin = plugin;
        }

        public static bool Requested
        {
            get { return File.Exists(RequestPath); }
        }

        public IEnumerator Run()
        {
            Plugin.Log.LogInfo("Auto-export requested by " + RequestPath);
            try
            {
                request = (JsonObject)JsonReader.Parse(File.ReadAllText(RequestPath));
                File.Delete(RequestPath);
            }
            catch (Exception e)
            {
                Finish("The request couldn't be read: " + e.Message);
                yield break;
            }

            // Into the female character maker from the title screen.
            while (!MakerAPI.InsideMaker)
            {
                var title = UnityEngine.Object.FindObjectOfType<TitleScene>();
                if (title != null)
                {
                    yield return new WaitForSecondsRealtime(2f);
                    Step("Opening the maker");
                    title.OnCustomFemale();
                    break;
                }
                yield return new WaitForSecondsRealtime(0.5f);
            }
            while (!MakerAPI.InsideAndLoaded)
            {
                yield return new WaitForSecondsRealtime(0.5f);
            }
            yield return new WaitForSecondsRealtime(2f);

            object cards;
            if (request.TryGet("folder", out cards) && cards != null)
            {
                Step("Exporting every card in " + cards);
                CardBatch batch = null;
                yield return plugin.StartCoroutine(plugin.ExportFolder((string)cards, Options(), (string)request["output"], b => batch = b));
                Finish(batch != null ? batch.Report(result) : plugin.Status);
                yield break;
            }

            Step("Loading the card");

            string error = null;
            try
            {
                Cards.Load((string)request["card"]);
            }
            catch (Exception e)
            {
                error = "The card couldn't be loaded: " + e.Message;
            }
            if (error != null)
            {
                Finish(error);
                yield break;
            }
            yield return new WaitForSecondsRealtime(3f);
            Step("Card loaded");

            object outfit;
            if (request.TryGet("outfit", out outfit) && outfit != null)
            {
                MakerAPI.GetCharacterControl().ChangeCoordinateTypeAndReload((ChaFileDefine.CoordinateType)(int)(double)outfit);
                yield return new WaitForSecondsRealtime(2f);
            }

            object dump;
            if (request.TryGet("dump_shaders", out dump) && dump != null)
            {
#if KKS
                var bundles = new List<string>();
                object names;
                if (request.TryGet("dump_bundles", out names) && names is JsonArray)
                {
                    foreach (var name in (JsonArray)names)
                    {
                        bundles.Add((string)name);
                    }
                }
                Kks.DumpShaders((string)dump, bundles);
                Plugin.Log.LogInfo("Wrote the shader table to " + dump);
#endif
            }

            object probe;
            if (request.TryGet("probe_corrections", out probe) && probe != null)
            {
                try
                {
                    var cha = MakerAPI.GetCharacterControl();
                    // Only Studio gives a Character its ExpressionBone; the maker and the main game
                    // leave the correction bones to the animations.
                    if (cha.expression == null)
                    {
                        cha.InitializeExpression();
                    }
                    var expression = cha.expression;
                    CorrectionProbe.Run(cha.objTop.transform, () => expression.LateUpdate(), (string)request["probe_poses"], (string)probe);
                    Finish(null);
                }
                catch (Exception e)
                {
                    Finish("The correction probe failed: " + e);
                }
                yield break;
            }

            Step("Exporting");
            BundleExport export = null;
            KkAdapter adapter = null;
            yield return plugin.StartCoroutine(plugin.Export(Options(), (string)request["output"], (e, a) => { export = e; adapter = a; }));
            if (adapter != null)
            {
                var warnings = new JsonArray();
                warnings.AddRange(adapter.Warnings.ConvertAll(w => (object)w));
                result.Add("warnings", warnings);
            }
            if (export == null)
            {
                Finish(plugin.Status);
            }
            else if (export.State != ExportState.Succeeded)
            {
                result.Add("bundle", export.BundlePath);
                Finish(plugin.Status);
            }
            else
            {
                result.Add("bundle", export.BundlePath);
                Finish(null);
            }
        }

        private static void Step(string what)
        {
            Plugin.Log.LogInfo("Auto-export: " + what + " (time scale " + Time.timeScale + ")");
        }

        private ExportOptions Options()
        {
            var options = plugin.CurrentOptions();
            object value;
            if (!request.TryGet("options", out value) || !(value is JsonObject))
            {
                return options;
            }
            var o = (JsonObject)value;
            options.AllOutfits = Flag(o, "all_outfits", options.AllOutfits);
            options.AllVariations = Flag(o, "all_variations", options.AllVariations);
            options.Physics = Flag(o, "physics", options.Physics);
            options.EnabledShapeKeys = Flag(o, "enabled_shape_keys", options.EnabledShapeKeys);
            options.CurrentPose = Flag(o, "current_pose", options.CurrentPose);
            return options;
        }

        private static bool Flag(JsonObject o, string name, bool fallback)
        {
            object v;
            return o.TryGet(name, out v) && v is bool ? (bool)v : fallback;
        }

        private void Finish(string error)
        {
            result.Add("state", error == null ? "succeeded" : "failed");
            result.Add("error", error);
            try
            {
                File.WriteAllText(ResultPath, JsonWriter.Write(result, true), new UTF8Encoding(false));
            }
            catch (Exception e)
            {
                Plugin.Log.LogError("Couldn't write " + ResultPath + ": " + e.Message);
            }
            Plugin.Log.LogInfo("Auto-export finished: " + (error ?? "succeeded") + ". Quitting.");
            Application.Quit();
        }
    }
}
