import os
import re
import time
import openai
import logging
import asyncio
import threading

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from difflib import SequenceMatcher

from modules.image_manager import ImageManager
from modules.markdown_utils import MarkdownProcessor
from modules.tts import ElevenLabsTTS

load_dotenv()

ASSETS_DIR = os.path.join(os.getcwd(), "assets")

class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        self.app = Flask(__name__,
                         static_folder=os.path.join(os.getcwd(), static_folder),
                         template_folder=os.path.join(os.getcwd(), template_folder))
        
        CORS(self.app)

        self.logger = self._setup_logger()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai
        self.speech = ""
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
        self.timeout = 45
        # Initialize TTS
        self.tts = ElevenLabsTTS()

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
        self.logger.info(f"Processing message from User ({user_id}): '{user_message}'")
        time.sleep(1.0)
        predefined_wait_response = ("answers\\cevabınız_hazırlanıyor.txt", "sounds\\cevabınız_hazırlanıyor.mp3")
        yield from self._auto_response(*predefined_wait_response)
        yield "\n\n"
        time.sleep(2.0)

        if self._is_image_request(user_message):
            yield from self._handle_image_request(user_message, user_id)
            return

        assistant_id = self.user_states.get(user_id) or self._select_assistant(user_message)
        if not assistant_id:
            yield "No suitable assistant found.\n".encode("utf-8")
            return

        self.user_states[user_id] = assistant_id


        # 3) Handle predefined responses
        predefined_responses = {
            "kamiq özellikleri": ("answers\\kamiq_özellikleri.txt", "sounds\\kamiq_özellikleri.mp3"),
            "scala özellikleri": ("answers\\scala_özellikleri.txt", "sounds\\scala_özellikleri.mp3"),
            "fabia özellikleri": ("answers\\fabia_özellikleri.txt", "sounds\\fabia_özellikleri.mp3"),
            "yüce auto genel": ("answers\\yüceauto_genel.txt", "sounds\\yüceauto_genel.mp3"),
            "kamiq genel": ("answers\\kamiq_genel.txt", "sounds\\kamiq_genel.mp3"),
            "scala genel": ("answers\\scala_genel.txt", "sounds\\scala_genel.mp3"),
            "fabia genel": ("answers\\fabia_genel.txt", "sounds\\fabia_genel.mp3"),
            "ortak avantajlar": ("answers\\ortak_avantajlar.txt", "sounds\\ortak_avantajlar.mp3"),
            "merhaba": ("answers\\greeting.txt", "sounds\\greeting.mp3"),
        }

        # Find the best match based on similarity
        best_match = None
        highest_similarity = 0.0
        for key in predefined_responses.keys():
            similarity = SequenceMatcher(None, user_message, key).ratio()
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = key
        print(best_match, highest_similarity)
        # If similarity is above 80%, select the best match
        if best_match and highest_similarity >= 0.55:
            path1, path2 = predefined_responses[best_match]
            print(path1, path2, "-------------------------------")
            yield from self._auto_response(path1, path2)
            return

        # 4) ChatGPT (OpenAI) response streaming
        try:
            thread = self.client.beta.threads.create(messages=[{"role": "user", "content": user_message}])
            run = self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
            start_time = time.time()

            while time.time() - start_time < self.timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)
                            content = self.markdown_processor.transform_text_to_markdown(content)

                            # Optional table extraction
                            tables = self.markdown_processor.extract_markdown_tables_from_text(content)
                            if tables:
                                self.logger.info(f"Found tables: {tables}")
                                for i, tbl in enumerate(tables, 1):
                                    html_table = self.markdown_processor.markdown_table_to_html(tbl)
                                    yield f"\n--- Table {i} (HTML) ---\n".encode("utf-8")
                                    yield html_table.encode("utf-8")
                                    yield b"\n"
                            yield content.encode("utf-8")
                    return

                elif run.status == "failed":
                    yield "Failed to generate a response.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            yield "Response timeout exceeded.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            yield f"An error occurred: {str(e)}\n".encode("utf-8")

    def _is_image_request(self, message: str):
        """
        Kullanıcının mesajında 'resim', 'fotoğraf' veya 'görsel' kelimesi geçiyor mu?
        """
        lower_msg = message.lower()
        if "resim" in lower_msg or "fotoğraf" in lower_msg or "görsel" in lower_msg:
            return True
        return False

    def _handle_image_request(self, message, user_id):
        assistant_id = self.user_states.get(user_id)
        if not assistant_id:
            yield "No assistant selected to display images.\n".encode("utf-8")
            return

        assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
        keyword = self._extract_image_keyword(message, assistant_name)
        filter_key = f"{assistant_name} {keyword}" if keyword else assistant_name

        found_images = self.image_manager.filter_images_multi_keywords(filter_key)
        if not found_images:
            yield f"No images found for '{filter_key}'.\n".encode("utf-8")
        else:
            yield f"Images for {assistant_name} (filter: '{keyword if keyword else 'None'}'):\n".encode("utf-8")
            for img in found_images:
                yield f'<img src="/static/images/{img}" alt="{img}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

    def _select_assistant(self, message):
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in message.lower() for keyword in keywords):
                return aid
        return None

    def _auto_response(self, path1, path2):
        text_file_path = os.path.join(ASSETS_DIR, path1)
        tts_file_path = os.path.join(ASSETS_DIR, path2)

        # 1. Yazılı cevabı döndür
        with open(text_file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # 2. Sesli cevabı oynat
        if not self.tts:
            yield content.encode("utf-8")  # Yazılı cevabı hemen döndür
            self.logger.error("TTS instance is not initialized.")
            yield "TTS system is unavailable at the moment.\n".encode("utf-8")
            return

        try:
            # Ses oynatma için async işlev
            async def play_audio():
                await self.tts.play(tts_file_path)
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)  # Yeni thread'e bir loop ata
            yield content.encode("utf-8")  # Yazılı cevabı hemen döndür
            new_loop.run_until_complete(play_audio())
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
            yield f"Audio playback failed: {e}\n".encode("utf-8")
        finally:
            new_loop.close()  # İşlem bitince loop'u güvenli bir şekilde kapat
            return


    def run(self, debug=True):
        self.app.run(debug=debug)
