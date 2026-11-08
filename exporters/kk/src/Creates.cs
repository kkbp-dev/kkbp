using System.Collections.Generic;
using System.Reflection;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// The game's create materials: each composites a material's main texture from an uncoloured base,
    /// masks and the Character's colours. Each one goes, as the kk "create" section, on the first material
    /// slot of every captured renderer the game gives its texture (contract-change-create-materials.md).
    /// </summary>
    internal sealed class Creates
    {
        // Both are protected in the game's assembly.
        private static readonly FieldInfo MatCreate = typeof(CustomTextureCreate).GetField("matCreate", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo TexMain = typeof(CustomTextureCreate).GetField("texMain", BindingFlags.Instance | BindingFlags.NonPublic);

        private readonly ChaControl cha;
        private readonly Materials materials;
        private readonly List<string> warnings;

        public Creates(ChaControl cha, Materials materials, List<string> warnings)
        {
            this.cha = cha;
            this.materials = materials;
            this.warnings = warnings;
        }

        /// <summary>The body's, face's and eyes' create materials, for the Body Pass.</summary>
        public void AttachBody(PassSink sink, List<CapturedMesh> captured)
        {
            Attach(sink, captured, cha.customTexCtrlBody, cha.rendBody);
            Attach(sink, captured, cha.customTexCtrlFace, cha.rendFace);
            if (cha.rendEyeW != null)
            {
                foreach (var renderer in cha.rendEyeW)
                {
                    Attach(sink, captured, cha.ctCreateEyeW, renderer);
                }
            }
            if (cha.rendEye != null && cha.rendEye.Length == 2)
            {
                Attach(sink, captured, cha.ctCreateEyeL, cha.rendEye[0]);
                Attach(sink, captured, cha.ctCreateEyeR, cha.rendEye[1]);
            }
        }

        /// <summary>
        /// The worn clothes' create materials, for an Outfit Pass. As the game's ChangeCustomClothes gives
        /// them out: [kind, 0] to rendNormal01, rendAlpha01 and rendAccessory, [kind, 1] to rendNormal02,
        /// [kind, 2] to rendNormal03, for the main and the sub clothes components alike.
        /// </summary>
        public void AttachClothes(PassSink sink, List<CapturedMesh> captured)
        {
            AttachClothes(sink, captured, cha.ctCreateClothes, cha.cusClothesCmp);
            AttachClothes(sink, captured, cha.ctCreateClothesSub, cha.cusClothesSubCmp);
        }

        private void AttachClothes(PassSink sink, List<CapturedMesh> captured, CustomTextureCreate[,] creates, ChaClothesComponent[] components)
        {
            if (creates == null || components == null)
            {
                return;
            }
            for (int kind = 0; kind < creates.GetLength(0) && kind < components.Length; kind++)
            {
                var component = components[kind];
                if (component == null)
                {
                    continue;
                }
                for (int i = 0; i < creates.GetLength(1); i++)
                {
                    var create = creates[kind, i];
                    if (create == null)
                    {
                        continue;
                    }
                    foreach (var renderer in Renderers(component, i))
                    {
                        Attach(sink, captured, create, renderer);
                    }
                }
            }
        }

        private static IEnumerable<Renderer> Renderers(ChaClothesComponent component, int i)
        {
            var lists = i == 0 ? new[] { component.rendNormal01, component.rendAlpha01 }
                : i == 1 ? new[] { component.rendNormal02 }
                : new[] { component.rendNormal03 };
            foreach (var list in lists)
            {
                if (list == null)
                {
                    continue;
                }
                foreach (var renderer in list)
                {
                    if (renderer != null)
                    {
                        yield return renderer;
                    }
                }
            }
            if (i == 0 && component.rendAccessory != null)
            {
                yield return component.rendAccessory;
            }
        }

        /// <summary>Puts the create on the renderer's first material slot, if that renderer was captured in this Pass.</summary>
        private void Attach(PassSink sink, List<CapturedMesh> captured, CustomTextureCreate create, Renderer renderer)
        {
            if (create == null || renderer == null)
            {
                return;
            }
            var mesh = captured.Find(m => m.Renderer == renderer);
            if (mesh == null || mesh.Slots.Length == 0 || mesh.Slots[0] == null)
            {
                return;
            }
            var data = sink.Materials.Find(x => x.Key == Meshes.MaterialKey(mesh.Data.Key, 0));
            if (data == null || data.Sections.Exists(s => s.Extension == "kk" && s.Field == "create"))
            {
                return;
            }
            var material = MatCreate.GetValue(create) as Material;
            if (material == null)
            {
                warnings.Add("The create material for " + data.Name + " has no material, so it was left out.");
                return;
            }
            data.Sections.Add(materials.CaptureCreate(material, TexMain.GetValue(create) as Texture));
        }
    }
}
