import os
import requests
import io
import pygame
from mutagen.mp3 import MP3
from dotenv import load_dotenv

# Çevresel değişkenleri yükleme
load_dotenv()

class ElevenLabsTTS:
    """
    ElevenLabs TTS sınıfı ile metni seslendirmek için bir API bağlantısı sağlar.
    """
    def __init__(self):
        """
        ElevenLabs TTS sınıfını başlatır ve gerekli ayarları yapar.
        """
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        # Pygame ses sistemi başlatılır
        pygame.mixer.init()

        if not self.api_key or not self.voice_id:
            raise ValueError("API anahtarı veya ses kimliği eksik. Lütfen .env dosyasını kontrol edin.")

    def speak(self, text, stability=0.6, similarity_boost=0.92):
        """
        Metni seslendiren bir fonksiyon.

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
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

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
                print(f"API Hatası: {response.status_code}, {response.json().get('error', 'Bilinmeyen hata')}")

        except requests.exceptions.RequestException as req_err:
            print(f"HTTP Hatası: {req_err}")
        except Exception as e:
            print(f"Beklenmeyen bir hata oluştu: {e}")

    async def play(self, file_path):
        """
        Yerel bir MP3 dosyasını çalmak için bir fonksiyon.

        :param file_path: Çalınacak MP3 dosyasının yolu
        """
        try:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            # Ses bitene kadar bekle
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        except FileNotFoundError as fnf_error:
            print(fnf_error)
        except Exception as e:
            print(f"Beklenmeyen bir hata oluştu: {e}")

    def get_duration(self, file_path):
        """
        MP3 dosyasının süresini döndüren bir fonksiyon.

        :param file_path: Süresi ölçülecek MP3 dosyasının yolu
        :return: MP3 dosyasının süresi (saniye cinsinden float)
        """
        try:
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

            audio = MP3(file_path)
            return audio.info.length  # Süreyi saniye cinsinden döndürür
        except FileNotFoundError as fnf_error:
            print(fnf_error)
        except Exception as e:
            print(f"MP3 süresi alınırken hata oluştu: {e}")
            return None

# Örnek kullanım
if __name__ == "__main__":
    try:
        # ElevenLabs TTS sınıfını başlat
        tts = ElevenLabsTTS()

        # Metni seslendirme
        tts.speak(
            text="Merhaba, bu ElevenLabs tarafından seslendiriliyor.",
            stability=0.3,
            similarity_boost=1.0,
        )

        # Yerel MP3 dosyasını çalma
        tts.play("example.mp3")

        # Yerel MP3 dosyasının süresini alma
        duration = tts.get_duration("example.mp3")
        print(f"Ses dosyası süresi: {duration:.2f} saniye")

    except Exception as e:
        print(f"Program hatası: {e}")
