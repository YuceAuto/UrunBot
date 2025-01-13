import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from openai import OpenAI

from image_paths import images  # Our pre-populated ImagePaths instance

load_dotenv()

class ChatbotAPI:
    def __init__(self, openai_key=None):
        """
        ChatbotAPI class manages OpenAI's API,
        handles user requests via Flask,
        includes logic for assistant selection,
        and loads images if needed.
        """
        # 1. Load the OpenAI API key
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.openai_key:
            raise ValueError("No OpenAI API key provided. Please set OPENAI_API_KEY as an environment variable.")

        # 2. Initialize the OpenAI client
        self.client = OpenAI(api_key=self.openai_key)

        # 3. Set up logging
        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger(__name__)

        # 4. Create the Flask application
        self.app = Flask(__name__)
        CORS(self.app)

        # 5. Use the pre-populated ImagePaths instance
        self.image_storage = images
        self.logger.warning("Loading images...")
        for image_name in self.image_storage.list_images():
            self.logger.warning(f"Loaded image: {image_name}")

        # 6. Assistant configuration
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],  # Skoda Kamiq Bot
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],  # Skoda Fabia Bot
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],  # Skoda Scala Bot
        }
        self.RELEVANT_KEYWORDS = ["Kamiq", "Fabia", "Scala"]

        # 7. Track the active assistant
        self.active_assistant_id = None

        # 8. Cache for storing last answers
        self.last_answers = {}  # Format: {assistant_id: "last response"}

        # 9. Define routes
        self._define_routes()

    def _define_routes(self):
        @self.app.route("/", methods=["GET"])
        def home():
            return "Chatbot API is running. Please POST your questions to the /ask endpoint."

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._handle_ask_route()

        @self.app.route("/last_answers", methods=["GET"])
        def get_last_answers():
            """
            Endpoint to retrieve the last answers from all assistants.
            """
            return jsonify(self.last_answers)

    def _handle_ask_route(self):
        """
        Main logic for /ask route (user question).
        """
        data = request.json or {}
        user_message = data.get("question", "")
        if not user_message:
            return jsonify({"response": "Lütfen bir soru girin."})

        self.logger.warning(f"Kullanıcı mesajı: {user_message}")
        relevant_keywords = ["kamiq", "scala", "fabia"]

        # Check for images with high similarity to the user message
        similar_images = []
        for image_name in self.image_storage.list_images():
            similarity = self._calculate_similarity(user_message, image_name)
            if similarity >= 90:  # Threshold for similarity
                similar_images.append({"name": image_name, "path": self.image_storage.get_image(image_name)})

        # If any similar images are found, include them in the response
        if similar_images:
            return jsonify({"response": "Eşleşen resimler bulundu.", "images": similar_images})

        # If no relevant keyword is found and no assistant is active
        if not any(k.lower() in user_message.lower() for k in relevant_keywords):
            if not self.active_assistant_id:
                self.logger.warning("Anahtar kelime bulunamadı. Daha fazla detay istendi.")
                return jsonify({"response": "Talebinizi daha detaylı girerseniz size yardımcı olabilirim."})
            # If an assistant is already active
            self.logger.warning(f"Aktif asistan: {self.active_assistant_id}. Aynı asistandan yanıt alınıyor.")
            _, response = self.process_assistant(self.active_assistant_id, user_message)
            return jsonify({"response": response})

        # If user_message contains a relevant keyword, see if we match a known assistant
        for assistant_id, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in user_message.lower() for k in keywords):
                self.active_assistant_id = assistant_id
                self.logger.warning(f"Direkt olarak {assistant_id} asistanına yönlendiriliyor.")
                _, response = self.process_assistant(assistant_id, user_message)
                return jsonify({"response": response})

        # If no direct assistant matched; fallback to previously active
        if self.active_assistant_id:
            self.logger.warning(f"Aktif asistan: {self.active_assistant_id}. Aynı asistandan yanıt alınıyor.")
            _, response = self.process_assistant(self.active_assistant_id, user_message)
            return jsonify({"response": response})

        # Parallel fallback if no assistant is active
        with ThreadPoolExecutor(max_workers=len(self.ASSISTANT_CONFIG)) as executor:
            results = list(
                executor.map(lambda aid: self.process_assistant(aid, user_message),
                             self.ASSISTANT_CONFIG.keys())
            )

        # Find a relevant answer
        for assistant_id, content in results:
            if content:
                self.active_assistant_id = assistant_id
                self.logger.warning(
                    f"Asistan {assistant_id} için anahtar kelimeler: "
                    f"{self.ASSISTANT_CONFIG.get(assistant_id, [])}"
                )
                return jsonify({"response": content})

        self.logger.warning("Hiçbir asistan uygun bir yanıt veremedi.")
        return jsonify({"response": "Hiçbir asistan uygun bir yanıt veremedi."})

    def process_assistant(self, assistant_id, user_message):
        """
        Query the specified assistant with user_message
        and return (assistant_id, response) if relevant, else (assistant_id, None).
        """
        try:
            self.logger.warning("cevap yanıtlanıyor...")

            # Create a thread for conversation
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            self.logger.warning(f"👉 Thread Created (Assistant: {assistant_id}): {thread.id}")

            # Start the run
            run = self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
            self.logger.warning(f"👉 Run Started (Assistant: {assistant_id}): {run.id}")

            # Wait until completion or timeout
            start_time = time.time()
            run_status = "queued"
            while run_status != "completed":
                if time.time() - start_time > 30:  # 10-second timeout
                    raise TimeoutError(f"Timeout for assistant {assistant_id}.")
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                run_status = run.status
                time.sleep(0.1)

            # Retrieve all messages from the thread
            msg_resp = self.client.beta.threads.messages.list(thread_id=thread.id)
            messages = msg_resp.data
            latest_msg = next((m for m in messages if m.role == "assistant"), None)

            if latest_msg and latest_msg.content:
                content = latest_msg.content
                # If content is a list (rare in some responses), join it
                if isinstance(content, list):
                    content_text = " ".join(str(c) for c in content)
                else:
                    content_text = str(content)

                # Save to last_answers cache
                self.last_answers[assistant_id] = content_text

                return assistant_id, content_text

            return assistant_id, None

        except Exception as e:
            self.logger.error(f"❗ Error (Assistant: {assistant_id}): {str(e)}")
            return assistant_id, None

    def _calculate_similarity(self, input_text, image_name):
        """
        Calculate the similarity between the user input and an image name.
        Uses a simple character overlap method; replace with a more robust algorithm if needed.
        """
        input_set = set(input_text.lower())
        name_set = set(image_name.lower())
        intersection = input_set.intersection(name_set)
        return len(intersection) / max(len(input_set), len(name_set)) * 100

    def run(self, debug=True):
        """
        Run the Flask application.
        """
        self.app.run(debug=debug)


if __name__ == "__main__":
    chatbot_api = ChatbotAPI()
    chatbot_api.run(debug=True)
