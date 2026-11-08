using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace KKBP.Exporter.Core
{
    /// <summary>
    /// Assigns Ids for one kind (mesh, material or bone) within one bundle (ADR 0005).
    /// </summary>
    public sealed class IdAllocator
    {
        public const int MaxLength = 63;

        private readonly string prefix;
        private readonly Dictionary<string, string> byKey = new Dictionary<string, string>();
        private readonly HashSet<string> used = new HashSet<string>();

        /// <param name="prefix">Used when a name simplifies to nothing: mesh, mat or bone.</param>
        public IdAllocator(string prefix)
        {
            this.prefix = prefix;
        }

        /// <summary>The Id for a key, assigning one from the game name the first time the key is seen.</summary>
        public string Get(string key, string name)
        {
            if (key == null)
            {
                throw new ExportException("An object with no key was given an Id (name '" + name + "').");
            }
            string id;
            if (byKey.TryGetValue(key, out id))
            {
                return id;
            }
            string stem = Simplify(name ?? "");
            if (stem.Length == 0)
            {
                stem = prefix;
            }
            id = Fit(stem, "");
            for (int n = 2; used.Contains(id); n++)
            {
                id = Fit(stem, "_" + n.ToString(CultureInfo.InvariantCulture));
            }
            used.Add(id);
            byKey.Add(key, id);
            return id;
        }

        /// <summary>The Id already assigned to a key.</summary>
        public bool TryFind(string key, out string id)
        {
            return byKey.TryGetValue(key, out id);
        }

        /// <summary>Keeps A–Z a–z 0–9 _ . -, turns anything else into _, collapses runs of _ and trims them.</summary>
        public static string Simplify(string name)
        {
            var sb = new StringBuilder(name.Length);
            foreach (char c in name)
            {
                bool keep = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '.' || c == '-';
                char next = keep ? c : '_';
                if (next == '_' && (sb.Length == 0 || sb[sb.Length - 1] == '_'))
                {
                    continue;
                }
                sb.Append(next);
            }
            return TrimUnderscores(sb.ToString());
        }

        private static string Fit(string stem, string suffix)
        {
            int room = MaxLength - suffix.Length;
            if (stem.Length > room)
            {
                stem = TrimUnderscores(stem.Substring(0, room));
            }
            return stem + suffix;
        }

        private static string TrimUnderscores(string s)
        {
            return s.Trim('_');
        }
    }
}
