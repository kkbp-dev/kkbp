using System.Collections.Generic;

namespace KKBP.Exporter.Core.Tests.Support
{
    /// <summary>Writes to disk like DiskBundleFiles, and records the order files were written in.</summary>
    public sealed class RecordingFiles : IBundleFiles
    {
        private readonly DiskBundleFiles disk;

        public RecordingFiles(string outputDirectory)
        {
            disk = new DiskBundleFiles(outputDirectory);
        }

        public List<string> Written { get; } = new List<string>();

        public string Open(string folderName)
        {
            return disk.Open(folderName);
        }

        public void Write(string relativePath, byte[] contents)
        {
            Written.Add(relativePath);
            disk.Write(relativePath, contents);
        }
    }
}
