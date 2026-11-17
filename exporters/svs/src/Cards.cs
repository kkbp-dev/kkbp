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
            ShowLoadedOutfit(human);
            human.Reload();
        }

        /// <summary>
        /// Points the Outfit the Character wears at the loaded card's. The game dresses the Character from
        /// its own copy of the current Outfit (coorde.nowCoordinate), which loading the card's data doesn't
        /// replace: without this every card in a batch kept the clothes of the one loaded before it.
        /// Keeps the Outfit the maker shows, or the first if the new card has fewer Outfits.
        /// </summary>
        private static void ShowLoadedOutfit(Human human)
        {
            var outfits = human.data.Coordinates;
            int outfit = human.fileStatus.coordinateType;
            if (outfit < 0 || outfit >= outfits.Length)
            {
                outfit = 0;
                human.coorde.ChangeCoordinateType((ChaFileDefine.CoordinateType)outfit);
            }
            human.coorde.SetNowCoordinate(outfits[outfit]);
        }
    }
}
