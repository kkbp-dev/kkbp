using BepInEx.Unity.IL2CPP.Utils.Collections;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// The exporter's IMGUI window in the maker, shown and hidden with Ctrl and the configured key
    /// (Ctrl+Tab by default, as in the legacy SVS exporter).
    /// Its options are the Export Options. Below the export button, the batch export picks a folder in a
    /// browser of its own and exports every card in it.
    /// </summary>
    internal sealed class Window
    {
        private readonly Plugin plugin;
        private Rect rect;
        private bool placed;
        private bool visible;
        private FolderBrowser browser;  // while picking the batch export's folder
        private Vector2 scroll;
        private static readonly GUILayoutOption[] None = new GUILayoutOption[0];

        public Window(Plugin plugin)
        {
            this.plugin = plugin;
        }

        public void Update()
        {
            bool held = Input.GetKey(KeyCode.LeftControl) || Input.GetKey(KeyCode.RightControl);
            if (held && Input.GetKeyDown(plugin.ShortcutKey.Value))
            {
                visible = !visible;
                Plugin.Logger.LogInfo("Exporter window " + (visible ? "shown" : "hidden"));
            }
        }

        public void Draw()
        {
            if (visible && CharacterCreation.HumanCustom.Initialized)
            {
                if (!placed)
                {
                    // Where the legacy KK exporter drew its options: just right of the middle, at the top.
                    rect = new Rect(Screen.width / 2f + 60f, 0f, 300f, 0f);
                    placed = true;
                }
                rect = GUILayout.Window(0x4B4B4250, rect, (GUI.WindowFunction)Contents, "KKBP Exporter " + ExporterVersion.Value, new GUILayoutOption[0]);
            }
        }

        private void Contents(int id)
        {
            bool busy = plugin.Exporting || plugin.Batch != null;
            GUI.enabled = !busy && browser == null;
            plugin.AllOutfits.Value = GUILayout.Toggle(plugin.AllOutfits.Value, "Export All Outfits", None);
            plugin.AllVariations.Value = GUILayout.Toggle(plugin.AllVariations.Value, "Export Variations", None);
            plugin.CurrentPose.Value = GUILayout.Toggle(plugin.CurrentPose.Value, "Freeze Current Pose", None);
            plugin.EnabledShapeKeys.Value = GUILayout.Toggle(plugin.EnabledShapeKeys.Value, "Freeze Shape Keys", None);
            plugin.DisablePhysics.Value = GUILayout.Toggle(plugin.DisablePhysics.Value, "Disable Physics", None);
            GUILayout.Space(6);
            if (GUILayout.Button("Export Model for KKBP", None))
            {
                plugin.Runner.StartCoroutine(plugin.Export(plugin.CurrentOptions(), plugin.Folder(), (export, adapter) => { }).WrapToIl2Cpp());
            }
            if (GUILayout.Button("Export every card in a folder…", None))
            {
                browser = new FolderBrowser(plugin.StartingCardFolder());
                scroll = Vector2.zero;
            }
            GUI.enabled = true;
            if (browser != null)
            {
                Browser();
            }
            if (plugin.Batch != null && GUILayout.Button("Stop after this card", None))
            {
                plugin.Batch.Stop();
            }
            if (!string.IsNullOrEmpty(plugin.Status))
            {
                GUILayout.Label(plugin.Status, None);
            }
            GUI.DragWindow();
        }

        private void Browser()
        {
            GUILayout.Space(6);
            GUILayout.Label(browser.Current, None);
            GUI.enabled = browser.CanGoUp;
            if (GUILayout.Button("Up", None))
            {
                browser.Up();
            }
            GUI.enabled = true;
            scroll = GUILayout.BeginScrollView(scroll, new[] { GUILayout.Height(160f) });
            string enter = null;
            foreach (string folder in browser.Subfolders)
            {
                if (GUILayout.Button(folder, None))
                {
                    enter = folder;
                }
            }
            GUILayout.EndScrollView();
            if (enter != null)
            {
                browser.Enter(enter);
                scroll = Vector2.zero;
            }
            GUILayout.Label(browser.CardCount + " card(s) here. Each one replaces the Character in the maker.", None);
            GUILayout.BeginHorizontal(None);
            if (GUILayout.Button("Cancel", None))
            {
                browser = null;
            }
            GUI.enabled = browser != null && browser.CardCount > 0;
            if (GUILayout.Button("Export them", None))
            {
                plugin.CardFolder.Value = browser.Current;
                plugin.Runner.StartCoroutine(plugin.ExportFolder(browser.Current, plugin.CurrentOptions(), plugin.Folder(), batch => { }).WrapToIl2Cpp());
                browser = null;
            }
            GUI.enabled = true;
            GUILayout.EndHorizontal();
        }
    }
}
