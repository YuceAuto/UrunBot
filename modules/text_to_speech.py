from gtts import gTTS
import os
import tempfile
import random
import pygame

ASSETS_DIR = os.path.join(os.getcwd(), "assets")

class TextToSpeech:
    def __init__(self, language='tr', assets_path='assets'):
        """
        Text-to-Speech (TTS) modülünü başlatır.

        :param language: Kullanılacak dil (varsayılan 'tr' - Türkçe)
        :param assets_path: Sabit metinlerin bulunduğu klasör
        """
        self.language = language
        self.assets_path = assets_path
        pygame.mixer.init()  # pygame ses sistemi başlatılır

    def speak(self, file_path=ASSETS_DIR+"curr_text.txt", speed_multiplier=1.5):
        """
        Reads text from a file and plays it as speech with an adjustable speed.

        :param file_path: Path to the text file to read from
        :param speed_multiplier: Speed multiplier for the speech (default 1.5)
        """
        if not os.path.exists(file_path):
            print(f"Error: The file '{file_path}' does not exist.")
            return

        try:
            # Read the file's content
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read().strip()

            if not text:
                print("Warning: The file is empty.")
                return

            # Generate speech
            tts = gTTS(text=text, lang=self.language, slow=False)

            # Save to a temporary audio file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                temp_file_path = temp_audio.name
                tts.save(temp_file_path)

            # Play the audio
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()

            # Wait until playback finishes
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

        except Exception as e:
            print(f"Error: An issue occurred while reading or playing the text. {e}")

    def play_random_fixed_text(self):
        """
        Sabit metinlerden rastgele birini sesli olarak okur.
        """
        try:
            txt_files = [f for f in os.listdir(self.assets_path) if f.endswith('.txt')]
            if not txt_files:
                print("Uyarı: Sabit metin dosyası bulunamadı.")
                return

            random_file = random.choice(txt_files)
            file_path = os.path.join(self.assets_path, random_file)

            with open(file_path, 'r', encoding='utf-8') as file:
                fixed_text = file.read().strip()

            print(f"Okunuyor (Sabit): {fixed_text}")
            self.speak(fixed_text)
        except Exception as e:
            print(f"Hata: Sabit metin okunurken bir sorun oluştu. {e}")

    def read_fixed_and_dynamic_text(self, fixed_text, dynamic_text):
        """
        Önce sabit bir metni (rastgele bir txt dosyasından), ardından dinamik bir metni okur.

        :param fixed_text: Sabit metin (örn: "Cevabınız hazırlanıyor...")
        :param dynamic_text: Dinamik metin (örn: API'den gelen cevap)
        """
        try:
            # Sabit metni oku
            self.play_random_fixed_text()

            # Dinamik metni oku
            if dynamic_text.strip():
                print(f"Okunuyor: {dynamic_text}")
                self.speak(dynamic_text)
        except Exception as e:
            print(f"Hata: Metin okunurken bir sorun oluştu. {e}")


# Örnek kullanım
if __name__ == "__main__":
    tts = TextToSpeech(language='tr', assets_path='assets')

    sabit_metin = "Cevabınız hazırlanıyor..."
    dinamik_metin = "Skoda Sıkala, modern tasarımı ve zengin özellikleriyle dikkat çeker."

    print("Metinler sırasıyla sesli okunuyor...")
    tts.read_fixed_and_dynamic_text(sabit_metin, dinamik_metin)
