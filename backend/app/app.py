from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import tempfile
from bs4 import BeautifulSoup
import re
import tensorflow as tf
import numpy as np
import pickle
import warnings
import os
import cv2
import easyocr
import pytesseract
from tensorflow.keras.preprocessing.sequence import pad_sequences  # Jangan lupa import ini
import yt_dlp
import subprocess
import json

warnings.filterwarnings("ignore")
reader = easyocr.Reader(['en'])

# ====== Inisialisasi Flask ======
app = Flask(__name__)
CORS(app)
app.config['PROPAGATE_EXCEPTIONS'] = True

# ====== Path Model & Tokenizer ======
MODEL_PATH = 'model_rnn.h5'
TOKENIZER_PATH = 'tokenizer_rnn.pkl'

# ====== Load Tokenizer (jika ada) ======
tokenizer = None
if os.path.exists(TOKENIZER_PATH):
    with open(TOKENIZER_PATH, 'rb') as handle:
        tokenizer = pickle.load(handle)
        print("✅ Tokenizer loaded successfully.")
else:
    print("⚠️ Tokenizer file not found, using None.")

# ====== Load Model (jika ada) ======
model = None
if os.path.exists(MODEL_PATH):
    model = tf.keras.models.load_model(MODEL_PATH)
    print("✅ Model loaded successfully.")
else:
    print("⚠️ Model file not found, using dummy mode.")

# ====== Fungsi Normalizer untuk hasil OCR ======
def normalize_ocr_text(text):
    text = text.lower()

    # Perbaikan umum OCR
    text = text.replace('0', 'o')
    text = text.replace('1', 'i')
    text = text.replace('3', 'e')
    text = text.replace('4', 'a')
    text = text.replace('5', 's')
    text = text.replace('8', 'b')
    text = text.replace('9', 'g')

    # Hilangkan karakter aneh
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Perbaikan kata yang sering rusak di OCR banner judi
    corrections = {
        "rpee8": "rp888", "rpeeb": "rp888", "rpeebcc": "rp888",
        "hemmember": "newmember", "kekalahai": "kekalahan",
        "rpenib": "rp888", "ratub": "ratu89", "jonus": "bonus",
        "ekeo": "depo", "wuib9": "judi89", "sirusslot": "situs slot",
        "eco": "gacor", "tkunbaru": "akunbaru"
    }

    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    return text

def find_gambling_keywords_in_text(text):
    """
    Deteksi kata kunci judi dengan pencarian fleksibel dan regex boundary.
    """
    gambling_keywords = [
        "judi", "slot", "gacor", "jackpot", "bet", "maxwin", "bo", "rtp",
        "casino", "toto", "qq", "poker", "bola", "parlay", "scatter",
        "bonus", "spin", "deposit", "wd", "situs", "bonus",
        "betting", "angka", "bandar", "slot gacor", "demo slot pg",
        "judol", "yoktogel", "nanastoto", "partaitogel", "mariatogel"
    ]

    text_lower = text.lower()
    detected = []

    for kw in gambling_keywords:
        pattern = r'\b' + re.escape(kw.lower()) + r'\b'
        if re.search(pattern, text_lower):
            detected.append(kw)

    return list(set(detected))

# ========= HITUNG CONFIDENCE BERDASARKAN KEYWORD =====
def calculate_confidence_based_on_keywords(keyword_count):
    """
    Menentukan confidence berdasar jumlah keyword:
    - 0 keyword: 0%
    - 1 keyword: 55%
    - 2 keyword: 60%
    - 3 keyword: 70%
    - 4 keyword: 85%
    - >=5 keyword: 100%
    """
    if keyword_count == 0:
        return 0.0
    elif keyword_count == 1:
        return 0.55
    elif keyword_count == 2:
        return 0.60
    elif keyword_count == 3:
        return 0.70
    elif keyword_count == 4:
        return 0.85
    else:
        return 1.0

# ================ PREPROCESS TEKS ====================
def preprocess_text(text, maxlen=200):
    """Konversi teks ke bentuk numerik untuk model RNN."""
    if not tokenizer:
        return np.zeros((1, maxlen))
    seq = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(seq, maxlen=maxlen, padding='post', truncating='post')
    return padded

# ====== Fungsi untuk Download & Ekstrak Info YouTube ======
def download_youtube_video(youtube_url, max_duration=300):
    """
    Download video YouTube dengan durasi maksimal 5 menit
    """
    try:
        # Konfigurasi yt-dlp
        ydl_opts = {
            'format': 'best[height<=720]',  # Maksimal 720p
            'outtmpl': tempfile.gettempdir() + '/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Dapatkan info video
            info = ydl.extract_info(youtube_url, download=False)
            video_id = info.get('id', 'unknown')
            video_title = info.get('title', '')
            video_duration = info.get('duration', 0)
            
            # Jika video terlalu panjang, batasi durasi
            if video_duration > max_duration:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
                ydl_opts['match_filter'] = yt_dlp.utils.match_filter_func(f"duration<={max_duration}")
            
            # Download video
            ydl.download([youtube_url])
            
            video_path = os.path.join(tempfile.gettempdir(), f"{video_id}.mp4")
            
            # Cek jika file berhasil didownload
            if os.path.exists(video_path):
                return video_path, video_title, video_duration
            else:
                # Cek ekstensi lain
                for ext in ['mp4', 'webm', 'mkv']:
                    alt_path = os.path.join(tempfile.gettempdir(), f"{video_id}.{ext}")
                    if os.path.exists(alt_path):
                        return alt_path, video_title, video_duration
                
                return None, video_title, video_duration
                
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        return None, "", 0

def extract_youtube_metadata(youtube_url):
    """
    Ekstrak metadata dari video YouTube
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            return {
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'uploader': info.get('uploader', ''),
                'upload_date': info.get('upload_date', ''),
                'tags': info.get('tags', []),
                'categories': info.get('categories', [])
            }
    except Exception as e:
        print(f"Error extracting YouTube metadata: {e}")
        return {}

# ====== Endpoint Utama ======
@app.route('/')
def index():
    return jsonify({'message': 'API Deteksi Iklan Judi Online aktif.'})

# ====== Endpoint Deteksi YouTube ======
@app.route('/api/detect-youtube', methods=['POST'])
def detect_youtube():
    try:
        data = request.get_json()
        youtube_url = data.get('youtube_url', '').strip()
        
        if not youtube_url:
            return jsonify({'success': False, 'error': 'URL YouTube tidak boleh kosong.'}), 400

        # Validasi URL YouTube
        youtube_pattern = r'^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})(\S*)?$'
        if not re.match(youtube_pattern, youtube_url):
            return jsonify({'success': False, 'error': 'URL YouTube tidak valid.'}), 400

        print(f"🔍 Memproses URL YouTube: {youtube_url}")

        # ====== 1. Ekstrak Metadata YouTube ======
        metadata = extract_youtube_metadata(youtube_url)
        title = metadata.get('title', '')
        description = metadata.get('description', '')
        tags = metadata.get('tags', [])
        
        # Gabungkan metadata untuk analisis
        metadata_text = f"{title} {description} {' '.join(tags)}"
        
        # ====== 2. Analisis Metadata ======
        metadata_keywords = find_gambling_keywords_in_text(metadata_text)
        metadata_keyword_count = len(metadata_keywords)
        
        # ====== 3. Download Video (maksimal 5 menit) ======
        video_path, video_title, video_duration = download_youtube_video(youtube_url)
        
        if not video_path:
            # Jika download gagal, gunakan metadata saja
            confidence = calculate_confidence_based_on_keywords(metadata_keyword_count)
            status = 'Terindikasi Iklan Judi' if metadata_keyword_count > 0 else 'Tidak Terindikasi Iklan Judi'
            
            return jsonify({
                'success': True,
                'youtube_url': youtube_url,
                'status': status,
                'confidence': f'{confidence * 100:.2f}%',
                'raw_confidence': confidence,
                'gambling_keywords': metadata_keywords,
                'keyword_count': metadata_keyword_count,
                'video_title': title,
                'video_duration': video_duration,
                'method': 'metadata_analysis_only',
                'note': 'Video tidak dapat diunduh, analisis berdasarkan metadata saja'
            })

        # ====== 4. Proses Video (OCR + Audio) ======
        try:
            # Ekstrak audio dari video
            audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
            try:
                from moviepy.editor import VideoFileClip
                clip = VideoFileClip(video_path)
                clip.audio.write_audiofile(audio_path, codec='pcm_s16le')
                clip.close()
            except Exception as e:
                print(f"Audio extraction error: {e}")
                audio_path = None

            # Speech-to-text
            audio_text = ""
            if audio_path and os.path.exists(audio_path):
                try:
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(audio_path) as source:
                        audio_data = recognizer.record(source)
                        audio_text = recognizer.recognize_google(audio_data, language="id-ID")
                    print(f"Audio transcription: {audio_text[:200]}...")
                except Exception as e:
                    print(f"Speech recognition error: {e}")

            # OCR dari frame video
            cap = cv2.VideoCapture(video_path)
            frame_count = 0
            all_ocr_texts = []
            max_frames = 30
            frame_interval = 3

            try:
                while cap.isOpened() and frame_count < max_frames:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_count % frame_interval == 0: 
                        try:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            denoised = cv2.medianBlur(gray, 3)
                            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                            enhanced = clahe.apply(denoised)
                            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                            
                            height, width = thresh.shape
                            if width > 1200:
                                scale = 1200 / width
                                resized = cv2.resize(thresh, (1200, int(height * scale)), interpolation=cv2.INTER_CUBIC)
                            else:
                                resized = thresh
                            
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_frame:
                                frame_path = temp_frame.name
                                cv2.imwrite(frame_path, resized)

                            ocr_results = []
                            try:
                                ocr_results.extend(reader.readtext(frame_path, detail=0, paragraph=True))
                            except:
                                pass
                            try:
                                result3 = pytesseract.image_to_string(frame_path, config='--psm 6')
                                if result3.strip():
                                    ocr_results.append(result3)
                            except:
                                pass

                            combined_text = ' '.join(ocr_results)
                            cleaned_text = re.sub(r'\s+', ' ', combined_text).strip()
                            if cleaned_text:
                                all_ocr_texts.append(cleaned_text)
                            
                            os.remove(frame_path)
                        except Exception as e:
                            print(f"OCR error at frame {frame_count}: {e}")

                    frame_count += 1

            finally:
                cap.release()

            combined_ocr_text = ' | '.join(all_ocr_texts)

            # ====== 5. Gabungkan semua teks untuk analisis ======
            all_text = f"{metadata_text} {combined_ocr_text} {audio_text}"
            
            # ====== 6. Analisis akhir ======
            all_keywords = find_gambling_keywords_in_text(all_text)
            all_keyword_count = len(all_keywords)
            
            # Gabungkan keyword dari metadata dan video
            combined_keywords = list(set(metadata_keywords + all_keywords))
            combined_keyword_count = len(combined_keywords)

            if combined_keyword_count > 0:
                confidence = calculate_confidence_based_on_keywords(combined_keyword_count)
                status = 'Terindikasi Iklan Judi'
            else:
                processed = preprocess_text(all_text)
                if model:
                    confidence = float(model.predict(processed, verbose=0)[0][0])
                    status = 'Terindikasi Iklan Judi' if confidence > 0.3 else 'Tidak Terindikasi Iklan Judi'
                else:
                    confidence = 0.0
                    status = 'Tidak Terindikasi Iklan Judi'

            result = {
                'success': True,
                'youtube_url': youtube_url,
                'status': status,
                'confidence': f'{confidence * 100:.2f}%',
                'raw_confidence': float(confidence),
                'gambling_keywords': combined_keywords,
                'keyword_count': combined_keyword_count,
                'video_title': title,
                'video_duration': video_duration,
                'video_metadata_analysis': {
                    'title_keywords': find_gambling_keywords_in_text(title),
                    'description_keywords': find_gambling_keywords_in_text(description),
                    'tags_keywords': find_gambling_keywords_in_text(' '.join(tags))
                },
                'video_content_analysis': {
                    'ocr_text_samples': combined_ocr_text[:500],
                    'audio_transcript': audio_text[:500],
                    'frames_processed': frame_count
                },
                'method': 'full_video_analysis'
            }

            return jsonify(result)

        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.remove(video_path)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

    except Exception as e:
        print(f"Error in YouTube detection: {e}")
        return jsonify({
            'success': False, 
            'error': f'Gagal memproses video YouTube: {str(e)}'
        }), 500

# ====== Endpoint Deteksi Berdasarkan Teks ======
@app.route('/api/detect-text', methods=['POST'])
def detect_text():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'success': False, 'error': 'Teks tidak boleh kosong.'}), 400

        # ====== Deteksi Keyword Judi ======
        gambling_keywords = find_gambling_keywords_in_text(text)
        keyword_count = len(gambling_keywords)

        # ====== Logika Deteksi ======
        if keyword_count > 0:
            # Hitung confidence berdasarkan jumlah keyword
            # Jika lebih dari 2 keyword, minimal 50%
            if keyword_count == 1:
                confidence = 0.55
            elif keyword_count == 2:
                confidence = 0.6
            elif keyword_count == 3:
                confidence = 0.7
            elif keyword_count == 4:
                confidence = 0.85
            else:
                confidence = 1.0

            status = 'Terindikasi Iklan Judi'

        else:
            # Jika tidak ada keyword, gunakan model prediksi (jika ada)
            processed = preprocess_text(text)
            if model:
                confidence = float(model.predict(processed, verbose=0)[0][0])
            else:
                confidence = 0.0

            status = 'Terindikasi Iklan Judi' if confidence > 0.5 else 'Tidak Terindikasi Iklan Judi'

        # ====== Return JSON Result ======
        return jsonify({
            'success': True,
            'status': status,
            'confidence': f'{confidence * 100:.2f}%',
            'raw_confidence': confidence,
            'gambling_keywords': gambling_keywords,
            'keyword_count': keyword_count,
            'method': 'text_analysis'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
# ====== Endpoint Deteksi Berdasarkan URL (Versi Tahan Error) ======
@app.route('/api/detect-url', methods=['POST'])
def detect_url():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'URL tidak boleh kosong'}), 400

        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        try:
            response = requests.get(url, headers=headers, timeout=15, verify=False, allow_redirects=True)
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'Tidak dapat mengakses URL: {str(e)}'
            }), 500

        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Gagal mengambil konten dari URL. Status: {response.status_code}'
            }), 500

        # Ambil teks dari HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        extracted_text = soup.get_text(separator=' ', strip=True)

        if not extracted_text or len(extracted_text) < 50:
            return jsonify({
                'success': False,
                'error': 'Konten halaman terlalu sedikit atau tidak dapat diambil.'
            }), 500

        # Deteksi kata kunci judi
        gambling_keywords = find_gambling_keywords_in_text(extracted_text)
        keyword_count = len(gambling_keywords)

        # LOGIKA YANG DIPERBAIKI:
        if keyword_count > 0:
            confidence = calculate_confidence_based_on_keywords(keyword_count)
            status = "Terindikasi Iklan Judi"
        else:
            confidence = 0.0
            status = "Tidak Terindikasi Iklan Judi"

        return jsonify({
            'success': True,
            'source_url': url,
            'status': status,
            'confidence': f"{confidence * 100:.2f}%",
            'raw_confidence': confidence,
            'gambling_keywords': gambling_keywords,
            'keyword_count': keyword_count,
            'logic': f'{keyword_count} keyword(s) detected'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Kesalahan Server: {str(e)}'}), 500

# ====== Endpoint untuk video (OCR + Audio Speech Detection) ======
@app.route('/api/detect-video', methods=['POST'])
def detect_video():
    if reader is None:
        return jsonify({'error': 'OCR engine tidak tersedia'}), 500
        
    file = request.files.get('video')
    if not file:
        return jsonify({'error': 'No video uploaded'}), 400

    # Simpan file sementara
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        file.save(temp_video.name)
        video_path = temp_video.name

    # ====== 1️⃣ Ekstraksi AUDIO dari video ======
    try:
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path, codec='pcm_s16le')
        clip.close()
    except Exception as e:
        print(f"Audio extraction error: {e}")
        audio_path = None

    # ====== 2️⃣ Speech-to-text (konversi audio ke teks) ======
    audio_text = ""
    if audio_path and os.path.exists(audio_path):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                audio_text = recognizer.recognize_google(audio_data, language="id-ID")
            print(f"Audio transcription: {audio_text[:200]}...")
        except Exception as e:
            print(f"Speech recognition error: {e}")
    else:
        print("Tidak ada audio ditemukan atau gagal diekstrak.")

    # ====== 3️⃣ Proses OCR frame seperti biasa ======
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    all_ocr_texts = []
    max_frames = 30
    frame_interval = 3

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0

    try:
        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0: 
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    denoised = cv2.medianBlur(gray, 3)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    enhanced = clahe.apply(denoised)
                    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    height, width = thresh.shape
                    if width > 1200:
                        scale = 1200 / width
                        resized = cv2.resize(thresh, (1200, int(height * scale)), interpolation=cv2.INTER_CUBIC)
                    else:
                        resized = thresh
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_frame:
                        frame_path = temp_frame.name
                        cv2.imwrite(frame_path, resized)

                    ocr_results = []
                    try:
                        ocr_results.extend(reader.readtext(frame_path, detail=0, paragraph=True))
                    except:
                        pass
                    try:
                        result3 = pytesseract.image_to_string(frame_path, config='--psm 6')
                        if result3.strip():
                            ocr_results.append(result3)
                    except:
                        pass

                    combined_text = ' '.join(ocr_results)
                    cleaned_text = re.sub(r'\s+', ' ', combined_text).strip()
                    if cleaned_text:
                        all_ocr_texts.append(cleaned_text)
                    
                    os.remove(frame_path)
                except Exception as e:
                    print(f"OCR error at frame {frame_count}: {e}")

            frame_count += 1

    finally:
        cap.release()
        if os.path.exists(video_path):
            os.remove(video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

    combined_ocr_text = ' | '.join(all_ocr_texts)
    total_ocr_characters = len(combined_ocr_text)

    # ====== 4️⃣ Gabungkan hasil OCR dan hasil audio speech ======
    combined_text = f"{combined_ocr_text} {audio_text}"
    print(f"Gabungan teks total: {len(combined_text)} karakter")

    # ====== 5️⃣ Analisis deteksi (pakai model dan keyword) ======
    gambling_keywords = find_gambling_keywords_in_text(combined_text)
    keyword_count = len(gambling_keywords)

    patterns = [
        r'slot.*online', r'togel.*online', r'judi.*online', 
        r'bonus.*deposit', r'free.*spin', r'jackpot',
        r'casino.*online', r'taruhan.*online', r'bet.*online'
    ]
    for pattern in patterns:
        if re.search(pattern, combined_text.lower()):
            gambling_keywords.append(pattern.replace('.*', '_'))
    gambling_keywords = list(set(gambling_keywords))
    keyword_count = len(gambling_keywords)

    if keyword_count > 0:
        confidence = calculate_confidence_based_on_keywords(keyword_count)
        status = 'Terindikasi Iklan Judi'
    else:
        processed = preprocess_text(combined_text)
        if model:
            confidence = float(model.predict(processed, verbose=0)[0][0])
            status = 'Terindikasi Iklan Judi' if confidence > 0.3 else 'Tidak Terindikasi Iklan Judi'
        else:
            confidence = 0.0
            status = 'Tidak Terindikasi Iklan Judi'

    result = {
        'status': status,
        'confidence': f'{confidence * 100:.2f}%',
        'raw_confidence': float(confidence),
        'gambling_keywords': gambling_keywords,
        'keyword_count': keyword_count,
        'combined_ocr_text': combined_ocr_text[:300],
        'audio_transcript': audio_text[:300],
        'frames_processed': frame_count,
        'video_info': {
            'total_frames': total_frames,
            'fps': fps,
            'duration_seconds': duration
        }
    }

    print(f"Final result: {status} ({confidence:.2f})")
    return jsonify(result)

# ====== Endpoint Deteksi Berdasarkan Gambar (OCR + Analisis Teks) ======
@app.route('/api/detect-image', methods=['POST'])
def detect_image():
    try:
        if reader is None:
            return jsonify({'error': 'OCR engine tidak tersedia'}), 500

        if 'image' not in request.files:
            return jsonify({'error': 'File gambar tidak ditemukan'}), 400

        image_file = request.files['image']
        image_bytes = image_file.read()

        # ====== OCR menggunakan EasyOCR ======
        ocr_result = reader.readtext(image_bytes, detail=0)
        extracted_text = ' '.join(ocr_result).strip()

        # ====== Normalisasi hasil OCR ======
        normalized_text = normalize_ocr_text(extracted_text)

        if not normalized_text:
            return jsonify({
                'ocr_text': '',
                'normalized_text': '',
                'status': 'Tidak Terindikasi Iklan Judi',
                'confidence': '0.00%',
                'raw_confidence': 0.0,
                'gambling_keywords': [],
                'keyword_count': 0
            }), 200

        # ====== Analisis kata kunci ======
        gambling_keywords = find_gambling_keywords_in_text(normalized_text)
        keyword_count = len(gambling_keywords)

        # ====== Logika Confidence ======
        if keyword_count > 0:
            # Jika ada minimal 1 keyword -> langsung terindikasi judi
            status = 'Terindikasi Iklan Judi'
            # Persentase bisa tetap dihitung berdasarkan jumlah keyword
            if keyword_count == 1:
                confidence = 0.55
            elif keyword_count == 2:
                confidence = 0.65
            elif keyword_count == 3:
                confidence = 0.75
            elif keyword_count == 4:
                confidence = 0.9
            else:
                confidence = 1.0

        else:
            # Jika tidak ada keyword -> pakai model prediksi
            processed = preprocess_text(normalized_text)
            if model:
                confidence = float(model.predict(processed, verbose=0)[0][0])
            else:
                confidence = 0.0

            status = 'Terindikasi Iklan Judi' if confidence > 0.5 else 'Tidak Terindikasi Iklan Judi'

        # ====== Hasil Akhir ======
        return jsonify({
            'ocr_text': extracted_text,
            'normalized_text': normalized_text,
            'status': status,
            'confidence': f'{confidence * 100:.2f}%',
            'raw_confidence': confidence,
            'gambling_keywords': gambling_keywords,
            'keyword_count': keyword_count,
            'text_length': len(normalized_text),
            'method': 'image_ocr_analysis'
        })

    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

# ====== Jalankan Server ======
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)