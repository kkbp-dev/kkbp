using System;
using System.Collections.Generic;
using System.IO;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// A batch export: every card directly in one folder, by file name, and what became of each.
    /// An adapter loads and exports the cards in turn; this keeps the list, the progress and the results.
    /// </summary>
    public sealed class CardBatch
    {
        private readonly List<string> cards;
        private int index = -1;
        private bool stopping;

        public CardBatch(string folder)
        {
            Folder = folder;
            cards = Cards(folder);
            Bundles = new List<string>();
            Failures = new List<KeyValuePair<string, string>>();
        }

        public string Folder { get; private set; }

        /// <summary>The bundle folders written, in card order.</summary>
        public List<string> Bundles { get; private set; }

        /// <summary>Each card that didn't export, with why.</summary>
        public List<KeyValuePair<string, string>> Failures { get; private set; }

        public int Count
        {
            get { return cards.Count; }
        }

        /// <summary>The card being exported now, or null before the first and after the last.</summary>
        public string Card
        {
            get { return index >= 0 && index < cards.Count ? cards[index] : null; }
        }

        public bool Stopped { get; private set; }

        /// <summary>Moves to the next card; false when there is none, or a stop was asked for.</summary>
        public bool Next()
        {
            if (stopping && index < cards.Count - 1)
            {
                Stopped = true;
            }
            if (Stopped || index >= cards.Count)
            {
                return false;
            }
            index++;
            return index < cards.Count;
        }

        /// <summary>Ends the batch once the current card is done.</summary>
        public void Stop()
        {
            stopping = true;
        }

        public void Succeeded(string bundle)
        {
            Bundles.Add(bundle);
        }

        public void Failed(string error)
        {
            Failures.Add(new KeyValuePair<string, string>(Card, error));
        }

        /// <summary>"Card 3 of 12: Chika.png".</summary>
        public string Progress
        {
            get { return "Card " + (index + 1) + " of " + cards.Count + ": " + Path.GetFileName(Card); }
        }

        /// <summary>"10 exported, 2 failed", and whether it was stopped.</summary>
        public string Summary
        {
            get
            {
                if (cards.Count == 0)
                {
                    return "No cards in " + Folder;
                }
                string text = Bundles.Count + " exported, " + Failures.Count + " failed";
                if (Stopped)
                {
                    text += ", stopped with " + (cards.Count - index - 1) + " left";
                }
                return text;
            }
        }

        /// <summary>
        /// Adds the auto-export result's "cards", "bundles" and "failures" ({ "card", "error" }) to
        /// <paramref name="result"/>. Returns null if every card exported, else why not.
        /// </summary>
        public string Report(JsonObject result)
        {
            var bundles = new JsonArray();
            bundles.AddRange(Bundles.ConvertAll(b => (object)b));
            var failures = new JsonArray();
            foreach (var failure in Failures)
            {
                failures.Add(new JsonObject().Add("card", failure.Key).Add("error", failure.Value));
            }
            result.Add("cards", (double)cards.Count).Add("bundles", bundles).Add("failures", failures);
            return cards.Count > 0 && Failures.Count == 0 && !Stopped ? null : Summary;
        }

        /// <summary>The .png files directly in <paramref name="folder"/>, by name, ignoring case.</summary>
        public static List<string> Cards(string folder)
        {
            var found = new List<string>();
            foreach (string file in Directory.GetFiles(folder))
            {
                if (string.Equals(Path.GetExtension(file), ".png", StringComparison.OrdinalIgnoreCase))
                {
                    found.Add(file);
                }
            }
            found.Sort((a, b) => string.Compare(Path.GetFileName(a), Path.GetFileName(b), StringComparison.OrdinalIgnoreCase));
            return found;
        }
    }

    /// <summary>
    /// The batch export's folder browser, without its drawing: the folder it is in, its subfolders and
    /// how many cards it holds. It never throws for a folder it can't read; it lists nothing there.
    /// </summary>
    public sealed class FolderBrowser
    {
        public FolderBrowser(string start)
        {
            Go(start);
        }

        public string Current { get; private set; }

        public List<string> Subfolders { get; private set; }

        public int CardCount { get; private set; }

        public bool CanGoUp
        {
            get { return Directory.GetParent(Current) != null; }
        }

        public void Up()
        {
            var parent = Directory.GetParent(Current);
            if (parent != null)
            {
                Go(parent.FullName);
            }
        }

        public void Enter(string subfolder)
        {
            Go(Path.Combine(Current, subfolder));
        }

        /// <summary>Goes to <paramref name="folder"/>, or to the nearest folder above it that exists.</summary>
        public void Go(string folder)
        {
            string path = Path.GetFullPath(folder);
            while (!Directory.Exists(path) && Directory.GetParent(path) != null)
            {
                path = Directory.GetParent(path).FullName;
            }
            Current = path;
            Subfolders = new List<string>();
            CardCount = 0;
            try
            {
                foreach (string dir in Directory.GetDirectories(path))
                {
                    Subfolders.Add(Path.GetFileName(dir));
                }
                Subfolders.Sort(StringComparer.OrdinalIgnoreCase);
                CardCount = CardBatch.Cards(path).Count;
            }
            catch (Exception e)
            {
                if (!(e is IOException || e is UnauthorizedAccessException))
                {
                    throw;
                }
            }
        }
    }

    /// <summary>What a card file holds besides its picture.</summary>
    public static class CardFile
    {
        /// <summary>The PNG image at the start of a card file: every chunk up to and including IEND, or null.</summary>
        public static byte[] PngPart(byte[] card)
        {
            int end = PngLength(card);
            if (end < 0)
            {
                return null;
            }
            var png = new byte[end];
            Array.Copy(card, png, end);
            return png;
        }

        /// <summary>
        /// The game's mark at the start of the card data after the picture, such as "【SVChara】" or
        /// "【KoiKatuClothes】" for an outfit card, or null if there is none (a plain picture).
        /// </summary>
        public static string Mark(byte[] card)
        {
            int pos = PngLength(card);
            if (pos < 0 || pos + 5 > card.Length)
            {
                return null;
            }
            pos += 4;  // the product number
            int length = 0, shift = 0;
            while (pos < card.Length && shift < 35)  // .NET's 7-bit encoded string length
            {
                byte b = card[pos++];
                length |= (b & 0x7F) << shift;
                shift += 7;
                if ((b & 0x80) == 0)
                {
                    break;
                }
            }
            if (length <= 0 || length > 64 || pos + length > card.Length)
            {
                return null;
            }
            return System.Text.Encoding.UTF8.GetString(card, pos, length);
        }

        private static int PngLength(byte[] card)
        {
            int pos = 8;
            while (pos + 12 <= card.Length)
            {
                int length = (card[pos] << 24) | (card[pos + 1] << 16) | (card[pos + 2] << 8) | card[pos + 3];
                bool end = card[pos + 4] == 'I' && card[pos + 5] == 'E' && card[pos + 6] == 'N' && card[pos + 7] == 'D';
                if (length < 0)
                {
                    return -1;
                }
                pos += 12 + length;
                if (end && pos <= card.Length)
                {
                    return pos;
                }
            }
            return -1;
        }
    }
}
