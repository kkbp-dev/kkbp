using System;
using System.Collections;
using System.IO;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using KKAPI.Maker;
using KKAPI.Maker.UI.Sidebar;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    [BepInPlugin(Guid, Name, ExporterVersion.Plugin)]
    [BepInDependency(KKAPI.KoikatuAPI.GUID)]
    public sealed class Plugin : BaseUnityPlugin
    {
        public const string Guid = "kkbp.exporter";
        public const string Name = "KKBP Exporter";

        internal static ManualLogSource Log;

        internal ConfigEntry<string> OutputFolder;
        internal ConfigEntry<string> CardFolder;
        internal ConfigEntry<bool> ShowWindow;
        internal ConfigEntry<bool> AllOutfits;
        internal ConfigEntry<bool> AllVariations;
        internal ConfigEntry<bool> CurrentPose;
        internal ConfigEntry<bool> EnabledShapeKeys;
        internal ConfigEntry<bool> DisablePhysics;

        private SidebarToggle sidebar;
        private Window window;

        /// <summary>True while an export runs; the window shows its progress.</summary>
        internal bool Exporting { get; private set; }

        internal string Status { get; private set; }

        /// <summary>The batch export running now, or null.</summary>
        internal CardBatch Batch { get; private set; }

        private void Awake()
        {
            Log = Logger;
            OutputFolder = Config.Bind("Export", "Output folder", "", "Where bundles are written. Empty means the 'KKBP Exports' folder in the game folder.");
            CardFolder = Config.Bind("Export", "Card folder", "", "The folder the batch export last exported. Empty means the game's UserData/chara folder.");
            ShowWindow = Config.Bind("Window", "Show in the maker", false, "Show the exporter window when the character maker opens.");
            // The option names are the legacy KK exporter's.
            AllOutfits = Config.Bind("Options", "Export All Outfits", false, "Export every Outfit, not only the current one.");
            AllVariations = Config.Bind("Options", "Export Variations", false, "Also export clothes shown only in the half-off clothing state.");
            CurrentPose = Config.Bind("Options", "Freeze Current Pose", false, "Keep the current pose instead of the T-pose.");
            EnabledShapeKeys = Config.Bind("Options", "Freeze Shape Keys", false, "Bake the shape keys enabled in the game into the meshes.");
            DisablePhysics = Config.Bind("Options", "Disable Physics", false, "Reset hair, skirts and breasts before capture instead of letting them settle for two seconds.");
            window = new Window(this);

            MakerAPI.MakerBaseLoaded += (sender, e) => sidebar = e.AddSidebarControl(new SidebarToggle("Show KKBP Exporter", ShowWindow.Value, this));
            MakerAPI.MakerExiting += (sender, e) => sidebar = null;
            Log.LogInfo(Name + " " + ExporterVersion.Value + " for " + Kks.Game + " loaded.");
        }

        private void Start()
        {
            if (AutoExport.Requested)
            {
                StartCoroutine(new AutoExport(this).Run());
            }
        }

        private void Update()
        {
            if (sidebar != null && sidebar.Value != ShowWindow.Value)
            {
                ShowWindow.Value = sidebar.Value;
            }
        }

        private void OnGUI()
        {
            if (ShowWindow.Value && MakerAPI.InsideAndLoaded)
            {
                window.Draw();
            }
        }

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
        /// logged and skipped. When it ends, <paramref name="done"/> gets the batch.
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
                Log.LogError(Status);
                done(null);
                yield break;
            }
            Batch = batch;
            Log.LogInfo("Batch export of " + batch.Count + " card(s) in " + cards);
            while (batch.Next())
            {
                string loadError = null;
                Log.LogInfo(batch.Progress);
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
                    Log.LogWarning("Skipped " + batch.Card + ": " + loadError);
                    batch.Failed(loadError);
                    continue;
                }
                // As long as the auto-export waits for a loaded card to settle.
                yield return new WaitForSecondsRealtime(3f);
                BundleExport export = null;
                yield return StartCoroutine(Export(options, folder, (e, a) => export = e));
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
            Log.LogInfo("Batch export: " + Status);
            foreach (var failure in batch.Failures)
            {
                Log.LogWarning("Not exported: " + failure.Key + ": " + failure.Value);
            }
            Batch = null;
            done(batch);
        }

        /// <summary>Exports the maker's Character. When it ends, <paramref name="done"/> gets the export.</summary>
        internal IEnumerator Export(ExportOptions options, string folder, Action<BundleExport, KkAdapter> done)
        {
            Exporting = true;
            Status = "Exporting…";
            KkAdapter adapter = null;
            BundleExport export = null;
            try
            {
                Directory.CreateDirectory(folder);
                adapter = new KkAdapter(MakerAPI.GetCharacterControl(), options);
                export = new BundleExport(adapter, folder);
            }
            catch (Exception e)
            {
                Log.LogError("The export couldn't start: " + e);
                Status = "Failed: " + e.Message;
                Exporting = false;
                done(null, adapter);
                yield break;
            }

            yield return StartCoroutine(export.Run());
            try
            {
                adapter.Restore();
            }
            catch (Exception e)
            {
                Log.LogWarning("Couldn't put the Character back as it was: " + e.Message);
            }
            foreach (string warning in adapter.Warnings)
            {
                Log.LogWarning(warning);
            }
            if (export.State == ExportState.Succeeded)
            {
                Status = "Exported to " + export.BundlePath;
                Log.LogInfo(Status);
            }
            else
            {
                string where = export.FailedPass != null ? " in the " + export.FailedPass : "";
                Status = "Failed" + where + ": " + export.Error.Message;
                Log.LogError("The export failed" + where + ". No Manifest was written. " + export.Error);
            }
            Exporting = false;
            done(export, adapter);
        }
    }
}
