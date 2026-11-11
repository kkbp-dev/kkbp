using System;
using System.Collections;
using System.IO;
using System.Text;
using BepInEx;
using Character;
using CharacterCreation;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Runs one export from a request file, then quits the game (ADR 0012). The request is
    /// BepInEx/config/kkbp-autoexport.json, as for KK and KKS:
    /// <code>
    /// { "card": "/path/card.png", "outfit": 0, "output": "/path/folder", "options": { … },
    ///   "diagnose": "/path/notes.txt" }
    /// </code>
    /// With "diagnose", it writes what it finds about the maker's Character there instead of exporting.
    /// With "stay": true, it leaves the game in the maker with the card loaded, for trying the window.
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
            Plugin.Logger.LogInfo("Auto-export requested by " + RequestPath);
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

            // Into the character maker from the title screen.
            while (UnityEngine.Object.FindObjectOfType<SV.Title.TitleScene>() == null)
            {
                yield return new WaitForSecondsRealtime(0.5f);
            }
            yield return new WaitForSecondsRealtime(3f);
            Step("Opening the maker");
            SV.Title.TitleScene.GotoCustomScene(false);
            while (!HumanCustom.Initialized || HumanCustom.Instance == null || HumanCustom.Instance.Human == null)
            {
                yield return new WaitForSecondsRealtime(0.5f);
            }
            yield return new WaitForSecondsRealtime(3f);

            object cards;
            if (request.TryGet("folder", out cards) && cards != null)
            {
                Step("Exporting every card in " + cards);
                CardBatch batch = null;
                var all = plugin.ExportFolder((string)cards, Options(), (string)request["output"], b => batch = b);
                while (all.MoveNext())
                {
                    yield return all.Current;
                }
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

            object stay;
            if (request.TryGet("stay", out stay) && stay is bool && (bool)stay)
            {
                Step("Staying in the maker");
                WriteResult(null);
                yield break;
            }

            object diagnose;
            if (request.TryGet("diagnose", out diagnose) && diagnose != null)
            {
                try
                {
                    File.WriteAllText((string)diagnose, Diagnostics.Describe(HumanCustom.Instance.Human), new UTF8Encoding(false));
                    Finish(null);
                }
                catch (Exception e)
                {
                    Finish("Diagnostics failed: " + e);
                }
                yield break;
            }

            object probe;
            if (request.TryGet("probe_corrections", out probe) && probe != null)
            {
                try
                {
                    var human = HumanCustom.Instance.Human;
                    // As in KK, the maker may leave the Character without its correction component.
                    if (human.body.expression == null)
                    {
                        human.body.expression = new HumanBody.Expression(human);
                    }
                    var bone = human.body.expression.bone;
                    CorrectionProbe.Run(human.objTop.transform, () => bone.LateUpdate(), (string)request["probe_poses"], (string)probe);
                    Finish(null);
                }
                catch (Exception e)
                {
                    Finish("The correction probe failed: " + e);
                }
                yield break;
            }

            object outfit;
            if (request.TryGet("outfit", out outfit) && outfit != null)
            {
                Svs.ChangeOutfit(HumanCustom.Instance.Human, (int)(double)outfit);
                yield return new WaitForSecondsRealtime(2f);
            }

            Step("Exporting");
            BundleExport export = null;
            SvsAdapter adapter = null;
            var run = plugin.Export(Options(), (string)request["output"], (e, a) => { export = e; adapter = a; });
            while (run.MoveNext())
            {
                yield return run.Current;
            }
            if (adapter != null)
            {
                var warnings = new JsonArray();
                warnings.AddRange(adapter.Warnings.ConvertAll(w => (object)w));
                result.Add("warnings", warnings);
            }
            if (export != null)
            {
                result.Add("bundle", export.BundlePath);
            }
            Finish(export != null && export.State == ExportState.Succeeded ? null : plugin.Status);
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

        private static void Step(string what)
        {
            Plugin.Logger.LogInfo("Auto-export: " + what + " (time scale " + Time.timeScale + ")");
        }

        private void Finish(string error)
        {
            WriteResult(error);
            Plugin.Logger.LogInfo("Auto-export finished: " + (error ?? "succeeded") + ". Quitting.");
            Application.Quit();
        }

        private void WriteResult(string error)
        {
            result.Add("state", error == null ? "succeeded" : "failed");
            result.Add("error", error);
            try
            {
                File.WriteAllText(ResultPath, JsonWriter.Write(result, true), new UTF8Encoding(false));
            }
            catch (Exception e)
            {
                Plugin.Logger.LogError("Couldn't write " + ResultPath + ": " + e.Message);
            }
        }
    }
}
