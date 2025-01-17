import os
import time
import logging
import re

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai

# Pillow ve Matplotlib (ImageManager'da kullanılabilir)
from PIL import Image
import matplotlib.pyplot as plt

load_dotenv()  # .env dosyanızda OPENAI_API_KEY vb. varsa yükler

# --------------------------------------------------
# ImageManager Sınıfı
# --------------------------------------------------
class ImageManager:
    def __init__(self, images_folder):
        """
        :param images_folder: Resimlerin yer aldığı klasörün yolu
        """
        self.images_folder = images_folder
        self.image_files = []

        # Stopword listesi (dosya adında arama sırasında devre dışı kalacak kelimeler)
        self.stopwords = {
            "model", "araç", "arac", "paylaşabilir", "paylaşır", "misin", "mısın",
            "lütfen", "istiyorum", "?", "görsel", "resim", "fotoğraf", "fotograf"
        }

    def load_images(self):
        """
        images_folder içerisindeki resim dosyalarını (png, jpg, jpeg) yükler
        ve self.image_files listesine atar.
        """
        if not os.path.exists(self.images_folder):
            raise FileNotFoundError(f"'{self.images_folder}' klasörü bulunamadı.")

        valid_extensions = ('.png', '.jpg', '.jpeg')
        self.image_files = [
            f for f in os.listdir(self.images_folder)
            if f.lower().endswith(valid_extensions)
        ]
        print(f"{len(self.image_files)} adet resim yüklendi:\n{self.image_files}")

    def filter_images_multi_keywords(self, keywords_string: str):
        """
        'keywords_string' içindeki tüm kelimeleri (boşluğa göre ayrılmış) 
        dosya adında alt dize olarak arar. (Stopword'lar hariç)

        Örnek: "Fabia kırmızı" => ["fabia", "kırmızı"]
        -> Tüm kelimelerin dosya adında geçmesi şartıyla eşleşme.
        """
        # 1) Küçük harfe çevir ve split
        splitted_raw = keywords_string.lower().split()

        # 2) Stopword temizliği
        splitted = [word for word in splitted_raw if word not in self.stopwords]

        matched_files = []
        for img in self.image_files:
            img_lower = img.lower()
            # Bütün kelimeler bu dosya adında var mı?
            if all(word in img_lower for word in splitted):
                matched_files.append(img)

        return matched_files

    def display_images(self, image_list):
        """
        (Opsiyonel) Server tarafında matplotlib ile gösterim örneği.
        """
        for image_name in image_list:
            image_path = os.path.join(self.images_folder, image_name)
            with Image.open(image_path) as img:
                plt.figure(figsize=(8, 6))
                plt.imshow(img)
                plt.axis("off")
                plt.title(os.path.splitext(image_name)[0])
                plt.show()

# --------------------------------------------------
# Yardımcı Fonksiyonlar (Markdown vb.)
# --------------------------------------------------

def transform_text_to_markdown(input_text):
    lines = input_text.split('\n')
    transformed_lines = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('- **') and stripped_line.endswith(':**'):
            heading_content = stripped_line.replace('- **', '').replace(':**', '').strip()
            transformed_lines.append(f'### {heading_content}')
        elif stripped_line.startswith('- '):
            bullet_content = stripped_line[2:]
            transformed_lines.append(f'- {bullet_content}')
        else:
            transformed_lines.append(stripped_line)
    return '\n'.join(transformed_lines)

def extract_markdown_tables_from_text(text):
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
    fixed_lines = []
    lines = table_markdown.split('\n')
    for line in lines:
        if '|' not in line:
            fixed_lines.append(line)
            continue
        columns = line.split('|')
        fixed_columns = []
        for col in columns:
            col = col.strip()
            col = col.replace('**', '')
            col = re.sub(r'(\d)\'\'(\d)', r'\1/\2', col)
            col = re.sub(r'([A-Za-z])//([A-Za-z])', r"\1'\2", col)
            fixed_columns.append(col)
        fixed_line = ' | '.join(fixed_columns)
        fixed_lines.append(fixed_line)
    return '\n'.join(fixed_lines)

def markdown_table_to_html(md_table_str):
    md_table_str = fix_table_characters(md_table_str)
    lines = md_table_str.strip().split("\n")
    if len(lines) < 2:
        return f"<p>{md_table_str}</p>"

    header_cols = [col.strip() for col in lines[0].split("|") if col.strip()]
    body_lines = lines[2:]

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

# --------------------------------------------------
# ChatbotAPI Sınıfı
# --------------------------------------------------
class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        self.app = Flask(__name__,
                         static_folder=static_folder,
                         template_folder=template_folder)
        CORS(self.app)

        self.logger = self._setup_logger()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        # Asistan -> tetikleyici kelimeler
        self.ASSISTANT_CONFIG = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }

        # Kullanıcı -> son kullanılan asistan (assistant_id)
        self.user_states = {}  # { user_id: assistant_id }

        # Asistan ID -> Model İsmi
        self.ASSISTANT_NAME_MAP = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": "Kamiq",
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": "Fabia",
            "asst_njSG1NVgg4axJFmvVYAIXrpM": "Scala",
        }

        # ImageManager kurulum
        images_path = os.path.join(self.app.static_folder, "images")
        self.image_manager = ImageManager(images_folder=images_path)
        self.image_manager.load_images()

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

        # 1) Görsel isteği var mı?
        if self._is_image_request(user_message):
            # ChatGPT'ye gitmiyoruz, direkt resim bulma aşamasına geçiyoruz.
            assistant_id = self.user_states.get(user_id)
            if not assistant_id:
                yield "Henüz bir asistan seçilmediği için görsel gösteremiyorum.\n".encode("utf-8")
                return

            assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
            if not assistant_name:
                yield "Asistan adını bulamadım.\n".encode("utf-8")
                return

            # Kullanıcının mesajındaki anahtar kelimeleri yakalamak
            keyword = self._extract_image_keyword(user_message, assistant_name)
            # keyword örn: "kırmızı model" => "kırmızı"

            if keyword:
                # "Fabia premium kırmızı" vb.
                full_filter = f"{assistant_name} {keyword}"
            else:
                # Belki sadece "Fabia görsel" demiş olabilir
                full_filter = assistant_name

            # >>> Çoklu kelime arama fonksiyonu <<<
            found_images = self.image_manager.filter_images_multi_keywords(full_filter)
            if not found_images:
                yield f"'{full_filter}' için uygun bir görsel bulamadım.\n".encode("utf-8")
            else:
                yield f"{assistant_name} asistanına ait görseller (filtre: '{keyword if keyword else 'None'}'):\n".encode("utf-8")
                for img_file in found_images:
                    img_url = f"/static/images/{img_file}"
                    yield f'<img src="{img_url}" alt="{img_file}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

            return

        # 2) Görsel isteği yoksa asistan seçimi yap
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        # 3) ChatGPT (OpenAI) akışı
        try:
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
                            content = str(msg.content)
                            content = transform_text_to_markdown(content)

                            # Opsiyonel tablo dönüştürme
                            pattern = r'value="([^"]+)"'
                            match = re.search(pattern, content)
                            if match:
                                extracted_text = match.group(1).replace("\\n", "\n")
                                tables = extract_markdown_tables_from_text(extracted_text)
                                if tables:
                                    self.logger.info(f"Bulunan tablolar: {tables}")
                                    for i, tbl in enumerate(tables, 1):
                                        html_table = markdown_table_to_html(tbl)
                                        yield f"\n--- Tablo {i} (HTML) ---\n".encode("utf-8")
                                        yield html_table.encode("utf-8")
                                        yield b"\n"

                            yield content.encode("utf-8")
                    return

                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    # -------------------------------------------------
    # Yardımcı metotlar
    # -------------------------------------------------
    def _is_image_request(self, message: str):
        """
        Kullanıcının mesajında 'resim', 'fotoğraf' veya 'görsel' kelimesi geçiyor mu?
        """
        lower_msg = message.lower()
        if "resim" in lower_msg or "fotoğraf" in lower_msg or "görsel" in lower_msg:
            return True
        return False

    def _extract_image_keyword(self, message: str, assistant_name: str):
        """
        Mesajdan 'fabia premium kırmızı model' gibi bir filtrenin çekilmesini sağlar.
        - Markayı (assistant_name) cümleden çıkartıyoruz
        - 'resim', 'fotoğraf', 'görsel' kelimelerini çıkarıyoruz (isterseniz stopwords'te de tutabilirsiniz)
        - 'paylaşabilir misin', 'lütfen' vb. kalıpları temizliyoruz
        - 'monte carlo' ifadesini 'monte_carlo' şeklinde dönüştürüyoruz
        """
        lower_msg = message.lower()
        brand_lower = assistant_name.lower()

        # Markayı çıkar
        cleaned = lower_msg.replace(brand_lower, "")

        # Örnek: 'resim', 'fotoğraf', 'görsel' vb. kelimeleri çıkar
        cleaned = re.sub(r"(resim|fotoğraf|görsel)\w*", "", cleaned, flags=re.IGNORECASE)

        # Yaygın ek kalıplar
        common_phrases = [
            r"paylaşabilir\s?misin", r"paylaşır\s?mısın", r"lütfen", r"istiyorum", r"\?$"
        ]
        for p in common_phrases:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)

        # "monte carlo" → "monte_carlo" (dosya adlarında monte_carlo şeklindeyse)
        cleaned = re.sub(r"monte\s+carlo", "monte_carlo", cleaned, flags=re.IGNORECASE)

        final_keyword = cleaned.strip()
        return final_keyword if final_keyword else None

    def _feedback(self):
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
