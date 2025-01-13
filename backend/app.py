import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# OpenAI API Client oluştur
client = OpenAI(api_key="")

# Flask uygulaması oluştur
app = Flask(__name__)
CORS(app)

# Asistan ID'leri
ASSISTANT_IDS = [
    "asst_1qGG7y8w6QcupPETaYQRdGsI",  # Skoda Kamiq Bot
    "asst_I7YubD3Cy6qU4kCc32mbYjUQ",  # Skoda Fabia Bot
    "asst_Ul4gzwnyRZxNcb3I5ot93lo9",  # Skoda Scala Bot
]

# İlgili anahtar kelimeler
RELEVANT_KEYWORDS = ["Kamiq", "Fabia", "Scala"]

@app.route("/", methods=["GET"])
def home():
    return "Chatbot API çalışıyor. Sorularınızı /ask endpointine POST edin."

def process_assistant(assistant_id, user_message):
    try:
        # Thread oluştur
        thread = client.beta.threads.create(
            messages=[{"role": "user", "content": user_message}]
        )
        print(f"👉 Thread Oluşturuldu (Asistan: {assistant_id}): {thread.id}")

        # Run başlat
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        print(f"👉 Run Başlatıldı (Asistan: {assistant_id}): {run.id}")

        # Run tamamlanana kadar bekle (zaman aşımı kontrolüyle)
        start_time = time.time()
        run_status = "queued"
        while run_status != "completed":
            if time.time() - start_time > 10:  # 10 saniye zaman aşımı
                raise TimeoutError(f"Asistan {assistant_id} için zaman aşımı oluştu.")
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            run_status = run.status
            time.sleep(0.2)  # Bekleme süresi optimize edildi

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

            # Yanıtın alakalı olup olmadığını kontrol et
            if any(keyword.lower() in content_text.lower() for keyword in RELEVANT_KEYWORDS):
                return assistant_id, content_text
        return assistant_id, None
    except Exception as e:
        print(f"❗ Hata (Asistan: {assistant_id}): {str(e)}")
        return assistant_id, None

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_message = data.get("question", "")

    if not user_message:
        return jsonify({"response": "Lütfen bir soru girin."})

    # Paralel işleme
    with ThreadPoolExecutor(max_workers=3) as executor:  # Maksimum 3 iş parçacığı
        results = list(executor.map(lambda aid: process_assistant(aid, user_message), ASSISTANT_IDS))

    # Alakalı yanıtı bul
    relevant_response = next((content for assistant_id, content in results if content), None)

    if relevant_response:
        return jsonify({"response": relevant_response})
    else:
        return jsonify({"response": "Hiçbir asistan uygun bir yanıt veremedi."})

if __name__ == "__main__":
    app.run(debug=True)
