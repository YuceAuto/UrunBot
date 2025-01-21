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

        # 1) Asistan seçimi
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in user_message.lower() for k in keywords):
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

            # Filtre ("Fabia Premium", "Scala Elite" vs.)
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

            # ========== Kullanıcı niyeti ==========
            # Monte Carlo istiyor ama Premium yok
            if ("monte carlo" in lower_msg) and ("premium" not in lower_msg):
                desired_group = "monte_carlo"
            # Premium istiyor ama Monte Carlo yok
            elif ("premium" in lower_msg) and ("monte carlo" not in lower_msg):
                desired_group = "premium"
            else:
                # Karma istek ya da ikisi de yok => default mantık
                desired_group = None

            # Sıralama
            sorted_images = self._multi_group_sort(found_images, desired_group)

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

        # 4) (Opsiyonel) OpenAI / ChatGPT akışı
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

    def _multi_group_sort(self, image_list, desired_group=None):
        """
        Kullanıcı "monte carlo" -> desired_group="monte_carlo"
        Kullanıcı "premium" -> desired_group="premium"
        Aksi => Normal mantık
        """

        # A) Monte Carlo listesi (12 adım)
        monte_carlo_12 = [
            ["monte", "carlo", "direksiyon", "simidi"],
            ["monte", "carlo", "döşeme", "standart"],
            ["monte", "carlo", "döşeme", "opsiyonel"],
            ["monte", "carlo", "ön", "dekor", "standart"],
            ["monte", "carlo", "ön", "dekor", "opsiyonel"],
            ["monte", "carlo", "ön", "konsol", "standart"],
            ["monte", "carlo", "ön", "konsol", "opsiyonel"],
            ["monte", "carlo", "gösterge", "paneli"],
            ["monte", "carlo", "multimedya"],
            ["monte", "carlo", "jant", "standart"],
            # 11) Opsiyonel PJF jant
            ["monte", "carlo", "opsiyonel", "pjf", "jant"],
            # 12) Normal opsiyonel jant
            ["monte", "carlo", "jant", "opsiyonel"]
        ]

        # B) Premium/Elite listesi (12 adım)
        premium_elite_12 = [
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
            ["jant", "opsiyonel"],
            # 12) => Premium ve Monte Carlo PJF jant
            ["premium", "ve", "monte", "carlo", "opsiyonel", "pjf", "jant"]
        ]

        default_list = []

        # Eğer kullanıcı net "monte carlo" diyorsa => Tüm dosyaları monte carlo listesinde sırala
        if desired_group == "monte_carlo":
            return self._sort_images_in_strict_order(image_list, monte_carlo_12)

        # Eğer kullanıcı net "premium" diyorsa => Tüm dosyaları premium listesinde sırala
        if desired_group == "premium":
            return self._sort_images_in_strict_order(image_list, premium_elite_12)

        # Aksi => Normal "monte carlo" / "premium" / "default" gruplama
        monte_carlo_files = []
        premium_elite_files = []
        default_files = []

        for img in image_list:
            replaced = img.lower().replace("_", " ")
            if "monte carlo" in replaced:
                monte_carlo_files.append(img)
            elif ("premium" in replaced) or ("elite" in replaced):
                premium_elite_files.append(img)
            else:
                default_files.append(img)

        sorted_mc = self._sort_images_in_strict_order(monte_carlo_files, monte_carlo_12)
        sorted_pe = self._sort_images_in_strict_order(premium_elite_files, premium_elite_12)
        sorted_def = self._sort_images_in_strict_order(default_files, default_list)
        return sorted_mc + sorted_pe + sorted_def

    def _sort_images_in_strict_order(self, image_list, priority_lists):
        """
        priority_lists içindeki satırları sırayla dener,
        eşleşenleri ekler, kalanları en sonda alfabetik ekler.
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
                print(f"[DEBUG] Eşleşen satır: {word_list} -> {matched_now}")
                sorted_results.extend(matched_now)
                for m in matched_now:
                    remaining.remove(m)

        if remaining:
            leftover_sorted = sorted(list(remaining))
            print(f"[DEBUG] Kalan (alfabetik ekle): {leftover_sorted}")
            sorted_results.extend(leftover_sorted)

        print(f"[DEBUG] Final sıralı liste: {sorted_results}")
        return sorted_results

    def _is_image_request(self, message: str):
        msg = message.lower()
        return ("resim" in msg) or ("fotoğraf" in msg) or ("görsel" in msg)

    def _extract_image_keyword(self, message: str, assistant_name: str):
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
