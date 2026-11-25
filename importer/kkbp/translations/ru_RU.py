"""Russian. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #2).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "Параметры импорта",
    "Pillow is required. Install it with the buttons below.": "Требуется Pillow. Установите его из панели KKBP.",
    "Import Export Bundle": "Импортировать пакет экспорта",
    "No Step or Hook declares an option yet.": "Пока ни один шаг или хук не объявил параметров.",
    "No hook scripts loaded": "Скрипты хуков не загружены",
    "no Hooks": "нет хуков",
    "not loaded": "не загружен",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "Импортёр glTF в Blender недоступен. Включите аддон «glTF 2.0 format» в настройках.",

    # Preferences
    "Run this Hook after each import": "Запускать этот хук после каждого импорта",
    "Hooks folder": "Папка хуков",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "Каждый файл .py в этой папке загружается как скрипт хука. Папки по умолчанию нет",
    "User Hooks run after the built-in Hooks, in this order:":
        "Пользовательские хуки запускаются после встроенных в таком порядке:",
    "Import Option defaults": "Значения параметров импорта по умолчанию",
    "Import Option defaults: the built-in ones": "Значения параметров импорта по умолчанию: встроенные",
    "Move Hook": "Переместить хук",
    "Move the selected Hook up or down the running order": "Переместить выбранный хук выше или ниже в порядке запуска",
    "Forget Hook": "Убрать хук из списка",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "Убирает выбранный хук из списка. Если он будет загружен снова, он вернётся в конец списка",
    "Use the built-in defaults": "Использовать встроенные значения",
    "Forget the saved Import Option defaults": "Сбросить сохранённые значения параметров импорта по умолчанию",

    # Importing
    "Import manifest.json": "Импортировать manifest.json",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no file chosen":
        "Импортирует персонажа из пакета экспорта: выберите его manifest.json или откройте его папку и импортируйте, не выбирая файл",
    "Download Pillow": "Установить Pillow",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "Скачать Pillow {version} с PyPI с помощью pip из Blender и установить его в KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "Доступ в интернет отключён в настройках Blender. Всё равно скачать Pillow?",
    "Install Pillow from local file": "Установить Pillow из файла",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "Установить wheel-файл Pillow (.whl), который вы скачали сами, для Python и платформы этого Blender",
    "Reload Hooks": "Перезагрузить хуки",
    "Load the scripts in the hooks folder again": "Заново загрузить скрипты из папки хуков",
    "Open KKBP Log": "Открыть журнал KKBP",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "Открыть журнал последнего импорта (kkbp_cache/log/log.txt в пакете экспорта) в текстовом редакторе",
    "Save as Defaults": "Сохранить как значения по умолчанию",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "Использовать параметры импорта этой сцены как значения по умолчанию для новых сцен и импорта из скриптов",

    # Import Options
    "Delete default scene": "Удалить сцену по умолчанию",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported Characters":
        "Удаляет куб, камеру и источник света из стартового файла Blender, если в файле нет ничего, кроме импортированных персонажей",
    "Which shaders the Character's materials use": "Какие шейдеры используют материалы персонажа",
    "Keeps the Eevee shaders": "Оставляет шейдеры Eevee",
    "Uses a modified shader setup for Eevee": "Использует изменённую настройку шейдеров для Eevee",
    "Cycles (toon)": "Cycles (тун)",
    "Toon shaders for Cycles": "Тун-шейдеры для Cycles",
    "Cycles (classic)": "Cycles (классический)",
    "The classic shaders for Cycles": "Классические шейдеры для Cycles",
    "A very simple material setup": "Очень простая настройка материала",
    "Separation type": "Тип разделения",
    "How the clothes are split into objects": "Как одежда делится на объекты",
    "One object per outfit": "Один объект на наряд",
    "Each Outfit's clothes are one object": "Одежда каждого наряда — один объект",
    "Separate all clothing": "Разделить всю одежду",
    "Each piece of clothing is its own object, named by its material":
        "Каждый предмет одежды — отдельный объект, названный по своему материалу",
    "Use outlines": "Использовать обводки",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "Добавляет телу, волосам и одежде материал обводки для каждого их материала",
    "Face cards": "Карточки лица",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts hidden":
        "Добавляет перед лицом 2D-карточки глаз и рта с текстурами глаз персонажа. Их коллекция изначально скрыта",
    "SFW mode": "Режим SFW",
    "Attempts to cover up some NSFW things": "Пытается скрыть некоторые элементы NSFW",
    "Use Rigify armature": "Использовать арматуру Rigify",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK armature, which is easier to export":
        "Создаёт управляющий риг Rigify, подходящий для анимации в Blender. Без него персонаж сохраняет FK-арматуру, которую проще экспортировать",
    "Low poly clothes and hair": "Низкополигональные одежда и волосы",
    "Adds a copy of each Outfit's clothes and hair with fewer faces and no outline, in a hidden Collection beside the Outfit's, for smoother playback":
        "Добавляет копию одежды и волос каждого наряда с меньшим числом граней и без обводки, в скрытую коллекцию рядом с коллекцией наряда, для более плавного воспроизведения",
    "No low poly copies": "Без низкополигональных копий",
    "Light (50%)": "Слабо (50%)",
    "Medium (25%)": "Средне (25%)",
    "Strong (10%)": "Сильно (10%)",
    "The copies keep half of the faces": "Копии сохраняют половину граней",
    "The copies keep a quarter of the faces": "Копии сохраняют четверть граней",
    "The copies keep a tenth of the faces": "Копии сохраняют десятую часть граней",
    "Separate eyes": "Отделить глаза",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so they can show through the hair with the compositor":
        "Переносит глаза и брови из Body в отдельные объекты, их ключи формы следуют за ключами Body, чтобы с помощью композитора их можно было показать сквозь волосы",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "Обводки",
    "Low poly": "Низкополигональные копии",
    "Separate Eyes": "Отделение глаз",
    "Separate meshes": "Разделение мешей",
    "Convert shaders": "Преобразование шейдеров",

    # Tools
    "Merge Weights": "Объединить веса",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "Передаёт веса выбранных костей их родителям и удаляет эти кости",
    "Export Prep": "Подготовка к экспорту",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on its Collection":
        "Готовит персонажа для другой программы: имена костей, упрощённый скелет, атлас и экспортёр FBX на его коллекции",
    "Atlas": "Атлас",
    "Largest atlas": "Наибольший атлас",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "Объект, чей атлас был бы шире этого размера, получает несколько атласов. Ничего не уменьшается",
    "Koikatsu": "Koikatsu",
    "No change": "Без изменений",
    "Very simple": "Очень простой",
    "Merges the deform details, the face and the tongue into their parents":
        "Объединяет с родителями кости деталей деформации, лица и языка",
    "Merges the helper bones only": "Объединяет только вспомогательные кости",
    "Keeps every bone": "Сохраняет все кости",
    "One atlas each for the light, dark and normal textures":
        "По одному атласу для светлых, тёмных текстур и текстур нормалей",
    "Atlas without the eyes": "Атлас без глаз",
    "As Atlas, with the eyes keeping their own textures": "Как «Атлас», но глаза сохраняют собственные текстуры",
    "Atlas of every texture": "Атлас всех текстур",
    "As Atlas, with the detail, alpha and colour masks too":
        "Как «Атлас», но также с масками детализации, альфа и цвета",
    "No atlas": "Без атласа",
    "The textures stay as they are": "Текстуры остаются как есть",
    "Run Hook": "Запустить хук",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "Запускает хук, например Rigify, на персонаже, импортированном без него",
    "Built in": "Встроенный",
    "Bulk Import": "Пакетный импорт",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside each bundle folder":
        "Импортирует все пакеты экспорта из папки, каждый в отдельном фоновом Blender, и сохраняет .blend рядом с папкой каждого пакета",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "Накладывает анимацию Koikatsu в формате .fbx на риг Rigify персонажа как новое действие",
    "Lengthen arms": "Удлинить руки",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "Делает руки на 5% длиннее, что в некоторых позах ближе к игре",
    "Snap IKs": "Привязать IK",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "Привязывает IK-контролы рига к их FK-позе и переключает конечности на IK",

    # Edit Material
    "Saturate": "Насыщенность",
    "What Edit Material does with the colours: Shown colours for a material that follows the game's shaders, Saturate for one from a modded shader":
        "Что «Редактировать материал» делает с цветами: видимые цвета для материала по шейдерам игры, насыщенность для материала модифицированного шейдера",
    "Shown colours": "Видимые цвета",
    "Each colour is the colour as it shows, so the eyedropper can pick it":
        "Каждый цвет — это цвет таким, каким он виден, поэтому его можно взять пипеткой",
    "Each colour is the game's own value, which shows graded and stronger":
        "Каждый цвет — собственное значение игры, которое после цветокоррекции выглядит насыщеннее",
    "Don't saturate": "Не насыщать",
    "Edit Material": "Редактировать материал",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be changed and saved":
        "Заменяет активный материал редактируемым, который воссоздаёт раскраску игры, чтобы его цвета можно было изменить и сохранить",
    "Cancel": "Отмена",
    "Puts the original material back and drops the changes": "Возвращает исходный материал и отбрасывает изменения",
    "Starts the edit again from the Export Bundle": "Начинает редактирование заново из пакета экспорта",
    "Bakes the edited colours into the original material's light and dark textures":
        "Запекает изменённые цвета в светлую и тёмную текстуры исходного материала",
    "Link Hair": "Связать волосы",
    "Puts every hair material into edit with the active hair material's settings":
        "Переводит все материалы волос в режим редактирования с настройками активного материала волос",
    # The Face panel (the Rigify Hook's face rig)
    "Face Preset": "Пресет лица",
    "Poses the face as this emotion. Shift-click adds it on top of the face as it is": "Придаёт лицу эту эмоцию. Shift+щелчок добавляет её к текущему лицу",
    "Add": "Добавить",
    "Adds the preset on top of the face as it is": "Добавляет пресет к текущему лицу",
    "Reset Face": "Сбросить лицо",
    "Puts every face control back and every face slider to 0": "Возвращает все контроллеры лица на место и все ползунки лица в 0",
    "Key Face": "Ключ лица",
    "Keys every face control and face slider at the current frame": "Ставит ключи на все контроллеры и ползунки лица в текущем кадре",
    "Emotions": "Эмоции",
    "Eyes": "Глаза",
    "More Expressions": "Другие выражения",
    "Strength": "Сила",
    "Shift-click adds on top": "Shift+щелчок добавляет сверху",
    "Target follows head": "Цель следует за головой",
    "Lids follow gaze": "Веки следуют за взглядом",
    "Iris size": "Размер радужки",
    "Neutral": "Нейтрально",
    "Happy": "Радость",
    "Laugh": "Смех",
    "Gentle smile": "Мягкая улыбка",
    "Sad": "Грусть",
    "Crying": "Плач",
    "Angry": "Злость",
    "Surprised": "Удивление",
    "Embarrassed": "Смущение",
    "Smug": "Самодовольство",
    "Sleepy": "Сонливость",
    "Pained": "Боль",
    "Brows": "Брови",
    "Mouth": "Рот",
    "Tears": "Слёзы",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Face": "Лицо",
    "Hooks": "Хуки",
    "Hook": "Хук",
}
