import os
import re
import time
import openai
import logging

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

from modules.image_manager import ImageManager
from modules.markdown_utils import MarkdownProcessor
from modules.text_to_speech import TextToSpeech

load_dotenv()

class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        self.app = Flask(__name__,
                         static_folder=os.path.join(os.getcwd(), static_folder),
                         template_folder=os.path.join(os.getcwd(), template_folder))
        
        CORS(self.app)

        self.logger = self._setup_logger()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        self.ASSISTANT_CONFIG = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }

        self.user_states = {}
        self.ASSISTANT_NAME_MAP = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": "Kamiq",
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": "Fabia",
            "asst_njSG1NVgg4axJFmvVYAIXrpM": "Scala",
        }

        images_path = os.path.join(static_folder, "images")
        self.image_manager = ImageManager(images_folder=images_path)
        self.image_manager.load_images()

        self.markdown_processor = MarkdownProcessor()

        # Initialize TTS
        self.tts = TextToSpeech(language='tr', assets_path='assets')

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
                return jsonify({"error": "Invalid JSON format."}), 400
        except Exception as e:
            self.logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({"error": "Invalid JSON format."}), 400

        user_message = data.get("question", "")
        user_id = data.get("user_id", "default_user")

        if not user_message:
            return jsonify({"response": "Please enter a question."})

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

            # yield "Yanıt hazırlanıyor...\n".encode("utf-8")

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
                            content = self.markdown_processor.transform_text_to_markdown(content)
                            # Opsiyonel tablo dönüştürme
                            pattern = r'value="([^"]+)"'
                            match = re.search(pattern, content)
                            if match:
                                extracted_text = match.group(1).replace("\\n", "\n")
                                tables = self.markdown_processor.extract_markdown_tables_from_text(extracted_text)
                                if tables:
                                    self.logger.info(f"Bulunan tablolar: {tables}")
                                    for i, tbl in enumerate(tables, 1):
                                        html_table = self.markdown_processor.markdown_table_to_html(tbl)
                                        yield f"\n--- Tablo {i} (HTML) ---\n".encode("utf-8")
                                        yield html_table.encode("utf-8")
                                        yield b"\n"
                            try:
                                print("----------------------------------")
                                print(content)
                                content = str(content).replace("[TextContentBlock(text=Text(annotations=[FileCitationAnnotation(end_index=1435, file_citation=FileCitation(file_id='file-EAtMSGfx719cu18X55wHTj'), start_index=1423, text='', type='file_citation')], value='", "")
                                content = content.replace("'), type='text')]", "")
                                print("----------------------------------")
                                print("REMOVED")
                                print("----------------------------------")
                                print(content)
                                print("----------------------------------")
                            except:
                                print("NOTHING")
                                pass
                            # Speak the response
                            self.tts.speak(content)
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