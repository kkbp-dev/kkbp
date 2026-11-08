using System;
using System.IO;

namespace KKBP.Exporter.Core.Tests.Support
{
    /// <summary>Paths inside the repository, found by walking up from the test assembly.</summary>
    public static class Repo
    {
        private static readonly Lazy<string> RootPath = new Lazy<string>(FindRoot);

        public static string Root
        {
            get { return RootPath.Value; }
        }

        public static string Path(string relative)
        {
            return System.IO.Path.Combine(Root, relative.Replace('/', System.IO.Path.DirectorySeparatorChar));
        }

        private static string FindRoot()
        {
            var dir = new DirectoryInfo(AppContext.BaseDirectory);
            while (dir != null)
            {
                if (Directory.Exists(System.IO.Path.Combine(dir.FullName, "contract", "schema")) && File.Exists(System.IO.Path.Combine(dir.FullName, "CONTEXT.md")))
                {
                    return dir.FullName;
                }
                dir = dir.Parent;
            }
            throw new InvalidOperationException("Could not find the repository root above " + AppContext.BaseDirectory);
        }
    }

    /// <summary>A temporary folder deleted when the test finishes.</summary>
    public sealed class TempDir : IDisposable
    {
        public TempDir()
        {
            Path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "kkbp-tests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(Path);
        }

        public string Path { get; }

        public void Dispose()
        {
            try
            {
                Directory.Delete(Path, true);
            }
            catch (IOException)
            {
            }
        }
    }
}
