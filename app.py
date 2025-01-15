import os
import time
import logging
import openai

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from backend.image_paths import ImagePaths

load_dotenv()

class ChatbotAPI:
    def __init__(self, api_key):
        """
        ChatbotAPI class manages OpenAI's API and serves Flask endpoints.
        """
        # Initialize OpenAI API key
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("No OpenAI API key provided. Please set it during initialization.")

        openai.api_key = self.api_key

        # Flask app setup
        self.app = Flask(
            __name__,
            static_folder='static',
            template_folder='templates'
        )
        CORS(self.app)

        # Logger setup
        self.logger = self._setup_logger()

        # Assistant configuration
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }
        self.user_states = {}

        # Image paths setup
        self.images = ImagePaths()
        self._load_images()

        # Define routes
        self._define_routes()

    def _setup_logger(self):
        """
        Setup logger for the application.
        """
        logger = logging.getLogger("ChatbotAPI")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _load_images(self):
        """
        Load predefined images into the ImagePaths instance.
        """
        ROOT_DIR = os.path.abspath(os.curdir)
        ASSET_DIR = os.path.join(ROOT_DIR, "assets", "images")

        image_definitions = {
            "Fabia Monte Carlo Ay Beyazı": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Ay Beyazı.png"),
            "Fabia Monte Carlo Büyülü Siyah": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Büyülü Siyah.png"),
            "Scala Premium Lodge Standart Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Premium Lodge Standart Döşeme.png"),
            "Kamiq Elite Gösterge Paneli": os.path.join(ASSET_DIR, "kamiq", "Kamiq Elite Gösterge Paneli.png"),
            # Add more images as needed
        }

        for name, path in image_definitions.items():
            try:
                self.images.add_image(name, path)
            except FileNotFoundError as e:
                self.logger.warning(f"Could not load image '{name}': {e}")

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
            return self.app.response_class(response_generator, mimetype="text/plain")

        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return jsonify({"error": "An error occurred."}), 500

    def _generate_response(self, user_message, user_id):
        """
        Generate a response for the user.
        """
        assistant_id = self.user_states.get(user_id)

        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        if not assistant_id:
            yield "No suitable assistant found.\n".encode("utf-8")
            return

        try:
            yield "Preparing a response...\n".encode("utf-8")

            # OpenAI Completion response generation
            response = openai.Completion.create(
                engine="gpt-4",
                prompt=f"You are {assistant_id}.\nUser: {user_message}\nAssistant:",
                max_tokens=150,
                temperature=0.7
            )

            if response and 'choices' in response:
                content = response['choices'][0]['text']
                for char in content:
                    yield char.encode("utf-8")
                    time.sleep(0.01)
            else:
                yield "Could not generate a response.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            yield f"An error occurred: {str(e)}\n".encode("utf-8")

    def _handle_feedback_route(self):
        """
        Handle user feedback via POST requests.
        """
        try:
            data = request.get_json()
            self.logger.info(f"Feedback received: {data}")
            return jsonify({"message": "Thank you for your feedback!"})
        except Exception as e:
            self.logger.error(f"Feedback error: {str(e)}")
            return jsonify({"error": "An error occurred."}), 500

    def run(self, debug=True):
        """
        Run the Flask application.
        """
        self.app.run(debug=debug)

class ImagePaths:
    """
    A simple class to maintain a dictionary of image names and their paths.
    """
    def __init__(self):
        # Initialize an empty dictionary or pre-populate if desired
        self._images = {}

    def add_image(self, name, path):
        """
        Add or update an image entry in the dictionary.

        :param name: Name or key for the image.
        :param path: The file path to the image.
        :raises FileNotFoundError: If the specified file does not exist.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"The file '{path}' does not exist.")
        self._images[name] = path

    def get_image(self, name):
        """
        Retrieve the file path of an image by exact name.

        :param name: Name or key for the image.
        :return: The file path if found, or None if not found.
        """
        return self._images.get(name)

    def list_images(self):
        """
        Retrieve a copy of the entire dictionary of images.

        :return: A dictionary of all image entries (name -> path).
        """
        return dict(self._images)

    def get_images_by_keyword(self, keyword):
        """
        Retrieve images whose names contain the given keyword (case-insensitive).

        :param keyword: The search keyword to look for in the image name.
        :return: A list of (name, path) tuples for matching images.
        """
        keyword_lower = keyword.lower()
        return [
            (name, path) for name, path in self._images.items()
            if keyword_lower in name.lower()
        ]

if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY", "")
    chatbot_api = ChatbotAPI(api_key)
    chatbot_api.run(debug=True)