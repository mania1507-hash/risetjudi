from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import cv2, tempfile, easyocr, pickle, os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import numpy as np
from urllib.parse import urlparse
import time
import urllib3
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ====== Load model ======
MODEL_PATH = os.path.abspath("rnn_model.h5")
model = tf.keras.models.load_model(MODEL_PATH)

# ====== Load tokenizer ======
TOKENIZER_PATH = os.path.abspath("tokenizer.pkl")
with open(TOKENIZER_PATH, 'rb') as f:
    tokenizer = pickle.load(f)

MAX_SEQUENCE_LENGTH = 100 

# ====== Init EasyOCR ======
try:
    reader = easyocr.Reader(['id', 'en'], gpu=False)
    print("EasyOCR berhasil diinisialisasi")
except Exception as e:
    print(f"Error inisialisasi EasyOCR: {e}")
    reader = None

# ====== Preprocess Text Function ======
def preprocess_text(text):
    sequence = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(sequence, maxlen=MAX_SEQUENCE_LENGTH, padding="post", truncating="post")
    return padded

@app.route('/', methods=['GET'])
def index():
    return "Running"

# ====== Fungsi untuk ekstrak SEMUA teks dari HTML (view-source) ======
def extract_all_text_from_viewsource(html_content):
    """Ekstrak SEMUA teks yang terlihat dari HTML view-source"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Hapus hanya script dan style, tapi pertahankan SEMUA teks lainnya
        for element in soup(["script", "style"]):
            element.decompose()
        
        # Dapatkan SEMUA teks dari HTML termasuk yang tersembunyi
        all_text = soup.get_text()
        
        # Bersihkan dan format teks
        lines = (line.strip() for line in all_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Hapus whitespace berlebihan
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()
        
    except Exception as e:
        print(f"Error extracting all text: {e}")
        return ""

# ====== Fungsi untuk deteksi judi berdasarkan SEMUA konten view-source ======
def detect_gambling_from_viewsource(full_text, url):
    """Deteksi judi online berdasarkan analisis SEMUA teks dari view-source"""
    if not full_text or len(full_text.strip()) < 50:
        return False, 0.0, [], "insufficient_content"
    
    try:
        # 1. Pertama, cari kata kunci judi yang SANGAT SPESIFIK dalam seluruh teks
        gambling_keywords = find_gambling_keywords_in_text(full_text)
        
        print(f"Found {len(gambling_keywords)} gambling keywords: {gambling_keywords}")
        
        # 2. Jika TIDAK ADA kata kunci judi, langsung return BUKAN JUDI
        if len(gambling_keywords) == 0:
            return False, 0.01, [], "no_gambling_keywords"
        
        # 3. Jika ADA kata kunci judi, hitung confidence berdasarkan keyword density
        total_words = len(full_text.split())
        keyword_count = len(gambling_keywords)
        keyword_density = (keyword_count / max(total_words, 1)) * 1000  # per 1000 words
        
        # Confidence berdasarkan density keyword
        if keyword_density > 10:  # Sangat tinggi
            keyword_confidence = 0.95
        elif keyword_density > 5:  # Tinggi
            keyword_confidence = 0.85
        elif keyword_density > 2:  # Sedang
            keyword_confidence = 0.70
        else:  # Rendah
            keyword_confidence = 0.50
        
        # 4. Juga gunakan model ML sebagai konfirmasi tambahan
        processed = preprocess_text(full_text)
        ml_confidence = model.predict(processed, verbose=0)[0][0]
        
        # 5. Gabungkan confidence (prioritaskan keyword detection)
        final_confidence = (keyword_confidence * 0.6) + (ml_confidence * 0.4)
        
        # 6. Tentukan status akhir
        is_gambling = final_confidence > 0.6 and len(gambling_keywords) > 0
        
        return is_gambling, float(final_confidence), gambling_keywords, "view_source_analysis"
        
    except Exception as e:
        print(f"Error in viewsource detection: {e}")
        return False, 0.0, [], "error"

# ====== Fungsi untuk mencari kata kunci judi dalam teks ======
def find_gambling_keywords_in_text(text):
    """Cari kata kunci judi yang SANGAT SPESIFIK dalam teks"""
    if not text or not isinstance(text, str):
        return []
    
    # Daftar kata kunci judi online yang SANGAT SPESIFIK
    gambling_keywords = [
        # Slot games - sangat spesifik
        'slot online', 'slot gacor', 'slot maxwin', 'slot pragmatic', 
        'slot pgsoft', 'slot jackpot', 'rtp slot', 'bocoran slot',
        'slot deposit', 'slot withdraw', 'slot bonus', 'slot88',
        'slothoki', 'slot joker', 'slot habanero', 'slot spadegaming',
        'slot microgaming', 'slot playtech', 'slot yggdrasil',
        
        # Casino & betting platforms
        'judi online', 'casino online', 'taruhan online', 'poker online',
        'togel online', 'sbobet', 'maxbet', 'bet365', 'sportsbook online',
        'sabung ayam online', 'live casino', 'idnpoker', 'idn poker',
        'pkv games', 'pkvgames', 'dominoqq online', 'domino online',
        'bandarq online', 'ceme online', 'capsa online', 'qiuqiu online',
        'cmd368', '188bet', 'betway', 'dafabet', '1xbet', 'melbet',
        'parimatch', 'fun88', 'pinnacle',
        
        # Financial transactions in gambling context
        'deposit judi', 'wd judi', 'withdraw judi', 'bonus new member',
        'freebet slot', 'freespin judi', 'cashback judi', 'rollingan slot',
        'referral judi', 'depo slot', 'wd cepat slot', 'tarik dana judi',
        
        # Gambling sites and agents
        'situs judi online', 'agen slot online', 'bandar judi online',
        'situs slot online', 'link slot gacor', 'daftar judi online',
        'login judi online', 'agen casino online', 'bandar slot online'
    ]
    
    found_keywords = []
    text_lower = text.lower()
    
    # Exact match dengan boundary checking
    for keyword in gambling_keywords:
        keyword_lower = keyword.lower()
        # Gunakan regex untuk exact word matching
        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        
        if re.search(pattern, text_lower):
            found_keywords.append(keyword)
    
    return list(set(found_keywords))

# ====== Endpoint utama untuk deteksi web ======
@app.route('/api/detect-web', methods=['POST'])
def detect_web():
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400
    
    try:
        # Validasi dan normalisasi URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = 'https://' + url
        
        print(f"Memproses URL: {url}")
        
        # Headers untuk mendapatkan view-source
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'id,en;q=0.9',
        }
        
        # Ambil konten web (view-source)
        response = requests.get(url, headers=headers, timeout=25, verify=False)
        response.raise_for_status()
        
        # Cek jika halaman memblokir akses
        content_lower = response.text.lower()
        blocked_indicators = [
            'enable javascript', 'enable cookies', 'just a moment', 
            'cloudflare', 'access denied', 'captcha', 'security check',
            'ddos protection', 'please enable javascript', 'checking your browser'
        ]
        
        is_blocked = any(indicator in content_lower for indicator in blocked_indicators)
        if is_blocked:
            return jsonify({
                'success': False, 
                'error': 'Halaman memblokir akses otomatis. Silakan coba URL lain.'
            }), 403
        
        # Ekstrak SEMUA teks dari view-source
        full_text = extract_all_text_from_viewsource(response.text)
        
        if len(full_text) < 100:
            return jsonify({
                'success': False,
                'error': 'Konten halaman terlalu sedikit atau tidak dapat diakses'
            }), 400
        
        print(f"Berhasil mengekstrak {len(full_text)} karakter dari view-source")
        
        # Analisis SEMUA teks dari view-source untuk deteksi judi
        is_gambling, confidence, gambling_keywords, detection_method = detect_gambling_from_viewsource(full_text, url)
        
        # Tentukan status berdasarkan kata kunci yang ditemukan
        if len(gambling_keywords) == 0:
            status = 'Bukan Situs Judi'
            # Force confidence to be low if no keywords found
            confidence = max(0.01, confidence)  # Minimum 1% jika tidak ada keyword
        else:
            status = 'Terindikasi Iklan Judi' if is_gambling else 'Bukan Situs Judi'
        
        # Siapkan hasil
        result = {
            'success': True,
            'status': status,
            'confidence': f'{confidence * 100:.2f}%',
            'raw_confidence': confidence,
            'gambling_keywords': gambling_keywords,
            'keyword_count': len(gambling_keywords),
            'extracted_text': full_text[:3000] + ('...' if len(full_text) > 3000 else ''),
            'full_text_length': len(full_text),
            'source_url': url,
            'detection_method': detection_method,
            'analysis_note': 'Berdasarkan analisis seluruh konten view-source website'
        }
        
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Gagal mengambil halaman web: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 400

# ====== Endpoint untuk fetch webpage (digunakan frontend) ======
@app.route('/api/fetch-webpage', methods=['GET'])
def fetch_webpage():
    url = request.args.get('url')
    if not url:
        return jsonify({'success': False, 'error': 'URL tidak boleh kosong'}), 400
    
    try:
        # Validasi URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        response.raise_for_status()
        
        # Ekstrak SEMUA teks dari view-source
        full_text = extract_all_text_from_viewsource(response.text)
        
        if len(full_text) < 50:
            return jsonify({'success': False, 'error': 'Konten halaman terlalu sedikit'}), 400
        
        return jsonify({
            'success': True,
            'content': full_text,
            'content_length': len(full_text)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Gagal mengambil halaman: {str(e)}'}), 400

# ====== Endpoint untuk teks langsung ======
@app.route('/api/detect-text', methods=['POST'])
def detect_text():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'Text tidak boleh kosong'}), 400

    # Analisis teks untuk kata kunci judi
    gambling_keywords = find_gambling_keywords_in_text(text)
    
    if len(gambling_keywords) == 0:
        # Jika tidak ada kata kunci judi, langsung return bukan judi
        result = {
            'status': 'Bukan Iklan Judi',
            'confidence': '0.00%',
            'raw_confidence': 0.0,
            'gambling_keywords': [],
            'keyword_count': 0,
            'text_length': len(text)
        }
    else:
        # Jika ada kata kunci, gunakan model ML
        processed = preprocess_text(text)
        prediction = model.predict(processed, verbose=0)[0][0]
        
        result = {
            'status': 'Terindikasi Iklan Judi' if prediction > 0.5 else 'Bukan Iklan Judi',
            'confidence': f'{prediction * 100:.2f}%',
            'raw_confidence': float(prediction),
            'gambling_keywords': gambling_keywords,
            'keyword_count': len(gambling_keywords),
            'text_length': len(text)
        }

    return jsonify(result)

# ====== Endpoint untuk gambar dengan OCR ======
@app.route('/api/detect-image', methods=['POST'])
def detect_image():
    if reader is None:
        return jsonify({'error': 'OCR engine tidak tersedia'}), 500
        
    if 'image' not in request.files:
        return jsonify({'error': 'File gambar tidak ditemukan'}), 400

    image_file = request.files['image']
    
    try:
        image_bytes = image_file.read()
        
        # OCR menggunakan easyocr
        ocr_result = reader.readtext(image_bytes, detail=0)
        extracted_text = ' '.join(ocr_result)

        if not extracted_text.strip():
            return jsonify({
                'ocr_text': '',
                'status': 'Bukan Iklan Judi',
                'confidence': '0.00%',
                'raw_confidence': 0.0,
                'gambling_keywords': [],
                'keyword_count': 0
            }), 200

        # Analisis teks untuk kata kunci judi
        gambling_keywords = find_gambling_keywords_in_text(extracted_text)
        
        if len(gambling_keywords) == 0:
            result = {
                'ocr_text': extracted_text,
                'status': 'Bukan Iklan Judi',
                'confidence': '0.00%',
                'raw_confidence': 0.0,
                'gambling_keywords': [],
                'keyword_count': 0,
                'text_length': len(extracted_text)
            }
        else:
            processed = preprocess_text(extracted_text)
            prediction = model.predict(processed, verbose=0)[0][0]
            
            result = {
                'ocr_text': extracted_text,
                'status': 'Terindikasi Iklan Judi' if prediction > 0.5 else 'Bukan Iklan Judi',
                'confidence': f'{prediction * 100:.2f}%',
                'raw_confidence': float(prediction),
                'gambling_keywords': gambling_keywords,
                'keyword_count': len(gambling_keywords),
                'text_length': len(extracted_text)
            }

        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

# ====== Endpoint untuk video ======
@app.route('/api/detect-video', methods=['POST'])
def detect_video():
    if reader is None:
        return jsonify({'error': 'OCR engine tidak tersedia'}), 500
        
    file = request.files.get('video')
    if not file:
        return jsonify({'error': 'No video uploaded'}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        file.save(temp_video.name)
        video_path = temp_video.name

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    all_ocr_texts = []
    max_frames = 20
    frame_interval = 5

    try:
        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0: 
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                    
                    height, width = blurred.shape
                    if width > 800:
                        scale = 800 / width
                        new_width = 800
                        new_height = int(height * scale)
                        resized = cv2.resize(blurred, (new_width, new_height))
                    else:
                        resized = blurred
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_frame:
                        frame_path = temp_frame.name
                        cv2.imwrite(frame_path, resized)

                    ocr_result = reader.readtext(frame_path, detail=0, paragraph=True)
                    os.remove(frame_path)

                    combined_text = ' '.join(ocr_result)
                    if combined_text.strip():
                        all_ocr_texts.append(combined_text)
                        
                except Exception as e:
                    print(f"Error processing frame {frame_count}: {e}")
                    if os.path.exists(frame_path):
                        os.remove(frame_path)

            frame_count += 1
            
    except Exception as e:
        print(f"Error processing video: {e}")
        return jsonify({'error': f'Error processing video: {str(e)}'}), 500
    finally:
        cap.release()
        if os.path.exists(video_path):
            os.remove(video_path)

    # Gabungkan semua teks OCR
    combined_ocr_text = ' '.join(all_ocr_texts) if all_ocr_texts else ""
    
    if not combined_ocr_text.strip():
        return jsonify({
            'status': 'Bukan Iklan Judi',
            'confidence': '0.00%',
            'raw_confidence': 0.0,
            'gambling_keywords': [],
            'keyword_count': 0,
            'combined_ocr_text': '',
            'total_ocr_characters': 0
        })

    # Analisis teks untuk kata kunci judi
    gambling_keywords = find_gambling_keywords_in_text(combined_ocr_text)
    
    if len(gambling_keywords) == 0:
        result = {
            'status': 'Bukan Iklan Judi',
            'confidence': '0.00%',
            'raw_confidence': 0.0,
            'gambling_keywords': [],
            'keyword_count': 0,
            'combined_ocr_text': combined_ocr_text,
            'total_ocr_characters': len(combined_ocr_text)
        }
    else:
        processed = preprocess_text(combined_ocr_text)
        prediction = model.predict(processed, verbose=0)[0][0]
        
        result = {
            'status': 'Terindikasi Iklan Judi' if prediction > 0.5 else 'Bukan Iklan Judi',
            'confidence': f'{prediction * 100:.2f}%',
            'raw_confidence': float(prediction),
            'gambling_keywords': gambling_keywords,
            'keyword_count': len(gambling_keywords),
            'combined_ocr_text': combined_ocr_text,
            'total_ocr_characters': len(combined_ocr_text)
        }

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0' )