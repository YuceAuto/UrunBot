import os
import time
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

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

        self.client = OpenAI(api_key=self.api_key)

        # Flask app setup
        self.app = Flask(__name__,
                         static_folder='static',
                         template_folder='templates')
        CORS(self.app)

        # Logger setup
        self.logger = logging.getLogger("ChatbotAPI")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Assistant configuration
        self.ASSISTANT_CONFIG = {
            "asst_1qGG7y8w6QcupPETaYQRdGsI": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }
        self.user_states = {}

        # Define routes
        self._define_routes()

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
                return jsonify({"error": "Geçersiz JSON formatı."}), 400

            user_message = data.get("question", "")
            user_id = data.get("user_id", "default_user")

            if not user_message:
                return jsonify({"response": "Lütfen bir soru girin."})

            self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")

            response_generator = self._generate_response(user_message, user_id)
            return self.app.response_class(response_generator, mimetype="text/plain")

        except Exception as e:
            self.logger.error(f"Hata: {str(e)}")
            return jsonify({"error": "Bir hata oluştu."}), 500

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
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        try:
            yield "Yanıt hazırlanıyor...\n".encode("utf-8")

            # Simulate OpenAI response generation
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are {assistant_id}"},
                    {"role": "user", "content": user_message}
                ]
            )

            if response and 'choices' in response:
                content = response['choices'][0]['message']['content']
                for char in content:
                    yield char.encode("utf-8")
                    time.sleep(0.01)
            else:
                yield "Yanıt oluşturulamadı.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    def _handle_feedback_route(self):
        """
        Handle user feedback via POST requests.
        """
        try:
            data = request.get_json()
            self.logger.info(f"Geri bildirim alındı: {data}")
            return jsonify({"message": "Geri bildiriminiz için teşekkür ederiz!"})
        except Exception as e:
            self.logger.error(f"Geri bildirim hatası: {str(e)}")
            return jsonify({"error": "Bir hata oluştu."}), 500

    def run(self, debug=True):
        """
        Run the Flask application.
        """
        self.app.run(debug=debug)

if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY", "")
    chatbot_api = ChatbotAPI(api_key)
    chatbot_api.run(debug=True)