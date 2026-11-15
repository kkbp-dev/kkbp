"""Simplified Chinese. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "导入选项",
    "Pillow is required. Install it with the buttons below.": "需要 Pillow。请在 KKBP 面板中安装。",
    "Import Export Bundle": "导入导出包",
    "No Step or Hook declares an option yet.": "还没有带选项的步骤或钩子。",
    "No hook scripts loaded": "没有加载钩子脚本",
    "no Hooks": "没有钩子",
    "not loaded": "未加载",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "Blender 的 glTF 导入器不可用。请在偏好设置中启用“glTF 2.0 format”插件。",

    # Preferences
    "Run this Hook after each import": "每次导入后运行此钩子",
    "Hooks folder": "钩子文件夹",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "此文件夹中的每个 .py 文件都会作为钩子脚本加载。没有默认文件夹",
    "User Hooks run after the built-in Hooks, in this order:": "用户钩子在内置钩子之后按以下顺序运行:",
    "Import Option defaults": "导入选项的默认值",
    "Import Option defaults: the built-in ones": "导入选项的默认值: 内置值",
    "Move Hook": "移动钩子",
    "Move the selected Hook up or down the running order": "在运行顺序中上移或下移所选钩子",
    "Forget Hook": "从列表移除钩子",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "从列表中移除所选钩子。如果再次加载，它会回到列表末尾",
    "Use the built-in defaults": "使用内置默认值",
    "Forget the saved Import Option defaults": "清除已保存的导入选项默认值",

    # Importing
    "Import manifest.json": "导入 manifest.json",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no "
    "file chosen":
        "从导出包导入角色: 选择其中的 manifest.json，或打开导出包文件夹后不选文件直接导入",
    "Download Pillow": "安装 Pillow",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "用 Blender 的 pip 从 PyPI 下载 Pillow {version} 并安装到 KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "Blender 偏好设置中已关闭在线访问。仍要下载 Pillow 吗?",
    "Install Pillow from local file": "从文件安装 Pillow",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "安装你自己下载的 Pillow wheel (.whl)，需与此 Blender 的 Python 和平台相符",
    "Reload Hooks": "重新加载钩子",
    "Load the scripts in the hooks folder again": "重新加载钩子文件夹中的脚本",
    "Open KKBP Log": "打开 KKBP 日志",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "用文本编辑器打开上次导入的日志 (导出包中的 kkbp_cache/log/log.txt)",
    "Save as Defaults": "保存为默认值",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "将此场景的导入选项用作新场景和脚本导入的默认值",

    # Import Options
    "Delete default scene": "删除默认场景",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported "
    "Characters":
        "如果文件中除导入的角色外没有其他内容，则删除 Blender 启动文件中的立方体、摄像机和灯光",
    "Which shaders the Character's materials use": "角色材质使用的着色器",
    "Keeps the Eevee shaders": "保留 Eevee 着色器",
    "Uses a modified shader setup for Eevee": "使用修改过的 Eevee 着色器设置",
    "Cycles (toon)": "Cycles (卡通)",
    "Toon shaders for Cycles": "用于 Cycles 的卡通着色器",
    "Cycles (classic)": "Cycles (经典)",
    "The classic shaders for Cycles": "用于 Cycles 的经典着色器",
    "A very simple material setup": "非常简单的材质设置",
    "Separation type": "分类类型",
    "How the clothes are split into objects": "如何将衣服拆分为对象",
    "One object per outfit": "每套服装一个对象",
    "Each Outfit's clothes are one object": "每套服装的衣服合为一个对象",
    "Separate all clothing": "分开所有衣服",
    "Each piece of clothing is its own object, named by its material": "每件衣服都是单独的对象，以其材质命名",
    "Use outlines": "使用轮廓线",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "为身体、头发和衣服的每个材质添加一个轮廓线材质",
    "Face cards": "脸部卡片",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts "
    "hidden":
        "在脸部前方添加使用角色眼睛贴图的 2D 眼睛和嘴巴卡片。它们的集合默认隐藏",
    "SFW mode": "和谐模式",
    "Attempts to cover up some NSFW things": "尝试遮盖一些不和谐的内容",
    "Use Rigify armature": "使用Rigify骨架",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK "
    "armature, which is easier to export":
        "生成适合在 Blender 中制作动画的 Rigify 控制绑定。禁用时角色保留 FK 骨架，更便于导出",
    "Separate eyes": "分离眼睛",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so "
    "they can show through the hair with the compositor":
        "将眼睛和眉毛从 Body 移到单独的对象中，其形态键跟随 Body，以便用合成器让它们透过头发显示",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "轮廓线",
    "Separate Eyes": "分离眼睛",
    "Separate meshes": "分离网格",
    "Convert shaders": "转换着色器",

    # Tools
    "Merge Weights": "合并权重",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "将所选骨骼的权重交给其父骨骼，并删除这些骨骼",
    "Export Prep": "导出准备",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on "
    "its Collection":
        "为其他软件准备角色: 骨骼名称、简化的骨架、图集，以及其集合上的 FBX 导出器",
    "Atlas": "图集",
    "Largest atlas": "最大图集尺寸",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "图集宽度超过此值的对象会得到多个图集。不会缩小任何贴图",
    "Koikatsu": "恋活",
    "No change": "无更改",
    "Very simple": "非常简单",
    "Merges the deform details, the face and the tongue into their parents": "将形变细节、脸部和舌头的骨骼合并到其父骨骼",
    "Merges the helper bones only": "只合并辅助骨骼",
    "Keeps every bone": "保留所有骨骼",
    "One atlas each for the light, dark and normal textures": "亮色、暗色和法线贴图各生成一个图集",
    "Atlas without the eyes": "图集 (不含眼睛)",
    "As Atlas, with the eyes keeping their own textures": "与图集相同，但眼睛保留自己的贴图",
    "Atlas of every texture": "所有贴图的图集",
    "As Atlas, with the detail, alpha and colour masks too": "与图集相同，并包含细节、透明和颜色遮罩",
    "No atlas": "不生成图集",
    "The textures stay as they are": "贴图保持原样",
    "Run Hook": "运行钩子",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "对导入时未使用某个钩子 (例如 Rigify) 的角色运行该钩子",
    "Built in": "内置",
    "Bulk Import": "批量导入",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside "
    "each bundle folder":
        "导入文件夹中的所有导出包，每个都在后台单独的 Blender 中导入，并在各导出包文件夹旁保存一个 .blend",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "将恋活的 .fbx 动画作为新动作添加到角色的 Rigify 绑定上",
    "Lengthen arms": "加长手臂",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "将手臂加长 5%，在某些姿势下更接近游戏中的样子",
    "Snap IKs": "吸附 IK",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "将绑定的 IK 控制器吸附到 FK 姿势，并将四肢切换到 IK",

    # Edit Material
    "Saturate": "饱和度校正",
    "Whether the textures and colours go through the game's colour grade, as the legacy importer did":
        "是否像旧版导入器那样，让贴图和颜色经过游戏的调色",
    "Hair and eyebrows saturate, everything else doesn't": "头发和眉毛进行饱和度校正，其他不进行",
    "Don't saturate": "不进行饱和度校正",
    "Edit Material": "编辑材质",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be "
    "changed and saved":
        "将活动材质替换为可编辑的材质，它会重建游戏的着色方式，以便修改并保存颜色",
    "Cancel": "取消",  # Blender's own word; it has none for a button of this name
    "Puts the original material back and drops the changes": "恢复原始材质并放弃更改",
    "Starts the edit again from the Export Bundle": "从导出包重新开始编辑",
    "Bakes the edited colours into the original material's light and dark textures":
        "将编辑后的颜色烘焙到原始材质的亮色和暗色贴图中",
    "Link Hair": "更新其他头发材质",
    "Puts every hair material into edit with the active hair material's settings":
        "用活动头发材质的设置，将所有头发材质置于编辑状态",
}

# In the "KKBP" translation context, where Blender's own word means something else (its "Hook" is the
# modifier, 钩挂).
IN_CONTEXT = {
    "Hooks": "钩子",
    "Hook": "钩子",
}
