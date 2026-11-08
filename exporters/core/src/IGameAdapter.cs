using System.Collections;
using System.Collections.Generic;

namespace KKBP.Exporter.Core
{
    /// <summary>
    /// The part of an exporter that reads one Game's Character and hands its data to the Core.
    /// </summary>
    public interface IGameAdapter
    {
        /// <summary>The Game id: KK, KKS or SVS.</summary>
        string Game { get; }

        string ExporterName { get; }
        string ExporterVersion { get; }

        ExportOptions Options { get; }

        /// <summary>Read once, before the first Pass.</summary>
        CharacterInfo Character { get; }

        /// <summary>The Body Pass first, then one Pass per Outfit to export.</summary>
        IList<PassInfo> Passes();

        /// <summary>
        /// Captures one Pass into the sink. It may yield to wait for game frames, for example after
        /// switching Outfits; the Core passes every yielded value on to its own caller unchanged.
        /// Yielding an IEnumerator runs it to completion first.
        /// </summary>
        IEnumerator Capture(PassInfo pass, PassSink sink);
    }

    /// <summary>Collects what an adapter captures for one Pass.</summary>
    public sealed class PassSink
    {
        public readonly PassInfo Pass;
        public readonly List<BoneData> Bones = new List<BoneData>();
        public readonly List<MeshData> Meshes = new List<MeshData>();
        public readonly List<MaterialData> Materials = new List<MaterialData>();
        public readonly List<PhysicsChain> Chains = new List<PhysicsChain>();
        public readonly List<PhysicsCollider> Colliders = new List<PhysicsCollider>();

        /// <summary>Outfit Passes only: textures this Outfit puts on materials the Body Pass captured.</summary>
        public readonly List<BodyTexture> BodyTextures = new List<BodyTexture>();

        /// <summary>Game Extension data for this Pass's data file.</summary>
        public JsonObject Extensions;

        internal PassSink(PassInfo pass)
        {
            Pass = pass;
        }
    }
}
