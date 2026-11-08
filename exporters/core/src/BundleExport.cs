using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace KKBP.Exporter.Core
{
    public enum ExportState
    {
        NotStarted,
        Running,
        Succeeded,
        Failed,
    }

    /// <summary>
    /// One export of one Character. Run it as a Unity coroutine: it asks the adapter to capture each
    /// Pass in order, passing on whatever the adapter yields while it waits for game frames, and writes
    /// the Manifest last. If anything fails, it stops and no Manifest is written.
    /// </summary>
    public sealed class BundleExport
    {
        private readonly IGameAdapter adapter;
        private readonly IBundleFiles files;
        private readonly Func<DateTime> utcNow;

        public BundleExport(IGameAdapter adapter, string outputDirectory)
            : this(adapter, new DiskBundleFiles(outputDirectory), () => DateTime.UtcNow)
        {
        }

        public BundleExport(IGameAdapter adapter, IBundleFiles files, Func<DateTime> utcNow)
        {
            if (adapter == null)
            {
                throw new ArgumentNullException("adapter");
            }
            if (files == null)
            {
                throw new ArgumentNullException("files");
            }
            this.adapter = adapter;
            this.files = files;
            this.utcNow = utcNow ?? (() => DateTime.UtcNow);
        }

        public ExportState State { get; private set; }

        /// <summary>The bundle folder, once it has been created.</summary>
        public string BundlePath { get; private set; }

        /// <summary>Why the export failed, or null.</summary>
        public Exception Error { get; private set; }

        /// <summary>The Pass that was running when the export failed, or null.</summary>
        public PassInfo FailedPass { get; private set; }

        public IEnumerator Run()
        {
            if (State != ExportState.NotStarted)
            {
                throw new InvalidOperationException("An export can only run once.");
            }
            State = ExportState.Running;

            DateTime exportedAt = DateTime.MinValue;
            CharacterInfo character = null;
            IList<PassInfo> passes = null;
            BundleWriter writer = null;
            try
            {
                exportedAt = utcNow().ToUniversalTime();
                character = adapter.Character;
                if (character == null || character.Name == null)
                {
                    throw new ExportException("The adapter gave no Character name.");
                }
                passes = adapter.Passes();
                CheckPasses(passes);
                BundlePath = files.Open(FolderName(exportedAt, character.Name));
                writer = new BundleWriter(files, adapter.ExporterName + " " + adapter.ExporterVersion);
            }
            catch (Exception e)
            {
                Fail(null, e);
            }
            if (State == ExportState.Failed)
            {
                yield break;
            }

            foreach (var pass in passes)
            {
                var sink = new PassSink(pass);
                var stack = new Stack<IEnumerator>();
                try
                {
                    IEnumerator capture = adapter.Capture(pass, sink);
                    if (capture != null)
                    {
                        stack.Push(capture);
                    }
                }
                catch (Exception e)
                {
                    Fail(pass, e);
                }

                while (State == ExportState.Running && stack.Count > 0)
                {
                    object current = null;
                    bool moved = false;
                    try
                    {
                        moved = stack.Peek().MoveNext();
                        if (moved)
                        {
                            current = stack.Peek().Current;
                        }
                    }
                    catch (Exception e)
                    {
                        Fail(pass, e);
                        break;
                    }
                    if (!moved)
                    {
                        stack.Pop();
                    }
                    else if (current is IEnumerator)
                    {
                        // Run nested waits here rather than handing Unity a nested coroutine.
                        stack.Push((IEnumerator)current);
                    }
                    else
                    {
                        yield return current;
                    }
                }

                if (State == ExportState.Running)
                {
                    try
                    {
                        writer.WritePass(sink);
                    }
                    catch (Exception e)
                    {
                        Fail(pass, e);
                    }
                }
                if (State == ExportState.Failed)
                {
                    yield break;
                }
            }

            try
            {
                writer.Finish(adapter, character, exportedAt);
                State = ExportState.Succeeded;
            }
            catch (Exception e)
            {
                Fail(null, e);
            }
        }

        /// <summary>Runs the whole export without a game loop, discarding what the adapter yields.</summary>
        public void RunToEnd()
        {
            var run = Run();
            while (run.MoveNext())
            {
            }
        }

        private void Fail(PassInfo pass, Exception e)
        {
            State = ExportState.Failed;
            FailedPass = pass;
            Error = e;
        }

        private static void CheckPasses(IList<PassInfo> passes)
        {
            if (passes == null || passes.Count == 0 || passes[0] == null || passes[0].Kind != PassKind.Body)
            {
                throw new ExportException("The first Pass must be the Body Pass.");
            }
            var outfits = new HashSet<int>();
            for (int i = 1; i < passes.Count; i++)
            {
                if (passes[i] == null || passes[i].Kind != PassKind.Outfit || !outfits.Add(passes[i].Outfit.Value))
                {
                    throw new ExportException("After the Body Pass, each Pass must be a different Outfit.");
                }
            }
        }

        /// <summary>
        /// The bundle folder name: the export time and the Character name, with characters that
        /// Windows doesn't allow in file names replaced, so the name is the same on every platform.
        /// </summary>
        public static string FolderName(DateTime exportedAtUtc, string characterName)
        {
            var sb = new StringBuilder();
            foreach (char c in characterName)
            {
                sb.Append(c < 0x20 || "<>:\"/\\|?*".IndexOf(c) >= 0 ? '_' : c);
            }
            string name = sb.ToString().Trim().TrimEnd('.');
            if (name.Length == 0)
            {
                name = "Character";
            }
            return exportedAtUtc.ToString("yyyyMMddHHmmss", CultureInfo.InvariantCulture) + "_" + name;
        }
    }
}
