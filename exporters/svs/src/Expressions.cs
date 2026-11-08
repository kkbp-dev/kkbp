using System;
using System.Globalization;
using System.Collections.Generic;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using Character;
using ILLGames.Unity;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>A captured mesh with what baking its shape keys needs.</summary>
    internal sealed class CapturedMesh
    {
        public Renderer Renderer;
        public MeshData Data;
        public Mesh Source;

        /// <summary>The materials it was captured with, which for a gag-eye mesh aren't its renderer's own.</summary>
        public Material[] Slots;

        /// <summary>Null when the shape keys can't be read (an unreadable mesh).</summary>
        public Matrix4x4[] Skin;
        public BoneWeight[] Weights;
    }

    /// <summary>
    /// Bakes complete expressions (ADR 0003): every eye, eyebrow and mouth pattern evaluated the way the
    /// game's face controllers evaluate it, including only the blend shapes that controller drives, plus
    /// the table's closed versions and recipes. Eye patterns also record the gag meshes they show, the
    /// eye parts they hide and the material values they set.
    /// </summary>
    internal sealed class Expressions
    {
        private readonly Human cha;
        private readonly ExpressionTable table;
        private readonly Materials materials;
        private readonly Dictionary<int, CapturedMesh> byRenderer = new Dictionary<int, CapturedMesh>();
        private readonly HashSet<CapturedMesh> driven = new HashSet<CapturedMesh>();
        private readonly List<CapturedMesh> meshes;
        private readonly List<string> warnings;
        private PassSink sink;

        public Expressions(Human cha, ExpressionTable table, Materials materials, List<CapturedMesh> meshes, List<string> warnings)
        {
            this.cha = cha;
            this.table = table;
            this.materials = materials;
            this.meshes = meshes;
            this.warnings = warnings;
            foreach (var m in meshes)
            {
                var smr = m.Renderer.TryCast<SkinnedMeshRenderer>();
                if (smr != null)
                {
                    byRenderer[smr.GetInstanceID()] = m;
                }
            }
        }

        /// <summary>An Outfit Pass: no face controller drives its meshes, so they only keep their own shape keys.</summary>
        public void BakeOwnShapeKeys()
        {
            OwnShapeKeys();
        }

        public void Bake(PassSink sink)
        {
            this.sink = sink;
            Controller(cha.face.eyesCtrl, ExpressionList.Eye);
            Controller(cha.face.eyebrowCtrl, ExpressionList.Eyebrow);
            Controller(cha.face.mouthCtrl, ExpressionList.Mouth);
            Recipes();
            OwnShapeKeys();
        }

        // Patterns ------------------------------------------------------------------------------------

        private void Controller(FBSBase ctrl, ExpressionList list)
        {
            if (ctrl == null || ctrl.FBSTarget == null)
            {
                return;
            }
            foreach (var target in ctrl.FBSTarget)
            {
                CapturedMesh m;
                var smr = target.GetSkinnedMeshRenderer();
                if (smr != null && byRenderer.TryGetValue(smr.GetInstanceID(), out m))
                {
                    driven.Add(m);
                }
            }

            if (list == ExpressionList.Eye)
            {
                var infos = Human.lstCtrl.GetCategoryInfo(ChaListDefine.CategoryNo.cha_eyeset);
                var keys = new List<int>();
                foreach (var pair in infos)
                {
                    keys.Add(pair.Key);
                }
                keys.Sort();
                Count(list, keys.Count);
                foreach (int j in keys)
                {
                    var info = infos[j];
                    var pattern = table.Find(list, j);
                    int gag = info.GetInfoInt(ChaListDefine.KeyType.EyeObjNo);
                    var category = pattern != null ? ContractNames.CategoryOf(pattern.Name).Value : (gag > 0 ? ExpressionCategory.Gag : ExpressionCategory.Eye);
                    var morphs = BakePattern(ctrl, info.GetInfoInt(ChaListDefine.KeyType.EyesPtn), 1, category, pattern != null ? pattern.Name : null, info.Name, j);
                    if (morphs.Count > 0)
                    {
                        EyeLinks(morphs[0], info);
                    }
                }
                return;
            }

            // SVS keeps no names for its eyebrow and mouth patterns; untranslated ones go by position.
            var names = new List<string>();
            int count = ctrl.GetMaxPtn();
            Count(list, count);
            var categoryOf = list == ExpressionList.Mouth ? ExpressionCategory.Mouth : ExpressionCategory.Eyebrow;
            for (int j = 0; j < count; j++)
            {
                var pattern = table.Find(list, j);
                string gameName = j < names.Count ? names[j] : null;
                var open = BakePattern(ctrl, j, 1, categoryOf, pattern != null ? pattern.Name : null, gameName, j);
                if (pattern != null && pattern.ClosedName != null)
                {
                    var closed = BakePattern(ctrl, j, 0, categoryOf, pattern.ClosedName, gameName, j);
                    DropSameAsOpen(open, closed);
                }
            }
        }

        private void Count(ExpressionList list, int count)
        {
            int named = 0;
            foreach (var p in table.Patterns)
            {
                if (p.List == list)
                {
                    named++;
                }
            }
            // The game may have more patterns than the table names (KKS's last mouths aren't in the maker's
            // list); only a table naming more than exist is wrong.
            if (named > count)
            {
                warnings.Add("The game has " + count + " " + list + " patterns but the translation table names " + named + ".");
            }
        }

        /// <summary>
        /// One pattern at an open rate, on every mesh the controller drives, using the controller's own
        /// formula: the Open key gets the openness and the Close key the rest. Returns the morphs added.
        /// </summary>
        private List<Core.MorphData> BakePattern(FBSBase ctrl, int ptn, float openRate, ExpressionCategory category, string name, string gameName, int index)
        {
            var added = new List<Core.MorphData>();
            int open = (int)Mathf.Clamp(Mathf.Lerp(ctrl.OpenMin, ctrl.OpenMax, openRate) * 100f, 0f, 100f);
            foreach (var target in ctrl.FBSTarget)
            {
                CapturedMesh m;
                var smr = target.GetSkinnedMeshRenderer();
                if (smr == null || !byRenderer.TryGetValue(smr.GetInstanceID(), out m) || m.Skin == null || ptn < 0 || ptn >= target.PtnSet.Length)
                {
                    continue;
                }
                var weights = new Dictionary<int, float>();
                Add(weights, target.PtnSet[ptn].Close, 100 - open);
                Add(weights, target.PtnSet[ptn].Open, open);
                var morph = ShapeKeys.Bake(m.Source, weights, m.Skin, m.Weights);
                if (morph == null)
                {
                    continue;
                }
                morph.Category = category;
                morph.ExpressionName = name;
                morph.GameName = gameName;
                if (name == null && (string.IsNullOrEmpty(gameName) || Has(m.Data, gameName)))
                {
                    // Two untranslated patterns can share a game name; keep each one apart by its position.
                    morph.GameName = (string.IsNullOrEmpty(gameName) ? category.ToString().ToLowerInvariant() : gameName) + " " + index;
                }
                if (Has(m.Data, morph.TargetName))
                {
                    warnings.Add(m.Data.Name + " already has a shape key named " + morph.TargetName + "; the second is left out.");
                    continue;
                }
                m.Data.Morphs.Add(morph);
                added.Add(morph);
            }
            return added;
        }

        private static void Add(Dictionary<int, float> weights, int index, float weight)
        {
            if (index < 0)
            {
                return;
            }
            float existing;
            weights.TryGetValue(index, out existing);
            weights[index] = existing + weight;
        }

        private static bool Has(MeshData mesh, string target)
        {
            return mesh.Morphs.Exists(m => m.TargetName == target);
        }

        /// <summary>A closed version is kept only on meshes where it differs from the open one.</summary>
        private void DropSameAsOpen(List<Core.MorphData> open, List<Core.MorphData> closed)
        {
            foreach (var c in closed)
            {
                foreach (var m in meshes)
                {
                    if (!m.Data.Morphs.Contains(c))
                    {
                        continue;
                    }
                    var o = open.Find(x => m.Data.Morphs.Contains(x));
                    if (o != null && Deltas.Same(o.PositionDeltas, c.PositionDeltas))
                    {
                        m.Data.Morphs.Remove(c);
                    }
                }
            }
        }

        /// <summary>
        /// What an eye pattern does besides moving shape keys, as the game's ChangeEyesPtn does it: which
        /// gag mesh shows, which eye parts hide, and the gag and eye material values it sets.
        /// </summary>
        private void EyeLinks(Core.MorphData morph, ListInfoBase info)
        {
            if (info.GetInfoInt(ChaListDefine.KeyType.EyeBase) != 1)
            {
                Hide(morph, cha.GetRefObject(Table.RefObjKey.N_EyeBase));
            }
            if (info.GetInfoInt(ChaListDefine.KeyType.EyeHitomi) == 0)
            {
                Hide(morph, cha.GetRefObject(Table.RefObjKey.N_Hitomi));
            }

            string eyeTexture = info.GetInfo(ChaListDefine.KeyType.EpsTex);
            string eyeBundle = info.GetInfo(ChaListDefine.KeyType.EpsTexAB);
            if (eyeTexture != "0" && eyeBundle != "0" && cha.face.rendEye != null)
            {
                foreach (var eye in cha.face.rendEye)
                {
                    var change = Pattern(eye, "_expression", eyeBundle, eyeTexture);
                    if (change != null)
                    {
                        change.Floats["_exppower"] = 1;
                        morph.MaterialChanges.Add(change);
                    }
                }
            }

            int gag = info.GetInfoInt(ChaListDefine.KeyType.EyeObjNo);
            if (gag < 1 || gag > 3)
            {
                return;
            }
            var gagObject = cha.GetRefObject(GagKeys[gag - 1]);
            var gagRenderer = gagObject != null ? gagObject.GetComponent<SkinnedMeshRenderer>() : null;
            CapturedMesh gagMesh;
            if (gagRenderer == null || !byRenderer.TryGetValue(gagRenderer.GetInstanceID(), out gagMesh))
            {
                warnings.Add("Eye pattern " + info.Name + " shows gag eyes " + gag + ", which weren't captured.");
                return;
            }
            morph.ShowsMeshKeys.Add(gagMesh.Data.Key);
            var gagChange = Pattern(gagRenderer, "_MainTex", info.GetInfo(ChaListDefine.KeyType.MainTexAB), info.GetInfo(ChaListDefine.KeyType.MainTex))
                ?? new MaterialChange { MaterialKey = Meshes.MaterialKey(gagMesh.Data.Key, 0) };
            gagChange.Floats["_SizeSpeed"] = info.GetInfoFloat(ChaListDefine.KeyType.SizeSpeed);
            gagChange.Floats["_SizeWidth"] = info.GetInfoFloat(ChaListDefine.KeyType.SizeWidth);
            gagChange.Floats["_AngleSpeed"] = info.GetInfoFloat(ChaListDefine.KeyType.AngleSpeed);
            gagChange.Floats["_yurayura"] = info.GetInfoFloat(ChaListDefine.KeyType.Yurayura);
            morph.MaterialChanges.Add(gagChange);
        }

        private static readonly Table.RefObjKey[] GagKeys =
        {
            Table.RefObjKey.N_Gag00, Table.RefObjKey.N_Gag01, Table.RefObjKey.N_Gag02,
        };

        private void Hide(Core.MorphData morph, GameObject obj)
        {
            if (obj == null)
            {
                return;
            }
            foreach (var renderer in obj.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                CapturedMesh m;
                if (byRenderer.TryGetValue(renderer.GetInstanceID(), out m) && !morph.HidesMeshKeys.Contains(m.Data.Key))
                {
                    morph.HidesMeshKeys.Add(m.Data.Key);
                }
            }
        }

        /// <summary>
        /// A change that switches a renderer's first material slot to one of the game's pattern textures,
        /// adding that pattern to the captured material. Null if the texture can't be loaded.
        /// </summary>
        private MaterialChange Pattern(Renderer renderer, string raw, string bundle, string texture)
        {
            CapturedMesh m;
            var smr = renderer.TryCast<SkinnedMeshRenderer>();
            if (smr == null || !byRenderer.TryGetValue(smr.GetInstanceID(), out m) || bundle == "0" || texture == "0")
            {
                return null;
            }
            string materialKey = Meshes.MaterialKey(m.Data.Key, 0);
            var material = sink.Materials.Find(x => x.Key == materialKey);
            if (material == null)
            {
                return null;
            }
            if (!material.Textures.Exists(t => t.Raw == raw && t.Pattern == texture))
            {
                var loaded = CommonLib.LoadAsset<Texture2D>(bundle, texture, false, null);
                if (loaded == null)
                {
                    warnings.Add("Couldn't load pattern texture " + texture + " from " + bundle + ".");
                    return null;
                }
                var source = m.Slots[0];
                material.Textures.Add(materials.Texture(raw, loaded, source.GetTextureOffset(raw), source.GetTextureScale(raw), texture));
            }
            var change = new MaterialChange { MaterialKey = materialKey };
            change.Textures[raw] = texture;
            return change;
        }

        // Recipes and other shape keys ----------------------------------------------------------------

        /// <summary>
        /// Expressions that aren't game patterns, from the table's recipes. Each mesh uses the recipe's
        /// shapes it has; a mesh with none of them gets nothing.
        /// </summary>
        private void Recipes()
        {
            foreach (var recipe in table.Recipes)
            {
                foreach (var m in driven)
                {
                    if (m.Skin == null)
                    {
                        continue;
                    }
                    var weights = new Dictionary<int, float>();
                    foreach (var shape in recipe.Shapes)
                    {
                        int index = m.Source.GetBlendShapeIndex(shape.Key);
                        if (index >= 0)
                        {
                            Add(weights, index, shape.Value * 100f);
                        }
                    }
                    var morph = weights.Count > 0 ? ShapeKeys.Bake(m.Source, weights, m.Skin, m.Weights) : null;
                    if (morph == null || Has(m.Data, recipe.Name))
                    {
                        continue;
                    }
                    morph.Category = ContractNames.CategoryOf(recipe.Name).Value;
                    morph.ExpressionName = recipe.Name;
                    m.Data.Morphs.Add(morph);
                }
            }
        }

        /// <summary>Meshes no face controller drives keep their own blend shapes, as category other.</summary>
        private void OwnShapeKeys()
        {
            foreach (var m in meshes)
            {
                if (driven.Contains(m) || m.Skin == null || m.Source.blendShapeCount == 0)
                {
                    continue;
                }
                for (int s = 0; s < m.Source.blendShapeCount; s++)
                {
                    string shape = m.Source.GetBlendShapeName(s);
                    var morph = ShapeKeys.Bake(m.Source, new Dictionary<int, float> { { s, 100f } }, m.Skin, m.Weights);
                    if (morph == null || Has(m.Data, shape))
                    {
                        continue;
                    }
                    morph.Category = ExpressionCategory.Other;
                    morph.GameName = shape;
                    m.Data.Morphs.Add(morph);
                }
            }
        }
    }
}
