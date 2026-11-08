using System.IO;

namespace KKBP.Exporter.Core
{
    /// <summary>Where a bundle's files go. The Core writes only through this.</summary>
    public interface IBundleFiles
    {
        /// <summary>Creates the bundle folder and returns its path. Adds _2, _3, … if the name is taken.</summary>
        string Open(string folderName);

        /// <summary>Writes one file, given by its path relative to the bundle root with forward slashes.</summary>
        void Write(string relativePath, byte[] contents);
    }

    public sealed class DiskBundleFiles : IBundleFiles
    {
        private readonly string outputDirectory;
        private string root;

        public DiskBundleFiles(string outputDirectory)
        {
            this.outputDirectory = outputDirectory;
        }

        public string Open(string folderName)
        {
            Directory.CreateDirectory(outputDirectory);
            string path = Path.Combine(outputDirectory, folderName);
            for (int n = 2; Directory.Exists(path) || File.Exists(path); n++)
            {
                path = Path.Combine(outputDirectory, folderName + "_" + n);
            }
            Directory.CreateDirectory(path);
            root = path;
            return path;
        }

        public void Write(string relativePath, byte[] contents)
        {
            string path = Path.Combine(root, relativePath.Replace('/', Path.DirectorySeparatorChar));
            string directory = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(directory))
            {
                Directory.CreateDirectory(directory);
            }
            File.WriteAllBytes(path, contents);
        }
    }
}
