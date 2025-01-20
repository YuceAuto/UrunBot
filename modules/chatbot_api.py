import os
import time
import logging
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai
from modules.image_manager import ImageManager
from modules.markdown_utils import MarkdownProcessor

load_dotenv()

def item_matches(img_lower: str, word_list: list) -> bool:
    """
    word_list içindeki normal kelimeler -> Dosya adında GEÇMELİ
    '!xyz' -> Dosya adında GEÇMEMELİ
    Ör: ["monte","carlo","standart","döşeme","!kapı"]
    """
    must_have = []
    must_not = []
    for w in word_list:
        if w.startswith("!"):
            must_not.append(w[1:])
        else:
            must_have.append(w)

    for mh in must_have:
        if mh not in img_lower:
            return False
    for mn in must_not:
        if mn in img_lower:
            return False
    return True


class ChatbotAPI:
    def __init__(self, static_folder='static', template_folder='templates'):
        self.app = Flask(
            __name__,
            static_folder=os.path.join(os.getcwd(), static_folder),
            template_folder=os.path.join(os.getcwd(), template_folder)
        )
        
        CORS(self.app)
        self.logger = self._setup_logger()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        self.ASSISTANT_CONFIG = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }

        self.user_states = {}
        self.ASSISTANT_NAME_MAP = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": "Kamiq",
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": "Fabia",
            "asst_njSG1NVgg4axJFmvVYAIXrpM": "Scala",
        }

        images_path = os.path.join(static_folder, "images")
        self.image_manager = ImageManager(images_folder=images_path)
        self.image_manager.load_images()

        self.markdown_processor = MarkdownProcessor()

        self._define_routes()

    def _setup_logger(self):
        logger = logging.getLogger("ChatbotAPI")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _define_routes(self):
        @self.app.route("/", methods=["GET"])
        def home():
            return render_template("index.html")

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._ask()

        @self.app.route("/feedback", methods=["POST"])
        def feedback():
            return self._feedback()

    def _ask(self):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON format."}), 400
        except Exception as e:
            self.logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({"error": "Invalid JSON format."}), 400

        user_message = data.get("question", "")
        user_id = data.get("user_id", "default_user")

        if not user_message:
            return jsonify({"response": "Please enter a question."})

        response_generator = self._generate_response(user_message, user_id)
        return self.app.response_class(response_generator, mimetype="text/plain")

    def _generate_response(self, user_message, user_id):
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")

        # 1) Asistan seçimi (Kullanıcı "Scala", "Kamiq", "Fabia" diyorsa)
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        # 2) Görsel isteği?
        if self._is_image_request(user_message):
            if not assistant_id:
                yield "Henüz bir asistan seçilmediği için görsel gösteremiyorum.\n".encode("utf-8")
                return

            assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
            if not assistant_name:
                yield "Asistan adını bulamadım.\n".encode("utf-8")
                return

            # Ek kelimeler
            keyword = self._extract_image_keyword(user_message, assistant_name)
            if keyword:
                full_filter = f"{assistant_name} {keyword}"
            else:
                full_filter = assistant_name

            found_images = self.image_manager.filter_images_multi_keywords(full_filter)
            if not found_images:
                yield f"'{full_filter}' için uygun bir görsel bulamadım.\n".encode("utf-8")
                return

            lower_msg = user_message.lower()

            # (A) "Tüm görselleri istemiyorum" derse kısa liste
            if self._user_doesnt_want_all_images(lower_msg):
                priority_lists = [
                    ["monte", "carlo"],
                    ["premium", "standart"],
                    ["premium", "opsiyonel"],
                    ["elite",   "standart"],
                    ["elite",   "opsiyonel"]
                ]
                sorted_images = self._sort_images_in_strict_order(found_images, priority_lists)
            else:
                # (B) Scala / Kamiq / Fabia -> monte carlo (8 adım), premium/elite (11 adım)
                if assistant_name.lower() in ["scala", "kamiq", "fabia"]:
                    sorted_images = self._multi_group_sort(found_images)
                else:
                    sorted_images = found_images

            # Sonuçları dön
            for img_file in sorted_images:
                img_url = f"/static/images/{img_file}"
                base_name, _ = os.path.splitext(img_file)
                pretty_name = base_name.replace("_", " ")

                yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

            return

        # 3) Görsel isteği yoksa => Chat akışı
        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        # 4) ChatGPT / OpenAI akışı (opsiyonel)
        try:
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )

            start_time = time.time()
            timeout = 30

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)
                            content = self.markdown_processor.transform_text_to_markdown(content)
                            yield content.encode("utf-8")
                    return
                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    def _multi_group_sort(self, image_list):
        """
        Monte Carlo => 8 adım
        Premium/Elite => 11 adım
        Default => en sona (boş liste)
        """
        # Monte Carlo (8 adım)
        monte_carlo_8 = [
            ["monte", "carlo", "standart", "direksiyon", "simidi"],
            ["monte", "carlo", "standart", "döşeme", "!kapı"],
            ["monte", "carlo", "standart", "kapı", "döşeme"],
            ["monte", "carlo", "standart", "ön", "dekor"],
            ["monte", "carlo", "standart", "ön", "konsol"],
            ["monte", "carlo", "standart", "gösterge", "panel"],
            ["monte", "carlo", "standart", "multimedya", "sistemi"],
            ["monte", "carlo", "standart", "jant"]
        ]

        # Premium / Elite (11 adım)
        premium_elite_11 = [
            ["direksiyon", "simidi"],
            ["döşeme", "standart"],
            ["döşeme", "opsiyonel"],
            ["ön", "dekor", "standart"],
            ["ön", "dekor", "opsiyonel"],
            ["ön", "konsol", "standart"],
            ["ön", "konsol", "opsiyonel"],
            ["gösterge", "paneli"],
            ["multimedya"],
            ["jant", "standart"],
            ["jant", "opsiyonel"]
        ]

        default_list = []

        # A) Gruplara ayır
        monte_carlo_files = []
        premium_elite_files = []
        default_files = []

        for img in image_list:
            img_lower = img.lower()
            if "monte carlo" in img_lower:
                monte_carlo_files.append(img)
            elif ("premium" in img_lower) or ("elite" in img_lower):
                premium_elite_files.append(img)
            else:
                default_files.append(img)

        # B) Her grubu ayrı listesiyle sırala
        sorted_mc = self._sort_images_in_strict_order(monte_carlo_files, monte_carlo_8)
        sorted_pe = self._sort_images_in_strict_order(premium_elite_files, premium_elite_11)
        sorted_def = self._sort_images_in_strict_order(default_files, default_list)

        # C) Birleştir (Monte Carlo -> Premium/Elite -> Default)
        return sorted_mc + sorted_pe + sorted_def

    def _sort_images_in_strict_order(self, image_list, priority_lists):
        """
        priority_lists içindeki satırları sırayla dener,
        eşleşenleri oradan çıkarır. Kalanlar en sonda alfabetik eklenir.
        """
        sorted_results = []
        remaining = set(image_list)

        for word_list in priority_lists:
            matched_now = []
            for img in list(remaining):
                if item_matches(img.lower(), word_list):
                    matched_now.append(img)
            if matched_now:
                matched_now.sort()
                sorted_results.extend(matched_now)
                for m in matched_now:
                    remaining.remove(m)

        if remaining:
            sorted_results.extend(sorted(list(remaining)))

        return sorted_results

    def _is_image_request(self, message: str):
        """
        'resim', 'fotoğraf' veya 'görsel' -> True
        """
        msg = message.lower()
        return ("resim" in msg) or ("fotoğraf" in msg) or ("görsel" in msg)

    def _extract_image_keyword(self, message: str, assistant_name: str):
        """
        Ör: "Kamiq Monte Carlo Standart Döşeme" -> 'monte carlo standart döşeme'
        """
        lower_msg = message.lower()
        brand_lower = assistant_name.lower()
        cleaned = lower_msg.replace(brand_lower, "")
        cleaned = re.sub(r"(resim|fotoğraf|görsel)\w*", "", cleaned, flags=re.IGNORECASE)

        common_phrases = [
            r"paylaşabilir\s?misin", r"paylaşır\s?mısın",
            r"lütfen", r"istiyorum", r"\?$"
        ]
        for p in common_phrases:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)

        final_keyword = cleaned.strip()
        return final_keyword if final_keyword else None

    def _user_doesnt_want_all_images(self, msg: str) -> bool:
        """
        'tüm görselleri istemiyorum', 'tümünü istemiyorum' vb.
        """
        negatives = ["istemiyorum", "istemem", "görmek istemiyorum", "görmek istemem"]
        if any(x in msg for x in ["tüm", "hepsi", "tamamı", "tamamını"]):
            for neg in negatives:
                if neg in msg:
                    return True
        return False

    def _feedback(self):
        try:
            data = request.get_json()
            self.logger.info(f"Geri bildirim alındı: {data}")
            return jsonify({"message": "Geri bildiriminiz için teşekkür ederiz!"})
        except Exception as e:
            self.logger.error(f"Geri bildirim hatası: {str(e)}")
            return jsonify({"error": "Bir hata oluştu."}), 500

    def run(self, debug=True):
        self.app.run(debug=debug)
