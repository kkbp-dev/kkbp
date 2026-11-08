using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// The exporter's IMGUI window in the maker. Its options are the Export Options. Below the export
    /// button, the batch export picks a folder in a browser of its own and exports every card in it.
    /// </summary>
    internal sealed class Window
    {
        private readonly Plugin plugin;
        private Rect rect;
        private bool placed;
        private FolderBrowser browser;  // while picking the batch export's folder
        private Vector2 scroll;

        public Window(Plugin plugin)
        {
            this.plugin = plugin;
        }

        public void Draw()
        {
            if (!placed)
            {
                // Where the legacy KK exporter drew its options: just right of the middle, at the top.
                rect = new Rect(Screen.width / 2f + 60f, 0f, 300f, 0f);
                placed = true;
            }
            rect = GUILayout.Window(0x4B4B4250, rect, Contents, "KKBP Exporter " + ExporterVersion.Value);
        }

        private void Contents(int id)
        {
            bool busy = plugin.Exporting || plugin.Batch != null;
            GUI.enabled = !busy && browser == null;
            plugin.AllOutfits.Value = GUILayout.Toggle(plugin.AllOutfits.Value, "Export All Outfits");
            plugin.AllVariations.Value = GUILayout.Toggle(plugin.AllVariations.Value, "Export Variations");
            plugin.CurrentPose.Value = GUILayout.Toggle(plugin.CurrentPose.Value, "Freeze Current Pose");
            plugin.EnabledShapeKeys.Value = GUILayout.Toggle(plugin.EnabledShapeKeys.Value, "Freeze Shape Keys");
            plugin.DisablePhysics.Value = GUILayout.Toggle(plugin.DisablePhysics.Value, "Disable Physics");
            GUILayout.Space(6);
            if (GUILayout.Button("Export Model for KKBP"))
            {
                plugin.StartCoroutine(plugin.Export(plugin.CurrentOptions(), plugin.Folder(), (export, adapter) => { }));
            }
            if (GUILayout.Button("Export every card in a folder…"))
            {
                browser = new FolderBrowser(plugin.StartingCardFolder());
                scroll = Vector2.zero;
            }
            GUI.enabled = true;
            if (browser != null)
            {
                Browser();
            }
            if (plugin.Batch != null && GUILayout.Button("Stop after this card"))
            {
                plugin.Batch.Stop();
            }
            if (!string.IsNullOrEmpty(plugin.Status))
            {
                GUILayout.Label(plugin.Status);
            }
            GUI.DragWindow();
        }

        private void Browser()
        {
            GUILayout.Space(6);
            GUILayout.Label(browser.Current);
            GUI.enabled = browser.CanGoUp;
            if (GUILayout.Button("Up"))
            {
                browser.Up();
            }
            GUI.enabled = true;
            scroll = GUILayout.BeginScrollView(scroll, GUILayout.Height(160));
            string enter = null;
            foreach (string folder in browser.Subfolders)
            {
                if (GUILayout.Button(folder))
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
            GUILayout.Label(browser.CardCount + " card(s) here. Each one replaces the Character in the maker.");
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Cancel"))
            {
                browser = null;
            }
            GUI.enabled = browser != null && browser.CardCount > 0;
            if (GUILayout.Button("Export them"))
            {
                plugin.CardFolder.Value = browser.Current;
                plugin.StartCoroutine(plugin.ExportFolder(browser.Current, plugin.CurrentOptions(), plugin.Folder(), batch => { }));
                browser = null;
            }
            GUI.enabled = true;
            GUILayout.EndHorizontal();
        }
    }
}
