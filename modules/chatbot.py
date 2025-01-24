import os
import re
import time
import openai

from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

from modules.image_manager import ImageManager
from modules.markdown_utils import MarkdownProcessor
from modules.config import Config
from modules.utils import Utils
# from modules.routes import Routes

load_dotenv()

class ChatbotAPI:
    def __init__(self):
        self.app = Flask(
            __name__,
            static_folder=os.path.join(os.getcwd(), "static"),
            template_folder=os.path.join(os.getcwd(), "templates")
        )
        CORS(self.app)
        
        self.config = Config()
        self.utils = Utils()
        self.image_manager = ImageManager()
        self.markdown_processor = MarkdownProcessor()

        self.logger = self.utils.setup_logger()


        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        # Asistan konfigürasyonu (model isimleri)
        self.ASSISTANT_CONFIG = self.config.ASSISTANT_CONFIG
        self.ASSISTANT_NAME_MAP = self.config.ASSISTANT_NAME_MAP

        self.user_states = {}

        self.images_path = self.config.image_paths
        self.image_manager.load_images()


        self._define_routes()

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

        # 1) Asistan seçimi (Kamiq / Fabia / Scala)
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in user_message.lower() for k in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        # 2) Görsel isteği mi?
        if self.utils._is_image_request(user_message):
            if not assistant_id:
                yield "Henüz bir asistan seçilmediği için görsel gösteremiyorum.\n".encode("utf-8")
                return

            assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
            if not assistant_name:
                yield "Asistan adını bulamadım.\n".encode("utf-8")
                return

            # Filtre
            keyword = self.utils._extract_image_keyword(user_message, assistant_name)
            if keyword:
                full_filter = f"{assistant_name} {keyword}"
            else:
                full_filter = assistant_name

            found_images = self.image_manager.filter_images_multi_keywords(full_filter)
            if not found_images:
                yield f"'{full_filter}' için uygun bir görsel bulamadım.\n".encode("utf-8")
                return

            # Kullanıcı mesajı
            lower_msg = user_message.lower()

            # 3) Hangi özel sıralama?
            if "scala görsel" in lower_msg:
                desired_group = "scala_custom"
            elif "kamiq görsel" in lower_msg:  # <-- YENİ EKLENDİ
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

            # 4) Sıralama ve yanıt üretimi
            sorted_images = self.utils._multi_group_sort(found_images, desired_group)

            for img_file in sorted_images:
                img_url = f"/static/images/{img_file}"
                base_name, _ = os.path.splitext(img_file)
                pretty_name = base_name.replace("_", " ")
                yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

            return

        # 5) Görsel isteği yoksa => normal chat
        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        # 6) (Örnek) OpenAI Chat'te işlem
        try:
            # Bu kısım tamamen demo/dummy
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )

            start_time = time.time()
            timeout = 30

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)
                            content = self.markdown_processor.transform_text_to_markdown(content)
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


    def run(self, debug=True):
        self.app.run(debug=debug)