# The face rig drives the expression keys through Face Key Roles

The Rigify rig's face was a grid of four controllers. One went round a circle of copied vowel keys, one went up and down through four copied eye keys, and two drove empty Custom keys. Beside it was a large eye-handle mechanism of markers, track bones and correction drivers, which slid the eye textures through the UV warps. The grid had no labels and no presets, and most of the Game's expressions weren't reachable from it.

The face rig replaces both. It was designed from four prototypes tried on the Golden Samples (a labelled board, controls on the face, a pattern picker, then the two combined) and from renders of every expression key of each Game.

- **Controls on the face.** These cover what has a place on the face: blink, each eye's wink, the brows (both, and each side), an emote control (sad up, angry down), each mouth corner (up, down, out), and the jaw.
- **A board beside the head** for the rest:
  - a look joystick;
  - a mouth shape grid and an open mood grid, which pick what the jaw opens;
  - two lip mood grids;
  - sliders for the other eye, brow and open-mouth expressions, the gag eyes and the tears.
- **The eyes.** One look-at target, with an offset for each eye. The UV warps' offset and scale are driven from where each eye aims and from the targets' scale. The lids close a little as the eyes look down.
- **Face Properties.** A key that no control reaches gets a 0–1 slider on the Face Properties bone.
- **Presets.** The twelve emotion presets pose the controls. They are buttons in the KKBP sidebar's Face panel, with Shift-click adding a preset on top of the current face.

Each control drives Face Key Roles, such as `blink`, `corner_down` or `vowel_o`, not Expression Names. The Game Profile maps each role to an Expression Name, or to a weighted mix of them (`FACE_KEYS`). The roles exist because the same name means different things in different Games. On SVS, `Mouth Lonely, Closed` pulls the mouth corner down; on KK it pulls the corner in, and KK's clean "down" is `Mouth Angry, Closed`. KK's blink is the legacy grid's soft close, `Eye Closed` at 0.35 with `Eye Happy, Closed` at 0.7.

Hooks don't get the profile, so the `record_face_keys` Step writes the roles Body has keys for onto Body's shape keys as JSON (`kkbp_face_keys`). The Hook reads them there.

## Considered Options

- **Name lists in the Hook**, first name found wins, as the grid's `MOUTH_SHAPEKEY_ALTERNATES` did. It fails where a name exists in both Games with different meanings, and choosing a table by which keys exist is a Game check in disguise.
- **Picking keys at import by how they move the face** (the lip-only key that moves the corner furthest down). This needs no table, but the choices are hard to predict and to override.
- **Game Profile tables, written on Body by a Step (chosen).** The Hook stays Game-blind, and a user who wants another key changes one line of a profile.

## Consequences

- **Every open-mouth key carries its own jaw drop.** Two of them together move the teeth and tongue twice. The jaw therefore opens one open key at a time: the vowel the mouth shape grid points at (A in its middle), or the open mood its grid is pushed towards, which takes over from the vowel. The lip mood grids use lip-only keys where the Game has good ones. The open-mouth sliders, and KK's open grit and tight moods, still carry a jaw drop of their own.
- **No Game has one-sided brow or mouth corner keys.** One side's control drives a half of the Game's key: a copy whose offsets fade out over a few millimetres across the face's middle (`Eyebrow Excited (L)`, `Mouth Smiling, Closed (R)`).
- **Simple expressions only.** Every driver is a simple expression, so the face moves with auto-run Python off. The panel is the add-on's, so no script is kept in the .blend.
- **Removed:** the eye handles, markers, eyeballs and track bones, `Eyesx`, the grid's bones and widgets, and its `(Copy)` and `Custom Key` shape keys. Head tracking, which shared the eye-handle code, is now `metarig/head_track.py`. Its target sits where the Eyes handle did, and its settings keep their names.
- **Bone collections.** The game face bones move from `Face` to a hidden `Face Tweak`, and the tongue from `Eyes/Rig.Tongue` to `Tongue`. `Emotions` holds the new face controls, the board and the Face Properties bone, and `Eyes` the eye targets; there is no `Face` collection.
- **Legacy names.** ADR 0023's rule that the rig keeps the legacy importer's names gives way for the face: an action keyed on the old eye handles or grid controllers no longer finds them. Head tracking keeps its names.
- **The rig changed on purpose.** The Hook snapshots and the rig fingerprint baseline were re-recorded (ADR 0043).
