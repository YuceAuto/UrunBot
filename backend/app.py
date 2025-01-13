import os
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Import the class (not as an instance).
from image_paths import ImagePaths

load_dotenv()

class ChatbotAPI:
    def __init__(self, openai_key=None):
        """
        ChatbotAPI class manages the interaction with OpenAI's API 
        and handles user requests via the Flask application.
        
        :param openai_key: (Optional) Provide the API key directly 
                           or rely on the environment variable.
        """
        # Load the OpenAI API key from an environment variable if not provided explicitly
        self.openai_key = openai_key or os.environ.get("OPENAI_API_KEY", "")
        if not self.openai_key:
            raise ValueError("No OpenAI API key provided. Please set OPENAI_API_KEY as an environment variable.")

        # Initialize the OpenAI client
        self.client = OpenAI(api_key=self.openai_key)
        self.image_dict = ImagePaths()

        # Create the Flask application
        self.app = Flask(__name__)
        CORS(self.app)

        # Assistant IDs
        self.ASSISTANT_IDS = [
            "asst_1qGG7y8w6QcupPETaYQRdGsI",  # Skoda Kamiq Bot
            "asst_I7YubD3Cy6qU4kCc32mbYjUQ",  # Skoda Fabia Bot
            "asst_Ul4gzwnyRZxNcb3I5ot93lo9",  # Skoda Scala Bot
        ]

        # Create an instance of ImagePaths and populate it
        
        self.IMAGE_DICT = self.image_dict._images

        # Relevant keywords
        self.RELEVANT_KEYWORDS = ["Kamiq", "Fabia", "Scala"]

        # Define Flask routes
        self._define_routes()

    def _define_routes(self):
        """
        Define all Flask routes within this method.
        """
        @self.app.route("/", methods=["GET"])
        def home():
            return self.home_route()

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self.ask_route()

    def home_route(self):
        """
        GET '/' endpoint:
        """
        return "Chatbot API is running. Please POST your questions to the /ask endpoint."

    def process_assistant(self, assistant_id, user_message):
        """
        Handles the user message for a single assistant 
        and returns the relevant response if any.

        :param assistant_id: The ID of the assistant to query.
        :param user_message: The user's question or message.
        :return: A tuple of (assistant_id, response) if relevant; otherwise (assistant_id, None).
        """
        try:
            # Create a thread for the conversation
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            print(f"👉 Thread Created (Assistant: {assistant_id}): {thread.id}")

            # Start a run for the created thread
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id, 
                assistant_id=assistant_id
            )
            print(f"👉 Run Started (Assistant: {assistant_id}): {run.id}")

            # Wait until the run is completed or timeout (10 seconds)
            start_time = time.time()
            run_status = "queued"
            while run_status != "completed":
                if time.time() - start_time > 10:  # Timeout: 10 seconds
                    raise TimeoutError(f"Timeout for assistant {assistant_id}.")
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                run_status = run.status
                time.sleep(0.2)  # Sleep to avoid rapid polling

            # Retrieve all messages from the thread
            message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
            messages = message_response.data
            latest_message = next((msg for msg in messages if msg.role == "assistant"), None)

            # Process the assistant's latest message
            if latest_message and latest_message.content:
                content = latest_message.content
                content_text = " ".join(str(c) for c in content) if isinstance(content, list) else str(content)

                # Check if the message is relevant (contains any relevant keyword)
                if any(keyword.lower() in content_text.lower() for keyword in self.RELEVANT_KEYWORDS):
                    return assistant_id, content_text

            return assistant_id, None

        except Exception as e:
            print(f"❗ Error (Assistant: {assistant_id}): {str(e)}")
            return assistant_id, None

    def ask_route(self):
        """
        POST '/ask' endpoint:
        Receives the user question, queries all assistants in parallel, 
        and returns the first relevant response (if any).
        """
        data = request.json
        user_message = data.get("question", "")

        if not user_message:
            return jsonify({"response": "Please provide a valid question."})

        # Process each assistant in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(
                lambda aid: self.process_assistant(aid, user_message), 
                self.ASSISTANT_IDS
            ))

        # Find the first relevant response
        relevant_response = next((content for assistant_id, content in results if content), None)

        if relevant_response:
            return jsonify({"response": relevant_response})
        else:
            return jsonify({"response": "No assistant provided a relevant answer."})

    def run(self, debug=True):
        """
        Run the Flask application.
        """
        self.app.run(debug=debug)


if __name__ == "__main__":
    # Optionally, you can pass openai_key directly or just rely on the environment variable.
    chatbot_api = ChatbotAPI()
    chatbot_api.run(debug=True)