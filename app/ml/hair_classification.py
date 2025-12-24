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

    if confidence < 0.90:
        raise ValueError("Gambar bukan citra kulit kepala yang valid")

    return labels[idx], confidence

#  BUSINESS LOGIC 
DISEASE_INFO = {
    "alopecia": {
        "display_name": "Alopecia Areata",
        "recommendation": [
            "Hindari stres berlebih karena dapat memicu kerontokan",
            "Gunakan perawatan rambut yang lembut",
            "Konsultasikan ke dokter spesialis kulit atau rambut"
        ]
    },
    "folliculitis": {
        "display_name": "Folliculitis",
        "recommendation": [
            "Jaga kebersihan kulit kepala",
            "Hindari menggaruk area yang terinfeksi",
            "Gunakan obat topikal sesuai anjuran dokter"
        ]
    },
    "headLice": {
        "display_name": "Head Lice (Kutu Rambut)",
        "recommendation": [
            "Gunakan sampo atau obat pembasmi kutu",
            "Cuci sprei, sisir, dan handuk dengan air panas",
            "Periksa dan obati anggota keluarga lain"
        ]
    },
    "ketombe": {
        "display_name": "Ketombe",
        "recommendation": [
            "Gunakan sampo anti-ketombe",
            "Keramas secara teratur",
            "Hindari penggunaan produk rambut berlebihan"
        ]
    },
    "lichenPlanus": {
        "display_name": "Lichen Planus",
        "recommendation": [
            "Hindari pemicu iritasi pada kulit kepala",
            "Gunakan obat sesuai resep dokter",
            "Lakukan pemeriksaan rutin ke dermatologis"
        ]
    },
    "malePatternBaldness": {
        "display_name": "Male Pattern Baldness (Kebotakan Pola Pria)",
        "recommendation": [
            "Gunakan perawatan rambut sesuai anjuran medis",
            "Jaga pola makan dan gaya hidup sehat",
            "Konsultasikan pilihan terapi ke dokter"
        ]
    },
    "normal": {
        "display_name": "Kulit Kepala Normal",
        "recommendation": [
            "Pertahankan kebersihan rambut dan kulit kepala",
            "Gunakan produk perawatan sesuai kebutuhan",
            "Hindari bahan kimia keras"
        ]
    },
    "psoriasis": {
        "display_name": "Psoriasis Kulit Kepala",
        "recommendation": [
            "Gunakan obat topikal sesuai anjuran dokter",
            "Hindari stres dan iritasi",
            "Lakukan kontrol rutin ke dokter kulit"
        ]
    },
    "seborrheicDermatitis": {
        "display_name": "Seborrheic Dermatitis",
        "recommendation": [
            "Gunakan sampo khusus dermatitis seboroik",
            "Kelola stres dengan baik",
            "Jaga kebersihan kulit kepala"
        ]
    },
    "skinInflammation": {
        "display_name": "Skin Inflammation (Peradangan Kulit Kepala)",
        "recommendation": [
            "Hindari produk yang dapat menyebabkan iritasi",
            "Gunakan sampo ringan",
            "Konsultasi ke dokter bila berlanjut"
        ]
    },
    "telogenEffluvium": {
        "display_name": "Telogen Effluvium",
        "recommendation": [
            "Kelola stres dan istirahat cukup",
            "Perbaiki asupan nutrisi",
            "Konsultasikan ke dokter"
        ]
    },
    "tineaCapitis": {
        "display_name": "Tinea Capitis",
        "recommendation": [
            "Gunakan obat antijamur sesuai resep",
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
