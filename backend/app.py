import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import logging
from rapidfuzz import process as rf_process

# Loglama ayarları
logger = logging.getLogger("ChatbotAPI")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# OpenAI API Client oluştur
client = OpenAI()

# Flask uygulaması oluştur
app = Flask(__name__)
CORS(app)

# Asistan ID'leri ve anahtar kelimeleri eşleştirme
ASSISTANT_CONFIG = {
    "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],  # Skoda Kamiq Bot
    "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],  # Skoda Fabia Bot
    "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],  # Skoda Scala Bot
}

# Aktif asistanı takip et (kullanıcı bazlı duruma optimize edildi)
user_states = {}

@app.route("/", methods=["GET"])
def home():
    return "Chatbot API çalışıyor. Sorularınızı /ask endpointine POST edin."

def keyword_match_fuzzy(text, keywords):
    # Daha hızlı ve optimize fuzzy eşleşme
    return any(rf_process.extractOne(text, keywords, score_cutoff=80))

def process_streamed_response(thread_id, run_id, timeout=30):
    """Yanıt akışı optimizasyonu."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == "completed":
            # Yanıtı döndür ve işlemi sonlandır
            message_response = client.beta.threads.messages.list(thread_id=thread_id)
            for msg in message_response.data:
                if msg.role == "assistant":
                    if isinstance(msg.content, list):  # Eğer içerik bir liste ise
                        for chunk in msg.content:
                            yield chunk.encode("utf-8")  # Her bir elemanı bayta dönüştür
                    else:  # Eğer içerik bir string ise
                        yield msg.content.encode("utf-8")  # Bayt olarak döndür
            break
        elif run.status == "failed":
            logger.error("Yanıt başarısız oldu!")
            return None
        time.sleep(0.1)  # Daha sık kontrol için aralığı küçülttük
    logger.error("Yanıt alma zaman aşımına uğradı.")
    return None

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_message = data.get("question", "")
    user_id = data.get("user_id", "default_user")

    if not user_message:
        return jsonify({"response": "Lütfen bir soru girin."})

    def generate_response():
        logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")
        # Anahtar kelimelere göre uygun asistana yönlendirme
        for assistant_id, keywords in ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                user_states[user_id] = assistant_id
                thread = client.beta.threads.create(
                    messages=[{"role": "user", "content": user_message}]
                )
                run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

                # Yanıt akışı
                response = process_streamed_response(thread.id, run.id)
                if response:
                    for chunk in response:
                        yield chunk  # Bayt olarak döndürüldü
                    return
        yield "Hiçbir asistan uygun bir yanıt veremedi.".encode("utf-8")  # Bayt olarak döndür

    return app.response_class(generate_response(), mimetype="text/plain")

if __name__ == "__main__":
    app.run(debug=True)
