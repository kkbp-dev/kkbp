# Outfit-owned objects are keyed per Pass

The adapters key the body skeleton's bones by their transform path from the Character's root, so a body bone has one Id in every Pass. Everything an Outfit owns is keyed with its Pass in front (`outfit00:` + transform path): clothes, hair and accessory meshes, their materials, and the bones that came with those objects. The game creates these objects again for each Outfit, and two Outfits can put different objects at the same path.

## Considered Options

- **Transform paths alone**: one hair bone seen in two Outfit Passes would keep one Id, but an accessory slot holding a different item in each Outfit would give one key two rest poses, which the Core rejects.
- **Pass-prefixed keys for Outfit-owned objects (chosen)**: each Outfit's objects are independent, as they are in the game.

## Consequences

- Hair is part of each Outfit Pass, so its bones appear once per Outfit, with Ids such as `cf_J_hairB_top_2`. The legacy exports duplicated them in the same way.
- A mesh or material Id is never shared between Passes. The Core rejects a mesh key that two Passes use, and would write a repeated material key only once.
