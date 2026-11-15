"""German. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "Importoptionen",
    "Pillow is required. Install it with the buttons below.": "Pillow wird benötigt. Installiere es über das KKBP-Panel.",
    "Import Export Bundle": "Export-Bundle importieren",
    "No Step or Hook declares an option yet.": "Noch kein Schritt oder Hook hat eine Option.",
    "No hook scripts loaded": "Keine Hook-Skripte geladen",
    "no Hooks": "keine Hooks",
    "not loaded": "nicht geladen",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "Blenders glTF-Importer ist nicht verfügbar. Aktiviere das Add-on „glTF 2.0 format“ in den Einstellungen.",

    # Preferences
    "Run this Hook after each import": "Diesen Hook nach jedem Import ausführen",
    "Hooks folder": "Hook-Ordner",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "Jede .py-Datei in diesem Ordner wird als Hook-Skript geladen. Es gibt keinen Standardordner",
    "User Hooks run after the built-in Hooks, in this order:":
        "Benutzer-Hooks laufen nach den eingebauten Hooks, in dieser Reihenfolge:",
    "Import Option defaults": "Standardwerte der Importoptionen",
    "Import Option defaults: the built-in ones": "Standardwerte der Importoptionen: die eingebauten",
    "Move Hook": "Hook verschieben",
    "Move the selected Hook up or down the running order":
        "Verschiebt den ausgewählten Hook in der Reihenfolge nach oben oder unten",
    "Forget Hook": "Hook aus der Liste entfernen",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "Entfernt den ausgewählten Hook aus der Liste. Wird er erneut geladen, erscheint er wieder am Ende",
    "Use the built-in defaults": "Eingebaute Standardwerte verwenden",
    "Forget the saved Import Option defaults": "Verwirft die gespeicherten Standardwerte der Importoptionen",

    # Importing
    "Import manifest.json": "manifest.json importieren",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no file chosen":
        "Importiert einen Charakter aus einem Export-Bundle: Wähle dessen manifest.json, oder öffne dessen Ordner und importiere, ohne eine Datei zu wählen",
    "Download Pillow": "Pillow installieren",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "Lädt Pillow {version} mit Blenders pip von PyPI herunter und installiert es in KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "Der Online-Zugriff ist in Blenders Einstellungen ausgeschaltet. Pillow trotzdem herunterladen?",
    "Install Pillow from local file": "Pillow aus Datei installieren",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "Installiert ein selbst heruntergeladenes Pillow-Wheel (.whl) für das Python und die Plattform dieses Blenders",
    "Reload Hooks": "Hooks neu laden",
    "Load the scripts in the hooks folder again": "Lädt die Skripte im Hook-Ordner erneut",
    "Open KKBP Log": "KKBP-Protokoll öffnen",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "Öffnet das Protokoll des letzten Imports (kkbp_cache/log/log.txt im Export-Bundle) in deinem Texteditor",
    "Save as Defaults": "Als Standard speichern",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "Verwendet die Importoptionen dieser Szene als Standard für neue Szenen und Importe per Skript",

    # Import Options
    "Delete default scene": "Standardszene löschen",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported Characters":
        "Löscht Würfel, Kamera und Licht aus Blenders Startdatei, wenn die Datei nichts außer importierten Charakteren enthält",
    "Fix body seams": "Körpernähte beheben",
    "Merges the vertices of the face and body materials that sit on top of each other (Merge by Distance). It can change the weights around the neck; without it, seams may show around the neck and down the chest when outlines are on":
        "Verschmilzt die übereinanderliegenden Vertices der Gesichts- und Körpermaterialien (Nach Abstand verschmelzen). Das kann die Gewichte am Hals verändern; ohne diese Option können bei eingeschalteten Umrandungen Nähte am Hals und auf der Brust sichtbar sein",
    "Which shaders the Character's materials use": "Welche Shader die Materialien des Charakters verwenden",
    "Keeps the Eevee shaders": "Behält die Eevee-Shader",
    "Uses a modified shader setup for Eevee": "Verwendet einen angepassten Shader-Aufbau für Eevee",
    "Cycles (toon)": "Cycles (Toon)",
    "Toon shaders for Cycles": "Toon-Shader für Cycles",
    "Cycles (classic)": "Cycles (klassisch)",
    "The classic shaders for Cycles": "Die klassischen Shader für Cycles",
    "A very simple material setup": "Ein sehr einfacher Materialaufbau",
    "Separation type": "Art der Trennung",
    "How the clothes are split into objects": "Wie die Kleidung in Objekte aufgeteilt wird",
    "One object per outfit": "Ein Objekt pro Outfit",
    "Each Outfit's clothes are one object": "Die Kleidung jedes Outfits ist ein Objekt",
    "Separate all clothing": "Alle Kleidungsstücke trennen",
    "Each piece of clothing is its own object, named by its material":
        "Jedes Kleidungsstück ist ein eigenes Objekt, benannt nach seinem Material",
    "Use outlines": "Umrandungen verwenden",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "Gibt Körper, Haaren und Kleidung für jedes ihrer Materialien ein Umrandungsmaterial",
    "Face cards": "Gesichtskarten",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts hidden":
        "Fügt vor dem Gesicht 2D-Karten für Augen und Mund hinzu, mit den Augentexturen des Charakters. Ihre Sammlung ist anfangs ausgeblendet",
    "SFW mode": "SFW-Modus",
    "Attempts to cover up some NSFW things": "Versucht, einige NSFW-Dinge zu verdecken",
    "Use Rigify armature": "Rigify-Skelett verwenden",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK armature, which is easier to export":
        "Erzeugt ein Rigify-Kontrollrig, das sich zum Animieren in Blender eignet. Ohne es behält der Charakter das FK-Skelett, das sich leichter exportieren lässt",
    "Separate eyes": "Augen trennen",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so they can show through the hair with the compositor":
        "Verschiebt Augen und Augenbrauen aus Body in eigene Objekte, deren Formschlüssel denen von Body folgen, damit sie mit dem Compositor durch die Haare hindurch sichtbar sein können",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "Umrandungen",
    "Separate Eyes": "Augen trennen",
    "Separate meshes": "Meshes trennen",
    "Convert shaders": "Shader umwandeln",

    # Tools
    "Merge Weights": "Gewichte zusammenführen",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "Gibt die Gewichte der ausgewählten Knochen an ihre Eltern und löscht die Knochen",
    "Export Prep": "Exportvorbereitung",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on its Collection":
        "Bereitet den Charakter für ein anderes Programm vor: Knochennamen, ein einfacheres Skelett, ein Atlas und ein FBX-Exporter an seiner Sammlung",
    "Atlas": "Atlas",
    "Largest atlas": "Größter Atlas",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "Ein Objekt, dessen Atlas breiter als dies wäre, erhält mehrere Atlanten. Nichts wird verkleinert",
    "Koikatsu": "Koikatsu",
    "No change": "Keine Änderung",
    "Very simple": "Sehr einfach",
    "Merges the deform details, the face and the tongue into their parents":
        "Führt die Verformungsdetails, das Gesicht und die Zunge mit ihren Eltern zusammen",
    "Merges the helper bones only": "Führt nur die Hilfsknochen zusammen",
    "Keeps every bone": "Behält jeden Knochen",
    "One atlas each for the light, dark and normal textures":
        "Je ein Atlas für die hellen, dunklen und Normalen-Texturen",
    "Atlas without the eyes": "Atlas ohne die Augen",
    "As Atlas, with the eyes keeping their own textures": "Wie Atlas, aber die Augen behalten ihre eigenen Texturen",
    "Atlas of every texture": "Atlas aller Texturen",
    "As Atlas, with the detail, alpha and colour masks too":
        "Wie Atlas, zusätzlich mit den Detail-, Alpha- und Farbmasken",
    "No atlas": "Kein Atlas",
    "The textures stay as they are": "Die Texturen bleiben, wie sie sind",
    "Run Hook": "Hook ausführen",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "Führt einen Hook, etwa Rigify, auf einem Charakter aus, der ohne ihn importiert wurde",
    "Built in": "Eingebaut",
    "Bulk Import": "Massenimport",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside each bundle folder":
        "Importiert jedes Export-Bundle in einem Ordner, jedes in einem eigenen Blender im Hintergrund, und speichert eine .blend neben jedem Bundle-Ordner",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "Legt eine Koikatsu-.fbx-Animation als neue Aktion auf das Rigify-Rig des Charakters",
    "Lengthen arms": "Arme verlängern",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "Macht die Arme 5 % länger, was in manchen Posen näher am Spiel aussieht",
    "Snap IKs": "IKs einrasten",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "Rastet die IK-Kontrollen des Rigs auf ihre FK-Pose ein und schaltet die Gliedmaßen auf IK",

    # Edit Material
    "Saturate": "Sättigen",
    "Whether the textures and colours go through the game's colour grade, as the legacy importer did":
        "Ob die Texturen und Farben durch die Farbkorrektur des Spiels laufen, wie beim alten Importer",
    "Hair and eyebrows saturate, everything else doesn't": "Haare und Augenbrauen werden gesättigt, alles andere nicht",
    "Don't saturate": "Nicht sättigen",
    "Edit Material": "Material bearbeiten",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be changed and saved":
        "Tauscht das aktive Material gegen ein bearbeitbares, das die Einfärbung des Spiels nachbaut, sodass seine Farben geändert und gespeichert werden können",
    "Cancel": "Abbrechen",
    "Puts the original material back and drops the changes":
        "Setzt das ursprüngliche Material zurück und verwirft die Änderungen",
    "Starts the edit again from the Export Bundle": "Beginnt die Bearbeitung neu aus dem Export-Bundle",
    "Bakes the edited colours into the original material's light and dark textures":
        "Backt die bearbeiteten Farben in die helle und dunkle Textur des ursprünglichen Materials",
    "Link Hair": "Haare verknüpfen",
    "Puts every hair material into edit with the active hair material's settings":
        "Versetzt jedes Haarmaterial mit den Einstellungen des aktiven Haarmaterials in die Bearbeitung",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Hooks": "Hooks",
    "Hook": "Hook",
}
