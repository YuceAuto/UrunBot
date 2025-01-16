import os
import re
import time
import logging

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai

load_dotenv()

class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        """
        Flask uygulamasını, loglamayı, OpenAI istemcisini ve asistan yapılandırmalarını
        sınıf tabanlı şekilde başlatır.
        """
        # Flask uygulamasını başlat
        self.app = Flask(
            __name__,
            static_folder=static_folder,
            template_folder=template_folder
        )
        CORS(self.app)

        # Loglama ayarları
        self.logger = self._setup_logger()

        # .env içinden API anahtarını al
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        # Asistan yapılandırması
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }
        self.user_states = {}

        # Rota tanımları
        self._define_routes()

    def _setup_logger(self):
        """
        Uygulama için logger tanımlayıp döndürür.
        """
        logger = logging.getLogger("ChatbotAPI")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _define_routes(self):
        """
        Flask rotalarını tanımlar.
        """
        @self.app.route("/", methods=["GET"])
        def home():
            return self._home()

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._ask()

        @self.app.route("/feedback", methods=["POST"])
        def feedback():
            return self._feedback()

    def _home(self):
        """
        Ana sayfa görünümü.
        """
        return render_template("index.html")

    def _ask(self):
        """
        Kullanıcıdan gelen soruları (POST) işleyen endpoint.
        Streaming (chunk) şeklinde yanıt döndürür.
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Geçersiz JSON formatı."}), 400
        except Exception as e:
            self.logger.error(f"JSON ayrıştırma hatası: {str(e)}")
            return jsonify({"error": "Geçersiz JSON formatı."}), 400

        user_message = data.get("question", "")
        user_id = data.get("user_id", "default_user")

        if not user_message:
            return jsonify({"response": "Lütfen bir soru girin."})

        # Yanıtı chunk olarak üreten generator
        response_generator = self._generate_response(user_message, user_id)
        return self.app.response_class(response_generator, mimetype="text/plain")

    def _generate_response(self, user_message, user_id):
        """
        Asistan ID seçer ve OpenAI üzerinden yanıtı parça parça (stream) oluşturur.
        """
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")
        assistant_id = self.user_states.get(user_id)

        # Mesaja göre asistan seç
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        try:
            # ChatGPT thread oluştur
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=assistant_id
            )

            start_time = time.time()
            timeout = 30

            # İlk "Yanıt hazırlanıyor..." mesajı
            yield "Yanıt hazırlanıyor...\n".encode("utf-8")

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )
                if run.status == "completed":
                    # Yanıtı al
                    message_response = self.client.beta.threads.messages.list(
                        thread_id=thread.id
                    )
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)
                            # Triple backtick içeriğini koruyan fonksiyonla temizle
                            content = self._strip_textcontentblock_keep_value(content)
                            yield content.encode("utf-8")
                    return

                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                # . animasyon satırı kaldırıldı (isterseniz ekleyebilirsiniz)
                time.sleep(0.5)

            yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    def _strip_textcontentblock_keep_value(self, original_text):
        """
        [TextContentBlock(...)] -> triple backtick JSON
        Sadece triple backtick içindeki veriyi koruyor, dışını atıyor.
        """
        pattern = r"""
        \[TextContentBlock         # Blokların başlangıcı
        \(                         # Parantez
        .*?                        # type, text, vs. rastgele
        value=['\"`]{3}            # triple tırnak veya backtick
        ([\s\S]*?)                 # <-- Yakalamak istediğimiz "value" içeriği
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

    def _feedback(self):
        """
        Geri bildirim endpoint'i.
        """
        try:
            data = request.get_json()
            self.logger.info(f"Geri bildirim alındı: {data}")
            return jsonify({"message": "Geri bildiriminiz için teşekkür ederiz!"})
        except Exception as e:
            self.logger.error(f"Geri bildirim hatası: {str(e)}")
            return jsonify({"error": "Bir hata oluştu."}), 500

    def run(self, debug=True):
        """
        Flask uygulamasını çalıştırır.
        """
        self.app.run(debug=debug)


if __name__ == "__main__":
    chatbot = ChatbotAPI()
    chatbot.run(debug=True)
