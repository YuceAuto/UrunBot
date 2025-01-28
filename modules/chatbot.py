import os
import time
import logging
import re
import openai
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

from modules.image_manager import ImageManager
from modules.markdown_utils import MarkdownProcessor
from modules.config import Config
from modules.utils import Utils

load_dotenv()

class ChatbotAPI:
    def __init__(self, logger=None, static_folder='static', template_folder='templates'):
        self.app = Flask(
            __name__,
            static_folder=os.path.join(os.getcwd(), static_folder),
            template_folder=os.path.join(os.getcwd(), template_folder)
        )
        CORS(self.app)

        self.logger = logger if logger else self._setup_logger()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        self.config = Config()
        self.utils = Utils()

        self.image_manager = ImageManager(images_folder=os.path.join(static_folder, "images"))
        self.image_manager.load_images()

        self.markdown_processor = MarkdownProcessor()

        self.ASSISTANT_CONFIG = self.config.ASSISTANT_CONFIG
        self.ASSISTANT_NAME_MAP = self.config.ASSISTANT_NAME_MAP

        # user_states[user_id] = { "assistant_id": ..., "pending_color_images": [...], ...}
        self.user_states = {}

        self._define_routes()

    def _setup_logger(self):
        logger = logging.getLogger("ChatbotAPI")
        if not logger.handlers:
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

    def _feedback(self):
        try:
            data = request.get_json()
            self.logger.info(f"Geri bildirim alındı: {data}")
            return jsonify({"message": "Geri bildiriminiz için teşekkür ederiz!"})
        except Exception as e:
            self.logger.error(f"Geri bildirim hatası: {str(e)}")
            return jsonify({"error": "Bir hata oluştu."}), 500

    def _generate_response(self, user_message, user_id):
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")

        if user_id not in self.user_states:
            self.user_states[user_id] = {}

        assistant_id = self.user_states[user_id].get("assistant_id", None)

        # Asistan seçimi
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in user_message.lower() for k in keywords):
                assistant_id = aid
                self.user_states[user_id]["assistant_id"] = assistant_id
                break

        lower_msg = user_message.lower()

        # 0) Kullanıcı "evet" derse ve pending_color_images varsa -> görselleri gönder
        if lower_msg.strip() in ["evet", "evet.", "evet!", "evet?", "evet,"]:
            pending_colors = self.user_states[user_id].get("pending_color_images", [])
            if pending_colors:
                if assistant_id is not None:
                    asst_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "scala")
                else:
                    asst_name = "scala"

                all_found_images = []
                for clr in pending_colors:
                    keywords = f"{asst_name} {clr}"
                    results = self.image_manager.filter_images_multi_keywords(keywords)
                    all_found_images.extend(results)

                if asst_name.lower() == "scala":
                    sorted_images = self.utils.multi_group_sort(all_found_images, "scala_custom")
                elif asst_name.lower() == "kamiq":
                    sorted_images = self.utils.multi_group_sort(all_found_images, "kamiq_custom")
                else:
                    sorted_images = self.utils.multi_group_sort(all_found_images, None)

                if not sorted_images:
                    yield "Bu renklerle ilgili görsel bulunamadı.\n".encode("utf-8")
                    return

                yield "<b>İşte seçtiğiniz renk görselleri:</b><br>".encode("utf-8")
                for img_file in sorted_images:
                    img_url = f"/static/images/{img_file}"
                    base_name, _ = os.path.splitext(img_file)
                    pretty_name = base_name.replace("_", " ")
                    yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                    yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

                self.user_states[user_id]["pending_color_images"] = []
                return

        # Özel kontrol: fabia + premium + monte carlo + görsel
        if ("fabia" in lower_msg
            and "premium" in lower_msg
            and "monte carlo" in lower_msg
            and self.utils.is_image_request(user_message)):

            fabia_pairs = [
                ("Fabia_Premium_Ay_Beyazı.png", "Fabia_Monte_Carlo_Ay_Beyazı.png"),
                ("Fabia_Premium_Gümüş.png", "Fabia_Monte_Carlo_Gümüş.png"),
                ("Fabia_Premium_Graphite_Gri.png", "Fabia_Monte_Carlo_Graphite_Gri.png"),
                ("Fabia_Premium_Büyülü_Siyah.png", "Fabia_Monte_Carlo_Büyülü_Siyah.png"),
                ("Fabia_Premium_Phoenix_Turuncu.png", "Fabia_Monte_Carlo_Phoenix_Turuncu.png"),
                ("Fabia_Premium_Yarış_Mavisi.png", "Fabia_Monte_Carlo_Yarış_Mavisi.png"),
                ("Fabia_Premium_Kadife_Kırmızısı.png", "Fabia_Monte_Carlo_Kadife_Kırmızı.png"),
                ("Fabia_Premium_Gösterge_Paneli.png", "Fabia_Monte_Carlo_Gösterge_Paneli.png"),
                ("Fabia_Premium_Direksiyon_Simidi.png", "Fabia_Monte_Carlo_Direksiyon_Simidi.png"),
                ("Fabia_Premium_Suite_Kumaş_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Döşeme.png"),
                ("Fabia_Premium_Suite_Kumaş_Koltuk_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Koltuk_Döşeme.png"),
                ("Fabia_Premium_Suite_Kumaş_Ön_Dekor.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Ön_Dekor.png"),
                ("Fabia_Premium_Lodge_Kumaş_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Döşeme.png"),
                ("Fabia_Premium_Lodge_Kumaş_Koltuk_Döşemesi.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Koltuk_Döşeme.png"),
                ("Fabia_Premium_Lodge_Kumaş_Ön_Dekor.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Ön_Dekor.png"),
                ("Fabia_Premium_Dynamic_Suedia_Kumaş_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Döşeme.png"),
                ("Fabia_Premium_Dynamic_Suedia_Kumaş_Koltuk_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Koltuk_Döşeme.png"),
                ("Fabia_Premium_Dynamic_Suedia_Kumaş_Ön_Dekor.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Ön_Dekor.png"),
                ("Fabia_Premium_Standart_PJ4_Proxima_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
                ("Fabia_Premium_Opsiyonel_PJ9_Procyon_Aero_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
                ("Fabia_Premium_Opsiyonel_PX0_Urus_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
                ("Fabia_Premium_ve_Monte_Carlo_Opsiyonel_PJF_Libra_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
            ]
            yield "<div style='display: flex; flex-direction: column; gap: 15px;'>".encode("utf-8")
            for left_img, right_img in fabia_pairs:
                left_url = f"/static/images/{left_img}"
                right_url = f"/static/images/{right_img}"
                left_title = left_img.replace("_", " ").replace(".png", "")
                right_title = right_img.replace("_", " ").replace(".png", "")

                html_pair = f"""
                <div style="display: flex; flex-direction: row; align-items: center; gap: 20px;">
                  <img src="{left_url}" alt="{left_title}" style="max-width: 300px;" />
                  <img src="{right_url}" alt="{right_title}" style="max-width: 300px;" />
                </div>
                """
                yield html_pair.encode("utf-8")
            yield "</div>".encode("utf-8")
            return

        # 2) Görsel isteği mi?
        if self.utils.is_image_request(user_message):
            if not assistant_id:
                yield "Henüz bir asistan seçilmediği için görsel gösteremiyorum.\n".encode("utf-8")
                return

            assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
            if not assistant_name:
                yield "Asistan adını bulamadım.\n".encode("utf-8")
                return

            keyword = self.utils.extract_image_keyword(user_message, assistant_name)
            if keyword:
                full_filter = f"{assistant_name} {keyword}"
            else:
                full_filter = assistant_name

            found_images = self.image_manager.filter_images_multi_keywords(full_filter)
            if not found_images:
                yield f"'{full_filter}' için uygun bir görsel bulamadım.\n".encode("utf-8")
                return

            if "scala görsel" in lower_msg:
                desired_group = "scala_custom"
            elif "kamiq görsel" in lower_msg:
                desired_group = "kamiq_custom"
            elif "monte carlo" in lower_msg:
                desired_group = "monte_carlo"
            elif ("premium" in lower_msg) or ("elite" in lower_msg):
                desired_group = "premium_elite"
            elif "fabia" in lower_msg:
                desired_group = "fabia_12"
            elif "scala" in lower_msg:
                desired_group = "scala_12"
            elif "kamiq" in lower_msg:
                desired_group = "kamiq_12"
            else:
                desired_group = None

            sorted_images = self.utils.multi_group_sort(found_images, desired_group)

            for img_file in sorted_images:
                img_url = f"/static/images/{img_file}"
                base_name, _ = os.path.splitext(img_file)
                pretty_name = base_name.replace("_", " ")
                yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

            return

        # 3) Normal chat akışı (OpenAI)
        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        try:
            # Demo
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )

            start_time = time.time()
            timeout = 30
            assistant_response = ""

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)
                            content_md = self.markdown_processor.transform_text_to_markdown(content)
                            assistant_response = content
                            yield content_md.encode("utf-8")
                    break
                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            if not assistant_response:
                yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")
                return

            # Cevapta renk geçiyorsa ve "görsel olarak görmek ister misiniz?" geçiyorsa:
            if "görsel olarak görmek ister misiniz?" in assistant_response.lower():
                detected_colors = self.utils.parse_color_names(assistant_response)
                if detected_colors:
                    self.user_states[user_id]["pending_color_images"] = detected_colors

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    def run(self, debug=True):
        self.app.run(debug=debug)
