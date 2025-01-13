import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import logging
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI API Client oluştur
client = OpenAI(api_key="")

# Flask uygulaması oluştur
app = Flask(__name__)
CORS(app)

# Asistan ID'leri ve anahtar kelimeleri eşleştirme
ASSISTANT_CONFIG = {
    "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],  # Skoda Kamiq Bot
    "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],  # Skoda Fabia Bot
    "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],  # Skoda Scala Bot
}

# Aktif asistanı takip et
active_assistant_id = None

@app.route("/", methods=["GET"])
def home():
    return "Chatbot API çalışıyor. Sorularınızı /ask endpointine POST edin."

def clean_text(text):
    """Yanıt metnini temizle ve eşleştirme için hazırla."""
    import re
    text = re.sub(r'\n|【.*?】|\[.*?\]', '', text)  # Ek açıklamaları temizle
    return text.strip().lower()

def process_assistant(assistant_id, user_message):
    try:
        # Thread oluştur
        thread = client.beta.threads.create(
            messages=[{"role": "user", "content": user_message}]
        )
        logger.info(f"Thread oluşturuldu (Asistan: {assistant_id}): {thread.id}")

        # Run başlat
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        logger.info(f"Run başlatıldı (Asistan: {assistant_id}): {run.id}")

        # Run tamamlanana kadar bekle (API çağrısı aralığını optimize ederek)
        start_time = time.time()
        run_status = "queued"
        while run_status != "completed":
            if time.time() - start_time > 30:  # 30 saniye zaman aşımı
                raise TimeoutError(f"Asistan {assistant_id} için zaman aşımı oluştu.")
            time.sleep(0.5)  # API yükünü azaltmak için sorgu aralığını artırdık
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            run_status = run.status

        # Yanıtları al
        message_response = client.beta.threads.messages.list(thread_id=thread.id)
        messages = message_response.data
        latest_message = next((msg for msg in messages if msg.role == "assistant"), None)

        if latest_message and latest_message.content:
            content = latest_message.content
            if isinstance(content, list):
                content_text = " ".join(str(c) for c in content)
            else:
                content_text = str(content)

            # Yanıt metnini temizle
            cleaned_content = clean_text(content_text)

            # HTML formatında döndür
            formatted_response = f"<html><body><p>{content_text.replace('\n', '<br>')}</p></body></html>"

            relevant_keywords = ASSISTANT_CONFIG.get(assistant_id, [])
            logger.info(f"Asistan {assistant_id} yanıt verdi: {content_text}")
            logger.info(f"Asistan {assistant_id} için kontrol edilen anahtar kelimeler: {relevant_keywords}")

            # Anahtar kelime sabit kontrol ve fuzzy eşleşme
            if any(keyword.lower() in cleaned_content for keyword in relevant_keywords):
                logger.info(f"Asistan {assistant_id} yanıtında sabit anahtar kelime bulundu.")
                return assistant_id, formatted_response
            elif any(fuzz.partial_ratio(keyword.lower(), cleaned_content) > 70 for keyword in relevant_keywords):
                logger.info(f"Asistan {assistant_id} yanıtı fuzzy eşleşme ile doğru bulundu.")
                return assistant_id, formatted_response
            else:
                logger.warning(f"Asistan {assistant_id} yanıt verdi ancak anahtar kelimelerle eşleşmedi: {content_text}")

        logger.info(f"Asistan {assistant_id} uygun bir yanıt vermedi.")
        return assistant_id, None
    except Exception as e:
        logger.error(f"Hata (Asistan: {assistant_id}): {str(e)}")
        return assistant_id, None

@app.route("/ask", methods=["POST"])
def ask():
    global active_assistant_id
    data = request.json
    user_message = data.get("question", "")

    if not user_message:
        return jsonify({"response": "Lütfen bir soru girin."})

    logger.info(f"Kullanıcı mesajı: {user_message}")

    # Anahtar kelimeleri kontrol et
    relevant_keywords = ["kamiq", "scala", "fabia"]
    if not any(keyword.lower() in user_message.lower() for keyword in relevant_keywords):
        # İlk mesajda anahtar kelime yoksa kullanıcıya uyarı ver
        if not active_assistant_id:
            logger.info("Anahtar kelime bulunamadı. Daha fazla detay istendi.")
            return jsonify({"response": "Talebinizi daha detaylı girerseniz size yardımcı olabilirim."})
        # Daha önce bir asistan aktifse, aynı asistandan yanıt al
        logger.info(f"Aktif asistan: {active_assistant_id}. Aynı asistandan yanıt alınıyor.")
        _, response = process_assistant(active_assistant_id, user_message)
        return jsonify({"response": response})

    for assistant_id, keywords in ASSISTANT_CONFIG.items():
        if any(keyword.lower() in user_message.lower() for keyword in keywords):
            active_assistant_id = assistant_id
            logger.info(f"Direkt olarak {assistant_id} asistanına yönlendiriliyor.")
            _, response = process_assistant(assistant_id, user_message)
            return jsonify({"response": response})

    # Eğer anahtar kelime yoksa önceki aktif asistandan yanıt al
    if active_assistant_id:
        logger.info(f"Aktif asistan: {active_assistant_id}. Aynı asistandan yanıt alınıyor.")
        _, response = process_assistant(active_assistant_id, user_message)
        return jsonify({"response": response})

    # Paralel işleme (hiçbir asistan aktif değilse)
    with ThreadPoolExecutor(max_workers=len(ASSISTANT_CONFIG)) as executor:
        results = list(executor.map(lambda aid: process_assistant(aid, user_message), ASSISTANT_CONFIG.keys()))

    # Alakalı yanıtı bul
    for assistant_id, content in results:
        if content:  # Eğer içerik varsa
            active_assistant_id = assistant_id  # Yeni aktif asistanı ayarla
            logger.info(f"Asistan {assistant_id} için anahtar kelimeler: {ASSISTANT_CONFIG.get(assistant_id, [])}")
            return jsonify({"response": content})

    logger.warning("Hiçbir asistan uygun bir yanıt veremedi.")
    return jsonify({"response": "Hiçbir asistan uygun bir yanıt veremedi."})

if __name__ == "__main__":
    app.run(debug=True)
