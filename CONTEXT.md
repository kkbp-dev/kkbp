# KKBP

Exporters that capture a game Character into an Export Bundle, and a Blender importer that rebuilds the Character from that bundle.

## Language

### Games and characters

**Game**:
One supported Illusion title, identified by a fixed id: `KK`, `KKS` or `SVS`.
_Avoid_: prefix, game name

**Game Profile**:
The importer's data about one Game that cannot come from the bundle, such as which shader templates it uses; it may extend another Game's profile.
_Avoid_: game config, game mode

**Character**:
The in-game person being exported, including body, hair, face and every Outfit.
_Avoid_: model, chara

**Card**:
The game's own save file for a Character, a PNG with embedded data.
_Avoid_: character file

**Outfit**:
One complete set of clothing and accessories a Character can wear.
_Avoid_: coordinate, clothing set, costume

### The export contract

**Export Bundle**:
The folder an exporter writes for one Character, and the only thing the importer reads.
_Avoid_: export folder, import dir, output files

**Manifest**:
The file that identifies an Export Bundle: its Game, Schema Version, Exporter Version and contents.
_Avoid_: config, header

**Schema Version**:
The `major.minor` version of the Export Bundle contract; the only version that decides whether an importer accepts a bundle.
_Avoid_: format version

**Exporter Version**:
The release of the exporter that wrote a bundle; informational only.
_Avoid_: plugin version

**Pass**:
One mesh capture within a bundle: the Body Pass, or one Outfit Pass per Outfit.
_Avoid_: coordinate pass

**Id**:
A stable identifier for a mesh, material or bone, unique among its kind within one Export Bundle and used for all matching between files.
_Avoid_: decorated name, alt name

**Texture Role**:
The meaning of a texture slot on a material (for example main, normal or alpha mask), drawn from a small closed set shared by every Game. A texture outside that set is known only by its Raw Property.
_Avoid_: suffix, texture type

**Raw Property**:
The game shader's own name for a material property or texture slot, as the Game defines it.
_Avoid_: shader prop name, texture slot

**Texture Variant**:
An exporter-produced alternative of one texture, such as its baked light or dark version.
_Avoid_: pre_light, pre_dark

**Bone Role**:
What a bone is for, such as body root, head or left eye, written by the exporter and drawn from a closed set.
_Avoid_: bone type, landmark

**Bone Group**:
The broad kind of a bone, such as deform, skirt, hair or accessory, written by the exporter for every bone.
_Avoid_: bone layer, bone collection, bone category

**Joint Correction**:
The game's own movement of a correction bone, such as an elbow, knee or twist bone, worked out each frame from the pose of the limbs; its rules are in the Game Profile.
_Avoid_: joint driver, correction driver, helper bone

**Game Scale**:
A bone's accumulated scale in the game at capture, which the rest pose leaves out and the Joint Corrections need.
_Avoid_: lossy scale, bone scale

**Material Role**:
What a material is for, such as face, body, eyebrow or tears, written by the exporter and drawn from a closed set.
_Avoid_: material type

**Blend Mode**:
How a material lets the background show through: opaque, cutout, alpha or glasses, written by the exporter.
_Avoid_: alpha shader, transparency type

**Expression Name**:
The canonical English name of an expression shape key, shared by every Game, alongside the Game's own name. It is the display name used in Blender, prefixed by its category, such as `Eye Happy` or `Gag Heart Eyes`.
_Avoid_: translated name, shape key alias

**Game Extension**:
The part of an Export Bundle holding data only one Game has, kept apart from the shared core.
_Avoid_: game-specific fields

**Create Material**:
The game material that composites a KK or KKS material's main texture from a base texture, masks and the Character's colours.
_Avoid_: matCreate, create texture

**Game Shader Model**:
A numpy model of one of a Game's shaders as the exporter bakes it, in `importer/tools/game_shaders/models.py`, checked against the Golden Samples; the specification an edit template's node groups follow (ADR 0041).
_Avoid_: shader recreation, approximation

**Maker Light**:
The light and global shading values a Game's light and dark bakes run with (the light term, the ambient colour and strength, the shadow floor), fitted to the Golden Samples (`models.KK`, `models.KKS`). A Game Profile sets its own on the edit templates (ADR 0041).
_Avoid_: scene light, lighting preset

### Exporting

**Exporter Core**:
The game-independent part shared by every exporter, which turns captured data into an Export Bundle.
_Avoid_: builder, PmxBuilder, shared lib

**Game Adapter**:
The part of an exporter that reads one Game's Character and hands its data to the Exporter Core.
_Avoid_: game plugin, game layer

### Importing

**Core Import**:
The built-in work that rebuilds a Character in Blender from an Export Bundle, finished before any Hook runs.
_Avoid_: main import, base import

**Step**:
One built-in unit of work within the Core Import.
_Avoid_: operation, stage, phase

**Hook**:
A script that runs after the Core Import, either built-in (such as Rigify conversion) or supplied by a user or another add-on.
_Avoid_: post operation, plugin, callback

**Import Option**:
A setting declared by a Step or Hook that changes how a Character is imported.
_Avoid_: preference, panel setting

**Character Key**:
The unique identifier given to a Character when it is imported into Blender, carried by every one of its Parts.
_Avoid_: character name, character id

**Part**:
One Blender object belonging to an imported Character.
_Avoid_: piece, component, child

**Part Role**:
What a Part is for, such as body, hair, outfit or armature, drawn from a closed set.
_Avoid_: object type, flag, tag

**Material Template**:
A KKBP shader material from the built-in library that bundle materials are rebuilt from.
_Avoid_: shader template, template material

**Template Description**:
The statement of which Texture Roles and named parameters a Material Template accepts, and where they connect inside it.
_Avoid_: template mapping, node map

**Template Set**:
The Material Templates a Game uses and the rules for choosing one per material; it may extend another set.
_Avoid_: shader set

**Cache**:
Files the importer derives from an Export Bundle and stores in its `kkbp_cache/` folder, never written by an exporter. The folder is visible on purpose (ADR 0030).
_Avoid_: baked files folder

### Testing

**Sample Card**:
One of the three Cards, one per Game, that the Golden Samples are exported from; kept in the repository.
_Avoid_: test card, input card

**Golden Sample**:
The Export Bundle of one Sample Card, made on each developer's own machine and never committed, that the tests check and import (ADR 0031).
_Avoid_: golden copy, sample export, reference bundle
