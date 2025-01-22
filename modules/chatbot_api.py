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

# ---------------------------
# A) Monte Carlo 12
# ---------------------------
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

# ---------------------------
# B) Premium/Elite 12
# ---------------------------
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

# ---------------------------
# C) Fabia / Scala / Kamiq 12
# ---------------------------
fabia_12 = [
    ["fabia", "direksiyon", "simidi"],
    ["fabia", "döşeme", "standart"],
    ["fabia", "döşeme", "opsiyonel"],
    ["fabia", "ön", "dekor", "standart"],
    ["fabia", "ön", "dekor", "opsiyonel"],
    ["fabia", "ön", "konsol", "standart"],
    ["fabia", "ön", "konsol", "opsiyonel"],
    ["fabia", "gösterge", "paneli"],
    ["fabia", "multimedya"],
    ["fabia", "jant", "standart"],
    ["fabia", "jant", "opsiyonel"],
    ["fabia", "opsiyonel", "pjf", "jant"]
]

scala_12 = [
    ["scala", "direksiyon", "simidi"],
    ["scala", "döşeme", "standart"],
    ["scala", "döşeme", "opsiyonel"],
    ["scala", "ön", "dekor", "standart"],
    ["scala", "ön", "dekor", "opsiyonel"],
    ["scala", "ön", "konsol", "standart"],
    ["scala", "ön", "konsol", "opsiyonel"],
    ["scala", "gösterge", "paneli"],
    ["scala", "multimedya"],
    ["scala", "jant", "standart"],
    ["scala", "jant", "opsiyonel"],
    ["scala", "opsiyonel", "pjf", "jant"]
]

kamiq_12 = [
    ["kamiq", "direksiyon", "simidi"],
    ["kamiq", "döşeme", "standart"],
    ["kamiq", "döşeme", "opsiyonel"],
    ["kamiq", "ön", "dekor", "standart"],
    ["kamiq", "ön", "dekor", "opsiyonel"],
    ["kamiq", "ön", "konsol", "standart"],
    ["kamiq", "ön", "konsol", "opsiyonel"],
    ["kamiq", "gösterge", "paneli"],
    ["kamiq", "multimedya"],
    ["kamiq", "jant", "standart"],
    ["kamiq", "jant", "opsiyonel"],
    ["kamiq", "opsiyonel", "pjf", "jant"]
]


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

        # Örnek asistan konfig (Kamiq / Fabia / Scala)
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

    # -------------- PRIORITY FUNCS (12 ADET + leftover) ---------------
    def get_priority_for_mc(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(monte_carlo_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        # leftover => premium(200), elite(300), else(999)
        if "premium" in lower_f:
            return 200
        if "elite" in lower_f:
            return 300
        return 999

    def get_priority_for_prem_elite(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(premium_elite_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        # leftover => MonteCarlo(200?), vs. ama siz isterseniz ekleyebilirsiniz.
        return 999

    def get_priority_for_fabia_12(self, filename: str) -> int:
        lower_f = filename.lower()
        # 1) fabia_12 eşleşmesi
        for index, pattern_keywords in enumerate(fabia_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        # 2) Eşleşmeyen leftover => premium(200) < elite(300) < others(999)
        if "premium" in lower_f:
            return 200
        if "elite" in lower_f:
            return 300
        return 999

    def get_priority_for_scala_12(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(scala_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        if "premium" in lower_f:
            return 200
        if "elite" in lower_f:
            return 300
        return 999

    def get_priority_for_kamiq_12(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(kamiq_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        if "premium" in lower_f:
            return 200
        if "elite" in lower_f:
            return 300
        return 999

    # --------------- 7 AŞAMALI default ---------------
    def _default_7step_sort(self, image_list):
        def is_monte_carlo_standard(name):
            return ("monte" in name and "carlo" in name and "opsiyonel" not in name)
        def is_monte_carlo_optional(name):
            return ("monte" in name and "carlo" in name and "opsiyonel" in name)
        def is_premium_standard(name):
            return ("premium" in name and "opsiyonel" not in name)
        def is_premium_optional(name):
            return ("premium" in name and "opsiyonel" in name)
        def is_elite_standard(name):
            return ("elite" in name and "opsiyonel" not in name)
        def is_elite_optional(name):
            return ("elite" in name and "opsiyonel" in name)

        mc_std, mc_opt = [], []
        p_std, p_opt = [], []
        e_std, e_opt = [], []
        leftover = []

        for img in image_list:
            lower_name = img.lower()
            if is_monte_carlo_standard(lower_name):
                mc_std.append(img)
            elif is_monte_carlo_optional(lower_name):
                mc_opt.append(img)
            elif is_premium_standard(lower_name):
                p_std.append(img)
            elif is_premium_optional(lower_name):
                p_opt.append(img)
            elif is_elite_standard(lower_name):
                e_std.append(img)
            elif is_elite_optional(lower_name):
                e_opt.append(img)
            else:
                leftover.append(img)

        mc_std.sort()
        mc_opt.sort()
        p_std.sort()
        p_opt.sort()
        e_std.sort()
        e_opt.sort()
        leftover.sort()

        return mc_std + mc_opt + p_std + p_opt + e_std + e_opt + leftover

    # --------------- ANA SIRALAMA ---------------
    def _multi_group_sort(self, image_list, desired_group=None):
        """
        desired_group = "monte_carlo"     => get_priority_for_mc
                        "premium_elite"   => get_priority_for_prem_elite
                        "fabia_12"        => get_priority_for_fabia_12
                        "scala_12"        => get_priority_for_scala_12
                        "kamiq_12"        => get_priority_for_kamiq_12
                        None veya başka   => 7 aşamalı default
        """
        if desired_group == "monte_carlo":
            image_list.sort(key=self.get_priority_for_mc)
            return image_list
        elif desired_group == "premium_elite":
            image_list.sort(key=self.get_priority_for_prem_elite)
            return image_list
        elif desired_group == "fabia_12":
            image_list.sort(key=self.get_priority_for_fabia_12)
            return image_list
        elif desired_group == "scala_12":
            image_list.sort(key=self.get_priority_for_scala_12)
            return image_list
        elif desired_group == "kamiq_12":
            image_list.sort(key=self.get_priority_for_kamiq_12)
            return image_list
        else:
            return self._default_7step_sort(image_list)

    def _generate_response(self, user_message, user_id):
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")

        # 1) Asistan seçimi
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in user_message.lower() for k in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        # 2) Görsel mi?
        if self._is_image_request(user_message):
            if not assistant_id:
                yield "Henüz bir asistan seçilmediği için görsel gösteremiyorum.\n".encode("utf-8")
                return

            assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
            if not assistant_name:
                yield "Asistan adını bulamadım.\n".encode("utf-8")
                return

            keyword = self._extract_image_keyword(user_message, assistant_name)
            if keyword:
                full_filter = f"{assistant_name} {keyword}"
            else:
                full_filter = assistant_name

            found_images = self.image_manager.filter_images_multi_keywords(full_filter)
            if not found_images:
                yield f"'{full_filter}' için uygun bir görsel bulamadım.\n".encode("utf-8")
                return

            # 3) desired_group kararı
            lower_msg = user_message.lower()
            if "monte carlo" in lower_msg:
                desired_group = "monte_carlo"
            elif ("premium" in lower_msg) or ("elite" in lower_msg):
                desired_group = "premium_elite"
            elif "fabia" in lower_msg:
                desired_group = "fabia_12"
            elif "scala" in lower_msg:
                desired_group = "scala_12"
            elif "kamiq" in lower_msg:
                desired_group = "kamiq_12"
            else:
                desired_group = None

            # 4) Sıralama
            sorted_images = self._multi_group_sort(found_images, desired_group)

            # 5) HTML çıkışı
            for img_file in sorted_images:
                img_url = f"/static/images/{img_file}"
                base_name, _ = os.path.splitext(img_file)
                pretty_name = base_name.replace("_", " ")
                yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

            return

        # 4) Görsel isteği yoksa => Chat
        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        # (Opsiyonel) ChatGPT / OpenAI
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
