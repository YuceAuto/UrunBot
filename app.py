import os
import time
import logging
import re

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai

load_dotenv()

def transform_text_to_markdown(input_text):
    """
    Gelen metindeki özel işaretleri ve kalıpları tespit ederek
    Markdown formatına dönüştürür.
    Örnek:
    - '- **Güvenlik:**' => '### Güvenlik'
    - '- metin' => '- metin' (madde imi)
    """
    lines = input_text.split('\n')
    transformed_lines = []

    for line in lines:
        stripped_line = line.strip()

        # Özel kalıp 1: '- **...:**' => '### ...'
        if stripped_line.startswith('- **') and stripped_line.endswith(':**'):
            # Örneğin: '- **Güvenlik:**' => 'Güvenlik'
            heading_content = stripped_line.replace('- **', '').replace(':**', '').strip()
            transformed_lines.append(f'### {heading_content}')

        # Özel kalıp 2: '- ' ile başlayan satırlar => normal bullet
        elif stripped_line.startswith('- '):
            bullet_content = stripped_line[2:]
            transformed_lines.append(f'- {bullet_content}')

        else:
            transformed_lines.append(stripped_line)

    return '\n'.join(transformed_lines)

def extract_markdown_tables_from_text(text):
    """
    Verilen text içinde '|' içeren satırları bularak potansiyel Markdown tablo satırlarını döndürür.
    Birden fazla tablo varsa, ardışık satırlara göre ayırır.
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

def fix_table_characters(table_markdown: str) -> str:
    """
    Markdown tablo metnindeki özel karakterleri temizler/düzeltir.
    Örnek:
      - Hücre başı/sonundaki '**' karakterlerini kaldırmak
      - Sayıların arasındaki '' => / dönüştürmesi
      - Harflerin arasındaki // => ' (veya tam tersi) dönüştürmesi
    """

    fixed_lines = []
    lines = table_markdown.split('\n')

    for line in lines:
        if '|' not in line:
            # Tablonun ayırıcı olmayan satırıysa direkt ekle.
            fixed_lines.append(line)
            continue

        columns = line.split('|')
        fixed_columns = []
        for col in columns:
            col = col.strip()
            
            # 1) '**' temizle
            col = col.replace('**', '')

            # 2) Sayıların arasında '' => /
            # Örnek: 123''456 => 123/456
            col = re.sub(r'(\d)\'\'(\d)', r'\1/\2', col)

            # 3) Harflerin arasında // => '
            # Örnek: A//B => A'B
            col = re.sub(r'([A-Za-z])//([A-Za-z])', r"\1'\2", col)

            fixed_columns.append(col)

        # Sabitlenmiş sütunları yeniden birleştir
        fixed_line = ' | '.join(fixed_columns)
        fixed_lines.append(fixed_line)

    return '\n'.join(fixed_lines)

def markdown_table_to_html(md_table_str):
    """
    Basit bir Markdown tabloyu HTML'e dönüştürür; tablo arka planı .my-blue-table ile mavi yapılır.
    """
    # (ÖNEMLİ) Önce tablo içindeki özel karakterleri düzeltelim
    md_table_str = fix_table_characters(md_table_str)

    lines = md_table_str.strip().split("\n")
    if len(lines) < 2:
        return f"<p>{md_table_str}</p>"
    
    header_cols = [col.strip() for col in lines[0].split("|") if col.strip()]
    body_lines = lines[2:]  # 2. satır ayraç olduğu için atlıyoruz

    html = '<table class="table table-bordered table-sm my-blue-table">\n'
    html += '<thead><tr>'
    for col in header_cols:
        html += f'<th>{col}</th>'
    html += '</tr></thead>\n<tbody>\n'

    for line in body_lines:
        row = line.strip()
        if not row:
            continue
        cols = [c.strip() for c in row.split("|") if c.strip()]
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

        # Örnek asistan yapılandırması (keyword -> asistan ID eşlemesi)
        self.ASSISTANT_CONFIG = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": ["Kamiq"],
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
            timeout = 30  # 30 saniye bekleme

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

                if run.status == "completed":
                    # Asistan cevabı hazır
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            # Orijinal içerik
                            content = str(msg.content)

                            # 1) Metni Markdown'a dönüştür
                            content = transform_text_to_markdown(content)

                            # 2) (isteğe bağlı) tabloları bulup HTML'e dönüştür
                            pattern = r'value="([^"]+)"'
                            match = re.search(pattern, content)
                            if match:
                                extracted_text = match.group(1).replace("\\n", "\n")
                                tables = extract_markdown_tables_from_text(extracted_text)

                                if tables:
                                    self.logger.info(f"Bulunan tablolar: {tables}")
                                    for i, tbl in enumerate(tables, 1):
                                        html_table = markdown_table_to_html(tbl)
                                        # Tabloyu HTML olarak chunk halinde gönderelim:
                                        yield f"\n--- Tablo {i} (HTML) ---\n".encode("utf-8")
                                        yield html_table.encode("utf-8")
                                        yield b"\n"

                            # 3) Dönüştürülmüş içeriği gönder
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
