"""French. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "Options d'import",
    "Pillow is required. Install it with the buttons below.": "Pillow est requis. Installez-le depuis le panneau KKBP.",
    "Import Export Bundle": "Importer un paquet d'export",
    "No Step or Hook declares an option yet.": "Aucune étape ni aucun hook ne déclare encore d'option.",
    "No hook scripts loaded": "Aucun script de hook chargé",
    "no Hooks": "aucun hook",
    "not loaded": "non chargé",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "L'importeur glTF de Blender n'est pas disponible. Activez l'add-on « glTF 2.0 format » dans les Préférences.",

    # Preferences
    "Run this Hook after each import": "Exécuter ce hook après chaque import",
    "Hooks folder": "Dossier des hooks",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "Chaque fichier .py de ce dossier est chargé comme script de hook. Il n'y a pas de dossier par défaut",
    "User Hooks run after the built-in Hooks, in this order:":
        "Les hooks utilisateur s'exécutent après les hooks intégrés, dans cet ordre :",
    "Import Option defaults": "Valeurs par défaut des options d'import",
    "Import Option defaults: the built-in ones": "Valeurs par défaut des options d'import : celles intégrées",
    "Move Hook": "Déplacer le hook",
    "Move the selected Hook up or down the running order":
        "Déplace le hook sélectionné vers le haut ou le bas dans l'ordre d'exécution",
    "Forget Hook": "Retirer le hook de la liste",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "Retire le hook sélectionné de la liste. S'il est chargé à nouveau, il revient à la fin",
    "Use the built-in defaults": "Utiliser les valeurs intégrées",
    "Forget the saved Import Option defaults": "Oublie les valeurs par défaut enregistrées des options d'import",

    # Importing
    "Import manifest.json": "Importer manifest.json",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no file chosen":
        "Importe un personnage depuis un paquet d'export : choisissez son manifest.json, ou ouvrez son dossier et importez sans choisir de fichier",
    "Download Pillow": "Installer Pillow",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "Télécharge Pillow {version} depuis PyPI avec le pip de Blender et l'installe dans KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "L'accès en ligne est désactivé dans les Préférences de Blender. Télécharger Pillow quand même ?",
    "Install Pillow from local file": "Installer Pillow depuis un fichier",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "Installe un wheel Pillow (.whl) que vous avez téléchargé vous-même, pour le Python et la plateforme de ce Blender",
    "Reload Hooks": "Recharger les hooks",
    "Load the scripts in the hooks folder again": "Charge à nouveau les scripts du dossier des hooks",
    "Open KKBP Log": "Ouvrir le journal KKBP",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "Ouvre le journal du dernier import (kkbp_cache/log/log.txt dans le paquet d'export) dans votre éditeur de texte",
    "Save as Defaults": "Enregistrer comme valeurs par défaut",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "Utilise les options d'import de cette scène comme valeurs par défaut pour les nouvelles scènes et les imports par script",

    # Import Options
    "Delete default scene": "Supprimer la scène par défaut",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported Characters":
        "Supprime le cube, la caméra et la lumière du fichier de démarrage de Blender, si le fichier ne contient rien d'autre que des personnages importés",
    "Which shaders the Character's materials use": "Les shaders utilisés par les matériaux du personnage",
    "Keeps the Eevee shaders": "Conserve les shaders Eevee",
    "Uses a modified shader setup for Eevee": "Utilise une configuration de shaders modifiée pour Eevee",
    "Cycles (toon)": "Cycles (toon)",
    "Toon shaders for Cycles": "Shaders toon pour Cycles",
    "Cycles (classic)": "Cycles (classique)",
    "The classic shaders for Cycles": "Les shaders classiques pour Cycles",
    "A very simple material setup": "Une configuration de matériau très simple",
    "Separation type": "Type de séparation",
    "How the clothes are split into objects": "Comment les vêtements sont répartis en objets",
    "One object per outfit": "Un objet par tenue",
    "Each Outfit's clothes are one object": "Les vêtements de chaque tenue forment un seul objet",
    "Separate all clothing": "Séparer tous les vêtements",
    "Each piece of clothing is its own object, named by its material":
        "Chaque vêtement est un objet à part, nommé d'après son matériau",
    "Use outlines": "Utiliser les contours",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "Donne au corps, aux cheveux et aux vêtements un matériau de contour pour chacun de leurs matériaux",
    "Face cards": "Cartes de visage",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts hidden":
        "Ajoute des cartes 2D d'yeux et de bouche devant le visage, avec les textures d'yeux du personnage. Leur collection est masquée au départ",
    "SFW mode": "Mode SFW",
    "Attempts to cover up some NSFW things": "Tente de masquer certains éléments NSFW",
    "Use Rigify armature": "Utiliser l'armature Rigify",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK armature, which is easier to export":
        "Génère un rig de contrôle Rigify, adapté à l'animation dans Blender. Sans lui, le personnage garde l'armature FK, plus facile à exporter",
    "Separate eyes": "Séparer les yeux",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so they can show through the hair with the compositor":
        "Déplace les yeux et les sourcils hors de Body vers leurs propres objets, leurs clés de forme suivant celles de Body, pour qu'ils puissent apparaître à travers les cheveux avec le compositeur",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "Contours",
    "Separate Eyes": "Séparer les yeux",
    "Separate meshes": "Séparer les maillages",
    "Convert shaders": "Convertir les shaders",

    # Tools
    "Merge Weights": "Fusionner les poids",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "Donne les poids des os sélectionnés à leurs parents et supprime ces os",
    "Export Prep": "Préparer l'export",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on its Collection":
        "Prépare le personnage pour un autre programme : noms des os, squelette simplifié, atlas et exporteur FBX sur sa collection",
    "Atlas": "Atlas",
    "Largest atlas": "Atlas le plus grand",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "Un objet dont l'atlas serait plus large que cela reçoit plusieurs atlas. Rien n'est réduit",
    "Koikatsu": "Koikatsu",
    "No change": "Aucun changement",
    "Very simple": "Très simple",
    "Merges the deform details, the face and the tongue into their parents":
        "Fusionne les détails de déformation, le visage et la langue avec leurs parents",
    "Merges the helper bones only": "Fusionne uniquement les os auxiliaires",
    "Keeps every bone": "Conserve tous les os",
    "One atlas each for the light, dark and normal textures":
        "Un atlas pour chacune des textures claire, sombre et de normales",
    "Atlas without the eyes": "Atlas sans les yeux",
    "As Atlas, with the eyes keeping their own textures": "Comme Atlas, mais les yeux gardent leurs propres textures",
    "Atlas of every texture": "Atlas de toutes les textures",
    "As Atlas, with the detail, alpha and colour masks too":
        "Comme Atlas, avec aussi les masques de détail, d'alpha et de couleur",
    "No atlas": "Pas d'atlas",
    "The textures stay as they are": "Les textures restent telles quelles",
    "Run Hook": "Exécuter un hook",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "Exécute un hook, comme Rigify, sur un personnage importé sans lui",
    "Built in": "Intégré",
    "Bulk Import": "Import par lot",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside each bundle folder":
        "Importe tous les paquets d'export d'un dossier, chacun dans son propre Blender en arrière-plan, et enregistre un .blend à côté de chaque dossier de paquet",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "Applique une animation .fbx de Koikatsu au rig Rigify du personnage comme nouvelle action",
    "Lengthen arms": "Allonger les bras",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "Allonge les bras de 5 %, ce qui se rapproche du jeu dans certaines poses",
    "Snap IKs": "Aligner les IK",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "Aligne les contrôles IK du rig sur leur pose FK et bascule les membres en IK",

    # Edit Material
    "Saturate": "Saturer",
    "What Edit Material does with the colours: Shown colours for a material that follows the game's shaders, Saturate for one from a modded shader":
        "Ce que Modifier le matériau fait des couleurs : Couleurs affichées pour un matériau qui suit les shaders du jeu, Saturer pour un matériau d'un shader moddé",
    "Shown colours": "Couleurs affichées",
    "Each colour is the colour as it shows, so the eyedropper can pick it":
        "Chaque couleur est la couleur telle qu'elle s'affiche, pour que la pipette puisse la prélever",
    "Each colour is the game's own value, which shows graded and stronger":
        "Chaque couleur est la valeur propre du jeu, qui s'affiche étalonnée et plus intense",
    "Don't saturate": "Ne pas saturer",
    "Edit Material": "Modifier le matériau",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be changed and saved":
        "Remplace le matériau actif par un matériau modifiable qui reconstruit la colorisation du jeu, afin de pouvoir changer et enregistrer ses couleurs",
    "Cancel": "Annuler",
    "Puts the original material back and drops the changes":
        "Remet le matériau d'origine et abandonne les modifications",
    "Starts the edit again from the Export Bundle": "Recommence la modification à partir du paquet d'export",
    "Bakes the edited colours into the original material's light and dark textures":
        "Bake les couleurs modifiées dans les textures claire et sombre du matériau d'origine",
    "Link Hair": "Lier les cheveux",
    "Puts every hair material into edit with the active hair material's settings":
        "Met tous les matériaux de cheveux en modification avec les réglages du matériau de cheveux actif",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Hooks": "Hooks",
    "Hook": "Hook",
}
