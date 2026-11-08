# The Cache folder is visible, kkbp_cache

The importer's Cache inside an Export Bundle is `kkbp_cache/`, without a leading dot. Until now it was `.kkbp_cache/`, which file browsers hide, so users couldn't find the KKBP log or the Edit material and bake images, and couldn't see what to delete. The name is the `CACHE_FOLDER` constant in `kkbp/bundle/bundle.py`; everything else goes through `bundle.cache_dir()`. The contract doesn't name the Cache, so no Schema Version changes.

## Considered Options

- **A hidden `.kkbp_cache/`, the usual habit for tool state (rejected)**: users look for the log and the images in a file browser.
- **A visible `kkbp_cache/` (chosen)**.

## Consequences

- An older `.kkbp_cache/` in a bundle is left alone: nothing moves or deletes it, and deleting it is safe. The first Edit material after the change makes its working images again; baked images are packed into the `.blend`.
- The hook interface stays at 1.0: `bundle.cache_dir(kind)` still returns a folder of the Cache, and only the folder's name in its description changed.
- `.gitignore` lists both names.
