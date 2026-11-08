using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;

namespace KKBP.Exporter.Core.Tests.Support
{
    /// <summary>Runs the Khronos glTF Validator from contract/tools through Node.</summary>
    public static class GltfValidator
    {
        public sealed class Result
        {
            public int ExitCode;
            public string Report;
        }

        public static Result Run(IEnumerable<string> glbFiles)
        {
            string script = Repo.Path("contract/tools/validate-gltf.mjs");
            if (!Directory.Exists(Repo.Path("contract/tools/node_modules/gltf-validator")))
            {
                throw new InvalidOperationException("The glTF Validator isn't installed. Run `npm ci` in contract/tools, or scripts/check-core.sh.");
            }
            var start = new ProcessStartInfo(FindNode())
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                WorkingDirectory = Repo.Path("contract/tools"),
            };
            start.ArgumentList.Add(script);
            foreach (var file in glbFiles)
            {
                start.ArgumentList.Add(file);
            }
            using (var process = Process.Start(start))
            {
                var stdout = process.StandardOutput.ReadToEndAsync();
                string stderr = process.StandardError.ReadToEnd();
                process.WaitForExit();
                return new Result { ExitCode = process.ExitCode, Report = stdout.Result + stderr };
            }
        }

        private static string FindNode()
        {
            string fromEnv = Environment.GetEnvironmentVariable("KKBP_NODE");
            if (!string.IsNullOrEmpty(fromEnv))
            {
                return fromEnv;
            }
            string name = OperatingSystem.IsWindows() ? "node.exe" : "node";
            foreach (var dir in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator).Where(d => d.Length > 0))
            {
                string candidate = Path.Combine(dir, name);
                if (File.Exists(candidate))
                {
                    return candidate;
                }
            }
            throw new InvalidOperationException("Node.js wasn't found. Put node on PATH or set KKBP_NODE.");
        }
    }
}
