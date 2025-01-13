import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from fuzzywuzzy import fuzz, process  # If you need fuzzy matching
from openai import OpenAI

# Import the ImagePaths class (not as an instance).
from image_paths import ImagePaths

load_dotenv()


class ChatbotAPI:
    def __init__(self, openai_key=None):
        """
        ChatbotAPI class manages the interaction with OpenAI's API,
        handles user requests via the Flask application,
        and includes logic for assistant selection and image storage.
        """

        # 1. Load the OpenAI API key from environment (or a passed-in parameter).
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.openai_key:
            raise ValueError("No OpenAI API key provided. Please set OPENAI_API_KEY as an environment variable.")

        self.client = OpenAI(api_key=self.openai_key)

        # 2. Create a logger for debugging/info purposes.
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # 3. Create an instance of the Flask application and enable CORS.
        self.app = Flask(__name__)
        CORS(self.app)

        # 4. Create an instance of ImagePaths (optional usage).
        #    You can add or remove images as needed.
        self.image_storage = ImagePaths()
        # Example: self.image_storage.add_image("Kamiq Image", "assets/images/kamiq/kamiq_example.png")

        # Store all images if you want a quick reference (optional).
        self.IMAGE_DICT = self.image_storage.list_images()

        # 5. Assistant configuration and relevant keywords
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],  # Skoda Kamiq Bot
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],  # Skoda Fabia Bot
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],  # Skoda Scala Bot
        }
        self.RELEVANT_KEYWORDS = ["Kamiq", "Fabia", "Scala"]

        # 6. Track the active assistant across requests
        self.active_assistant_id = None

        # 7. Define Flask routes
        self._define_routes()

    def _define_routes(self):
        """
        Define all Flask routes within this method.
        """

        @self.app.route("/", methods=["GET"])
        def home():
            """
            GET '/' endpoint
            """
            return "Chatbot API is running. Please POST your questions to the /ask endpoint."

        @self.app.route("/ask", methods=["POST"])
        def ask():
            """
            POST '/ask' endpoint: The main logic for routing user questions
            to the correct assistant and tracking the active assistant.
            """
            return self._handle_ask_route()

    def _handle_ask_route(self):
        """
        Internal method for the '/ask' route to keep the code organized.
        """
        data = request.json
        user_message = data.get("question", "")

        if not user_message:
            return jsonify({"response": "Lütfen bir soru girin."})

        self.logger.info(f"Kullanıcı mesajı: {user_message}")

        # Check for relevant keywords in user's message (simple approach).
        relevant_keywords = ["kamiq", "scala", "fabia"]
        if not any(keyword.lower() in user_message.lower() for keyword in relevant_keywords):
            # If no keyword is found and there's no active assistant yet,
            # ask for more detail.
            if not self.active_assistant_id:
                self.logger.info("Anahtar kelime bulunamadı. Daha fazla detay istendi.")
                return jsonify({"response": "Talebinizi daha detaylı girerseniz size yardımcı olabilirim."})

            # If there's an active assistant, use it.
            self.logger.info(f"Aktif asistan: {self.active_assistant_id}. Aynı asistandan yanıt alınıyor.")
            _, response = self.process_assistant(self.active_assistant_id, user_message)
            return jsonify({"response": response})

        # If message contains a relevant keyword, see if we match a known assistant
        for assistant_id, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                self.active_assistant_id = assistant_id
                self.logger.info(f"Direkt olarak {assistant_id} asistanına yönlendiriliyor.")
                _, response = self.process_assistant(assistant_id, user_message)
                return jsonify({"response": response})

        # No direct assistant matched; fallback to the previously active one if any
        if self.active_assistant_id:
            self.logger.info(f"Aktif asistan: {self.active_assistant_id}. Aynı asistandan yanıt alınıyor.")
            _, response = self.process_assistant(self.active_assistant_id, user_message)
            return jsonify({"response": response})

        # Parallel fallback if no assistant is active
        with ThreadPoolExecutor(max_workers=len(self.ASSISTANT_CONFIG)) as executor:
            results = list(executor.map(
                lambda aid: self.process_assistant(aid, user_message),
                self.ASSISTANT_CONFIG.keys()
            ))

        # Find a relevant answer
        for assistant_id, content in results:
            if content:  # if we got a response
                self.active_assistant_id = assistant_id
                self.logger.info(f"Asistan {assistant_id} için anahtar kelimeler: {self.ASSISTANT_CONFIG.get(assistant_id, [])}")
                return jsonify({"response": content})

        self.logger.warning("Hiçbir asistan uygun bir yanıt veremedi.")
        return jsonify({"response": "Hiçbir asistan uygun bir yanıt veremedi."})

    def process_assistant(self, assistant_id, user_message):
        """
        Query the specified assistant with user_message and 
        return (assistant_id, response) if relevant, else (assistant_id, None).
        """
        try:
            # Create a thread for conversation
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            self.logger.info(f"👉 Thread Created (Assistant: {assistant_id}): {thread.id}")

            # Start the run
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            self.logger.info(f"👉 Run Started (Assistant: {assistant_id}): {run.id}")

            # Wait until completion or timeout
            start_time = time.time()
            run_status = "queued"
            while run_status != "completed":
                if time.time() - start_time > 10:  # 10-second timeout
                    raise TimeoutError(f"Timeout for assistant {assistant_id}.")
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                run_status = run.status
                time.sleep(0.2)

            # Retrieve all messages from the thread
            msg_resp = self.client.beta.threads.messages.list(thread_id=thread.id)
            messages = msg_resp.data
            latest_msg = next((m for m in messages if m.role == "assistant"), None)

            if latest_msg and latest_msg.content:
                content = latest_msg.content
                content_text = " ".join(str(c) for c in content) if isinstance(content, list) else str(content)

                # Check relevance
                if any(keyword.lower() in content_text.lower() for keyword in self.RELEVANT_KEYWORDS):
                    return assistant_id, content_text

            return assistant_id, None

        except Exception as e:
            self.logger.error(f"❗ Error (Assistant: {assistant_id}): {str(e)}")
            return assistant_id, None

    def run(self, debug=True):
        """
        Run the Flask application.
        """
        self.app.run(debug=debug)


# If you want to run this module directly:
if __name__ == "__main__":
    chatbot_api = ChatbotAPI()
    chatbot_api.run(debug=True)
