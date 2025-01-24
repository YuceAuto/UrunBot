from flask import app, request, jsonify, render_template
from modules.chatbot import ChatbotAPI
from modules.utils import Utils

class Routes:

    def __init__(self):
        self.utils = Utils()

    def define_routes(self, logger):
        self.chatbot = ChatbotAPI(logger)

    @app.route("/", methods=["GET"])
    def home():
        return render_template("index.html")

    @app.route("/ask", methods=["POST"])
    def ask():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON format."}), 400
            user_message = data.get("question", "")
            user_id = data.get("user_id", "default_user")
            response = chatbot.generate_response(user_message, user_id)
            return jsonify({"response": response})
        except Exception as e:
            self.utils.logger.error(f"Error in /ask: {str(e)}")
            return jsonify({"error": "An error occurred."}), 500

    @app.route("/feedback", methods=["POST"])
    def feedback():
        try:
            data = request.get_json()
            self.utils.logger.info(f"Feedback received: {data}")
            return jsonify({"message": "Thank you for your feedback!"})
        except Exception as e:
            self.utils.logger.error(f"Error in /feedback: {str(e)}")
            return jsonify({"error": "An error occurred."}), 500
