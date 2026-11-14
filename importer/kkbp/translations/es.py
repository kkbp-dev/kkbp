"""Spanish. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "Opciones de importación",
    "Pillow is required. Install it from the KKBP panel.": "Se necesita Pillow. Instálalo desde el panel de KKBP.",
    "Import Export Bundle": "Importar paquete de exportación",
    "No Step or Hook declares an option yet.": "Ningún paso o hook declara opciones todavía.",
    "No hook scripts loaded": "No hay scripts de hooks cargados",
    "no Hooks": "sin hooks",
    "not loaded": "no cargado",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "El importador glTF de Blender no está disponible. Activa el complemento «glTF 2.0 format» en Preferencias.",

    # Preferences
    "Run this Hook after each import": "Ejecutar este hook después de cada importación",
    "Hooks folder": "Carpeta de hooks",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "Cada archivo .py de esta carpeta se carga como script de hook. No hay carpeta predeterminada",
    "User Hooks run after the built-in Hooks, in this order:":
        "Los hooks de usuario se ejecutan después de los integrados, en este orden:",
    "Import Option defaults": "Valores predeterminados de las opciones de importación",
    "Import Option defaults: the built-in ones":
        "Valores predeterminados de las opciones de importación: los integrados",
    "Move Hook": "Mover hook",
    "Move the selected Hook up or down the running order":
        "Mueve el hook seleccionado hacia arriba o hacia abajo en el orden de ejecución",
    "Forget Hook": "Quitar hook de la lista",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "Quita el hook seleccionado de la lista. Si se vuelve a cargar, reaparece al final",
    "Use the built-in defaults": "Usar los valores integrados",
    "Forget the saved Import Option defaults":
        "Olvida los valores predeterminados guardados de las opciones de importación",

    # Importing
    "Import manifest.json": "Importar manifest.json",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no file chosen":
        "Importa un personaje desde un paquete de exportación: elige su manifest.json, o abre su carpeta e importa sin elegir ningún archivo",
    "Install Pillow": "Instalar Pillow",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "Descarga Pillow {version} de PyPI con el pip de Blender y lo instala en KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "El acceso en línea está desactivado en las Preferencias de Blender. ¿Descargar Pillow de todos modos?",
    "Install Pillow from File": "Instalar Pillow desde archivo",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "Instala un wheel de Pillow (.whl) que hayas descargado tú, para el Python y la plataforma de este Blender",
    "Reload Hooks": "Recargar hooks",
    "Load the scripts in the hooks folder again": "Vuelve a cargar los scripts de la carpeta de hooks",
    "Open KKBP Log": "Abrir registro de KKBP",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "Abre el registro de la última importación (kkbp_cache/log/log.txt en el paquete de exportación) en tu editor de texto",
    "Save as Defaults": "Guardar como predeterminados",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "Usa las opciones de importación de esta escena como valores predeterminados para escenas nuevas e importaciones por script",

    # Import Options
    "Joint corrections": "Correcciones de articulaciones",
    "Moves the elbow, knee, shoulder, hip and other correction bones with the limbs, as the game does":
        "Mueve los huesos de corrección de codos, rodillas, hombros, caderas y otros junto con las extremidades, como hace el juego",
    "Delete default scene": "Eliminar escena predeterminada",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported Characters":
        "Elimina el cubo, la cámara y la luz del archivo de inicio de Blender, si el archivo no contiene nada más que personajes importados",
    "Fix body seams": "Corregir costuras del cuerpo",
    "Merges the vertices of the face and body materials that sit on top of each other (Merge by Distance). It can change the weights around the neck; without it, seams may show around the neck and down the chest when outlines are on":
        "Fusiona los vértices de los materiales de la cara y del cuerpo que están superpuestos (Fusionar por distancia). Puede cambiar los pesos alrededor del cuello; sin esto, pueden verse costuras alrededor del cuello y en el pecho cuando los contornos están activados",
    "Which shaders the Character's materials use": "Qué shaders usan los materiales del personaje",
    "Keeps the Eevee shaders": "Mantiene los shaders de Eevee",
    "Uses a modified shader setup for Eevee": "Usa una configuración de shaders modificada para Eevee",
    "Cycles (toon)": "Cycles (toon)",
    "Toon shaders for Cycles": "Shaders toon para Cycles",
    "Cycles (classic)": "Cycles (clásico)",
    "The classic shaders for Cycles": "Los shaders clásicos para Cycles",
    "A very simple material setup": "Una configuración de material muy simple",
    "Separation type": "Tipo de separación",
    "How the clothes are split into objects": "Cómo se divide la ropa en objetos",
    "One object per outfit": "Un objeto por atuendo",
    "Each Outfit's clothes are one object": "La ropa de cada atuendo es un solo objeto",
    "Separate all clothing": "Separar toda la ropa",
    "Each piece of clothing is its own object, named by its material":
        "Cada prenda es un objeto propio, con el nombre de su material",
    "Use outlines": "Usar contornos",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "Da al cuerpo, al pelo y a la ropa un material de contorno por cada uno de sus materiales",
    "Face cards": "Tarjetas de cara",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts hidden":
        "Añade tarjetas 2D de ojos y boca delante de la cara, con las texturas de ojos del personaje. Su colección empieza oculta",
    "SFW mode": "Modo SFW",
    "Attempts to cover up some NSFW things": "Intenta ocultar algunas cosas NSFW",
    "Use Rigify armature": "Usar esqueleto Rigify",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK armature, which is easier to export":
        "Genera un rig de control Rigify, adecuado para animar en Blender. Sin él, el personaje conserva el esqueleto FK, que es más fácil de exportar",
    "Teeth bones": "Huesos de los dientes",
    "Gives the Rigify rig five controls for each row of teeth, and moves the teeth's weights onto new bones under the mouth bones. Does nothing without Rigify":
        "Da al rig de Rigify cinco controles por cada fila de dientes y mueve los pesos de los dientes a huesos nuevos bajo los huesos de la boca. No hace nada sin Rigify",
    "Separate eyes": "Separar ojos",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so they can show through the hair with the compositor":
        "Mueve los ojos y las cejas de Body a objetos propios, con sus formas clave siguiendo las de Body, para que puedan verse a través del pelo con el compositor",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "Contornos",
    "Separate Eyes": "Separar ojos",
    "Separate meshes": "Separar mallas",
    "Convert shaders": "Convertir shaders",

    # Tools
    "Merge Weights": "Fusionar pesos",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "Da los pesos de los huesos seleccionados a sus padres y elimina esos huesos",
    "Export Prep": "Preparar exportación",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on its Collection":
        "Prepara el personaje para otro programa: nombres de huesos, un esqueleto más simple, un atlas y un exportador FBX en su colección",
    "Atlas": "Atlas",
    "Largest atlas": "Atlas más grande",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "Un objeto cuyo atlas sería más ancho que esto recibe varios atlas. No se reduce nada",
    "Koikatsu": "Koikatsu",
    "No change": "Sin cambios",
    "Very simple": "Muy simple",
    "Merges the deform details, the face and the tongue into their parents":
        "Fusiona los detalles de deformación, la cara y la lengua con sus padres",
    "Merges the helper bones only": "Fusiona solo los huesos auxiliares",
    "Keeps every bone": "Conserva todos los huesos",
    "One atlas each for the light, dark and normal textures":
        "Un atlas para cada una de las texturas clara, oscura y de normales",
    "Atlas without the eyes": "Atlas sin los ojos",
    "As Atlas, with the eyes keeping their own textures": "Como Atlas, pero los ojos conservan sus propias texturas",
    "Atlas of every texture": "Atlas de todas las texturas",
    "As Atlas, with the detail, alpha and colour masks too":
        "Como Atlas, también con las máscaras de detalle, alfa y color",
    "No atlas": "Sin atlas",
    "The textures stay as they are": "Las texturas se quedan como están",
    "Run Hook": "Ejecutar hook",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "Ejecuta un hook, como Rigify, en un personaje importado sin él",
    "Built in": "Integrado",
    "Bulk Import": "Importación por lotes",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside each bundle folder":
        "Importa todos los paquetes de exportación de una carpeta, cada uno en su propio Blender en segundo plano, y guarda un .blend junto a la carpeta de cada paquete",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "Pone una animación .fbx de Koikatsu en el rig Rigify del personaje como una acción nueva",
    "Lengthen arms": "Alargar brazos",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "Hace los brazos un 5% más largos, lo que se parece más al juego en algunas poses",
    "Snap IKs": "Ajustar IK",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "Ajusta los controles IK del rig a su pose FK y cambia las extremidades a IK",

    # Edit Material
    "Saturate": "Saturar",
    "Whether the textures and colours go through the game's colour grade, as the legacy importer did":
        "Si las texturas y los colores pasan por la gradación de color del juego, como hacía el importador antiguo",
    "Hair and eyebrows saturate, everything else doesn't": "El pelo y las cejas se saturan, lo demás no",
    "Don't saturate": "No saturar",
    "Edit Material": "Editar material",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be changed and saved":
        "Cambia el material activo por uno editable que reconstruye el coloreado del juego, para poder cambiar y guardar sus colores",
    "Cancel": "Cancelar",
    "Puts the original material back and drops the changes":
        "Vuelve a poner el material original y descarta los cambios",
    "Starts the edit again from the Export Bundle": "Empieza la edición de nuevo desde el paquete de exportación",
    "Bakes the edited colours into the original material's light and dark textures":
        "Hornea los colores editados en las texturas clara y oscura del material original",
    "Link Hair": "Vincular pelo",
    "Puts every hair material into edit with the active hair material's settings":
        "Pone todos los materiales de pelo en edición con los ajustes del material de pelo activo",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Hooks": "Hooks",
    "Hook": "Hook",
}
