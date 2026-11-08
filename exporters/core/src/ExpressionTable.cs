using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core
{
    /// <summary>Which of the game's pattern lists a pattern comes from.</summary>
    public enum ExpressionList
    {
        Eye,
        Eyebrow,
        Mouth,
    }

    public sealed class ExpressionPattern
    {
        public ExpressionList List;
        public int Index;
        public string GameName;
        public string Name;

        /// <summary>The name for the closed version, or null if the pattern has none.</summary>
        public string ClosedName;
    }

    public sealed class ExpressionRecipe
    {
        public string Name;
        public List<KeyValuePair<string, float>> Shapes = new List<KeyValuePair<string, float>>();
    }

    /// <summary>
    /// A Game's expression translation table, contract/expressions/&lt;game&gt;.json, which each exporter
    /// embeds when it's built (ADR 0004). Patterns are found by list and position, never by game name.
    /// </summary>
    public sealed class ExpressionTable
    {
        private readonly Dictionary<string, ExpressionPattern> patterns = new Dictionary<string, ExpressionPattern>();

        public string Game { get; private set; }
        public List<ExpressionRecipe> Recipes { get; private set; }

        private ExpressionTable()
        {
            Recipes = new List<ExpressionRecipe>();
        }

        /// <summary>The table's entry for a pattern, or null if the table doesn't name it.</summary>
        public ExpressionPattern Find(ExpressionList list, int index)
        {
            ExpressionPattern pattern;
            return patterns.TryGetValue(Key(list, index), out pattern) ? pattern : null;
        }

        public IEnumerable<ExpressionPattern> Patterns
        {
            get { return patterns.Values; }
        }

        public static ExpressionTable Parse(string json)
        {
            var root = JsonReader.Parse(json) as JsonObject;
            if (root == null)
            {
                throw new FormatException("An expression table must be a JSON object.");
            }
            var table = new ExpressionTable { Game = (string)root["game"] };
            foreach (JsonObject p in (JsonArray)root["patterns"])
            {
                object closed;
                p.TryGet("closed_name", out closed);
                var pattern = new ExpressionPattern
                {
                    List = ParseList((string)p["list"]),
                    Index = (int)(double)p["index"],
                    GameName = (string)p["game_name"],
                    Name = (string)p["name"],
                    ClosedName = (string)closed,
                };
                string key = Key(pattern.List, pattern.Index);
                if (table.patterns.ContainsKey(key))
                {
                    throw new FormatException("The expression table lists " + key + " twice.");
                }
                table.patterns.Add(key, pattern);
            }
            foreach (JsonObject r in (JsonArray)root["recipes"])
            {
                var recipe = new ExpressionRecipe { Name = (string)r["name"] };
                foreach (JsonObject s in (JsonArray)r["shapes"])
                {
                    recipe.Shapes.Add(new KeyValuePair<string, float>((string)s["shape"], (float)(double)s["weight"]));
                }
                table.Recipes.Add(recipe);
            }
            return table;
        }

        private static ExpressionList ParseList(string list)
        {
            switch (list)
            {
                case "eye": return ExpressionList.Eye;
                case "eyebrow": return ExpressionList.Eyebrow;
                case "mouth": return ExpressionList.Mouth;
                default: throw new FormatException("Unknown expression list '" + list + "'.");
            }
        }

        private static string Key(ExpressionList list, int index)
        {
            return list + ":" + index;
        }
    }
}
