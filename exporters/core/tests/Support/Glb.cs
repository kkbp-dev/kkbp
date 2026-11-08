using System;
using System.IO;
using System.Text;
using System.Text.Json;

namespace KKBP.Exporter.Core.Tests.Support
{
    /// <summary>Reads the JSON chunk of a .glb file.</summary>
    public static class Glb
    {
        public static JsonDocument ReadJson(string path)
        {
            byte[] bytes = File.ReadAllBytes(path);
            if (BitConverter.ToUInt32(bytes, 0) != 0x46546C67 || BitConverter.ToUInt32(bytes, 4) != 2)
            {
                throw new InvalidDataException(path + " is not a glTF 2.0 binary.");
            }
            int length = (int)BitConverter.ToUInt32(bytes, 12);
            if (BitConverter.ToUInt32(bytes, 16) != 0x4E4F534A)
            {
                throw new InvalidDataException(path + " has no JSON chunk first.");
            }
            return JsonDocument.Parse(Encoding.UTF8.GetString(bytes, 20, length));
        }
    }
}
