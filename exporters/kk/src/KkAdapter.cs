using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>The Game Adapter for KK and KKS: reads the maker's Character and hands it to the Core.</summary>
    internal sealed class KkAdapter : IGameAdapter
    {
        /// <summary>
        /// Mosaic and male-part stand-ins, never part of a Character's look, and the ChaAlphaMask plugin's
        /// o_Mask quad (shader AlphaMaskMultiply), which only renders its body masks.
        /// </summary>
        private static readonly HashSet<string> NeverExported = new HashSet<string>
        {
            "o_mnpa", "o_mnpb", "o_dankon", "o_gomu", "o_dan_f", "n_tang_silhouette", "o_shadowcaster", "o_Mask", "o_Mask(Clone)",
        };

        /// <summary>
        /// Meshes the game hides until an expression needs them. They are captured even when inactive,
        /// hidden inside the head, with a key that shows them (ADR 0010).
        /// </summary>
        private static readonly Dictionary<string, KeyValuePair<ExpressionCategory, string>> HiddenUntilShown = new Dictionary<string, KeyValuePair<ExpressionCategory, string>>
        {
            { "cf_O_namida_L", new KeyValuePair<ExpressionCategory, string>(ExpressionCategory.Tears, "Tears big") },
            { "cf_O_namida_M", new KeyValuePair<ExpressionCategory, string>(ExpressionCategory.Tears, "Tears med") },
            { "cf_O_namida_S", new KeyValuePair<ExpressionCategory, string>(ExpressionCategory.Tears, "Tears small") },
            { "cf_O_gag_eye_00", new KeyValuePair<ExpressionCategory, string>(ExpressionCategory.Gag, "Gag eye 00") },
            { "cf_O_gag_eye_01", new KeyValuePair<ExpressionCategory, string>(ExpressionCategory.Gag, "Gag eye 01") },
            { "cf_O_gag_eye_02", new KeyValuePair<ExpressionCategory, string>(ExpressionCategory.Gag, "Gag eye 02") },
        };

        private readonly ChaControl cha;
        private readonly ExpressionTable table;
        private readonly int startOutfit;
        private readonly Materials materials = new Materials();
        private Rig rig;
        private Meshes meshes;
        private Physics physics;
        private readonly Dictionary<Renderer, MaterialRole> roles = new Dictionary<Renderer, MaterialRole>();
        private float animationSpeed = 1;
        private FaceState startFace;

        public KkAdapter(ChaControl cha, ExportOptions options)
        {
            this.cha = cha;
            Options = options;
            using (var stream = typeof(KkAdapter).Assembly.GetManifestResourceStream("KKBP.Expressions.json"))
            using (var reader = new StreamReader(stream))
            {
                table = ExpressionTable.Parse(reader.ReadToEnd());
            }
            startOutfit = cha.fileStatus.coordinateType;
            Character = new Core.CharacterInfo { Name = cha.chaFile.parameter.fullname, CardPng = Card() };
        }

        public string Game
        {
            get { return Kks.Game; }
        }

        public string ExporterName
        {
            get { return "KKBP Exporter for " + Kks.Game; }
        }

        public string ExporterVersion
        {
            get { return Exporter.ExporterVersion.Value; }
        }

        public ExportOptions Options { get; private set; }

        public Core.CharacterInfo Character { get; private set; }

        /// <summary>Messages about things left out of the bundle, for the log.</summary>
        public readonly List<string> Warnings = new List<string>();

        /// <summary>Where SymmetryProbe writes the Body Pass's skinning, or null for no probe.</summary>
        public string ProbeSymmetryPath;

        public IList<PassInfo> Passes()
        {
            var passes = new List<PassInfo> { PassInfo.Body() };
            if (Options.AllOutfits)
            {
                for (int i = 0; i < cha.chaFile.coordinate.Length; i++)
                {
                    passes.Add(PassInfo.ForOutfit(i));
                }
            }
            else
            {
                passes.Add(PassInfo.ForOutfit(startOutfit));
            }
            return passes;
        }

        public IEnumerator Capture(PassInfo pass, PassSink sink)
        {
            if (pass.Kind == PassKind.Body)
            {
                yield return Prepare();
                rig = new Rig(cha.transform, cha.objTop.transform);
                meshes = new Meshes(rig, !Options.CurrentPose);
                physics = new Physics(rig);
                rig.RecordBody();
                CaptureBody(sink);
                yield break;
            }

            int outfit = pass.Outfit.Value;
            if (cha.fileStatus.coordinateType != outfit)
            {
                cha.ChangeCoordinateTypeAndReload((ChaFileDefine.CoordinateType)outfit);
                yield return null;
                yield return null;
                yield return Settle();
            }
            CaptureOutfit(sink);
        }

        /// <summary>Puts things back the way the export found them.</summary>
        public void Restore()
        {
            if (Options.CurrentPose && cha.animBody != null)
            {
                cha.animBody.speed = animationSpeed;
            }
            if (startFace != null)
            {
                startFace.Apply(cha);
            }
            if (cha.fileStatus.coordinateType != startOutfit)
            {
                cha.ChangeCoordinateTypeAndReload((ChaFileDefine.CoordinateType)startOutfit);
            }
        }

        // Preparing the scene -------------------------------------------------------------------------

        private IEnumerator Prepare()
        {
            startFace = new FaceState(cha);
            cha.ChangeEyesBlinkFlag(false);
            cha.ChangeLookEyesTarget(1, null, 0f);
            cha.ChangeLookNeckPtn(3);
            cha.ChangeEyesPtn(0, false);
            cha.ChangeEyebrowPtn(0, false);
            cha.ChangeMouthPtn(0, false);
            cha.ChangeEyesOpenMax(1f);
            cha.ChangeEyebrowOpenMax(1f);
            cha.ChangeMouthOpenMax(1f);
            cha.ReleaseHitObject();
            if (Options.CurrentPose)
            {
                animationSpeed = cha.animBody.speed;
                cha.animBody.speed = 0;
            }
            else
            {
                Kks.PlayTPose();
            }
            yield return null;
            yield return null;
            yield return Settle();
        }

        /// <summary>With physics, lets dynamic bones settle for two seconds; without, resets them.</summary>
        private IEnumerator Settle()
        {
            if (Options.Physics)
            {
                // Real time: the maker can stop game time, and dynamic bones settle on frames anyway.
                yield return new WaitForSecondsRealtime(2f);
                yield return new WaitForEndOfFrame();
            }
            else
            {
                cha.resetDynamicBoneAll = true;
                yield return null;
                yield return null;
            }
        }

        /// <summary>
        /// The face settings Prepare changes, as the maker had them (issue 22). They live in the card's
        /// status: without putting them back, the next export starts from the exported face, and on a fixed
        /// mouth ChangeMouthOpenMax also sets the mouth's FixedRate, so a closed mouth stays open.
        /// ChangeMouthFixed comes after ChangeMouthOpenMax and sets FixedRate from both. The eye-look target
        /// is rebuilt from the saved status (given a transform, ChangeLookEyesTarget doesn't save the rate,
        /// angle or range), then the maker's own target transform goes back.
        /// </summary>
        private sealed class FaceState
        {
            private readonly int eyesPtn, eyebrowPtn, mouthPtn, lookEyesPtn, lookNeckPtn;
            private readonly float eyesOpenMax, eyebrowOpenMax, mouthOpenMax;
            private readonly bool blink, mouthFixed;
            private readonly int lookType;
            private readonly float lookRate, lookAngle, lookRange;
            private readonly Transform lookTarget;

            public FaceState(ChaControl cha)
            {
                eyesPtn = cha.GetEyesPtn();
                eyebrowPtn = cha.GetEyebrowPtn();
                mouthPtn = cha.GetMouthPtn();
                lookEyesPtn = cha.GetLookEyesPtn();
                lookNeckPtn = cha.GetLookNeckPtn();
                eyesOpenMax = cha.GetEyesOpenMax();
                eyebrowOpenMax = cha.GetEyebrowOpenMax();
                mouthOpenMax = cha.GetMouthOpenMax();
                mouthFixed = cha.GetMouthFixed();
                blink = cha.GetEyesBlinkFlag();
                var status = cha.fileStatus;
                lookType = status.eyesTargetType;
                lookRate = status.eyesTargetRate;
                lookAngle = status.eyesTargetAngle;
                lookRange = status.eyesTargetRange;
                lookTarget = cha.eyeLookCtrl != null ? cha.eyeLookCtrl.target : null;
            }

            public void Apply(ChaControl cha)
            {
                cha.ChangeEyesPtn(eyesPtn, false);
                cha.ChangeEyebrowPtn(eyebrowPtn, false);
                cha.ChangeMouthPtn(mouthPtn, false);
                cha.ChangeLookEyesPtn(lookEyesPtn);
                cha.ChangeLookEyesTarget(lookType, null, lookRate, lookAngle, lookRange);
                if (cha.eyeLookCtrl != null && lookTarget != null)
                {
                    cha.eyeLookCtrl.target = lookTarget;
                }
                cha.ChangeLookNeckPtn(lookNeckPtn);
                cha.ChangeEyesBlinkFlag(blink);
                cha.ChangeEyesOpenMax(eyesOpenMax);
                cha.ChangeEyebrowOpenMax(eyebrowOpenMax);
                cha.ChangeMouthOpenMax(mouthOpenMax);
                cha.ChangeMouthFixed(mouthFixed);
            }
        }

        private byte[] Card()
        {
            using (var stream = new MemoryStream())
            {
                cha.chaFile.SaveCharaFile(stream, true);
                var bytes = stream.ToArray();
                if (bytes.Length < 8 || bytes[0] != 0x89 || bytes[1] != 0x50)
                {
                    Warnings.Add("The card has no image, so the bundle has no card.png.");
                    return null;
                }
                return bytes;
            }
        }

        // Body Pass -----------------------------------------------------------------------------------

        private void CaptureBody(PassSink sink)
        {
            FindRoles();
            sink.Bones.AddRange(rig.BeginPass(sink.Pass));
            var captured = new List<CapturedMesh>();
            var seen = new HashSet<Renderer>();
            foreach (var renderer in Renderers())
            {
                if (rig.OwnerOf(renderer.transform) == Owner.Body)
                {
                    Keep(captured, AddRenderer(sink, renderer));
                    seen.Add(renderer);
                }
            }
            foreach (var renderer in cha.objHead.GetComponentsInChildren<Renderer>(true))
            {
                if (HiddenUntilShown.ContainsKey(renderer.name) && !seen.Contains(renderer) && rig.OwnerOf(renderer.transform) == Owner.Body)
                {
                    Keep(captured, AddRenderer(sink, renderer));
                }
            }
            var riggedTongue = RiggedTongue();
            if (riggedTongue != null && !seen.Contains(riggedTongue))
            {
                Keep(captured, AddRenderer(sink, riggedTongue));
            }
            new Expressions(cha, table, materials, captured, Warnings).Bake(sink);
            new Creates(cha, materials, Warnings).AttachBody(sink, captured);
            HideUntilShown(sink);
            BakeLightAndDark(sink, captured.FindAll(m => m.Renderer != riggedTongue));
            physics.Capture(cha.objTop.transform, sink, t => rig.OwnerOf(t) == Owner.Body);
            if (ProbeSymmetryPath != null)
            {
                SymmetryProbe.Write(ProbeSymmetryPath, captured);
            }
        }

        /// <summary>
        /// The body's own tongue (n_tang/o_tang), weighted to the cf_j_tang_* chain. The game shows it in
        /// place of the head's tongue only when fileStatus.tongueState is 1, so it is usually inactive. It is
        /// captured anyway, without expressions or a light and dark bake: the importer takes its tongue-bone
        /// weights for the head's tongue and drops it.
        /// </summary>
        private Renderer RiggedTongue()
        {
            var obj = cha.GetReferenceInfo(ChaReference.RefObjKey.S_TongueB);
            if (obj == null)
            {
                return null;
            }
            var renderer = obj.GetComponent<Renderer>();
            if (renderer == null || !(renderer is SkinnedMeshRenderer) || NeverExported.Contains(obj.name) || rig.OwnerOf(renderer.transform) != Owner.Body)
            {
                return null;
            }
            return renderer;
        }

        /// <summary>Adds the baked light and dark Variants to every captured material but the tears' and gag eyes'.</summary>
        private void BakeLightAndDark(PassSink sink, List<CapturedMesh> captured)
        {
            using (var bake = new Bake(cha))
            {
                foreach (var m in captured)
                {
                    if (HiddenUntilShown.ContainsKey(m.Data.Name))
                    {
                        continue;
                    }
                    bool skin = m.Renderer == cha.rendBody || m.Renderer == cha.rendFace;
                    for (int slot = 0; slot < m.Slots.Length; slot++)
                    {
                        string key = Meshes.MaterialKey(m.Data.Key, slot);
                        var data = m.Slots[slot] != null ? sink.Materials.Find(x => x.Key == key) : null;
                        if (data == null)
                        {
                            continue;
                        }
                        try
                        {
                            bake.Add(m.Renderer, m.Slots[slot], slot, data, skin, m.Renderer == cha.rendFace);
                        }
                        catch (Exception e)
                        {
                            Warnings.Add("Couldn't bake light and dark textures for " + data.Name + ": " + e.Message);
                        }
                    }
                }
            }
        }

        /// <summary>Pushes the tear and gag-eye meshes inside the head and gives each its showing key (ADR 0010).</summary>
        private void HideUntilShown(PassSink sink)
        {
            var face = cha.rendFace != null ? sink.Meshes.Find(m => m.Name == cha.rendFace.name) : null;
            if (face == null)
            {
                Warnings.Add("No face mesh, so the tear and gag-eye meshes aren't hidden.");
                return;
            }
            var offset = HiddenBasis.Offset(face.Positions);
            var middle = HiddenBasis.Middle(face.Positions);
            foreach (var mesh in sink.Meshes)
            {
                KeyValuePair<ExpressionCategory, string> show;
                if (HiddenUntilShown.TryGetValue(mesh.Name, out show))
                {
                    HiddenBasis.Apply(mesh, offset, middle, show.Key, show.Value);
                }
            }
        }

        // Outfit Passes -------------------------------------------------------------------------------

        private void CaptureOutfit(PassSink sink)
        {
            FindRoles();
            var bones = rig.BeginPass(sink.Pass);
            sink.Bones.AddRange(bones);
            if (rig.Missing.Count > 0)
            {
                Warnings.Add(sink.Pass + ": " + rig.Missing.Count + " body bones went away when the Outfit changed (" + string.Join(", ", rig.Missing.GetRange(0, Math.Min(5, rig.Missing.Count)).ToArray()) + "); they keep their Body Pass pose.");
            }
            var captured = new List<CapturedMesh>();
            foreach (var renderer in Renderers())
            {
                var owner = rig.OwnerOf(renderer.transform);
                if (owner != Owner.Body)
                {
                    Keep(captured, AddRenderer(sink, renderer, owner == Owner.Hair ? MaterialRole.Hair : (MaterialRole?)null));
                }
            }
            if (Options.AllVariations)
            {
                foreach (var renderer in AlternateRenderers())
                {
                    var m = AddRenderer(sink, renderer);
                    if (m != null)
                    {
                        m.Data.Alternate = true;
                        captured.Add(m);
                    }
                }
            }
            new Expressions(cha, table, materials, captured, Warnings).BakeOwnShapeKeys();
            new Creates(cha, materials, Warnings).AttachClothes(sink, captured);
            BakeLightAndDark(sink, captured);
            physics.Capture(cha.objTop.transform, sink, t => rig.OwnerOf(t) != Owner.Body);
            AddBodyTextures(sink);
            BoneRules.MarkUnweightedHelpers(Rig.OutfitBones(bones), BoneRules.WeightedBones(sink.Meshes), BoneRules.PhysicsBones(sink.Chains, sink.Colliders));
        }

        // Renderers -----------------------------------------------------------------------------------

        /// <summary>The renderers to capture, in walk order: enabled ones on active objects.</summary>
        private IEnumerable<Renderer> Renderers()
        {
            foreach (var t in Rig.Walk(cha.objTop.transform))
            {
                // Highlight_* renderers are SliderHighlight's maker-only overlays, not part of the Character.
                if (NeverExported.Contains(t.name) || t.name.StartsWith("Highlight_", StringComparison.Ordinal) || Rig.IsHit(t))
                {
                    continue;
                }
                var renderer = t.GetComponent<Renderer>();
                if (renderer != null && renderer.enabled && (renderer is SkinnedMeshRenderer || renderer is MeshRenderer))
                {
                    yield return renderer;
                }
            }
        }

        /// <summary>
        /// Clothes shown only half off. The game keeps them under its "NUGE" reference objects, which are
        /// inactive while the clothes are fully on, so the normal walk doesn't find them.
        /// </summary>
        private IEnumerable<Renderer> AlternateRenderers()
        {
            var seen = new HashSet<Renderer>();
            foreach (ChaReference.RefObjKey key in Enum.GetValues(typeof(ChaReference.RefObjKey)))
            {
                if (key.ToString().IndexOf("NUGE", StringComparison.OrdinalIgnoreCase) < 0)
                {
                    continue;
                }
                var obj = cha.GetReferenceInfo(key);
                if (obj == null || obj.activeInHierarchy)
                {
                    continue;
                }
                foreach (var renderer in obj.GetComponentsInChildren<Renderer>(true))
                {
                    if ((renderer is SkinnedMeshRenderer || renderer is MeshRenderer) && seen.Add(renderer) && rig.OwnerOf(renderer.transform) != Owner.Body)
                    {
                        yield return renderer;
                    }
                }
            }
        }

        private static void Keep(List<CapturedMesh> captured, CapturedMesh mesh)
        {
            if (mesh != null)
            {
                captured.Add(mesh);
            }
        }

        private CapturedMesh AddRenderer(PassSink sink, Renderer renderer, MaterialRole? roleForAll = null)
        {
            string key = rig.ObjectKey(renderer.transform);
            var slots = Slots(renderer);
            var mesh = meshes.Capture(renderer, slots, key, Options.EnabledShapeKeys);
            if (mesh == null)
            {
                Warnings.Add("Left out " + renderer.name + ": " + meshes.Skipped + ".");
                return null;
            }
            MaterialRole role;
            bool hasRole = roles.TryGetValue(renderer, out role);
            for (int slot = 0; slot < slots.Length; slot++)
            {
                if (slots[slot] == null)
                {
                    continue;
                }
                MaterialRole? slotRole = roleForAll;
                if (hasRole && (slot == 0 || !ContractNames.IsUnique(role)))
                {
                    slotRole = role;
                }
                if (hasRole && slot == 1 && role == MaterialRole.EyelineUpper)
                {
                    slotRole = MaterialRole.EyelineShadow;
                }
                bool body = renderer == cha.rendBody && slot == 0;
                if (body)
                {
                    bodyMaterialKey = Meshes.MaterialKey(key, slot);
                }
                sink.Materials.Add(materials.Capture(slots[slot], Meshes.MaterialKey(key, slot), slotRole, body ? OutfitBodySlots : null));
            }
            sink.Meshes.Add(mesh);
            return new CapturedMesh { Renderer = renderer, Data = mesh, Source = Meshes.SourceMesh(renderer), Slots = slots, Skin = meshes.Skin, Weights = meshes.SkinWeights };
        }

        /// <summary>
        /// A renderer's materials. A gag-eye mesh has none until a gag pattern gives it one, so it gets the
        /// game's gag-eye material for its slot.
        /// </summary>
        private Material[] Slots(Renderer renderer)
        {
            var slots = renderer.sharedMaterials;
            if (slots.Length > 0 && slots[0] != null)
            {
                return slots;
            }
            for (int i = 0; i < GagNames.Length; i++)
            {
                if (renderer.name == GagNames[i] && cha.matGag != null && i < cha.matGag.Length && cha.matGag[i] != null)
                {
                    return new[] { cha.matGag[i] };
                }
            }
            return slots;
        }

        private static readonly string[] GagNames = { "cf_O_gag_eye_00", "cf_O_gag_eye_01", "cf_O_gag_eye_02" };

        /// <summary>
        /// Slots of the body material that the Outfit fills: the alpha mask hides the skin under the
        /// clothes. The Body Pass leaves them out and each Outfit Pass writes its own.
        /// </summary>
        private static readonly HashSet<string> OutfitBodySlots = new HashSet<string> { "_AlphaMask" };

        private string bodyMaterialKey;

        private void AddBodyTextures(PassSink sink)
        {
            var material = cha.rendBody != null ? cha.rendBody.sharedMaterial : null;
            if (material == null || bodyMaterialKey == null)
            {
                return;
            }
            foreach (string raw in OutfitBodySlots)
            {
                var texture = material.HasProperty(raw) ? material.GetTexture(raw) : null;
                if (texture != null)
                {
                    sink.BodyTextures.Add(new BodyTexture
                    {
                        MaterialKey = bodyMaterialKey,
                        Texture = materials.Texture(raw, texture, material.GetTextureOffset(raw), material.GetTextureScale(raw), null),
                    });
                }
            }
        }

        /// <summary>Material Roles come from the renderers the game itself keeps track of.</summary>
        private void FindRoles()
        {
            roles.Clear();
            Set(cha.rendBody, MaterialRole.Body);
            Set(cha.rendFace, MaterialRole.Face);
            Set(cha.rendEyebrow, MaterialRole.Eyebrow);
            Set(cha.rendEyelineUp, MaterialRole.EyelineUpper);
            Set(cha.rendEyelineDown, MaterialRole.EyelineLower);
            Set(cha.rendNose, MaterialRole.NoseLine);
            if (cha.rendEye != null && cha.rendEye.Length == 2)
            {
                Set(cha.rendEye[0], MaterialRole.EyeL);
                Set(cha.rendEye[1], MaterialRole.EyeR);
            }
            if (cha.rendEyeW != null)
            {
                foreach (var r in cha.rendEyeW)
                {
                    Set(r, MaterialRole.EyeWhite);
                }
            }
            foreach (var key in new[] { ChaReference.RefObjKey.N_Gag00, ChaReference.RefObjKey.N_Gag01, ChaReference.RefObjKey.N_Gag02 })
            {
                SetObject(cha.GetReferenceInfo(key), MaterialRole.GagEyes);
            }
            SetObject(cha.GetReferenceInfo(ChaReference.RefObjKey.ObjDoubleTooth), MaterialRole.Teeth);
            SetObject(cha.GetReferenceInfo(ChaReference.RefObjKey.S_TongueB), MaterialRole.Tongue);
            // The game keeps no field for these, so they are found by name.
            foreach (var t in cha.objHead.GetComponentsInChildren<Transform>(true))
            {
                switch (t.name)
                {
                    case "cf_O_tooth":
                        SetObject(t.gameObject, MaterialRole.Teeth);
                        break;
                    case "o_tang":
                        SetObject(t.gameObject, MaterialRole.Tongue);
                        break;
                    case "cf_O_namida_L":
                    case "cf_O_namida_M":
                    case "cf_O_namida_S":
                        SetObject(t.gameObject, MaterialRole.Tears);
                        break;
                }
            }
        }

        private void Set(Renderer renderer, MaterialRole role)
        {
            if (renderer != null)
            {
                roles[renderer] = role;
            }
        }

        private void SetObject(GameObject obj, MaterialRole role)
        {
            if (obj != null)
            {
                Set(obj.GetComponent<Renderer>(), role);
            }
        }
    }
}
