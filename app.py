import os
import time
import json
import openai
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from modules.image_paths import ImagePaths
from modules.parse_attributes import AttributeParser

load_dotenv()

class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        # Initialize Flask app
        self.app = Flask(
            __name__,
            static_folder=static_folder,
            template_folder=template_folder
        )
        CORS(self.app)

        # Set up logging
        self.logger = self._setup_logger()

        # OpenAI API setup
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        # Load configurations
        self.ASSISTANT_CONFIG = self._load_assistant_config()
        self.user_states = {}

        # Load ImagePaths and AttributeParser
        self.image_paths = ImagePaths()
        self.attribute_parser = AttributeParser(self.image_paths)

        # Define routes
        self._define_routes()

    def _setup_logger(self):
        """Set up a logger for the application."""
        logger = logging.getLogger("ChatbotAPI")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _load_assistant_config(self):
        """Load assistant configuration."""
        return {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }

    def _define_routes(self):
        """Define Flask routes."""
        @self.app.route("/", methods=["GET"])
        def home():
            return self._home()

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._ask()

    def _home(self):
        """Home page rendering."""
        return render_template("index.html")

    def _ask(self):
        """Handle user queries."""
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
            self.logger.error(f"Error in /ask endpoint: {str(e)}")
            return jsonify({"error": "An error occurred."}), 500

    def _generate_response(self, user_message, user_id):
        """
        Generates a response by selecting an assistant ID and parsing OpenAI's response.
        """
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")
        assistant_id = self._select_assistant(user_message, user_id)

        if not assistant_id:
            yield json.dumps({"response": "No suitable assistant found."})
            return

        try:
            # Initial "Preparing response..." message
            yield json.dumps({"response": "Preparing response..."})

            # Create ChatGPT thread
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=assistant_id
            )

            start_time = time.time()
            timeout = 60

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )
                if run.status == "completed":
                    # Retrieve and parse OpenAI's response
                    message_response = self.client.beta.threads.messages.list(
                        thread_id=thread.id
                    )
                    content_value = self._parse_openai_response(message_response)
                    content_value = self.attribute_parser.parse_dat
                    # Send the formatted response back to the frontend
                    yield json.dumps({"response": content_value})
                    return

                elif run.status == "failed":
                    yield json.dumps({"response": "Response generation failed."})
                    return

                time.sleep(0.5)

            yield json.dumps({"response": "Response timed out."})

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            yield json.dumps({"response": f"An error occurred: {str(e)}"})


    def _select_assistant(self, user_message, user_id):
        """Select the appropriate assistant based on user message."""
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break
        return assistant_id

    def _interact_with_openai(self, user_message, assistant_id):
        """Interact with OpenAI API and retrieve the response."""
        try:
            thread = self.client.beta.threads.create(messages=[{"role": "user", "content": user_message}])
            run = self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
            
            start_time = time.time()
            timeout = 60

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                    return self._parse_openai_response(messages)

                elif run.status == "failed":
                    return "Response generation failed."

                time.sleep(0.5)

            return "Response timed out."

        except Exception as e:
            self.logger.error(f"Error interacting with OpenAI: {str(e)}")
            return None

    def _parse_openai_response(self, message_response):
        """Extract and format the response from OpenAI."""
        extracted_values = [
            block.text.value for msg in message_response.data if msg.role == "assistant"
            for block in msg.content if block.type == "text" and hasattr(block.text, "value")
        ]
        return "\n".join(extracted_values) if extracted_values else "No valid content found."

    def run(self, debug=True):
        """Run the Flask app."""
        self.app.run(debug=debug)

if __name__ == "__main__":
    chatbot = ChatbotAPI()
    chatbot.run(debug=True)
