using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using KKBP.Exporter.Core.Tests.Support;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    /// <summary>
    /// Checks real exports against the contract: the golden samples in contract/samples/, and any
    /// bundles named in KKBP_CHECK_BUNDLES (separated like PATH), such as a fresh game export.
    /// </summary>
    public class SampleBundleTests
    {
        public static IEnumerable<object[]> Bundles()
        {
            var bundles = new List<string>();
            string samples = Repo.Path("contract/samples");
            if (Directory.Exists(samples))
            {
                bundles.AddRange(Directory.GetDirectories(samples).OrderBy(d => d, StringComparer.Ordinal));
            }
            string extra = Environment.GetEnvironmentVariable("KKBP_CHECK_BUNDLES");
            if (!string.IsNullOrEmpty(extra))
            {
                bundles.AddRange(extra.Split(Path.PathSeparator).Where(p => p.Length > 0));
            }
            // A theory needs at least one row; an empty string stands for "nothing to check".
            if (bundles.Count == 0)
            {
                bundles.Add("");
            }
            return bundles.Select(b => new object[] { b });
        }

        [Theory]
        [MemberData(nameof(Bundles))]
        public void Bundle_passes_the_contract_and_the_glTF_Validator(string bundle)
        {
            if (bundle == "")
            {
                return;
            }
            Assert.True(Directory.Exists(bundle), "No bundle at " + bundle);
            var problems = ContractChecker.Check(bundle);
            Assert.True(problems.Count == 0, string.Join("\n", problems));
            var glbs = Directory.GetFiles(bundle, "*.glb", SearchOption.AllDirectories).OrderBy(p => p, StringComparer.Ordinal).ToList();
            var result = GltfValidator.Run(glbs);
            Assert.True(result.ExitCode == 0, result.Report);
        }
    }
}
