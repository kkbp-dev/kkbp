using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Json.Schema;

namespace KKBP.Exporter.Core.Tests.Support
{
    /// <summary>The JSON Schemas in contract/schema/, loaded once.</summary>
    public static class ContractSchemas
    {
        public const string BaseUri = "https://schemas.kkbp.invalid/1.1/";

        private static readonly Lazy<Dictionary<string, JsonSchema>> Schemas = new Lazy<Dictionary<string, JsonSchema>>(Load);

        /// <summary>Validates a JSON document against a schema file, such as "manifest.schema.json".</summary>
        public static List<string> Validate(string schemaFile, string json)
        {
            var schema = Schemas.Value[schemaFile];
            using (var doc = JsonDocument.Parse(json))
            {
                var results = schema.Evaluate(doc.RootElement, new EvaluationOptions { OutputFormat = OutputFormat.List });
                if (results.IsValid)
                {
                    return new List<string>();
                }
                var errors = new List<string>();
                foreach (var detail in results.Details ?? new List<EvaluationResults>())
                {
                    if (detail.Errors == null)
                    {
                        continue;
                    }
                    foreach (var error in detail.Errors)
                    {
                        errors.Add(schemaFile + " " + detail.InstanceLocation + ": " + error.Value);
                    }
                }
                if (errors.Count == 0)
                {
                    errors.Add(schemaFile + ": invalid");
                }
                return errors;
            }
        }

        public static List<string> ValidateFile(string schemaFile, string path)
        {
            return Validate(schemaFile, File.ReadAllText(path));
        }

        /// <summary>A closed set's members, from contract/schema/sets/&lt;name&gt;.schema.json.</summary>
        public static string[] SetMembers(string set)
        {
            return ReadSet(set, "enum");
        }

        /// <summary>A closed set's x-unique list.</summary>
        public static string[] SetUnique(string set)
        {
            return ReadSet(set, "x-unique");
        }

        private static string[] ReadSet(string set, string property)
        {
            using (var doc = JsonDocument.Parse(File.ReadAllText(Repo.Path("contract/schema/sets/" + set + ".schema.json"))))
            {
                return doc.RootElement.GetProperty(property).EnumerateArray().Select(e => e.GetString()).ToArray();
            }
        }

        private static Dictionary<string, JsonSchema> Load()
        {
            var options = new BuildOptions { SchemaRegistry = new SchemaRegistry() };
            var result = new Dictionary<string, JsonSchema>();
            // Sets first, then the shared definitions, then the schemas that refer to them.
            var files = Directory.GetFiles(Repo.Path("contract/schema/sets"), "*.schema.json").OrderBy(f => f, StringComparer.Ordinal).ToList();
            files.Add(Repo.Path("contract/schema/common.schema.json"));
            files.AddRange(Directory.GetFiles(Repo.Path("contract/schema"), "*.schema.json")
                .Where(f => !f.EndsWith("common.schema.json", StringComparison.Ordinal))
                .OrderBy(f => f, StringComparer.Ordinal));
            foreach (var file in files)
            {
                var schema = JsonSchema.FromText(File.ReadAllText(file), options);
                options.SchemaRegistry.Register(schema);
                string name = System.IO.Path.GetFileName(file);
                result[file.Contains(System.IO.Path.DirectorySeparatorChar + "sets" + System.IO.Path.DirectorySeparatorChar) ? "sets/" + name : name] = schema;
            }
            return result;
        }
    }
}
