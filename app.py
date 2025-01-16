import os
import time
import logging
import re

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai

load_dotenv()

def extract_markdown_tables_from_text(text):
    """
    Verilen text içinde '|' içeren satırları bularak potansiyel Markdown tablo satırlarını döndürür.
    Birden fazla tablo bulunması durumunda, tabloları ardışık satırlara göre ayırır.
    """
    lines = text.splitlines()
    tables = []
    current_table = []

    for line in lines:
        if '|' in line.strip():
            current_table.append(line)
        else:
            if current_table:
                tables.append('\n'.join(current_table))
                current_table = []
    
    if current_table:
        tables.append('\n'.join(current_table))

    return tables

def markdown_table_to_html(md_table_str):
    """
    Basit bir Markdown tabloyu HTML tabloya dönüştürür.
    """
    lines = md_table_str.strip().split("\n")
    if len(lines) < 2:
        return f"<p>{md_table_str}</p>"
    
    # 1. satır başlık
    header_cols = [col.strip() for col in lines[0].split("|") if col.strip()]
    # 2. satır (ayraç) => lines[1], geri kalan satırlar => body
    body_lines = lines[2:]  # satır 2'den sonuna

    html = '<table class="table table-bordered table-sm" style="background-color:#fff; color:#000;">\n'
    html += '<thead><tr>'
    for col in header_cols:
        html += f'<th>{col}</th>'
    html += '</tr></thead>\n<tbody>\n'

    for line in body_lines:
        line = line.strip()
        if not line:
            continue
        cols = [c.strip() for c in line.split("|") if c.strip()]
        html += '<tr>'
        for c in cols:
            html += f'<td>{c}</td>'
        html += '</tr>\n'

    html += '</tbody>\n</table>'
    return html


class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        self.app = Flask(__name__,
                         static_folder=static_folder,
                         template_folder=template_folder)
        CORS(self.app)

        self.logger = self._setup_logger()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        # Örnek asistan yapılandırması (anahtar kelime -> asistan ID eşlemesi)
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }
        self.user_states = {}

        self._define_routes()

    def _setup_logger(self):
        logger = logging.getLogger("ChatbotAPI")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _define_routes(self):
        @self.app.route("/", methods=["GET"])
        def home():
            return render_template("index.html")

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._ask()

        @self.app.route("/feedback", methods=["POST"])
        def feedback():
            return self._feedback()

    def _ask(self):
        """
        Kullanıcının sorusunu alır, ChatGPT'ye gönderir ve yanıtı text/plain
        olarak chunk halinde döndürür.
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

        response_generator = self._generate_response(user_message, user_id)
        return self.app.response_class(response_generator, mimetype="text/plain")

    def _generate_response(self, user_message, user_id):
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")

        # Kullanıcının mesajındaki anahtar kelimeler doğrultusunda asistan seçimi
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        try:
            # Yeni bir thread oluştur
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )

            yield "Yanıt hazırlanıyor...\n".encode("utf-8")

            start_time = time.time()
            timeout = 30  # 30 saniye bekleme süresi

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

                if run.status == "completed":
                    # Asistan cevabı hazır
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)

                            # 1) value="..." içeriğini bulmaya çalışalım
                            pattern = r'value="([^"]+)"'
                            match = re.search(pattern, content)
                            if match:
                                extracted_text = match.group(1)
                                # Kaçış karakterlerini düzelt
                                extracted_text = extracted_text.replace("\\n", "\n")

                                # 2) Tabloları Markdown olarak ayrıştır
                                tables = extract_markdown_tables_from_text(extracted_text)
                                if tables:
                                    self.logger.info(f"Bulunan tablolar: {tables}")

                                    # İsterseniz tabloyu HTML'e dönüştürüp
                                    # client'a HTML olarak da gönderebilirsiniz:
                                    for i, tbl in enumerate(tables, 1):
                                        html_table = markdown_table_to_html(tbl)
                                        # Deneme amaçlı tabloyu HTML olarak gönderelim
                                        yield f"\n--- Tablo {i} (HTML) ---\n".encode("utf-8")
                                        yield html_table.encode("utf-8")
                                        yield b"\n"

                            # Son olarak orijinal cevabı da gönderelim
                            yield content.encode("utf-8")
                    return

                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            # Zaman aşımı
            yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    def _feedback(self):
        """
        Örnek bir feedback endpoint
        """
        try:
            data = request.get_json()
            self.logger.info(f"Geri bildirim alındı: {data}")
            return jsonify({"message": "Geri bildiriminiz için teşekkür ederiz!"})
        except Exception as e:
            self.logger.error(f"Geri bildirim hatası: {str(e)}")
            return jsonify({"error": "Bir hata oluştu."}), 500

    def run(self, debug=True):
        self.app.run(debug=debug)


if __name__ == "__main__":
    chatbot = ChatbotAPI()
    chatbot.run(debug=True)
