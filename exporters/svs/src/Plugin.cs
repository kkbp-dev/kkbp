using System;
using System.Collections;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using BepInEx.Unity.IL2CPP.Utils.Collections;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    [BepInPlugin(Guid, Name, ExporterVersion.Plugin)]
    public sealed class Plugin : BasePlugin
    {
        public const string Guid = "kkbp.exporter";
        public const string Name = "KKBP Exporter";

        internal static ManualLogSource Logger;
        internal static Plugin Instance;

        internal ConfigEntry<string> OutputFolder;
        internal ConfigEntry<string> CardFolder;
        internal ConfigEntry<KeyCode> ShortcutKey;
        internal ConfigEntry<bool> AllOutfits;
        internal ConfigEntry<bool> AllVariations;
        internal ConfigEntry<bool> CurrentPose;
        internal ConfigEntry<bool> EnabledShapeKeys;
        internal ConfigEntry<bool> DisablePhysics;

        internal Behaviour Runner { get; private set; }

        public override void Load()
        {
            Logger = Log;
            Instance = this;
            OutputFolder = Config.Bind("Export", "Output folder", "", "Where bundles are written. Empty means the 'KKBP Exports' folder in the game folder.");
            CardFolder = Config.Bind("Export", "Card folder", "", "The folder the batch export last exported. Empty means the game's UserData/chara folder.");
            ShortcutKey = Config.Bind("Window", "Show or hide key", KeyCode.Tab, "With Ctrl held, shows or hides the exporter window in the character maker.");
            // The option names are the legacy KK exporter's.
            AllOutfits = Config.Bind("Options", "Export All Outfits", false, "Export every Outfit, not only the current one.");
            AllVariations = Config.Bind("Options", "Export Variations", false, "Also export clothes shown only in the half-off clothing state.");
            CurrentPose = Config.Bind("Options", "Freeze Current Pose", false, "Keep the current pose instead of the T-pose.");
            EnabledShapeKeys = Config.Bind("Options", "Freeze Shape Keys", false, "Bake the shape keys enabled in the game into the meshes.");
            DisablePhysics = Config.Bind("Options", "Disable Physics", false, "Reset physics before capture instead of letting them settle for two seconds.");
            Runner = AddComponent<Behaviour>();
            Logger.LogInfo(Name + " " + ExporterVersion.Value + " for SVS loaded.");
        }

        internal bool Exporting { get; private set; }

        internal string Status { get; private set; }

        /// <summary>Set by AutoExport: where the next export writes its SymmetryProbe file, or null.</summary>
        internal string ProbeSymmetry;

        /// <summary>The auto-export request's "probe_bake" file (BakeProbe), or null.</summary>
        internal string ProbeBake;

        /// <summary>The batch export running now, or null.</summary>
        internal CardBatch Batch { get; private set; }

        internal ExportOptions CurrentOptions()
        {
            return new ExportOptions
            {
                AllOutfits = AllOutfits.Value,
                AllVariations = AllVariations.Value,
                Physics = !DisablePhysics.Value,
                EnabledShapeKeys = EnabledShapeKeys.Value,
                CurrentPose = CurrentPose.Value,
            };
        }

        internal string Folder()
        {
            return string.IsNullOrEmpty(OutputFolder.Value) ? Path.Combine(Paths.GameRootPath, "KKBP Exports") : OutputFolder.Value;
        }

        /// <summary>Where the batch export's folder browser opens.</summary>
        internal string StartingCardFolder()
        {
            return string.IsNullOrEmpty(CardFolder.Value) ? Path.Combine(Path.Combine(Paths.GameRootPath, "UserData"), "chara") : CardFolder.Value;
        }

        /// <summary>
        /// Exports every card in <paramref name="cards"/>, one bundle each, by loading it into the maker and
        /// running <see cref="Export"/> with <paramref name="options"/>. A card that doesn't load or export is
        /// logged and skipped. When it ends, <paramref name="done"/> gets the batch. Like Export, it steps the
        /// coroutines it runs itself.
        /// </summary>
        internal IEnumerator ExportFolder(string cards, ExportOptions options, string folder, Action<CardBatch> done)
        {
            CardBatch batch;
            try
            {
                batch = new CardBatch(cards);
            }
            catch (Exception e)
            {
                Status = "Couldn't read " + cards + ": " + e.Message;
                Logger.LogError(Status);
                done(null);
                yield break;
            }
            Batch = batch;
            Logger.LogInfo("Batch export of " + batch.Count + " card(s) in " + cards);
            while (batch.Next())
            {
                string loadError = null;
                Logger.LogInfo(batch.Progress);
                Status = "Loading the card…";
                try
                {
                    Cards.Load(batch.Card);
                }
                catch (Exception e)
                {
                    loadError = e.Message;
                }
                if (loadError != null)
                {
                    Logger.LogWarning("Skipped " + batch.Card + ": " + loadError);
                    batch.Failed(loadError);
                    continue;
                }
                // As long as the auto-export waits for a loaded card to settle.
                yield return new WaitForSecondsRealtime(3f);
                BundleExport export = null;
                var run = Export(options, folder, (e, a) => export = e);
                while (run.MoveNext())
                {
                    yield return run.Current;
                }
                if (export != null && export.State == ExportState.Succeeded)
                {
                    batch.Succeeded(export.BundlePath);
                }
                else
                {
                    batch.Failed(Status);
                }
            }
            Status = batch.Summary + (batch.Count > 0 ? " (bundles in " + folder + ")" : "");
            Logger.LogInfo("Batch export: " + Status);
            foreach (var failure in batch.Failures)
            {
                Logger.LogWarning("Not exported: " + failure.Key + ": " + failure.Value);
            }
            Batch = null;
            done(batch);
        }

        /// <summary>
        /// Exports the maker's Character. It steps the Core's coroutine itself and passes on what it yields,
        /// so the IL2CPP coroutine wrapper is never handed a nested coroutine.
        /// </summary>
        internal IEnumerator Export(ExportOptions options, string folder, Action<BundleExport, SvsAdapter> done)
        {
            Exporting = true;
            Status = "Exporting…";
            SvsAdapter adapter = null;
            BundleExport export = null;
            try
            {
                Directory.CreateDirectory(folder);
                adapter = new SvsAdapter(CharacterCreation.HumanCustom.Instance.Human, options);
                adapter.ProbeSymmetryPath = ProbeSymmetry;
                adapter.ProbeBakePath = ProbeBake;
                export = new BundleExport(adapter, folder);
            }
            catch (Exception e)
            {
                Logger.LogError("The export couldn't start: " + e);
                Status = "Failed: " + e.Message;
                Exporting = false;
                done(null, adapter);
                yield break;
            }

            var run = export.Run();
            while (run.MoveNext())
            {
                yield return run.Current;
            }
            try
            {
                adapter.Restore();
            }
            catch (Exception e)
            {
                Logger.LogWarning("Couldn't put the Character back as it was: " + e.Message);
            }
            foreach (string warning in adapter.Warnings)
            {
                Logger.LogWarning(warning);
            }
            if (export.State == ExportState.Succeeded)
            {
                Status = "Exported to " + export.BundlePath;
                Logger.LogInfo(Status);
            }
            else
            {
                string where = export.FailedPass != null ? " in the " + export.FailedPass : "";
                Status = "Failed" + where + ": " + export.Error.Message;
                Logger.LogError("The export failed" + where + ". No Manifest was written. " + export.Error);
            }
            Exporting = false;
            done(export, adapter);
        }

        /// <summary>The plugin's MonoBehaviour: runs coroutines and draws the window.</summary>
        public sealed class Behaviour : MonoBehaviour
        {
            public Behaviour(System.IntPtr pointer) : base(pointer)
            {
            }

            private Window window;

            private void Start()
            {
                window = new Window(Instance);
                if (AutoExport.Requested)
                {
                    StartCoroutine(new AutoExport(Instance).Run().WrapToIl2Cpp());
                }
            }

            private void Update()
            {
                window.Update();
            }

            private void OnGUI()
            {
                window.Draw();
            }
        }
    }
}
