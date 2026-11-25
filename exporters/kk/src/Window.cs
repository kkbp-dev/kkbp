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
        private const float Width = 300f;
        private readonly Plugin plugin;
        private Rect rect;
        private bool placed;
        private bool fit;  // shrink the window to its contents in the next Layout event
        private bool wasBatching;
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
                rect = new Rect(Screen.width / 2f + 60f, 0f, Width, 0f);
                placed = true;
            }
            // GUILayout.Window grows a window to fit its contents but never shrinks it. When something leaves
            // the window (the folder browser, or the Stop button once a batch export ends), it goes back to its
            // original size and grows to fit from there. Only once, and only in a Layout event: resizing it
            // every frame, or in the click's own event, makes it flash.
            if (wasBatching && plugin.Batch == null)
            {
                fit = true;
            }
            wasBatching = plugin.Batch != null;
            if (fit && Event.current.type == EventType.Layout)
            {
                rect.width = Width;
                rect.height = 0f;
                fit = false;
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
            // The batch's progress has a line of its own: Status changes with each card's export.
            if (plugin.Batch != null && plugin.Batch.Card != null)
            {
                GUILayout.Label(plugin.Batch.Progress);
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
                fit = true;
            }
            GUI.enabled = browser != null && browser.CardCount > 0;
            if (GUILayout.Button("Export them"))
            {
                plugin.CardFolder.Value = browser.Current;
                plugin.StartCoroutine(plugin.ExportFolder(browser.Current, plugin.CurrentOptions(), plugin.Folder(), batch => { }));
                browser = null;
                fit = true;
            }
            GUI.enabled = true;
            GUILayout.EndHorizontal();
        }
    }
}
