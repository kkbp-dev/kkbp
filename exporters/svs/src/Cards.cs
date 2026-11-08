using System.IO;
using Character;
using CharacterCreation;
using KKBP.Exporter.Core.AdapterKit;

namespace KKBP.Exporter
{
    /// <summary>Loading a card into the maker, for the auto-export and the batch export.</summary>
    internal static class Cards
    {
        /// <summary>The mark SVS's character cards carry after their picture.</summary>
        public const string CharacterMark = "【SVChara】";

        /// <summary>
        /// Loads a character card into the maker. Throws for any other file: LoadFileLimited returns false
        /// even for a good card, so the card's own mark decides.
        /// </summary>
        public static void Load(string card)
        {
            byte[] bytes = File.ReadAllBytes(card);
            string mark = CardFile.Mark(bytes);
            if (mark != CharacterMark)
            {
                throw new IOException(Path.GetFileName(card) + " isn't an SVS character card (" + (mark ?? "no card data") + ")");
            }
            var human = HumanCustom.Instance.Human;
            if (!human.data.LoadFileLimited(card, HumanData.LoadLimited.Flags.All))
            {
                Plugin.Logger.LogInfo("LoadFileLimited returned false for " + card + ", as it does for good cards too");
            }
            // Keep the card's picture: the exported card needs it.
            var png = CardFile.PngPart(bytes);
            if (png != null)
            {
                human.data.SetPng(png);
            }
            human.Reload();
        }
    }
}
