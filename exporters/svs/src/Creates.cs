using System.Collections.Generic;
using Character;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// SVS's create materials (LIF/lif_create_main_cloth, _skin_body, _skin_head): each composites a
    /// lit material's `_Create_main_texture` (or the face's `_Create_jm_main_skin_head`) from its base,
    /// masks, patterns and the Character's colours. Each goes, as the svs "create" section (Schema
    /// Version 1.3, issue 62), on the first material slot of the captured renderer the game gives it.
    /// </summary>
    internal sealed class Creates
    {
        private readonly Human cha;
        private readonly Materials materials;
        private readonly List<string> warnings;

        public Creates(Human cha, Materials materials, List<string> warnings)
        {
            this.cha = cha;
            this.materials = materials;
            this.warnings = warnings;
        }

        /// <summary>The body's and face's create materials, for the Body Pass.</summary>
        public void AttachBody(PassSink sink, List<CapturedMesh> captured)
        {
            Attach(sink, captured, cha.body.customTexCtrlBody, cha.body.rendBody);
            Attach(sink, captured, cha.face.customTexCtrlFace, cha.face.rendFace);
        }

        /// <summary>
        /// The worn clothes' create materials, for an Outfit Pass. As the clothes component's Rebuild01..03
        /// take them: [0] to rendNormal01 and rendAccessory, [1] to rendNormal02, [2] to rendNormal03.
        /// </summary>
        public void AttachClothes(PassSink sink, List<CapturedMesh> captured)
        {
            var clothes = cha.cloth != null ? cha.cloth.clothess : null;
            if (clothes == null)
            {
                return;
            }
            foreach (var part in clothes)
            {
                var component = part.cusClothesCmp;
                var creates = part.ctCreateClothes;
                if (component == null || creates == null)
                {
                    continue;
                }
                for (int i = 0; i < creates.Length; i++)
                {
                    foreach (var renderer in Renderers(component, i))
                    {
                        Attach(sink, captured, creates[i], renderer);
                    }
                }
            }
        }

        private static IEnumerable<Renderer> Renderers(ChaClothesComponent component, int i)
        {
            var list = i == 0 ? component.rendNormal01 : i == 1 ? component.rendNormal02 : i == 2 ? component.rendNormal03 : null;
            if (list != null)
            {
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
            int id = renderer.GetInstanceID();
            var mesh = captured.Find(m => m.Renderer != null && m.Renderer.GetInstanceID() == id && !m.Data.Alternate);
            if (mesh == null || mesh.Slots.Length == 0 || mesh.Slots[0] == null)
            {
                return;
            }
            var data = sink.Materials.Find(x => x.Key == Meshes.MaterialKey(mesh.Data.Key, 0));
            if (data == null || data.Sections.Exists(s => s.Extension == "svs" && s.Field == "create"))
            {
                return;
            }
            var material = create._matCreate;
            if (material == null)
            {
                warnings.Add("The create material for " + data.Name + " has no material, so it was left out.");
                return;
            }
            data.Sections.Add(materials.CaptureCreate(material));
        }
    }
}
