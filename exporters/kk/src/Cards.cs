using System.IO;
using ChaCustom;
using KKAPI.Maker;
using KKBP.Exporter.Core.AdapterKit;

namespace KKBP.Exporter
{
    /// <summary>Loading a card into the maker, for the auto-export and the batch export.</summary>
    internal static class Cards
    {
        /// <summary>
        /// Loads a character card into the maker, as the maker's own Load does. Throws for a file that
        /// isn't one of the game's character cards, or that the game rejects.
        /// </summary>
        public static void Load(string card)
        {
            byte[] bytes = File.ReadAllBytes(card);
            string mark = CardFile.Mark(bytes);
            if (System.Array.IndexOf(Kks.CardMarks, mark) < 0)
            {
                throw new IOException(Path.GetFileName(card) + " isn't a " + Kks.Game + " character card (" + (mark ?? "no card data") + ")");
            }
            var cha = MakerAPI.GetCharacterControl();
            // LoadFileLimited always returns false; the game reports a bad card through the error code.
            cha.chaFile.LoadFileLimited(card, cha.sex, true, true, true, true, true);
            int code = cha.chaFile.GetLastErrorCode();
            if (code != 0)
            {
                throw new IOException("the game rejected " + card + " (error " + code + ")");
            }
            // KK's LoadFileLimited doesn't keep the card's picture, and the exported card needs it. Always
            // from this card: in a batch the last card's picture would still be there.
            cha.chaFile.pngData = CardFile.PngPart(bytes) ?? cha.chaFile.pngData;
            cha.ChangeCoordinateType(true);
            cha.Reload(false, false, false, false);
            CustomBase.Instance.updateCustomUI = true;
        }

    }
}
