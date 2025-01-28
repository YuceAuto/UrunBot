# ----------------------------------------------------
# app.py
# ----------------------------------------------------
from modules.chatbot_api import ChatbotAPI
import sys
import os

# modules klasörünü path'e ekle
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

if __name__ == "__main__":
    chatbot = ChatbotAPI()
    chatbot.run(debug=True)
