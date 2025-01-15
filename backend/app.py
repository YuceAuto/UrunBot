import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from rapidfuzz import fuzz
from image_paths import ImagePaths  # Preloaded image paths

load_dotenv()


class ChatbotAPI:
    def __init__(self, openai_key=None):
        """
        ChatbotAPI class manages OpenAI's API,
        handles user requests via Flask,
        includes logic for assistant selection,
        and loads images if needed.
        """
        self.user_states = {}

        # Load the OpenAI API key
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.openai_key:
            raise ValueError("No OpenAI API key provided. Please set OPENAI_API_KEY as an environment variable.")

        # Initialize the OpenAI client
        self.client = OpenAI(api_key=self.openai_key)

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Create the Flask application
        self.app = Flask(__name__)
        CORS(self.app)  # Restrict in production: CORS(self.app, resources={r"/ask": {"origins": "your-frontend.com"}})

        # Use the pre-populated ImagePaths instance
        self.image_storage = ImagePaths()
        self.logger.info("Loading images...")
        for image_name in self.image_storage.list_images():
            self.logger.info(f"Loaded image: {image_name}")

        # Assistant configuration
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],  # Skoda Kamiq Bot
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],  # Skoda Fabia Bot
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],  # Skoda Scala Bot
        }
        self.RELEVANT_KEYWORDS = ["Kamiq", "Fabia", "Scala"]
        self.IMAGE_KEYWORDS = ["görsel", "görselleri", "resim", "resimler", "fotoğraf", "fotoğraflar"]

        # Track the active assistant
        self.active_assistant_id = None

        # Cache for storing last answers
        self.last_answers = {}

        # Define routes
        self._define_routes()

    def _define_routes(self):
        @self.app.route("/", methods=["GET"])
        def home():
            return "Chatbot API is running. Please POST your questions to the /ask endpoint."

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._handle_ask_route()

        @self.app.route("/static/<path:path>", methods=["GET"])
        def serve_static_file(path):
            return send_from_directory('static', path)

    def _handle_ask_route(self):
        data = request.json or {}
        user_message = data.get("question", "").strip()
        user_id = data.get("user_id", "default_user")

        if not user_message:
            return jsonify({"response": "Lütfen bir soru yazın."})

        self.logger.info(f"User ({user_id}) input: {user_message}")

        # Check if the message is about images
        if any(keyword in user_message.lower() for keyword in self.IMAGE_KEYWORDS):
            matching_images = self._find_best_image_match(user_message)
            if matching_images:
                return jsonify({
                    "response": "Eşleşen resimler bulundu.",
                    "images": matching_images
                })
            return jsonify({"response": "Eşleşen görseller bulunamadı."})

        # Handle assistant responses
        response = self._get_assistant_response(user_message, user_id)
        return jsonify(response)

    def _find_best_image_match(self, user_message):
        """
        Find all images with a similarity score above a threshold.
        """
        threshold = 85
        matching_images = []

        try:
            for image_name, image_path in self.image_storage.list_images().items():
                similarity = fuzz.token_sort_ratio(user_message.lower(), image_name.lower())
                if similarity >= threshold:
                    matching_images.append({
                        "name": str(image_name),
                        "path": str(image_path)
                    })
        except Exception as e:
            self.logger.error(f"Error during image matching: {str(e)}")

        return matching_images

    def _get_assistant_response(self, user_message, user_id):
        """
        Fetch a response from the appropriate assistant based on user input.
        """
        for assistant_id, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                self.user_states[user_id] = assistant_id
                try:
                    thread = self.client.beta.threads.create(
                        messages=[{"role": "user", "content": user_message}]
                    )
                    run = self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
                    response = self._process_streamed_response(thread.id, run.id)
                    if response:
                        return {"response": response}
                except Exception as e:
                    self.logger.error(f"Error in assistant response: {e}")
                    return {"response": "Bir hata oluştu, lütfen tekrar deneyin."}

        return {"response": "Hiçbir asistan uygun bir yanıt veremedi."}

    def _process_streamed_response(self, thread_id, run_id, timeout=30):
        """
        Retrieve streamed responses from OpenAI API with a timeout mechanism.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=thread_id).data
                for msg in messages:
                    if msg.role == "assistant":
                        return msg.content
            elif run.status == "failed":
                self.logger.error("Response failed.")
                return None
            time.sleep(0.1)
        self.logger.error("Response timed out.")
        return None

    def run(self, debug=True):
        """
        Run the Flask application.
        """
        self.app.run(debug=debug)

if __name__ == "__main__":
    chatbot_api = ChatbotAPI()
    chatbot_api.run(debug=True)