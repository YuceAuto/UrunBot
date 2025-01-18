from gtts import gTTS
import os
import tempfile

class TextToSpeech:
    def __init__(self, language='tr'):
        """
        Text-to-Speech (TTS) modülünü başlatır.

        :param language: Kullanılacak dil (varsayılan 'tr' - Türkçe)
        """
        self.language = language

    def speak(self, text):
        """
        Verilen metni sesli olarak okur.

        :param text: Okunacak metin
        """
        if not text.strip():
            print("Uyarı: Okunacak metin boş.")
            return

        try:
            tts = gTTS(text=text, lang=self.language, slow=False)
            with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as temp_audio:
                tts.save(temp_audio.name)
                os.system(f"start {temp_audio.name}")  # Windows için. MacOS/Linux için 'xdg-open' veya 'open' kullanılabilir.
        except Exception as e:
            print(f"Hata: Metin okunurken bir sorun oluştu. {e}")

    def read_fixed_and_dynamic_text(self, fixed_text, dynamic_text):
        """
        Önce sabit bir metni, ardından dinamik bir metni okur.

        :param fixed_text: Sabit metin (örn: "Cevabınız hazırlanıyor...")
        :param dynamic_text: Dinamik metin (örn: API'den gelen cevap)
        """
        try:
            # Sabit metni oku
            if fixed_text.strip():
                print(f"Okunuyor: {fixed_text}")
                self.speak(fixed_text)

            # Dinamik metni oku
            if dynamic_text.strip():
                print(f"Okunuyor: {dynamic_text}")
                self.speak(dynamic_text)
        except Exception as e:
            print(f"Hata: Metin okunurken bir sorun oluştu. {e}")

# Örnek kullanım
if __name__ == "__main__":
    tts = TextToSpeech(language='tr')

    sabit_metin = "Cevabınız hazırlanıyor..."
    dinamik_metin = "Skoda Sıkala, modern tasarımı ve zengin özellikleriyle dikkat çeker."

    print("Metinler sırasıyla sesli okunuyor...")
    tts.read_fixed_and_dynamic_text(sabit_metin, dinamik_metin)
