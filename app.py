import time
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
import logging
from dotenv import load_dotenv
import openai
import os
# .env dosyasından ortam değişkenlerini yükleyelim
load_dotenv()


app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
CORS(app)

# Loglama
logger = logging.getLogger("ChatbotAPI")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

openai.api_key = os.getenv("OPENAI_API_KEY")

# openai nesnesini client olarak kullanmak istiyorsanız:
client = openai

# Asistan ID / Anahtar Kelime
ASSISTANT_CONFIG = {
    "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],
    "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
    "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
}
user_states = {}

# -------------------------------------------------
#  [TextContentBlock(...)] -> triple backtick JSON
#  Sadece triple backtick içindeki metni koruyoruz
# -------------------------------------------------
def strip_textcontentblock_keep_value(original_text):
    """
    [TextContentBlock(text=Text(...), value='''json ... ''', type='text')]
    gibi bloklardan, sadece triple backtick (''' ... ''') içindeki
    veriyi saklayıp, geri kalan sarmalayıcı ifadeyi atar.
    """
    pattern = r"""
    \[TextContentBlock         # Blokların başlangıcı
    \(                         # Parantez
    .*?                        # type, text, vs. rastgele
    value=['\"`]{3}            # triple tırnak veya backtick
    ([\s\S]*?)                 # <-- Burası asıl yakalamak istediğimiz "value" içeriği
    ['\"`]{3}                  # triple tırnak/backtick kapanışı
    .*?                        # Kalan kısımları (annotations vs.)
    \)                         # Blok parantez sonu
    \]                         # Köşeli parantez kapanışı
    """

    compiled = re.compile(pattern, flags=re.VERBOSE | re.DOTALL)

    def replacer(match):
        # Yakalanan group(1) -> triple backtick içi
        inner_value = match.group(1)
        # Bunu tekrar code fence'e sararak geri döndürüyoruz
        return f"```json\n{inner_value}\n```"

    return compiled.sub(replacer, original_text)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    """
    Streaming (chunk) yanıt döndüren endpoint.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Geçersiz JSON formatı."}), 400
    except Exception as e:
        logger.error(f"JSON ayrıştırma hatası: {str(e)}")
        return jsonify({"error": "Geçersiz JSON formatı."}), 400

    user_message = data.get("question", "")
    user_id = data.get("user_id", "default_user")

    if not user_message:
        return jsonify({"response": "Lütfen bir soru girin."})

    def generate_response():
        logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")
        assistant_id = user_states.get(user_id)

        # Mesaja göre asistan seç
        for aid, keywords in ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                user_states[user_id] = assistant_id
                break

        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        try:
            # ChatGPT thread oluştur
            thread = client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

            start_time = time.time()
            timeout = 30

            # "Yanıt hazırlanıyor..." KALSIN
            yield "Yanıt hazırlanıyor...\n".encode("utf-8")

            while time.time() - start_time < timeout:
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    # Yanıtı al
                    message_response = client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)

                            # Yalnızca triple backtick verisini koruyacak şekilde
                            content = strip_textcontentblock_keep_value(content)

                            # Aşağıda isterseniz FileCitationAnnotation vb. ek notasyonları da temizleyebilirsiniz
                            # content = re.sub(r"\[FileCitationAnnotation[\s\S]*?\)", "", content)

                            # Tek chunk olarak gönderelim (isterseniz harf harf de yapabilirsiniz)
                            yield content.encode("utf-8")
                    return

                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                # Nokta (.) animasyonunu kaldırmak için bu satırı yorumluyoruz:
                # yield ".".encode("utf-8")
                time.sleep(0.5)

            yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")

        except Exception as e:
            logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    return app.response_class(generate_response(), mimetype="text/plain")

@app.route("/feedback", methods=["POST"])
def feedback():
    try:
        data = request.get_json()
        logger.info(f"Geri bildirim alındı: {data}")
        return jsonify({"message": "Geri bildiriminiz için teşekkür ederiz!"})
    except Exception as e:
        logger.error(f"Geri bildirim hatası: {str(e)}")
        return jsonify({"error": "Bir hata oluştu."}), 500

if __name__ == "__main__":
    app.run(debug=True)
