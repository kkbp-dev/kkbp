"""Thai. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "ตัวเลือกการนำเข้า",
    "Pillow is required. Install it with the buttons below.": "จำเป็นต้องมี Pillow ติดตั้งได้จากแผง KKBP",
    "Import Export Bundle": "นำเข้าชุดส่งออก",
    "No Step or Hook declares an option yet.": "ยังไม่มีขั้นตอนหรือฮุกใดประกาศตัวเลือก",
    "No hook scripts loaded": "ไม่ได้โหลดสคริปต์ฮุก",
    "no Hooks": "ไม่มีฮุก",
    "not loaded": "ไม่ได้โหลด",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "ตัวนำเข้า glTF ของ Blender ใช้งานไม่ได้ ให้เปิดใช้ส่วนเสริม \"glTF 2.0 format\" ในการตั้งค่า",

    # Preferences
    "Run this Hook after each import": "เรียกใช้ฮุกนี้หลังการนำเข้าทุกครั้ง",
    "Hooks folder": "โฟลเดอร์ฮุก",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "ไฟล์ .py ทุกไฟล์ในโฟลเดอร์นี้จะถูกโหลดเป็นสคริปต์ฮุก ไม่มีโฟลเดอร์เริ่มต้น",
    "User Hooks run after the built-in Hooks, in this order:": "ฮุกของผู้ใช้ทำงานหลังฮุกในตัว ตามลำดับนี้:",
    "Import Option defaults": "ค่าเริ่มต้นของตัวเลือกการนำเข้า",
    "Import Option defaults: the built-in ones": "ค่าเริ่มต้นของตัวเลือกการนำเข้า: ค่าในตัว",
    "Move Hook": "ย้ายฮุก",
    "Move the selected Hook up or down the running order": "ย้ายฮุกที่เลือกขึ้นหรือลงในลำดับการทำงาน",
    "Forget Hook": "นำฮุกออกจากรายการ",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "นำฮุกที่เลือกออกจากรายการ หากถูกโหลดอีกครั้ง ฮุกจะกลับมาอยู่ท้ายรายการ",
    "Use the built-in defaults": "ใช้ค่าเริ่มต้นในตัว",
    "Forget the saved Import Option defaults": "ล้างค่าเริ่มต้นของตัวเลือกการนำเข้าที่บันทึกไว้",

    # Importing
    "Import manifest.json": "นำเข้า manifest.json",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no file chosen":
        "นำเข้าตัวละครจากชุดส่งออก: เลือก manifest.json ของชุดนั้น หรือเปิดโฟลเดอร์ของชุดแล้วนำเข้าโดยไม่เลือกไฟล์",
    "Download Pillow": "ติดตั้ง Pillow",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "ดาวน์โหลด Pillow {version} จาก PyPI ด้วย pip ของ Blender แล้วติดตั้งลงใน KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "การเข้าถึงออนไลน์ถูกปิดอยู่ในการตั้งค่าของ Blender จะดาวน์โหลด Pillow ต่อไปหรือไม่?",
    "Install Pillow from local file": "ติดตั้ง Pillow จากไฟล์",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "ติดตั้งไฟล์ wheel ของ Pillow (.whl) ที่คุณดาวน์โหลดเอง สำหรับ Python และแพลตฟอร์มของ Blender นี้",
    "Reload Hooks": "โหลดฮุกใหม่",
    "Load the scripts in the hooks folder again": "โหลดสคริปต์ในโฟลเดอร์ฮุกอีกครั้ง",
    "Open KKBP Log": "เปิดบันทึกของ KKBP",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "เปิดบันทึกของการนำเข้าครั้งล่าสุด (kkbp_cache/log/log.txt ในชุดส่งออก) ในโปรแกรมแก้ไขข้อความ",
    "Save as Defaults": "บันทึกเป็นค่าเริ่มต้น",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "ใช้ตัวเลือกการนำเข้าของฉากนี้เป็นค่าเริ่มต้นสำหรับฉากใหม่และการนำเข้าผ่านสคริปต์",

    # Import Options
    "Delete default scene": "ลบฉากเริ่มต้น",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported Characters":
        "ลบลูกบาศก์ กล้อง และไฟของไฟล์เริ่มต้นของ Blender หากในไฟล์ไม่มีอะไรนอกจากตัวละครที่นำเข้า",
    "Which shaders the Character's materials use": "วัสดุของตัวละครใช้เชดเดอร์ใด",
    "Keeps the Eevee shaders": "คงเชดเดอร์ Eevee ไว้",
    "Uses a modified shader setup for Eevee": "ใช้ชุดเชดเดอร์ที่ปรับแต่งสำหรับ Eevee",
    "Cycles (toon)": "Cycles (ตูน)",
    "Toon shaders for Cycles": "เชดเดอร์ตูนสำหรับ Cycles",
    "Cycles (classic)": "Cycles (คลาสสิก)",
    "The classic shaders for Cycles": "เชดเดอร์คลาสสิกสำหรับ Cycles",
    "A very simple material setup": "ชุดวัสดุแบบเรียบง่ายมาก",
    "Separation type": "ประเภทการแยก",
    "How the clothes are split into objects": "วิธีแยกเสื้อผ้าออกเป็นวัตถุ",
    "One object per outfit": "หนึ่งวัตถุต่อหนึ่งชุด",
    "Each Outfit's clothes are one object": "เสื้อผ้าของแต่ละชุดเป็นวัตถุเดียว",
    "Separate all clothing": "แยกเสื้อผ้าทั้งหมด",
    "Each piece of clothing is its own object, named by its material":
        "เสื้อผ้าแต่ละชิ้นเป็นวัตถุของตัวเอง ตั้งชื่อตามวัสดุ",
    "Use outlines": "ใช้เส้นขอบ",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "เพิ่มวัสดุเส้นขอบให้ลำตัว ผม และเสื้อผ้า สำหรับวัสดุแต่ละชิ้น",
    "Face cards": "การ์ดใบหน้า",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts hidden":
        "เพิ่มการ์ดตาและปากแบบ 2D ไว้หน้าใบหน้า โดยใช้เท็กซ์เจอร์ตาของตัวละคร คอลเลกชันของการ์ดจะถูกซ่อนไว้ตอนเริ่มต้น",
    "SFW mode": "โหมด SFW",
    "Attempts to cover up some NSFW things": "พยายามปกปิดสิ่งที่เป็น NSFW บางส่วน",
    "Use Rigify armature": "ใช้โครงร่าง Rigify",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK armature, which is easier to export":
        "สร้างริกควบคุม Rigify ที่เหมาะกับการทำแอนิเมชันใน Blender หากไม่ใช้ ตัวละครจะคงโครงร่าง FK ไว้ ซึ่งส่งออกได้ง่ายกว่า",
    "Separate eyes": "แยกดวงตา",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so they can show through the hair with the compositor":
        "ย้ายดวงตาและคิ้วออกจาก Body ไปเป็นวัตถุของตัวเอง โดยให้ชีปคีย์ตามของ Body เพื่อให้แสดงทะลุผมได้ด้วยคอมโพสิเตอร์",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "เส้นขอบ",
    "Separate Eyes": "แยกดวงตา",
    "Separate meshes": "แยกเมช",
    "Convert shaders": "แปลงเชดเดอร์",

    # Tools
    "Merge Weights": "รวมน้ำหนัก",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "ย้ายน้ำหนักของกระดูกที่เลือกไปให้กระดูกแม่ แล้วลบกระดูกเหล่านั้น",
    "Export Prep": "เตรียมส่งออก",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on its Collection":
        "เตรียมตัวละครสำหรับโปรแกรมอื่น: ชื่อกระดูก โครงกระดูกที่เรียบง่ายขึ้น แอตลาส และตัวส่งออก FBX บนคอลเลกชันของตัวละคร",
    "Atlas": "แอตลาส",
    "Largest atlas": "แอตลาสใหญ่สุด",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "วัตถุที่แอตลาสจะกว้างกว่านี้จะได้แอตลาสหลายแผ่น ไม่มีการย่อขนาดใด ๆ",
    "Koikatsu": "Koikatsu",
    "No change": "ไม่เปลี่ยนแปลง",
    "Very simple": "เรียบง่ายมาก",
    "Merges the deform details, the face and the tongue into their parents":
        "รวมกระดูกรายละเอียดการเปลี่ยนรูป ใบหน้า และลิ้นเข้ากับกระดูกแม่",
    "Merges the helper bones only": "รวมเฉพาะกระดูกตัวช่วย",
    "Keeps every bone": "เก็บกระดูกทุกชิ้นไว้",
    "One atlas each for the light, dark and normal textures":
        "แอตลาสอย่างละหนึ่งแผ่นสำหรับเท็กซ์เจอร์สว่าง มืด และนอร์มัล",
    "Atlas without the eyes": "แอตลาสไม่รวมดวงตา",
    "As Atlas, with the eyes keeping their own textures": "เหมือนแอตลาส แต่ดวงตาใช้เท็กซ์เจอร์ของตัวเอง",
    "Atlas of every texture": "แอตลาสของทุกเท็กซ์เจอร์",
    "As Atlas, with the detail, alpha and colour masks too": "เหมือนแอตลาส และรวมมาสก์รายละเอียด อัลฟา และสีด้วย",
    "No atlas": "ไม่ใช้แอตลาส",
    "The textures stay as they are": "เท็กซ์เจอร์คงไว้ตามเดิม",
    "Run Hook": "เรียกใช้ฮุก",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "เรียกใช้ฮุก เช่น Rigify กับตัวละครที่นำเข้าโดยไม่ได้ใช้ฮุกนั้น",
    "Built in": "ในตัว",
    "Bulk Import": "นำเข้าจำนวนมาก",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside each bundle folder":
        "นำเข้าชุดส่งออกทุกชุดในโฟลเดอร์ แต่ละชุดใน Blender ของตัวเองเบื้องหลัง แล้วบันทึก .blend ไว้ข้างโฟลเดอร์ของแต่ละชุด",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "ใส่แอนิเมชัน .fbx ของ Koikatsu ลงบนริก Rigify ของตัวละครเป็นแอ็กชันใหม่",
    "Lengthen arms": "ยืดแขน",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "ทำให้แขนยาวขึ้น 5% ซึ่งดูใกล้เคียงกับในเกมมากขึ้นในบางท่า",
    "Snap IKs": "สแนป IK",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "สแนปตัวควบคุม IK ของริกไปยังท่า FK และสลับแขนขาไปใช้ IK",

    # Edit Material
    "Saturate": "ปรับความอิ่มสี",
    "What Edit Material does with the colours: Shown colours for a material that follows the game's shaders, Saturate for one from a modded shader":
        "สิ่งที่แก้ไขวัสดุทำกับสี: สีที่แสดงสำหรับวัสดุที่ทำตามเชดเดอร์ของเกม ปรับความอิ่มสีสำหรับวัสดุจากเชดเดอร์ม็อด",
    "Shown colours": "สีที่แสดง",
    "Each colour is the colour as it shows, so the eyedropper can pick it":
        "แต่ละสีคือสีตามที่แสดง เพื่อให้ใช้หลอดดูดสีเลือกได้",
    "Each colour is the game's own value, which shows graded and stronger":
        "แต่ละสีคือค่าดั้งเดิมของเกม ซึ่งแสดงผลหลังปรับสีและเข้มกว่า",
    "Don't saturate": "ไม่ปรับความอิ่มสี",
    "Edit Material": "แก้ไขวัสดุ",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be changed and saved":
        "สลับวัสดุที่ใช้งานอยู่เป็นวัสดุที่แก้ไขได้ ซึ่งสร้างการลงสีของเกมขึ้นใหม่ เพื่อให้เปลี่ยนสีและบันทึกได้",
    "Cancel": "ยกเลิก",
    "Puts the original material back and drops the changes": "นำวัสดุเดิมกลับมาและทิ้งการเปลี่ยนแปลง",
    "Starts the edit again from the Export Bundle": "เริ่มการแก้ไขใหม่จากชุดส่งออก",
    "Bakes the edited colours into the original material's light and dark textures":
        "เบกสีที่แก้ไขลงในเท็กซ์เจอร์สว่างและมืดของวัสดุเดิม",
    "Link Hair": "ลิงก์ผม",
    "Puts every hair material into edit with the active hair material's settings":
        "ทำให้วัสดุผมทั้งหมดเข้าสู่การแก้ไขด้วยการตั้งค่าของวัสดุผมที่ใช้งานอยู่",
    # The Face panel (the Rigify Hook's face rig)
    "Face Preset": "พรีเซ็ตใบหน้า",
    "Poses the face as this emotion. Shift-click adds it on top of the face as it is": "ทำให้ใบหน้าแสดงอารมณ์นี้ Shift+คลิกเพื่อเพิ่มทับใบหน้าปัจจุบัน",
    "Add": "เพิ่ม",
    "Adds the preset on top of the face as it is": "เพิ่มพรีเซ็ตทับใบหน้าปัจจุบัน",
    "Reset Face": "รีเซ็ตใบหน้า",
    "Puts every face control back and every face slider to 0": "คืนตัวควบคุมใบหน้าทั้งหมดและตั้งแถบเลื่อนใบหน้าทั้งหมดเป็น 0",
    "Key Face": "ใส่คีย์ใบหน้า",
    "Keys every face control and face slider at the current frame": "ใส่คีย์ให้ตัวควบคุมและแถบเลื่อนใบหน้าทั้งหมดที่เฟรมปัจจุบัน",
    "Emotions": "อารมณ์",
    "Eyes": "ดวงตา",
    "More Expressions": "การแสดงออกอื่น ๆ",
    "Strength": "ความแรง",
    "Shift-click adds on top": "Shift+คลิกเพื่อเพิ่มทับ",
    "Target follows head": "เป้าหมายตามศีรษะ",
    "Lids follow gaze": "เปลือกตาตามสายตา",
    "Iris size": "ขนาดม่านตา",
    "Neutral": "ปกติ",
    "Happy": "มีความสุข",
    "Laugh": "หัวเราะ",
    "Gentle smile": "ยิ้มอ่อน",
    "Sad": "เศร้า",
    "Crying": "ร้องไห้",
    "Angry": "โกรธ",
    "Surprised": "ประหลาดใจ",
    "Embarrassed": "เขิน",
    "Smug": "ภูมิใจในตัวเอง",
    "Sleepy": "ง่วงนอน",
    "Pained": "เจ็บปวด",
    "Brows": "คิ้ว",
    "Mouth": "ปาก",
    "Tears": "น้ำตา",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Face": "ใบหน้า",
    "Hooks": "ฮุก",
    "Hook": "ฮุก",
}
