"""Indonesian. English string -> translation; see the package's docstring for what belongs here.

Every entry is unreviewed: none has been checked by a native speaker yet (issue #37).
"""

TRANSLATIONS = {
    # The panel
    "Import Options": "Opsi Impor",
    "Pillow is required. Install it from the KKBP panel.": "Pillow diperlukan. Pasang dari panel KKBP.",
    "Import Export Bundle": "Impor Bundel Ekspor",
    "No Step or Hook declares an option yet.": "Belum ada Langkah atau Hook yang mendeklarasikan opsi.",
    "No hook scripts loaded": "Tidak ada skrip hook yang dimuat",
    "no Hooks": "tidak ada Hook",
    "not loaded": "tidak dimuat",
    "Blender's glTF importer isn't available. Enable the \"glTF 2.0 format\" add-on in Preferences.":
        "Pengimpor glTF Blender tidak tersedia. Aktifkan add-on \"glTF 2.0 format\" di Preferensi.",

    # Preferences
    "Run this Hook after each import": "Jalankan Hook ini setelah setiap impor",
    "Hooks folder": "Folder hook",
    "Every .py file in this folder is loaded as a Hook script. There is no default folder":
        "Setiap file .py di folder ini dimuat sebagai skrip Hook. Tidak ada folder bawaan",
    "User Hooks run after the built-in Hooks, in this order:":
        "Hook pengguna dijalankan setelah Hook bawaan, dengan urutan ini:",
    "Import Option defaults": "Nilai bawaan Opsi Impor",
    "Import Option defaults: the built-in ones": "Nilai bawaan Opsi Impor: nilai bawaan asli",
    "Move Hook": "Pindahkan Hook",
    "Move the selected Hook up or down the running order":
        "Pindahkan Hook terpilih ke atas atau ke bawah dalam urutan jalan",
    "Forget Hook": "Lupakan Hook",
    "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again":
        "Menghapus Hook terpilih dari daftar. Hook itu muncul lagi di akhir daftar jika dimuat kembali",
    "Use the built-in defaults": "Gunakan nilai bawaan asli",
    "Forget the saved Import Option defaults": "Lupakan nilai bawaan Opsi Impor yang tersimpan",

    # Importing
    "Import manifest.json": "Impor manifest.json",
    "Import a Character from an Export Bundle: choose its manifest.json, or open its folder and import with no file chosen":
        "Mengimpor Karakter dari Bundel Ekspor: pilih manifest.json-nya, atau buka foldernya dan impor tanpa memilih file",
    "Install Pillow": "Pasang Pillow",
    "Download Pillow {version} from PyPI with Blender's pip and install it into KKBP":
        "Unduh Pillow {version} dari PyPI dengan pip milik Blender dan pasang ke KKBP",
    "Online access is turned off in Blender's Preferences. Download Pillow anyway?":
        "Akses daring dimatikan di Preferensi Blender. Tetap unduh Pillow?",
    "Install Pillow from File": "Pasang Pillow dari File",
    "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform":
        "Pasang wheel Pillow (.whl) yang Anda unduh sendiri, untuk Python dan platform Blender ini",
    "Reload Hooks": "Muat Ulang Hook",
    "Load the scripts in the hooks folder again": "Muat lagi skrip di folder hook",
    "Open KKBP Log": "Buka Log KKBP",
    "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor":
        "Buka log impor terakhir (kkbp_cache/log/log.txt di Bundel Ekspor) di editor teks Anda",
    "Save as Defaults": "Simpan sebagai Bawaan",
    "Use this scene's Import Options as the defaults for new scenes and scripted imports":
        "Gunakan Opsi Impor adegan ini sebagai bawaan untuk adegan baru dan impor lewat skrip",

    # Import Options
    "Delete default scene": "Hapus adegan bawaan",
    "Deletes the cube, camera and light of Blender's startup file, if the file holds nothing else but imported Characters":
        "Menghapus kubus, kamera, dan lampu dari file awal Blender, jika file tidak berisi apa pun selain Karakter yang diimpor",
    "Fix body seams": "Perbaiki sambungan badan",
    "Merges the vertices of the face and body materials that sit on top of each other (Merge by Distance). It can change the weights around the neck; without it, seams may show around the neck and down the chest when outlines are on":
        "Menggabungkan verteks material wajah dan badan yang saling bertumpuk (Gabung berdasarkan Jarak). Ini dapat mengubah bobot di sekitar leher; tanpanya, sambungan bisa terlihat di sekitar leher dan dada saat garis luar aktif",
    "Which shaders the Character's materials use": "Shader yang dipakai material Karakter",
    "Keeps the Eevee shaders": "Mempertahankan shader Eevee",
    "Uses a modified shader setup for Eevee": "Memakai susunan shader yang dimodifikasi untuk Eevee",
    "Cycles (toon)": "Cycles (toon)",
    "Toon shaders for Cycles": "Shader toon untuk Cycles",
    "Cycles (classic)": "Cycles (klasik)",
    "The classic shaders for Cycles": "Shader klasik untuk Cycles",
    "A very simple material setup": "Susunan material yang sangat sederhana",
    "Separation type": "Jenis pemisahan",
    "How the clothes are split into objects": "Cara pakaian dipisah menjadi objek",
    "One object per outfit": "Satu objek per kostum",
    "Each Outfit's clothes are one object": "Pakaian tiap kostum menjadi satu objek",
    "Separate all clothing": "Pisahkan semua pakaian",
    "Each piece of clothing is its own object, named by its material":
        "Tiap potong pakaian menjadi objek sendiri, dinamai menurut materialnya",
    "Use outlines": "Gunakan garis luar",
    "Gives the body, hair and clothes an outline material for each of their materials":
        "Memberi badan, rambut, dan pakaian satu material garis luar untuk tiap materialnya",
    "Face cards": "Kartu wajah",
    "Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. Their Collection starts hidden":
        "Menambahkan kartu mata dan mulut 2D di depan wajah, dengan tekstur mata Karakter. Koleksinya awalnya tersembunyi",
    "SFW mode": "Mode SFW",
    "Attempts to cover up some NSFW things": "Mencoba menutupi beberapa hal NSFW",
    "Use Rigify armature": "Gunakan kerangka Rigify",
    "Generates a Rigify control rig, suitable for animating in Blender. Without it the Character keeps the FK armature, which is easier to export":
        "Membuat rig kontrol Rigify yang cocok untuk animasi di Blender. Tanpanya, Karakter tetap memakai kerangka FK, yang lebih mudah diekspor",
    "Separate eyes": "Pisahkan mata",
    "Moves the eyes and eyebrows out of Body into their own objects, with their shape keys following Body's, so they can show through the hair with the compositor":
        "Memindahkan mata dan alis dari Body ke objek tersendiri, dengan kunci bentuk yang mengikuti milik Body, sehingga bisa tampil menembus rambut lewat kompositor",

    # The built-in Hooks' names, as the panel lists them
    "Outlines": "Garis luar",
    "Separate Eyes": "Pisahkan Mata",
    "Separate meshes": "Pisahkan mesh",
    "Convert shaders": "Konversi shader",

    # Tools
    "Merge Weights": "Gabungkan Bobot",
    "Gives the selected bones' weights to their parents and deletes the bones":
        "Memberikan bobot tulang terpilih ke induknya dan menghapus tulang tersebut",
    "Export Prep": "Persiapan Ekspor",
    "Readies the Character for another program: bone names, a simpler skeleton, an atlas, and an FBX exporter on its Collection":
        "Menyiapkan Karakter untuk program lain: nama tulang, kerangka yang lebih sederhana, atlas, dan pengekspor FBX pada Koleksinya",
    "Atlas": "Atlas",
    "Largest atlas": "Atlas terbesar",
    "An object whose atlas would be wider than this gets several atlases. Nothing is scaled down":
        "Objek yang atlasnya akan lebih lebar dari ini mendapat beberapa atlas. Tidak ada yang diperkecil",
    "Koikatsu": "Koikatsu",
    "No change": "Tanpa perubahan",
    "Very simple": "Sangat sederhana",
    "Merges the deform details, the face and the tongue into their parents":
        "Menggabungkan detail deformasi, wajah, dan lidah ke induknya",
    "Merges the helper bones only": "Hanya menggabungkan tulang bantu",
    "Keeps every bone": "Mempertahankan semua tulang",
    "One atlas each for the light, dark and normal textures":
        "Satu atlas masing-masing untuk tekstur terang, gelap, dan normal",
    "Atlas without the eyes": "Atlas tanpa mata",
    "As Atlas, with the eyes keeping their own textures": "Seperti Atlas, tetapi mata tetap memakai teksturnya sendiri",
    "Atlas of every texture": "Atlas semua tekstur",
    "As Atlas, with the detail, alpha and colour masks too": "Seperti Atlas, ditambah mask detail, alfa, dan warna",
    "No atlas": "Tanpa atlas",
    "The textures stay as they are": "Tekstur dibiarkan apa adanya",
    "Run Hook": "Jalankan Hook",
    "Runs a Hook, such as Rigify, on a Character imported without it":
        "Menjalankan Hook, misalnya Rigify, pada Karakter yang diimpor tanpa Hook itu",
    "Built in": "Bawaan",
    "Bulk Import": "Impor Massal",
    "Imports every Export Bundle in a folder, each in its own Blender in the background, and saves a .blend beside each bundle folder":
        "Mengimpor setiap Bundel Ekspor dalam sebuah folder, masing-masing di Blender tersendiri di latar belakang, dan menyimpan .blend di samping tiap folder bundel",
    "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action":
        "Memasang animasi .fbx Koikatsu pada rig Rigify Karakter sebagai aksi baru",
    "Lengthen arms": "Panjangkan lengan",
    "Makes the arms 5% longer, which looks closer to the game in some poses":
        "Membuat lengan 5% lebih panjang, yang pada beberapa pose terlihat lebih mirip dengan game",
    "Snap IKs": "Tempelkan IK",
    "Snaps the rig's IK controls to their FK pose and switches the limbs to IK":
        "Menempelkan kontrol IK rig ke pose FK-nya dan mengalihkan anggota badan ke IK",

    # Edit Material
    "Saturate": "Saturasi",
    "Whether the textures and colours go through the game's colour grade, as the legacy importer did":
        "Apakah tekstur dan warna melewati gradasi warna game, seperti pada pengimpor lama",
    "Hair and eyebrows saturate, everything else doesn't": "Rambut dan alis disaturasi, yang lain tidak",
    "Don't saturate": "Jangan saturasi",
    "Edit Material": "Edit Material",
    "Swaps the active material for an editable one that rebuilds the game's colouring, so its colours can be changed and saved":
        "Menukar material aktif dengan material yang bisa diedit dan membangun ulang pewarnaan game, sehingga warnanya bisa diubah dan disimpan",
    "Cancel": "Batal",
    "Puts the original material back and drops the changes": "Mengembalikan material asli dan membuang perubahan",
    "Starts the edit again from the Export Bundle": "Memulai lagi pengeditan dari Bundel Ekspor",
    "Bakes the edited colours into the original material's light and dark textures":
        "Mem-bake warna hasil edit ke tekstur terang dan gelap material asli",
    "Link Hair": "Tautkan Rambut",
    "Puts every hair material into edit with the active hair material's settings":
        "Memasukkan semua material rambut ke mode edit dengan pengaturan material rambut aktif",
}

# In the "KKBP" translation context, where Blender's own word means something else.
IN_CONTEXT = {
    "Hooks": "Hook",
    "Hook": "Hook",
}
