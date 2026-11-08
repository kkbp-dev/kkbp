using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace KKBP.Exporter.Core
{
    /// <summary>
    /// A JSON object that keeps its keys in insertion order, so output is deterministic.
    /// Values may be null, bool, int, long, float, double, string, JsonObject or JsonArray.
    /// </summary>
    public sealed class JsonObject
    {
        private readonly List<KeyValuePair<string, object>> members = new List<KeyValuePair<string, object>>();

        public int Count
        {
            get { return members.Count; }
        }

        public IEnumerable<KeyValuePair<string, object>> Members
        {
            get { return members; }
        }

        /// <summary>Adds a member and returns this object, so calls can be chained.</summary>
        public JsonObject Add(string key, object value)
        {
            if (key == null)
            {
                throw new ArgumentNullException("key");
            }
            for (int i = 0; i < members.Count; i++)
            {
                if (members[i].Key == key)
                {
                    throw new ArgumentException("Duplicate JSON key: " + key);
                }
            }
            members.Add(new KeyValuePair<string, object>(key, value));
            return this;
        }

        public bool TryGet(string key, out object value)
        {
            for (int i = 0; i < members.Count; i++)
            {
                if (members[i].Key == key)
                {
                    value = members[i].Value;
                    return true;
                }
            }
            value = null;
            return false;
        }

        public object this[string key]
        {
            get
            {
                object value;
                if (!TryGet(key, out value))
                {
                    throw new KeyNotFoundException("Missing JSON key: " + key);
                }
                return value;
            }
        }
    }

    public sealed class JsonArray : List<object>
    {
        public JsonArray()
        {
        }

        public JsonArray(IEnumerable<object> items) : base(items)
        {
        }
    }

    /// <summary>
    /// Writes JSON the same way on every PC locale. Floats use the shortest form that round-trips;
    /// NaN and infinities are rejected because JSON has no way to write them.
    /// </summary>
    public static class JsonWriter
    {
        private static readonly UTF8Encoding Utf8 = new UTF8Encoding(false, true);

        public static byte[] ToUtf8(object value, bool indented)
        {
            return Utf8.GetBytes(Write(value, indented));
        }

        public static string Write(object value, bool indented)
        {
            var sb = new StringBuilder();
            WriteValue(sb, value, indented, 0);
            if (indented)
            {
                sb.Append('\n');
            }
            return sb.ToString();
        }

        private static void WriteValue(StringBuilder sb, object value, bool indented, int depth)
        {
            if (value == null)
            {
                sb.Append("null");
            }
            else if (value is string)
            {
                WriteString(sb, (string)value);
            }
            else if (value is bool)
            {
                sb.Append((bool)value ? "true" : "false");
            }
            else if (value is int)
            {
                sb.Append(((int)value).ToString(CultureInfo.InvariantCulture));
            }
            else if (value is long)
            {
                sb.Append(((long)value).ToString(CultureInfo.InvariantCulture));
            }
            else if (value is float)
            {
                sb.Append(FormatFloat((float)value));
            }
            else if (value is double)
            {
                sb.Append(FormatDouble((double)value));
            }
            else if (value is JsonObject)
            {
                WriteObject(sb, (JsonObject)value, indented, depth);
            }
            else if (value is JsonArray)
            {
                WriteArray(sb, (JsonArray)value, indented, depth);
            }
            else
            {
                throw new ArgumentException("Cannot write a " + value.GetType().Name + " as JSON.");
            }
        }

        private static void WriteObject(StringBuilder sb, JsonObject obj, bool indented, int depth)
        {
            if (obj.Count == 0)
            {
                sb.Append("{}");
                return;
            }
            sb.Append('{');
            bool first = true;
            foreach (var member in obj.Members)
            {
                if (!first)
                {
                    sb.Append(',');
                }
                first = false;
                NewLine(sb, indented, depth + 1);
                WriteString(sb, member.Key);
                sb.Append(indented ? ": " : ":");
                WriteValue(sb, member.Value, indented, depth + 1);
            }
            NewLine(sb, indented, depth);
            sb.Append('}');
        }

        private static void WriteArray(StringBuilder sb, JsonArray array, bool indented, int depth)
        {
            if (array.Count == 0)
            {
                sb.Append("[]");
                return;
            }
            // Short arrays of numbers (vectors, colours) stay on one line.
            bool inline = !indented || IsNumberTuple(array);
            sb.Append('[');
            for (int i = 0; i < array.Count; i++)
            {
                if (i > 0)
                {
                    sb.Append(inline && indented ? ", " : ",");
                }
                if (!inline)
                {
                    NewLine(sb, true, depth + 1);
                }
                WriteValue(sb, array[i], indented, depth + 1);
            }
            if (!inline)
            {
                NewLine(sb, true, depth);
            }
            sb.Append(']');
        }

        private static bool IsNumberTuple(JsonArray array)
        {
            if (array.Count > 16)
            {
                return false;
            }
            foreach (var item in array)
            {
                if (!(item is float || item is double || item is int || item is long))
                {
                    return false;
                }
            }
            return true;
        }

        private static void NewLine(StringBuilder sb, bool indented, int depth)
        {
            if (!indented)
            {
                return;
            }
            sb.Append('\n');
            sb.Append(' ', depth * 2);
        }

        public static string FormatFloat(float value)
        {
            if (float.IsNaN(value) || float.IsInfinity(value))
            {
                throw new ExportException("JSON cannot hold the number " + value.ToString(CultureInfo.InvariantCulture) + ".");
            }
            return value.ToString("R", CultureInfo.InvariantCulture);
        }

        public static string FormatDouble(double value)
        {
            if (double.IsNaN(value) || double.IsInfinity(value))
            {
                throw new ExportException("JSON cannot hold the number " + value.ToString(CultureInfo.InvariantCulture) + ".");
            }
            return value.ToString("R", CultureInfo.InvariantCulture);
        }

        private static void WriteString(StringBuilder sb, string s)
        {
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\b': sb.Append("\\b"); break;
                    case '\f': sb.Append("\\f"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20)
                        {
                            sb.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
                        }
                        else
                        {
                            sb.Append(c);
                        }
                        break;
                }
            }
            sb.Append('"');
        }
    }

    /// <summary>
    /// A small JSON reader, used only for the data files embedded in the exporters
    /// (the expression tables). Numbers are read as doubles.
    /// </summary>
    public sealed class JsonReader
    {
        private readonly string text;
        private int pos;

        private JsonReader(string text)
        {
            this.text = text;
        }

        public static object Parse(string text)
        {
            if (text == null)
            {
                throw new ArgumentNullException("text");
            }
            var reader = new JsonReader(text);
            if (reader.text.Length > 0 && reader.text[0] == '﻿')
            {
                reader.pos = 1;
            }
            object value = reader.ReadValue();
            reader.SkipWhitespace();
            if (reader.pos != reader.text.Length)
            {
                throw reader.Error("Unexpected text after the JSON value");
            }
            return value;
        }

        private object ReadValue()
        {
            SkipWhitespace();
            if (pos >= text.Length)
            {
                throw Error("Unexpected end of JSON");
            }
            char c = text[pos];
            switch (c)
            {
                case '{': return ReadObject();
                case '[': return ReadArray();
                case '"': return ReadString();
                case 't': Expect("true"); return true;
                case 'f': Expect("false"); return false;
                case 'n': Expect("null"); return null;
                default:
                    if (c == '-' || (c >= '0' && c <= '9'))
                    {
                        return ReadNumber();
                    }
                    throw Error("Unexpected character '" + c + "'");
            }
        }

        private JsonObject ReadObject()
        {
            var obj = new JsonObject();
            pos++;
            SkipWhitespace();
            if (Peek() == '}')
            {
                pos++;
                return obj;
            }
            while (true)
            {
                SkipWhitespace();
                if (Peek() != '"')
                {
                    throw Error("Expected a string key");
                }
                string key = ReadString();
                SkipWhitespace();
                if (Peek() != ':')
                {
                    throw Error("Expected ':'");
                }
                pos++;
                try
                {
                    obj.Add(key, ReadValue());
                }
                catch (ArgumentException e)
                {
                    throw Error(e.Message);
                }
                SkipWhitespace();
                char c = Peek();
                pos++;
                if (c == '}')
                {
                    return obj;
                }
                if (c != ',')
                {
                    throw Error("Expected ',' or '}'");
                }
            }
        }

        private JsonArray ReadArray()
        {
            var array = new JsonArray();
            pos++;
            SkipWhitespace();
            if (Peek() == ']')
            {
                pos++;
                return array;
            }
            while (true)
            {
                array.Add(ReadValue());
                SkipWhitespace();
                char c = Peek();
                pos++;
                if (c == ']')
                {
                    return array;
                }
                if (c != ',')
                {
                    throw Error("Expected ',' or ']'");
                }
            }
        }

        private string ReadString()
        {
            var sb = new StringBuilder();
            pos++;
            while (true)
            {
                if (pos >= text.Length)
                {
                    throw Error("Unterminated string");
                }
                char c = text[pos++];
                if (c == '"')
                {
                    return sb.ToString();
                }
                if (c < 0x20)
                {
                    throw Error("Control character in string");
                }
                if (c != '\\')
                {
                    sb.Append(c);
                    continue;
                }
                if (pos >= text.Length)
                {
                    throw Error("Unterminated escape");
                }
                char e = text[pos++];
                switch (e)
                {
                    case '"': sb.Append('"'); break;
                    case '\\': sb.Append('\\'); break;
                    case '/': sb.Append('/'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'n': sb.Append('\n'); break;
                    case 'r': sb.Append('\r'); break;
                    case 't': sb.Append('\t'); break;
                    case 'u':
                        if (pos + 4 > text.Length)
                        {
                            throw Error("Short \\u escape");
                        }
                        int code;
                        if (!int.TryParse(text.Substring(pos, 4), NumberStyles.AllowHexSpecifier, CultureInfo.InvariantCulture, out code))
                        {
                            throw Error("Bad \\u escape");
                        }
                        sb.Append((char)code);
                        pos += 4;
                        break;
                    default:
                        throw Error("Unknown escape '\\" + e + "'");
                }
            }
        }

        private double ReadNumber()
        {
            int start = pos;
            if (Peek() == '-')
            {
                pos++;
            }
            while (pos < text.Length && "0123456789.eE+-".IndexOf(text[pos]) >= 0)
            {
                pos++;
            }
            double value;
            if (!double.TryParse(text.Substring(start, pos - start), NumberStyles.Float, CultureInfo.InvariantCulture, out value))
            {
                pos = start;
                throw Error("Bad number");
            }
            return value;
        }

        private void Expect(string word)
        {
            if (string.CompareOrdinal(text, pos, word, 0, word.Length) != 0)
            {
                throw Error("Expected '" + word + "'");
            }
            pos += word.Length;
        }

        private char Peek()
        {
            return pos < text.Length ? text[pos] : '\0';
        }

        private void SkipWhitespace()
        {
            while (pos < text.Length && (text[pos] == ' ' || text[pos] == '\t' || text[pos] == '\n' || text[pos] == '\r'))
            {
                pos++;
            }
        }

        private FormatException Error(string message)
        {
            return new FormatException(message + " at character " + pos + ".");
        }
    }
}
