import os
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

class ChatbotConfig:
    def __init__(self, static_folder='static', template_folder='templates'):
        """
        Initializes the ChatbotConfig class, setting up Flask, logging, OpenAI client,
        and assistant configurations.
        """
        # Initialize Flask app
        self.app = Flask(
            __name__,
            static_folder=static_folder,
            template_folder=template_folder
        )
        CORS(self.app)

        # Initialize logging
        self.logger = self._setup_logger()

        # OpenAI client setup
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        # Assistant ID and keywords configuration
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }
        self.user_states = {}

        # Initialize image paths from the external module
        self.image_paths = ImagePaths()

        # Define routes
        self._define_routes()

    def _setup_logger(self):
        """
        Sets up a logger for the chatbot application.
        """
        logger = logging.getLogger("ChatbotAPI")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _define_routes(self):
        """
        Define Flask routes.
        """
        @self.app.route("/", methods=["GET"])
        def home():
            return self._render_home()

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._handle_ask_route()

        @self.app.route("/feedback", methods=["POST"])
        def feedback():
            return self._handle_feedback_route()

    def _render_home(self):
        """
        Render the home page template.
        """
        return render_template("index.html")

    def _handle_ask_route(self):
        """
        Handle user questions via POST requests.
        """
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
        Generate a response for the user.
        """
        assistant_id = self.user_states.get(user_id)

        # Match user message with assistant keywords
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        if not assistant_id:
            yield json.dumps({"response": "No suitable assistant found."}).encode("utf-8")
            return

        try:
            # Find similar images
            similar_images = self.image_paths.find_similar_images(user_message)

            # Simulate response generation
            response = {
                "response": f"Generated response for {assistant_id}.",
                "images": similar_images
            }
            yield json.dumps(response).encode("utf-8")

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            error_response = {"response": f"An error occurred: {str(e)}"}
            yield json.dumps(error_response).encode("utf-8")

    def _handle_feedback_route(self):
        """
        Handle user questions via POST requests.
        """
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

    def run(self, debug=True):
        """
        Run the Flask application.
        """
        self.app.run(debug=debug)

if __name__ == "__main__":
    config = ChatbotConfig()
    config.run(debug=True)
