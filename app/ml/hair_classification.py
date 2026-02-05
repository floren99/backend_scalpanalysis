import os, io
import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

interpreter = tf.lite.Interpreter(
    model_path=os.path.join(MODEL_DIR, "vgg16_final.tflite")
)
interpreter.allocate_tensors()

labels = [l.strip() for l in open(os.path.join(MODEL_DIR, "labels.txt"))]
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise ValueError("File bukan gambar valid")

    if img.width < 200 or img.height < 200:
        raise ValueError("Gambar terlalu kecil atau tidak jelas")

    img_np = np.array(img)

    gray = np.mean(img_np, axis=2)

    brightness = np.mean(gray)
    contrast = np.std(gray)
    color_std = np.std(img_np, axis=(0, 1))  # per channel
    mean_color_std = np.mean(color_std)
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    edge_strength = np.mean(gx) + np.mean(gy)


    if mean_color_std < 15:
        raise ValueError("Gambar bukan citra kulit kepala yang valid")
   
    if brightness < 40:
        raise ValueError("Gambar terlalu gelap dan tidak terdeteksi sebagai kulit kepala")

    if contrast < 18:
        raise ValueError("Gambar terlalu polos dan bukan citra kulit kepala")

    if edge_strength < 12:
        raise ValueError("Gambar Tidak ditemukan tekstur rambut")
    
    laplacian = np.var(np.diff(gray, 2))
    if laplacian < 15:
        raise ValueError("Gambar terlalu halus / blur")
    
    r = img_np[:,:,0]
    g = img_np[:,:,1]
    b = img_np[:,:,2]

    skin_mask = (r > 95) & (g > 40) & (b > 20) & \
                ((np.max(img_np,axis=2)-np.min(img_np,axis=2)) > 15) & \
                (np.abs(r-g) > 15) & (r > g) & (r > b)

    skin_ratio = np.sum(skin_mask) / skin_mask.size

    if skin_ratio < 0.10:
        raise ValueError("Gambar tidak terdeteksi warna kulit kepala")

    img = img.resize((224, 224))
    arr = np.array(img).astype(np.float32)

    arr = arr[..., ::-1]
    arr[..., 0] -= 103.939
    arr[..., 1] -= 116.779
    arr[..., 2] -= 123.68

    arr = np.expand_dims(arr, axis=0)
    return arr.astype(input_details[0]["dtype"])

def predict(image_bytes):
    x = preprocess(image_bytes)
    interpreter.set_tensor(input_details[0]["index"], x)
    interpreter.invoke()

    probs = interpreter.get_tensor(output_details[0]["index"])[0]
    idx = int(np.argmax(probs))
    confidence = float(probs[idx])

    if confidence < 0.40:
        raise ValueError("Gambar bukan citra kulit kepala yang valid")

    status = "high" if confidence >= 0.80 else "low"
    return labels[idx], confidence, status

#  BUSINESS LOGIC 
DISEASE_INFO = {
    "alopecia": {
        "display_name": "Alopecia",
        "recommendation": [
            "Gunakan obat oles seperti minoxidil & kortikosteroid, obat minum seperti finasteride & JAK inhibitor (misal baricitinib).",
            "Imunoterapi (misal DPCP), fototerapi, Terapi PRP (Platelet-Rich Plasma) di perlukan jika obat oles dan minum tidak berhasil mengatasi permasalahan.",
            "Lakukan transplantasi rambut (jika kebotakan parah).",
            "Catatan: Alopecia merupakan penyakit yang cukup krusial sehingga agar lebih detail anda disarankan untuk tetap melakukan konsultasikan ke dokter spesialis rambut."
        ]
    },
    "folliculitis": {
        "display_name": "Folliculitis",
        "recommendation": [
            "Jaga kebersihan kulit kepala.",
            "Hindari menggaruk area yang terinfeksi.",
            "Gunakan Pembersih antibakteri (benzoyl peroxide atau chlorhexidine).",
            "Antibiotik topikal atau oral diperlukan jika keadaan semakin parah.",
            "Kompres hangat kulit kepala dapat membantu untuk mengurangi nyeri dan bengkak."
            "Catatan: Jika dalam 1 minggu tidak ada perubahan Anda perlu berkonsultasi kedokter spesialis masalah kulit atau rambut."
        ]
    },
    "headLice": {
        "display_name": "Head Lice (Kutu Rambut)",
        "recommendation": [
        "Gunakan sampo atau obat pembasmi kutu yang mengandung permethrin, pyrethrin, atau dimethicone dan dapat dibeli di apotek terdekat. Ikuti petunjuk penggunaan yang tertera pada kemasan.",
        "Selama 3 hari berturut-turut, Anda wajib keramas menggunakan sampo anti kutu. Jangan menggunakan sampo biasa selama 2 hari pertama masa pengobatan."
        "Gunakan sisir serit untuk mengangkat telur (nits)."
        "Cuci sprei, sisir, dan handuk dengan air panas.",
        "Periksa dan obati anggota keluarga lain."
        ]
    },
    "ketombe": {
        "display_name": "Ketombe",
        "recommendation": [
            "Gunakan sampo anti-ketombe yang mengandung zinc pyrithione, selenium sulfide, atau ketoconazole.",
            "Keramas secara teratur, 2-3 kali seminggu.",
            "Hindari stress berlebihan.",
            "Hindari penggunaan produk rambut berlebihan.",
            "Hindari makanan yang berminyak."
        ]
    },
    "lichenPlanus": {
        "display_name": "Lichen Planus",
        "recommendation": [
            "Lakukan pengobatan menggunakan krim obat oles yang mengandung kortikosteroid, yang diaplikasikan langsung pada kulit kepala ",
            "Jika kortikosteroid tidak mempan, dapat digunakan salep (tretinoin) atau tablet (isotretinoin, acitretin)."
            "Jika rasa gatak berlebih, gunakan obat yang mengandung Antihistamin"
            " Jika obat-obatan dirasa kurang membantu dalam 7 hari segera konsultasi ke dokter rambut atau kulit untuk melakukan Fototerapi (Terapi Sinar UV) "
        ]
    },
    "malePatternBaldness": {
        "display_name": "Male Pattern Baldness (Kebotakan Pola Pria)",
        "recommendation": [
            "Gunakan perawatan rambut yang mengandung Minoxidil (2 persen atau 5%)untuk membantu merangsang pertumbuhan rambut.",
            "Minum obat yang mengandung Finasteride untuk membantu mengurangi kerontokan rambut."
            "Jaga pola makan dan gaya hidup sehat",
            "Jika dalam 1 bulan tidak ada pertumbuhan sedikitpun dan kebotakan semakin parah Konsultasikan terapi PRP atau transplantasi rambut ke dokter"
        ]
    },
    "normal": {
        "display_name": "Kulit Kepala Normal",
        "recommendation": [
            "Pertahankan kebersihan rambut dan kulit kepala.",
            "Gunakan produk perawatan sesuai kebutuhan.",
            "Hindari bahan kimia keras."
        ]
    },
    "psoriasis": {
        "display_name": "Psoriasis Kulit Kepala",
        "recommendation": [
            "Gunakan Sampo yang bahan dasarnya tar batubara atau asam salisilat.",
            "Hindari stres dan menggaruk kulit kepala.",
            "Gunakanbat sistemik untuk kasus berat (misal: methotrexate, biologics)."
            "Lakukan kontrol ke dokter jika kondisi semakin buruk."
        ]
    },
    "seborrheicDermatitis": {
        "display_name": "Seborrheic Dermatitis",
        "recommendation": [
            "Gunakan sampo  anti jamur (ketoconazole, selenium sulfide).",
            "Krim kortikosteroid ringan.",
            "Kelola stres dengan baik.",
            "Jaga kebersihan kulit kepala."
        ]
    },
    "skinInflammation": {
        "display_name": "Skin Inflammation (Peradangan Kulit Kepala)",
        "recommendation": [
            "Hindari produk yang dapat menyebabkan iritasi.",
            "Gunakan Krim atau salep antiinflamasi (kortikosteroid topikal).",
            "Gunakan Obat antihistamin jika ada reaksi alergi.",
            "Hindari pemicu iritasi (pewarna rambut, sampo keras).",
            "Hindari menggaruk kulit kepala.",
            "Konsultasi ke dokter bila masalah kuliit kepala berlanjut lebih dari 3 minggu"
        ]
    },
    "telogenEffluvium": {
        "display_name": "Telogen Effluvium",
        "recommendation": [
            "Kelola stres dan istirahat cukup",
            "Konsumsi Suplemen multivitamin (biotin, zinc, vitamin D). ",
            "Perbaiki asupan nutrisi",
            "Jika rontok berlebihan silahkan menggunakan Minoxidil topikal dan berkonsultasi ke dokter spesialis kulit dan rambut"
           
        ]
    },
    "tineaCapitis": {
        "display_name": "Tinea Capitis",
        "recommendation": [
            "Gunakan obat antijamur dengan obat oral yang menggandung griseofulvin, terbinafine",
            "Pakai sampo anti jamur (ketoconazole) untuk mencegah penularan.",
            "Jaga kebersihan kulit kepala",
            "Hindari berbagi alat rambut"
        ]
    }
}

def get_disease_info(label: str):
    return DISEASE_INFO.get(label, {
        "display_name": label,
        "recommendation": [
            "Belum tersedia rekomendasi khusus",
            "Disarankan konsultasi tenaga medis"
        ]
    })

