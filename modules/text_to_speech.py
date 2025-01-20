import os
import requests
import io
import pygame
from dotenv import load_dotenv

load_dotenv()

class ElevenLabsTTS:
    def __init__(self, api_key, voice_id):
        """
        ElevenLabs TTS sınıfı başlatılır.

        :param api_key: ElevenLabs API anahtarı
        :param voice_id: Kullanılacak ses kimliği (varsayılan: "21m00Tcm4TlvDq8ikWAM")
        """
        self.api_key = api_key
        self.voice_id = "x5J0w1JGs0MQNyzjoYDc"
        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/x5J0w1JGs0MQNyzjoYDc"
        pygame.mixer.init()  # Pygame ses sistemi başlatılır

    def speak(self, text, stability=0.5, similarity_boost=0.8):
        """
        ElevenLabs API ile metni sesli olarak oynatır.

        :param text: Seslendirilmek istenen metin
        :param stability: Sesin stabilitesi (0.0 - 1.0 arası)
        :param similarity_boost: Ses benzerliği artırma (0.0 - 1.0 arası)
        """
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        data = {
            "text": text,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }
        print(data)
        try:
            response = requests.post(self.url, json=data, headers=headers)
            if response.status_code == 200:
                # Ses verisini bellekte işleme
                audio_stream = io.BytesIO(response.content)
                pygame.mixer.music.load(audio_stream, "mp3")
                pygame.mixer.music.play()

                # Ses bitene kadar bekle
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            else:
                print(f"API Hatası: {response.status_code}, {response.text}")

        except Exception as e:
            print(f"Hata: {e}")

# Örnek kullanım
if __name__ == "__main__":
    # .env dosyasındaki API anahtarını al
    API_KEY = os.getenv("ELEVENLABS_API_KEY")
    tts = ElevenLabsTTS(api_key=API_KEY)

    # Metni seslendirme
    tts.speak(
        text="Merhaba, bu ElevenLabs tarafından seslendiriliyor.",
        stability=0.7,
        similarity_boost=0.9,
    )
