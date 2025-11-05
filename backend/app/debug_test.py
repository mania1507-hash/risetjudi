import tensorflow as tf
import pickle
import os
import re
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Load model dan tokenizer
MODEL_PATH = os.path.abspath("rnn_model.h5")
TOKENIZER_PATH = os.path.abspath("tokenizer.pkl")

print("=== LOADING MODEL & TOKENIZER ===")
model = tf.keras.models.load_model(MODEL_PATH)
with open(TOKENIZER_PATH, 'rb') as f:
    tokenizer = pickle.load(f)

print(f"Model input shape: {model.input_shape}")
print(f"Tokenizer word index size: {len(tokenizer.word_index)}")

# Fungsi cleansing dari cleansing.py
def casefolding(text):
    text = text.lower()
    text = text.replace('\r', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize_text(text):
    nstr = text.split()
    dat = []
    a = -1
    for hu in nstr:
        a = a+1
        if hu == '':
            dat.append(a)
    p=0
    b=0
    for q in dat:
        b = q - p
        del nstr[b]
        p = p + 1
    return nstr

# Coba import Sastrawi untuk stemming
try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    
    def stemming(text):
        do = []
        for w in text:
            dt = stemmer.stem(w)
            do.append(dt)
        d_clean = " ".join(do)
        return d_clean
        
except ImportError:
    print("Sastrawi tidak tersedia, menggunakan casefolding saja")
    def stemming(text):
        return " ".join(text)

def clean_text(text):
    """Cleansing text dengan proses yang sama seperti training"""
    text = casefolding(text)
    tokens = tokenize_text(text)
    cleaned_text = stemming(tokens)
    return cleaned_text

def preprocess_text(text, use_cleansing=True):
    """Preprocess text dengan atau tanpa cleansing"""
    if use_cleansing:
        cleaned_text = clean_text(text)
        print(f"Text setelah cleansing: '{cleaned_text}'")
        sequence = tokenizer.texts_to_sequences([cleaned_text])
    else:
        print(f"Text tanpa cleansing: '{text}'")
        sequence = tokenizer.texts_to_sequences([text])
    
    padded = pad_sequences(sequence, maxlen=100, padding="post", truncating="post")
    return padded

def test_prediction(text, description, use_cleansing=True):
    """Test prediction untuk satu text"""
    print(f"\n=== TEST: {description} ===")
    print(f"Original text: '{text}'")
    
    processed = preprocess_text(text, use_cleansing)
    prediction = model.predict(processed, verbose=0)[0][0]
    
    status = "JUDI" if prediction > 0.5 else "BUKAN JUDI"
    print(f"Prediction: {prediction:.4f} -> {status}")
    print(f"Use cleansing: {use_cleansing}")
    
    return prediction

# Test cases
test_cases = [
    ("ChatGPT adalah asisten AI", "ChatGPT text"),
    ("slot online judi casino", "Gambling text jelas"), 
    ("deepseek chat assistant", "DeepSeek text"),
    ("bantuan dan dukungan teknis", "Help text"),
    ("deposit bonus free spin jackpot", "Clear gambling text"),
    ("main slot online bonus new member", "Gambling text Indonesia"),
    ("saya mau bertanya tentang programming", "Programming question"),
    ("live casino dan sportsbook online", "Gambling casino"),
]

print("\n" + "="*60)
print("TEST DENGAN CLEANSING")
print("="*60)

results_with_cleansing = []
for text, desc in test_cases:
    pred = test_prediction(text, desc, use_cleansing=True)
    results_with_cleansing.append((desc, pred))

print("\n" + "="*60)
print("TEST TANPA CLEANSING")
print("="*60)

results_without_cleansing = []
for text, desc in test_cases:
    pred = test_prediction(text, desc, use_cleansing=False)
    results_without_cleansing.append((desc, pred))

print("\n" + "="*60)
print("PERBANDINGAN HASIL")
print("="*60)

print("\nDengan Cleansing:")
for desc, pred in results_with_cleansing:
    status = "JUDI" if pred > 0.5 else "BUKAN JUDI"
    print(f"  {desc:30} -> {pred:.4f} ({status})")

print("\nTanpa Cleansing:")
for desc, pred in results_without_cleansing:
    status = "JUDI" if pred > 0.5 else "BUKAN JUDI"
    print(f"  {desc:30} -> {pred:.4f} ({status})")

# Test specific problematic words
print("\n" + "="*60)
print("TEST KATA SPESIFIK")
print("="*60)

problematic_words = ['chat', 'gpt', 'ai', 'assistant', 'slot', 'judi', 'casino', 'bonus']
for word in problematic_words:
    processed = preprocess_text(word, use_cleansing=True)
    prediction = model.predict(processed, verbose=0)[0][0]
    status = "JUDI" if prediction > 0.5 else "BUKAN JUDI"
    print(f"  '{word:15}' -> {prediction:.4f} ({status})")

# Test dengan text panjang ChatGPT
print("\n" + "="*60)
print("TEST TEXT PANJANG CHATGPT")
print("="*60)

chatgpt_long_text = """
ChatGPT adalah asisten AI yang dikembangkan oleh OpenAI untuk membantu 
pengguna dengan berbagai tugas seperti menulis, coding, analisis, 
dan percakapan sehari-hari. Model ini menggunakan teknologi language 
model yang canggih untuk memahami dan merespons pertanyaan pengguna.
"""

test_prediction(chatgpt_long_text, "ChatGPT Long Text", use_cleansing=True)
test_prediction(chatgpt_long_text, "ChatGPT Long Text", use_cleansing=False)

print("\n" + "="*60)
print("KESIMPULAN")
print("="*60)
print("Cek perbedaan hasil antara dengan cleansing dan tanpa cleansing.")
print("Jika hasilnya berbeda signifikan, berarti masalahnya di preprocessing.")
print("Jika hasilnya sama, berarti masalahnya di model/training data.")