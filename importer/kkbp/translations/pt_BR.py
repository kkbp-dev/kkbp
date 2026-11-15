"""Portuguese. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "Opções de importação",
    "Pillow is required. Install it with the buttons below.": "O Pillow é necessário. Instale-o pelo painel do KKBP.",
    "Import Export Bundle": "Importar pacote de exportação",
    "No Step or Hook declares an option yet.": "Nenhum passo ou hook declara opções ainda.",
    "No hook scripts loaded": "Nenhum script de hook carregado",
    "no Hooks": "sem hooks",
    "not loaded": "não carregado",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "O importador glTF do Blender não está disponível. Ative o complemento \"glTF 2.0 format\" nas Preferências.",

    # Preferences
    "Run this Hook after each import": "Executar este hook após cada importação",
    "Hooks folder": "Pasta de hooks",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "Cada arquivo .py nesta pasta é carregado como script de hook. Não há pasta padrão",
    "User Hooks run after the built-in Hooks, in this order:":
        "Os hooks do usuário são executados depois dos hooks integrados, nesta ordem:",
    "Import Option defaults": "Padrões das opções de importação",
    "Import Option defaults: the built-in ones": "Padrões das opções de importação: os integrados",
    "Move Hook": "Mover hook",
    "Move the selected Hook up or down the running order":
        "Move o hook selecionado para cima ou para baixo na ordem de execução",
    "Forget Hook": "Remover hook da lista",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "Remove o hook selecionado da lista. Ele volta, no final, se for carregado de novo",
    "Use the built-in defaults": "Usar os padrões integrados",
    "Forget the saved Import Option defaults": "Esquece os padrões salvos das opções de importação",

    # Importing
    "Import manifest.json": "Importar manifest.json",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no file chosen":
        "Importa um personagem de um pacote de exportação: escolha o manifest.json dele, ou abra a pasta dele e importe sem escolher nenhum arquivo",
    "Download Pillow": "Instalar Pillow",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "Baixa o Pillow {version} do PyPI com o pip do Blender e o instala no KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "O acesso online está desativado nas Preferências do Blender. Baixar o Pillow mesmo assim?",
    "Install Pillow from local file": "Instalar Pillow de um arquivo",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "Instala um wheel do Pillow (.whl) que você mesmo baixou, para o Python e a plataforma deste Blender",
    "Reload Hooks": "Recarregar hooks",
    "Load the scripts in the hooks folder again": "Carrega de novo os scripts da pasta de hooks",
    "Open KKBP Log": "Abrir log do KKBP",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "Abre o log da última importação (kkbp_cache/log/log.txt no pacote de exportação) no seu editor de texto",
    "Save as Defaults": "Salvar como padrões",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "Usa as opções de importação desta cena como padrões para cenas novas e importações por script",

    # Import Options
    "Delete default scene": "Excluir cena padrão",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported Characters":
        "Exclui o cubo, a câmera e a luz do arquivo inicial do Blender, se o arquivo não tiver nada além de personagens importados",
    "Which shaders the Character's materials use": "Quais shaders os materiais do personagem usam",
    "Keeps the Eevee shaders": "Mantém os shaders do Eevee",
    "Uses a modified shader setup for Eevee": "Usa uma configuração de shaders modificada para o Eevee",
    "Cycles (toon)": "Cycles (toon)",
    "Toon shaders for Cycles": "Shaders toon para o Cycles",
    "Cycles (classic)": "Cycles (clássico)",
    "The classic shaders for Cycles": "Os shaders clássicos para o Cycles",
    "A very simple material setup": "Uma configuração de material bem simples",
    "Separation type": "Tipo de separação",
    "How the clothes are split into objects": "Como as roupas são divididas em objetos",
    "One object per outfit": "Um objeto por traje",
    "Each Outfit's clothes are one object": "As roupas de cada traje são um único objeto",
    "Separate all clothing": "Separar todas as roupas",
    "Each piece of clothing is its own object, named by its material":
        "Cada peça de roupa é um objeto próprio, com o nome do seu material",
    "Use outlines": "Usar contornos",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "Dá ao corpo, ao cabelo e às roupas um material de contorno para cada um dos seus materiais",
    "Face cards": "Cartões de rosto",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts hidden":
        "Adiciona cartões 2D de olhos e boca na frente do rosto, com as texturas dos olhos do personagem. A coleção deles começa oculta",
    "SFW mode": "Modo SFW",
    "Attempts to cover up some NSFW things": "Tenta cobrir algumas coisas NSFW",
    "Use Rigify armature": "Usar armação Rigify",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK armature, which is easier to export":
        "Gera um rig de controle Rigify, adequado para animar no Blender. Sem ele, o personagem mantém a armação FK, que é mais fácil de exportar",
    "Separate eyes": "Separar olhos",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so they can show through the hair with the compositor":
        "Move os olhos e as sobrancelhas de Body para objetos próprios, com as chaves de formato seguindo as de Body, para que possam aparecer através do cabelo com o compositor",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "Contornos",
    "Separate Eyes": "Separar olhos",
    "Separate meshes": "Separar malhas",
    "Convert shaders": "Converter shaders",

    # Tools
    "Merge Weights": "Mesclar pesos",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "Passa os pesos dos ossos selecionados para os pais deles e exclui esses ossos",
    "Export Prep": "Preparar exportação",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on its Collection":
        "Prepara o personagem para outro programa: nomes de ossos, um esqueleto mais simples, um atlas e um exportador FBX na coleção dele",
    "Atlas": "Atlas",
    "Largest atlas": "Maior atlas",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "Um objeto cujo atlas ficaria mais largo que isto recebe vários atlas. Nada é reduzido",
    "Koikatsu": "Koikatsu",
    "No change": "Sem alteração",
    "Very simple": "Muito simples",
    "Merges the deform details, the face and the tongue into their parents":
        "Mescla os detalhes de deformação, o rosto e a língua com os pais deles",
    "Merges the helper bones only": "Mescla apenas os ossos auxiliares",
    "Keeps every bone": "Mantém todos os ossos",
    "One atlas each for the light, dark and normal textures":
        "Um atlas para cada uma das texturas clara, escura e de normais",
    "Atlas without the eyes": "Atlas sem os olhos",
    "As Atlas, with the eyes keeping their own textures": "Como Atlas, mas os olhos mantêm as próprias texturas",
    "Atlas of every texture": "Atlas de todas as texturas",
    "As Atlas, with the detail, alpha and colour masks too":
        "Como Atlas, também com as máscaras de detalhe, alfa e cor",
    "No atlas": "Sem atlas",
    "The textures stay as they are": "As texturas ficam como estão",
    "Run Hook": "Executar hook",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "Executa um hook, como o Rigify, em um personagem importado sem ele",
    "Built in": "Integrado",
    "Bulk Import": "Importação em lote",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside each bundle folder":
        "Importa todos os pacotes de exportação de uma pasta, cada um em seu próprio Blender em segundo plano, e salva um .blend ao lado da pasta de cada pacote",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "Coloca uma animação .fbx do Koikatsu no rig Rigify do personagem como uma nova ação",
    "Lengthen arms": "Alongar braços",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "Deixa os braços 5% mais longos, o que fica mais parecido com o jogo em algumas poses",
    "Snap IKs": "Ajustar IKs",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "Ajusta os controles IK do rig à pose FK e muda os membros para IK",

    # Edit Material
    "Saturate": "Saturar",
    "Whether the textures and colours go through the game's colour grade, as the legacy importer did":
        "Se as texturas e as cores passam pela gradação de cor do jogo, como fazia o importador antigo",
    "Hair and eyebrows saturate, everything else doesn't": "Cabelo e sobrancelhas saturam, o resto não",
    "Don't saturate": "Não saturar",
    "Edit Material": "Editar material",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be changed and saved":
        "Troca o material ativo por um editável que reconstrói a coloração do jogo, para que as cores possam ser alteradas e salvas",
    "Cancel": "Cancelar",
    "Puts the original material back and drops the changes":
        "Coloca o material original de volta e descarta as alterações",
    "Starts the edit again from the Export Bundle": "Recomeça a edição a partir do pacote de exportação",
    "Bakes the edited colours into the original material's light and dark textures":
        "Faz o bake das cores editadas nas texturas clara e escura do material original",
    "Link Hair": "Vincular cabelo",
    "Puts every hair material into edit with the active hair material's settings":
        "Coloca todos os materiais de cabelo em edição com as configurações do material de cabelo ativo",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Hooks": "Hooks",
    "Hook": "Hook",
}
