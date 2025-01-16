import os
import re
import time
import json
import openai
import logging

from rapidfuzz import fuzz
from flask_cors import CORS
from dotenv import load_dotenv
from modules.image_paths import ImagePaths
from flask import Flask, request, jsonify, render_template

load_dotenv()

class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        self.app = Flask(
            __name__,
            static_folder=static_folder,
            template_folder=template_folder
        )
        CORS(self.app)
        self.logger = self._setup_logger()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }
        self.user_states = {}
        self.image_paths = ImagePaths()
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
            return self._home()

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._ask()

    def _home(self):
        return render_template("index.html")

    def _ask(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON format."}), 400

            user_message = data.get("question", "")
            user_id = data.get("user_id", "default_user")

            if not user_message:
                return jsonify({"response": "Please provide a question."})

            self.logger.info(f"User ({user_id}) message: {user_message}")

            response_generator = self._generate_response(user_message, user_id)
            return self.app.response_class(response_generator, mimetype="application/json")

        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return jsonify({"error": "An error occurred."}), 500

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
            response = {"response": "No suitable assistant found.", "images": []}
            self.logger.info(f"Yanıt JSON formatı: {json.dumps(response)}")  # Console log
            return jsonify(response)

        try:
            # Resim eşleşmelerini bul
            similar_images = self.image_paths.find_similar_images(user_message)
            image_urls = [
                {
                    "name": img["name"],
                    "url": f"/static/images/{os.path.basename(img['path'])}"
                }
                for img in similar_images
            ]

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
            initial_response = {"response": "Preparing response...", "images": image_urls}
            self.logger.info(f"Başlangıç JSON formatı: {json.dumps(initial_response)}")  # Console log
            yield json.dumps(initial_response).encode("utf-8")

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
                            response = {
                                "response": content,
                                "images": image_urls
                            }
                            self.logger.info(f"Tamamlanan yanıt JSON formatı: {json.dumps(response)}")  # Console log
                            yield json.dumps(response).encode("utf-8")
                    return

                elif run.status == "failed":
                    failed_response = {"response": "Response generation failed."}
                    self.logger.info(f"Hata JSON formatı: {json.dumps(failed_response)}")  # Console log
                    yield json.dumps(failed_response).encode("utf-8")
                    return

                time.sleep(0.5)

            timeout_response = {"response": "Response timed out."}
            self.logger.info(f"Zaman aşımı JSON formatı: {json.dumps(timeout_response)}")  # Console log
            yield json.dumps(timeout_response).encode("utf-8")

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            error_response = {"response": f"An error occurred: {str(e)}", "images": []}
            self.logger.info(f"Exception JSON formatı: {json.dumps(error_response)}")  # Console log
            yield json.dumps(error_response).encode("utf-8")


    def run(self, debug=True):
        self.app.run(debug=debug)


if __name__ == "__main__":
    chatbot = ChatbotAPI()
    chatbot.run(debug=True)
