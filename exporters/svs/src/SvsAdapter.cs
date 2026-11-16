using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using Character;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>The Game Adapter for SVS: reads the maker's Character and hands it to the Core.</summary>
    internal sealed class SvsAdapter : IGameAdapter
    {
        /// <summary>Mosaic and male-part stand-ins, never part of a Character's look.</summary>
        private static readonly HashSet<string> NeverExported = new HashSet<string>
        {
            "mnpa", "mnpb", "o_dankon", "o_gomu", "o_dan_f", "n_body_silhouette", "n_tang_silhouette", "o_body_shadow",
        };

        /// <summary>
        /// The shader of the hair outline shells (hair_*_line), never exported: the importer makes its own
        /// outlines. Legacy SVS left them out too.
        /// </summary>
        private const string HairOutlineShader = "LIF/lif_main_hair_outline";

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

        private readonly Human cha;
        private readonly ExpressionTable table;
        private readonly int startOutfit;
        private readonly Materials materials = new Materials();
        private Rig rig;
        private Meshes meshes;
        private Physics physics;
        private readonly Dictionary<int, MaterialRole> roles = new Dictionary<int, MaterialRole>();
        private float animationSpeed = 1;
        private FaceState startFace;

        public SvsAdapter(Human cha, ExportOptions options)
        {
            this.cha = cha;
            Options = options;
            using (var stream = typeof(SvsAdapter).Assembly.GetManifestResourceStream("KKBP.Expressions.json"))
            using (var reader = new StreamReader(stream))
            {
                table = ExpressionTable.Parse(reader.ReadToEnd());
            }
            startOutfit = cha.fileStatus.coordinateType;
            Character = new Core.CharacterInfo { Name = cha.fileParam.fullname, CardPng = Card() };
        }

        public string Game
        {
            get { return "SVS"; }
        }

        public string ExporterName
        {
            get { return "KKBP Exporter for SVS"; }
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
                for (int i = 0; i < cha.data.Coordinates.Length; i++)
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
                if (!Options.CurrentPose && !Svs.ArmsLevel(cha, true))
                {
                    throw new ExportException("The Character isn't in a T-pose: the arms aren't level.");
                }
                rig = new Rig(cha.transform, cha.objTop.transform);
                meshes = new Meshes(rig);
                physics = new Physics(rig);
                rig.RecordBody();
                CaptureBody(sink);
                yield break;
            }

            int outfit = pass.Outfit.Value;
            if (cha.fileStatus.coordinateType != outfit)
            {
                Svs.ChangeOutfit(cha, outfit);
                yield return null;
                yield return null;
                yield return Settle();
            }
            CaptureOutfit(sink);
        }

        /// <summary>Puts things back the way the export found them.</summary>
        public void Restore()
        {
            var animator = cha.body.animBody;
            if (animator != null)
            {
                animator.enabled = true;
                animator.speed = animationSpeed;
            }
            if (startFace != null)
            {
                startFace.Apply(cha);
            }
            if (cha.fileStatus.coordinateType != startOutfit)
            {
                Svs.ChangeOutfit(cha, startOutfit);
            }
        }

        // Preparing the scene -------------------------------------------------------------------------

        private IEnumerator Prepare()
        {
            var face = cha.face;
            startFace = new FaceState(cha);
            face.ChangeEyesBlinkFlag(false);
            face.ChangeLookEyesTarget(1, null, 0f);
            face.ChangeEyesPtn(0, false);
            face.ChangeEyebrowPtn(0, false);
            face.ChangeMouthPtn(0, false);
            face.ChangeEyesOpenMax(1f);
            face.ChangeEyebrowOpenMax(1f);
            face.ChangeMouthOpenMax(1f);
            animationSpeed = cha.body.animBody.speed;
            if (Options.CurrentPose)
            {
                cha.body.animBody.speed = 0;
            }
            else
            {
                Svs.PlayTPose(cha);
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
                cha.ResetClothAll();
                yield return null;
                yield return null;
            }
        }

        /// <summary>
        /// The face settings Prepare changes, as the maker had them. Without putting them back, the next
        /// export starts from the exported face (issue 22): on a fixed mouth, ChangeMouthOpenMax also sets
        /// the mouth's FixedRate, so the maker's closed mouth stays open, and the next card.png saves it so.
        /// The eye-look target is rebuilt from the saved status (given a transform, ChangeLookEyesTarget
        /// doesn't save the rate, angle or range), then the maker's own target transform goes back.
        /// </summary>
        private sealed class FaceState
        {
            private readonly int eyesPtn, eyebrowPtn, mouthPtn, lookEyesPtn;
            private readonly float eyesOpenMax, eyebrowOpenMax, mouthOpenMin, mouthOpenMax;
            private readonly float eyesFixedRate, eyebrowFixedRate, mouthFixedRate;
            private readonly bool blink, mouthFixed;
            private readonly int lookType;
            private readonly float lookRate, lookAngle, lookRange;
            private readonly Transform lookTarget;

            public FaceState(Human cha)
            {
                var face = cha.face;
                eyesPtn = face.GetEyesPtn();
                eyebrowPtn = face.GetEyebrowPtn();
                mouthPtn = face.GetMouthPtn();
                lookEyesPtn = face.GetLookEyesPtn();
                eyesOpenMax = face.GetEyesOpenMax();
                eyebrowOpenMax = face.GetEyebrowOpenMax();
                mouthOpenMin = face.GetMouthOpenMin();
                mouthOpenMax = face.GetMouthOpenMax();
                mouthFixed = face.GetMouthFixed();
                blink = face.GetEyesBlinkFlag();
                eyesFixedRate = face.eyesCtrl.FixedRate;
                eyebrowFixedRate = face.eyebrowCtrl.FixedRate;
                mouthFixedRate = face.mouthCtrl.FixedRate;
                var status = cha.fileStatus;
                lookType = status.eyesTargetType;
                lookRate = status.eyesTargetRate;
                lookAngle = status.eyesTargetAngle;
                lookRange = status.eyesTargetRange;
                lookTarget = face.eyeLookCtrl != null ? face.eyeLookCtrl.Target : null;
            }

            public void Apply(Human cha)
            {
                var face = cha.face;
                face.ChangeEyesPtn(eyesPtn, false);
                face.ChangeEyebrowPtn(eyebrowPtn, false);
                face.ChangeMouthPtn(mouthPtn, false);
                face.ChangeLookEyesPtn(lookEyesPtn);
                face.ChangeLookEyesTarget(lookType, null, lookRate, lookAngle, lookRange);
                if (face.eyeLookCtrl != null && lookTarget != null)
                {
                    face.eyeLookCtrl.Target = lookTarget;
                }
                face.ChangeEyesOpenMax(eyesOpenMax);
                face.ChangeEyebrowOpenMax(eyebrowOpenMax);
                face.ChangeMouthOpenMin(mouthOpenMin);
                face.ChangeMouthOpenMax(mouthOpenMax);
                face.ChangeMouthFixed(mouthFixed);
                face.ChangeEyesBlinkFlag(blink);
                // Last: the calls above can set these themselves.
                face.eyesCtrl.SetFixedRate(eyesFixedRate);
                face.eyebrowCtrl.SetFixedRate(eyebrowFixedRate);
                face.mouthCtrl.SetFixedRate(mouthFixedRate);
            }
        }

        private byte[] Card()
        {
            var bytes = Svs.Card(cha);
            if (bytes.Length < 8 || bytes[0] != 0x89 || bytes[1] != 0x50)
            {
                Warnings.Add("The card has no image, so the bundle has no card.png.");
                return null;
            }
            return bytes;
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
            foreach (var renderer in cha.face.objHead.GetComponentsInChildren<Renderer>(true))
            {
                if (HiddenUntilShown.ContainsKey(renderer.name) && !seen.Contains(renderer) && rig.OwnerOf(renderer.transform) == Owner.Body)
                {
                    Keep(captured, AddRenderer(sink, renderer));
                }
            }
            var riggedTongue = RiggedTongue();
            if (riggedTongue != null && !captured.Exists(m => Same(m.Renderer, riggedTongue)))
            {
                Keep(captured, AddRenderer(sink, riggedTongue));
            }
            new Expressions(cha, table, materials, captured, Warnings).Bake(sink);
            CloseGagSeams(sink);
            HideUntilShown(sink);
            // After the expressions: they find captured meshes by renderer, and each copy shares its eye's.
            var baked = captured.FindAll(m => !Same(m.Renderer, riggedTongue));
            baked.AddRange(AddEyeWhites(sink, captured));
            BakeLightAndDark(sink, baked);
            physics.Capture(cha.objTop.transform, sink, t => rig.OwnerOf(t) == Owner.Body);
            if (ProbeSymmetryPath != null)
            {
                SymmetryProbe.Write(ProbeSymmetryPath, captured);
            }
        }

        /// <summary>
        /// The body's own tongue (n_body/o_tang), weighted to the cf_j_tang_* chain. The game shows it in
        /// place of the head's tongue only in some tongue states, so it is usually inactive. It is captured
        /// anyway, without expressions or a light and dark bake: the importer takes its tongue-bone weights
        /// for the head's tongue and drops it.
        /// </summary>
        private Renderer RiggedTongue()
        {
            var renderer = cha.body.rendTongueBody;
            if (renderer == null || renderer.TryCast<SkinnedMeshRenderer>() == null || rig.OwnerOf(renderer.transform) != Owner.Body)
            {
                return null;
            }
            return renderer;
        }

        /// <summary>
        /// Bakes the face again without its eyeshadow (ADR 0046). The game draws the eyeshadow into the
        /// head's texture with the face's create material, so its colour is made clear there and the
        /// texture drawn again for the bake, then both are put back.
        /// </summary>
        private void BakeWithoutEyeshadow(Bake bake, Renderer renderer, Material source, int slot, MaterialData data)
        {
            var control = cha.face.customTexCtrlFace;
            var create = control != null ? control._matCreate : null;
            int texture = ChaShader.Face.CreateShader.sEyeshadowTextureID;
            int colorId = ChaShader.Face.CreateShader.sEyeshadowColorID;
            if (create == null || !create.HasProperty(texture) || !create.HasProperty(colorId) || create.GetTexture(texture) == null)
            {
                return;
            }
            var color = create.GetColor(colorId);
            if (color.a <= 0)
            {
                return;
            }
            try
            {
                control.SetColor(colorId, new UnityEngine.Color(color.r, color.g, color.b, 0));
                control.SetNewCreateTexture();
                bake.Add(renderer, source, slot, data, true, TextureVariant.LightNoEyeshadow, TextureVariant.DarkNoEyeshadow);
            }
            finally
            {
                control.SetColor(colorId, color);
                control.SetNewCreateTexture();
            }
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
                    bool skin = Same(m.Renderer, cha.body.rendBody) || Same(m.Renderer, cha.face.rendFace);
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
                            bake.Add(m.Renderer, m.Slots[slot], slot, data, skin);
                            if (data.Role == MaterialRole.Face)
                            {
                                BakeWithoutEyeshadow(bake, m.Renderer, m.Slots[slot], slot, data);
                            }
                        }
                        catch (Exception e)
                        {
                            Warnings.Add("Couldn't bake light and dark textures for " + data.Name + ": " + e.Message);
                        }
                    }
                }
            }
        }

        /// <summary>
        /// SVS draws each eye's white and pupil with one material. Each eye gets a copy as its eye white,
        /// resting just behind it, as KK's eye whites do (ADR 0034); the bake then draws the white on the
        /// copy and only the pupil on the eye. The copy hides whenever the game hides its eye.
        /// </summary>
        private List<CapturedMesh> AddEyeWhites(PassSink sink, List<CapturedMesh> captured)
        {
            var whites = new List<CapturedMesh>();
            if (cha.face.rendEye == null)
            {
                return whites;
            }
            foreach (var eye in cha.face.rendEye)
            {
                var m = captured.Find(c => Same(c.Renderer, eye));
                if (m == null)
                {
                    continue;
                }
                string eyeKey = m.Data.Key;
                var copy = EyeWhites.Copy(m.Data, k => eyeKey + EyeWhites.Suffix + k.Substring(eyeKey.Length));
                for (int slot = 0; slot < m.Slots.Length; slot++)
                {
                    if (m.Slots[slot] == null)
                    {
                        continue;
                    }
                    var white = materials.Capture(m.Slots[slot], Meshes.MaterialKey(copy.Key, slot), MaterialRole.EyeWhite, Bake.IrisTextures);
                    white.Name += EyeWhites.Suffix;
                    white.BlendMode = BlendMode.Opaque;
                    sink.Materials.Add(white);
                }
                sink.Meshes.Insert(sink.Meshes.IndexOf(m.Data), copy);
                EyeWhites.HideWith(sink.Meshes, eyeKey, copy.Key);
                whites.Add(new CapturedMesh { Renderer = m.Renderer, Data = copy, Source = m.Source, Slots = m.Slots, Skin = m.Skin, Weights = m.Weights });
            }
            return whites;
        }

        /// <summary>
        /// Closes the half-millimetre crack the game's gag shape leaves between each eye socket's disc
        /// and its rim on the face (ADR 0033).
        /// </summary>
        private void CloseGagSeams(PassSink sink)
        {
            var face = cha.face.rendFace != null ? sink.Meshes.Find(m => m.Name == cha.face.rendFace.name) : null;
            if (face == null)
            {
                return;
            }
            var closed = SeamClosing.Close(face, ExpressionCategory.Gag);
            Plugin.Logger.LogInfo("Closed the eye seam in " + closed.Count + " gag shape keys");
        }

        /// <summary>Pushes the tear and gag-eye meshes inside the head and gives each its showing key (ADR 0010).</summary>
        private void HideUntilShown(PassSink sink)
        {
            var face = cha.face.rendFace != null ? sink.Meshes.Find(m => m.Name == cha.face.rendFace.name) : null;
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
                if (renderer != null && renderer.enabled && (renderer.TryCast<SkinnedMeshRenderer>() != null || renderer.TryCast<MeshRenderer>() != null) && !IsHairOutline(renderer))
                {
                    yield return renderer;
                }
            }
        }

        /// <summary>True when every material on the renderer is a hair outline shell's.</summary>
        private static bool IsHairOutline(Renderer renderer)
        {
            bool any = false;
            foreach (var material in renderer.sharedMaterials)
            {
                if (material == null)
                {
                    continue;
                }
                if (material.shader == null || material.shader.name != HairOutlineShader)
                {
                    return false;
                }
                any = true;
            }
            return any;
        }

        /// <summary>
        /// Clothes shown only in another clothing state (half off, tucked in or out). SVS keeps them as
        /// inactive objects inside each clothing item, so the normal walk doesn't find them.
        /// </summary>
        private IEnumerable<Renderer> AlternateRenderers()
        {
            foreach (var clothes in cha.objTop.GetComponentsInChildren<ChaClothesComponent>(true))
            {
                foreach (var renderer in clothes.GetComponentsInChildren<Renderer>(true))
                {
                    if (!renderer.gameObject.activeInHierarchy && (renderer.TryCast<SkinnedMeshRenderer>() != null || renderer.TryCast<MeshRenderer>() != null))
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
            bool hasRole = roles.TryGetValue(renderer.GetInstanceID(), out role);
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
                bool body = cha.body.rendBody != null && renderer.GetInstanceID() == cha.body.rendBody.GetInstanceID() && slot == 0;
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
            Material[] slots = renderer.sharedMaterials;
            if (slots.Length > 0 && slots[0] != null)
            {
                return slots;
            }
            var gags = cha.face.matGag;
            for (int i = 0; i < GagNames.Length; i++)
            {
                if (renderer.name == GagNames[i] && gags != null && i < gags.Length && gags[i] != null)
                {
                    return new[] { gags[i] };
                }
            }
            return slots;
        }

        private static readonly string[] GagNames = { "cf_O_gag_eye_00", "cf_O_gag_eye_01", "cf_O_gag_eye_02" };

        /// <summary>
        /// Slots of the body material that the Outfit fills: the alpha mask hides the skin under the
        /// clothes. The Body Pass leaves them out and each Outfit Pass writes its own.
        /// </summary>
        private static readonly HashSet<string> OutfitBodySlots = new HashSet<string> { "_Cloth_alpha", "_Cloth_alpha_bot" };

        private string bodyMaterialKey;

        private void AddBodyTextures(PassSink sink)
        {
            var material = cha.body.rendBody != null ? cha.body.rendBody.sharedMaterial : null;
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
            var face = cha.face;
            Set(cha.body.rendBody, MaterialRole.Body);
            Set(face.rendFace, MaterialRole.Face);
            Set(face.rendEyebrow, MaterialRole.Eyebrow);
            Set(face.rendEyelid, MaterialRole.Eyelid);
            if (face.rendEye != null && face.rendEye.Length == 2)
            {
                Set(face.rendEye[0], MaterialRole.EyeL);
                Set(face.rendEye[1], MaterialRole.EyeR);
            }
            Set(face.rendTooth, MaterialRole.Teeth);
            Set(face.rendDoubleTooth, MaterialRole.Teeth);
            Set(face.rendTongueFace, MaterialRole.Tongue);
            Set(cha.body.rendTongueBody, MaterialRole.Tongue);
            if (face.objGags != null)
            {
                foreach (var gag in face.objGags)
                {
                    SetObject(gag, MaterialRole.GagEyes);
                }
            }
            // The game keeps no field for these, so they are found by name.
            foreach (var t in face.objHead.GetComponentsInChildren<Transform>(true))
            {
                switch (t.name)
                {
                    case "cf_O_eyelash_up":
                        SetObject(t.gameObject, MaterialRole.Eyelash);
                        break;
                    case "cf_O_namida_L":
                    case "cf_O_namida_M":
                    case "cf_O_namida_S":
                        SetObject(t.gameObject, MaterialRole.Tears);
                        break;
                }
            }
        }

        private static bool Same(UnityEngine.Object a, UnityEngine.Object b)
        {
            return a != null && b != null && a.GetInstanceID() == b.GetInstanceID();
        }

        private void Set(Renderer renderer, MaterialRole role)
        {
            if (renderer != null)
            {
                roles[renderer.GetInstanceID()] = role;
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
