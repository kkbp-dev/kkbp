"""Japanese. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "インポートオプション",
    "Pillow is required. Install it with the buttons below.": "Pillowが必要です。このパネルからインストールしてください。",
    "Import Export Bundle": "エクスポートバンドルをインポート",
    "No Step or Hook declares an option yet.": "オプションを持つステップやフックはまだありません。", 
    "No hook scripts loaded": "フックスクリプトは読み込まれていません",
    "no Hooks": "フックなし",
    "not loaded": "未読み込み",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "BlenderのglTFインポーターが使えません。プリファレンスで「glTF 2.0 format」アドオンを有効化。",

    # Preferences
    "Run this Hook after each import": "インポートの後にこのフックを実行する",
    "Hooks folder": "フックフォルダー",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "このフォルダー内のすべての.pyファイルがフックスクリプトとして読み込まれます。既定のフォルダーはありません",
    "User Hooks run after the built-in Hooks, in this order:": "ユーザーフックは組み込みフックの後に、次の順番で実行されます:",
    "Import Option defaults": "インポートオプションの既定値",
    "Import Option defaults: the built-in ones": "インポートオプションの既定値: 組み込みの値",
    "Move Hook": "フックを移動",
    "Move the selected Hook up or down the running order": "選択したフックの実行順を上または下に移動する",
    "Forget Hook": "フックを一覧から外す",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "選択したフックを一覧から外します。もう一度読み込まれると、一覧の最後に戻ります",
    "Use the built-in defaults": "組み込みの既定値を使う", #not visible text
    "Forget the saved Import Option defaults": "保存したインポートオプションの既定値を消去する", #not visible text

    # Importing
    "Import manifest.json": "manifest.jsonをインポート",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no "
    "file chosen":
        "エクスポートバンドルからキャラクターをインポートします。manifest.jsonを選ぶか、"
        "バンドルのフォルダーを開いてファイルを選ばずにインポートボタン使えて",
    "Download Pillow": "Pillowをダウンロード",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "Blenderのpipを使ってPyPIからPillow {version}をダウンロードし、KKBPにインストールする",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "Blenderのプリファレンスでオンラインアクセスが無効になっています。それでもPillowをダウンロードしますか?",
    "Install Pillow from local file": "ファイルからPillowをインストール",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "自分でダウンロードしたPillowのwheel (.whl) をインストールします。このBlenderのPythonとプラットフォーム用のものを選んでください",
    "Reload Hooks": "フックを再読み込み",
    "Load the scripts in the hooks folder again": "フックフォルダー内のスクリプトを読み込み直す",
    "Open KKBP Log": "KKBPのログを開く",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "最後のインポートのログ (エクスポートバンドル内の kkbp_cache/log/log.txt) をテキストエディターで開く",
    "Save as Defaults": "既定値として保存",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "このシーンのインポートオプションを、新しいシーンとスクリプトからのインポートの既定値にする",

    # Import Options
    "Delete default scene": "デフォルトシーンを削除",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported "
    "Characters":
        "ファイルにインポートしたキャラクター以外何もない場合、Blenderのスタートアップファイルのキューブ、カメラ、ライトを削除する",
    "Which shaders the Character's materials use": "キャラクターのマテリアルに使うシェーダー",
    "Keeps the Eevee shaders": "Eeveeシェーダーにする",
    "Uses a modified shader setup for Eevee": "別のEeveeシェーダー設定にする",
    "Cycles (toon)": "Cycles (トゥーン)",
    "Toon shaders for Cycles": "Cycles用のトゥーンシェーダー",
    "Cycles (classic)": "Cycles (クラシック)",
    "The classic shaders for Cycles": "Cycles用のクラシックシェーダー",
    "A very simple material setup": "とても簡易なマテリアル設定",
    "Separation type": "分離タイプ",
    "How the clothes are split into objects": "服の分離方法", 
    "One object per outfit": "1コーデにつき1オブジェクト",
    "Each Outfit's clothes are one object": "コーデごとに服を1つのオブジェクトにする",
    "Separate all clothing": "すべての服を別々にする",
    "Each piece of clothing is its own object, named by its material": "服を1着ずつ別のオブジェクトにし、マテリアル名を付ける",
    "Use outlines": "アウトラインを使う",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "体、髪、服のマテリアルごとにアウトラインマテリアルを付ける",
    "Face cards": "顔カード",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts "
    "hidden":
        "キャラクターの目のテクスチャで、2Dの目と口のカードを顔の前に追加します。最初はカードのコレクションがシーンに除外される",
    "SFW mode": "エロ無しモード",
    "Attempts to cover up some NSFW things": "エロの部分をなるべく隠す",
    "Use Rigify armature": "Rigifyアーマチュアにする",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK "
    "armature, which is easier to export":
        "Blenderでのアニメーションに向いたRigifyのコントロールリグを生成します。無効にするとキャラクターはFKアーマチュアのままで、"
        "エクスポートしやすくなります",
    "Separate eyes": "目を分離",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so "
    "they can show through the hair with the compositor":
        "目と眉をBodyから別のオブジェクトに移します。Bodyは目と眉のシェイプキーをまだ持ってます。コンポジターで目と眉を髪にオーバーレイできます",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "アウトライン",
    "Separate Eyes": "目を分離",
    "Separate meshes": "メッシュを分離",
    "Convert shaders": "シェーダーを変換",

    # Tools
    "Merge Weights": "ウェイトをマージ", #never displayed
    "Gives the selected bones' weights to their parents and deletes the bones": #never displayed
        "選択したボーンのウェイトを親ボーンに渡し、そのボーンを削除する",
    "Export Prep": "エクスポートの準備",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on "
    "its Collection":
        "キャラクターを他のソフト向けに準備します: ボーン名、簡略化したスケルトン、アトラス、コレクションのFBXエクスポーター",
    "Atlas": "アトラス",
    "Largest atlas": "アトラスの最大サイズ",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "アトラスがこの幅を超えるオブジェクトには複数のアトラスが作られます。縮小はされません",
    "Koikatsu": "コイカツ",
    "No change": "変更なし",
    "Very simple": "超シンプル",
    "Merges the deform details, the face and the tongue into their parents": "変形の細部、顔、舌のボーンを親にマージする",
    "Merges the helper bones only": "補助ボーンだけをマージする",
    "Keeps every bone": "すべてのボーンを残す",
    "One atlas each for the light, dark and normal textures": "ライト、ダーク、ノーマルのテクスチャごとにアトラスを1つ作る",
    "Atlas without the eyes": "アトラス (目は別)",
    "As Atlas, with the eyes keeping their own textures": "アトラスと同じですが、目は元のテクスチャのままにする",
    "Atlas of every texture": "すべてのテクスチャのアトラス",
    "As Atlas, with the detail, alpha and colour masks too": "アトラスと同じですが、ディテール、アルファ、カラーマスクも含める",
    "No atlas": "アトラスなし",
    "The textures stay as they are": "テクスチャはそのままにする",
    "Run Hook": "フックを実行",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "フックをインポートしたキャラクターに実行する",
    "Built in": "組み込み",
    "Bulk Import": "バルクインポート",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside "
    "each bundle folder":
        "フォルダー内のすべてのエクスポートバンドルを、それぞれバックグラウンドの別のBlenderでインポートし、"
        "各バンドルフォルダーの隣に.blendを保存する",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "コイカツの.fbxアニメーションを、キャラクターのRigifyリグに新しいアクションとして付ける",
    "Lengthen arms": "腕を伸ばす",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "腕を5%長くします。ポーズによってはゲームの見た目に近くなります",
    "Snap IKs": "IKをスナップ",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "リグのIKコントロールをFKのポーズにスナップし、手足をIKに切り替える",

    # Edit Material
    "Saturate": "彩度補正", #will be removed
    "Whether the textures and colours go through the game's colour grade, as the legacy importer did":
        "従来のインポーターと同じように、テクスチャと色にゲームのカラーグレーディングをかけるかどうか", #will be removed
    "Saturate. A material that follows the game's shaders takes its colours as they show instead, so the eyedropper can pick them":
        "彩度補正。ゲームのシェーダーに従うマテリアルでは、代わりに表示どおりの色を使うため、スポイトで色を拾えます",
    "Hair and eyebrows saturate, everything else doesn't": "髪と眉は彩度補正し、他はしない", #will be removed
    "Don't saturate": "彩度補正しない", #will be removed
    "Edit Material": "マテリアルを編集",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be "
    "changed and saved":
        "アクティブなマテリアルを、ゲームの色付けを再現する編集用マテリアルに入れ替えます。色を変更して保存できます",
    "Cancel": "キャンセル",  # Blender's own word; it has none for a button of this name
    "Puts the original material back and drops the changes": "元のマテリアルに戻し、変更を破棄する",
    "Starts the edit again from the Export Bundle": "エクスポートバンドルから編集をやり直す",
    "Bakes the edited colours into the original material's light and dark textures":
        "編集した色を元のマテリアルのライトとダークのテクスチャに保存する",
    "Link Hair": "他の髪マテリアルをアップデート",
    "Puts every hair material into edit with the active hair material's settings":
        "アクティブな髪マテリアルの設定で、すべての髪マテリアルを編集状態にする",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Hooks": "フック",
    "Hook": "フック",
}
