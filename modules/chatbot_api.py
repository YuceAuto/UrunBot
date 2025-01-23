# ----------------------------------------------------
# chatbot_api.py
# ----------------------------------------------------
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

# ---------------------------------------------------------
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
    ["monte", "carlo", "opsiyonel", "pjf", "jant"],
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
    ["premium", "ve", "monte", "carlo", "opsiyonel", "pjf", "jant"]
]

# ---------------------------------------------------------
# C) Fabia / Scala / Kamiq için 12'li örnek listeler
# ---------------------------------------------------------
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

        # Asistan konfigürasyonu (model isimleri)
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

    # ----------------------------------------------------
    # 1) Scala özel sıralama fonksiyonu
    # ----------------------------------------------------
    def _custom_scala_sort(self, image_list):
        """
        "Scala görsel" sorusu geldiğinde,
        kullanıcı tarafından talep edilen özel sırayı uygulamak için
        özel bir sıralama fonksiyonu.
        """
        custom_order = [
            ["scala", "elite", "standart", "direksiyon", "simidi"],          # 3
            ["scala", "premium", "standart", "direksiyon", "simidi"],        # 2
            ["scala", "monte", "carlo", "standart", "direksiyon", "simidi"],  # 1
            ["scala", "elite", "studio", "standart", "döşeme"],              # 10
            ["scala", "elite", "studio", "standart", "kapı", "döşeme"],      # 11
            ["scala", "premium", "lodge", "standart", "döşeme"],             # 6
            ["scala", "premium", "lodge", "standart", "kapı", "döşeme"],     # 7
            ["scala", "premium", "suite", "opsiyonel", "döşeme"],            # 8
            ["scala", "premium", "suite", "opsiyonel", "kapı", "döşeme"],    # 9
            ["scala", "monte", "carlo", "standart", "döşeme"],               # 4
            ["scala", "monte", "carlo", "standart", "kapı", "döşeme"],       # 5
            ["scala", "elite", "studio", "standart", "ön", "dekor"],         # 15
            ["scala", "premium", "lodge", "standart", "ön", "dekor"],        # 13
            ["scala", "premium", "suite", "opsiyonel", "ön", "dekor"],       # 14
            ["scala", "monte", "carlo", "standart", "ön", "dekor"],          # 12
            ["scala", "elite", "studio", "standart", "ön", "konsol"],        # 19
            ["scala", "premium", "lodge", "standart", "ön", "konsol"],       # 17
            ["scala", "premium", "suite", "opsiyonel", "ön", "konsol"],      # 18
            ["scala", "monte", "carlo", "standart", "ön", "konsol"],         # 16
            ["scala", "monte", "carlo", "standart", "dijital", "gösterge", "paneli"], # 20
            ["scala", "premium", "standart", "gösterge", "paneli"],          # 21
            ["scala", "elite", "standart", "gösterge", "paneli"],            # 22
            ["scala", "monte", "carlo", "standart", "multimedya", "sistemi"],# 23
            ["scala", "premium", "standart", "multimedya", "sistemi"],       # 24
            ["scala", "elite", "standart", "multimedya", "sistemi"],         # 25
            ["scala", "monte", "carlo", "pji", "standart", "jant"],          # 26
            ["scala", "premium", "pj5", "standart", "jant"],                 # 27
            ["scala", "1.0", "premium", "pj7", "opsiyonel", "jant"],         # 28
            ["scala", "premium", "pjg", "opsiyonel", "jant"],                # 29
            ["scala", "premium", "pjn", "opsiyonel", "jant"],                # 30
            ["scala", "premium", "pjp", "opsiyonel", "jant"],                # 31
            ["scala", "elite", "pj5", "standart", "jant"],                   # 32
            ["scala", "elite", "pj7", "opsiyonel", "jant"],                  # 33
            ["scala", "elite", "pjg", "opsiyonel", "jant"],                  # 34
            ["scala", "elite", "pjp", "opsiyonel", "jant"],                  # 35
            ["scala", "ay", "beyazı"],                                       # 36
            ["scala", "gümüş"],                                             # 37
            ["scala", "çelik", "gri"],                                       # 38
            ["scala", "grafit", "gri"],                                      # 39
            ["scala", "büyülü", "siyah"],                                    # 40
            ["scala", "kadife", "kırmızısı"],                                # 41
            ["scala", "yarış", "mavisi"]                                     # 42
        ]

        def order_key(item):
            item_lower = item.lower()
            for index, keywords in enumerate(custom_order):
                if all(keyword in item_lower for keyword in keywords):
                    return index
            return len(custom_order)

        return sorted(image_list, key=order_key)

    # ----------------------------------------------------
    # 2) Kamiq özel sıralama fonksiyonu (YENİ EKLENEN)
    # ----------------------------------------------------
    def _custom_kamiq_sort(self, image_list):
        """
        "Kamiq görsel" sorusu geldiğinde,
        kullanıcı tarafından talep edilen özel sırayı uygulamak için
        özel bir sıralama fonksiyonu.
        """

        # İstediğiniz tam sıra:
        custom_order = [
            ["kamiq", "monte", "carlo", "standart", "direksiyon", "simidi"],  # 1
            ["kamiq", "premium", "standart", "direksiyon", "simidi"],        # 2
            ["kamiq", "elite", "standart", "direksiyon", "simidi"],          # 3
            ["kamiq", "monte", "carlo", "standart", "döşeme"],               # 4
            ["kamiq", "monte", "carlo", "standart", "kapı", "döşeme"],       # 5
            ["kamiq", "premium", "lodge", "standart", "döşeme"],             # 6
            ["kamiq", "premium", "lodge", "standart", "kapı", "döşeme"],     # 7
            ["kamiq", "premium", "suite", "opsiyonel", "döşeme"],            # 8
            ["kamiq", "premium", "suite", "opsiyonel", "kapı", "döşeme"],    # 9
            ["kamiq", "elite", "studio", "standart", "döşeme"],              # 10
            ["kamiq", "elite", "studio", "standart", "kapı", "döşeme"],      # 11
            ["kamiq", "monte", "carlo", "standart", "ön", "dekor"],          # 12
            ["kamiq", "premium", "lodge", "standart", "ön", "dekor"],        # 13
            ["kamiq", "premium", "suite", "opsiyonel", "ön", "dekor"],       # 14
            ["kamiq", "elite", "studio", "standart", "ön", "dekor"],         # 15
            ["kamiq", "monte", "carlo", "standart", "ön", "konsol"],         # 16
            ["kamiq", "premium", "lodge", "standart", "ön", "konsol"],       # 17
            ["kamiq", "premium", "suite", "opsiyonel", "ön", "konsol"],      # 18
            ["kamiq", "elite", "studio", "standart", "ön", "konsol"],        # 19
            ["kamiq", "monte", "carlo", "standart", "dijital", "gösterge", "paneli"], # 20
            ["kamiq", "premium", "standart", "gösterge", "paneli"],          # 21
            ["kamiq", "elite", "standart", "gösterge", "paneli"],            # 22
            ["kamiq", "monte", "carlo", "standart", "multimedya", "sistemi"],# 23
            ["kamiq", "premium", "standart", "multimedya", "sistemi"],       # 24
            ["kamiq", "elite", "standart", "multimedya", "sistemi"],         # 25
            ["kamiq", "monte", "carlo", "pji", "standart", "jant"],          # 26
            ["kamiq", "premium", "pjg", "standart", "jant"],                 # 27
            ["kamiq", "1.0", "premium", "pj7", "opsiyonel", "jant"],         # 28
            ["kamiq", "premium", "pjg", "opsiyonel", "jant"],                # 29
            ["kamiq", "premium", "pjn", "opsiyonel", "jant"],                # 30
            ["kamiq", "premium", "pjp", "opsiyonel", "jant"],                # 31
            ["kamiq", "elite", "p02", "standart", "jant"],                   # 32
            ["kamiq", "1.0", "elite", "pj7", "opsiyonel", "jant"],           # 33
            ["kamiq", "elite", "pjg", "opsiyonel", "jant"],                  # 34
            ["kamiq", "elite", "pjp", "opsiyonel", "jant"],                  # 35
            ["kamiq", "ay", "beyazı"],                                       # 36
            ["kamiq", "gümüş"],                                             # 37
            ["kamiq", "graptihe", "gri"],                                    # 38
            ["kamiq", "büyülü", "siyah"],                                    # 39
            ["kamiq", "kadife", "kırmızısı"],                                # 40
            ["kamiq", "yarış", "mavisi"],                                    # 41
            ["kamiq", "phoenix", "turuncu"]                                  # 42
        ]

        def order_key(item):
            item_lower = item.lower()
            for index, keywords in enumerate(custom_order):
                if all(keyword in item_lower for keyword in keywords):
                    return index
            return len(custom_order)

        return sorted(image_list, key=order_key)

    # -------------------------------------------------------
    # Öncelik fonksiyonları (12 adım)
    # -------------------------------------------------------
    def get_priority_for_mc(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(monte_carlo_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        return 999

    def get_priority_for_prem_elite(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(premium_elite_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        return 999

    def get_priority_for_fabia_12(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(fabia_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        return 999

    def get_priority_for_scala_12(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(scala_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        return 999

    def get_priority_for_kamiq_12(self, filename: str) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(kamiq_12):
            if all(k in lower_f for k in pattern_keywords):
                return index
        return 999

    # -------------------------------------------------------
    # 7 AŞAMALI VARSAYILAN SIRALAMA
    # -------------------------------------------------------
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

        monte_carlo_std = []
        monte_carlo_opt = []
        premium_std = []
        premium_opt = []
        elite_std = []
        elite_opt = []
        leftover = []

        for img in image_list:
            lower_name = img.lower()
            if is_monte_carlo_standard(lower_name):
                monte_carlo_std.append(img)
            elif is_monte_carlo_optional(lower_name):
                monte_carlo_opt.append(img)
            elif is_premium_standard(lower_name):
                premium_std.append(img)
            elif is_premium_optional(lower_name):
                premium_opt.append(img)
            elif is_elite_standard(lower_name):
                elite_std.append(img)
            elif is_elite_optional(lower_name):
                elite_opt.append(img)
            else:
                leftover.append(img)

        # Gruplar içinde alfabetik
        monte_carlo_std.sort()
        monte_carlo_opt.sort()
        premium_std.sort()
        premium_opt.sort()
        elite_std.sort()
        elite_opt.sort()
        leftover.sort()

        return (
            monte_carlo_std
            + monte_carlo_opt
            + premium_std
            + premium_opt
            + elite_std
            + elite_opt
            + leftover
        )

    # -------------------------------------------------------
    # TEK BİR FONKSİYONDA SIRALAMA YÖNETİMİ
    # -------------------------------------------------------
    def _multi_group_sort(self, image_list, desired_group=None):
        """
        desired_group şunları alabilir:
          "monte_carlo"
          "premium_elite"
          "fabia_12"
          "scala_12"
          "kamiq_12"
          "scala_custom" -> özel sıralama
          "kamiq_custom" -> yeni eklediğimiz özel sıralama
          None -> 7 aşamalı default
        """
        if desired_group == "scala_custom":
            return self._custom_scala_sort(image_list)
        elif desired_group == "kamiq_custom":  # <-- YENİ EKLENDİ
            return self._custom_kamiq_sort(image_list)
        elif desired_group == "monte_carlo":
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
            # None => 7 aşamalı default
            return self._default_7step_sort(image_list)

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

        if user_message == "Scala renkleri nelerdir":
            time.sleep(2.0)
            yield "Scala renk seçenekleri şunlardır: Kadife Kırmızısı, Ay Beyazı, Yarış Mavisi, Gümüş, Çelik Gri, Büyülü Siyah, Grafit Gri."
            yield "Birbirinden göz alıcı renklerimizden Kadife Kırmızısı rengimizin görselini görmek ister misin?"
            assistant_id  = "Scala"
            keyword = "Scala Kadife Kırmızısı"
            return
        
        if user_message == "Kamiq'te cam tavan var mı":
            time.sleep(2.0)
            yield "Evet, Skoda Kamiq Premium donanım seviyesinde cam tavan opsiyonel olarak sunulurken, Monte Carlo donanım seviyesinde standart olarak sunulmaktadır."
            return

        if user_message == "Fabia Monte Carlo döşeme görselleri":
            assistant_id = "Fabia"
            # 1) Asistan seçimi (Kamiq / Fabia / Scala)
            assistant_id = self.user_states.get(user_id)
            for aid, keywords in self.ASSISTANT_CONFIG.items():
                if any(k.lower() in user_message.lower() for k in keywords):
                    assistant_id = aid
                    self.user_states[user_id] = assistant_id
                    break

        # 2) Görsel isteği mi?
        if self._is_image_request(user_message):
            if user_message == "Evet" or user_message == "evet":
                time.sleep(2.0)
                yield "Bu tercihinizi duyduğuma çok sevindim! İşte, Scala Kadife Kırmızısı görselini paylaşıyorum."
                assistant_name = "Scala"
                keyword = "Scala Kadife Kırmızısı"

            if user_message == "Fabia Monte Carlo döşeme görselleri":
                time.sleep(2.0)
                yield "İçindeyken çok özel hissedeceğiniz Monte Carlo’nun döşeme görsellerini aşağıda bulabilirsiniz. Gerçekten de çok şık bir tercih :)"
                assistant_name = "Fabia"
                keyword = "Fabia Monte Carlo döşeme görselleri"

            # if not assistant_id:
            #    yield "Henüz bir asistan seçilmediği için görsel gösteremiyorum.\n".encode("utf-8")
            #    return

            # assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
            # if not assistant_name:
            #     yield "Asistan adını bulamadım.\n".encode("utf-8")
            #     return

            # Filtre
            # keyword = self._extract_image_keyword(user_message, assistant_name)
            print(assistant_name, keyword)
            if keyword:
                full_filter = f"{assistant_name} {keyword}"
            else:
                full_filter = assistant_name
            print(full_filter)
            found_images = self.image_manager.filter_images_multi_keywords(full_filter)
            if not found_images:
                yield f"'{full_filter}' için uygun bir görsel bulamadım.\n".encode("utf-8")
                return

            # Kullanıcı mesajı
            lower_msg = user_message.lower()

            # 3) Hangi özel sıralama?
            if "scala görsel" in lower_msg:
                desired_group = "scala_custom"
            elif "kamiq görsel" in lower_msg:  # <-- YENİ EKLENDİ
                desired_group = "kamiq_custom"
            elif "monte carlo" in lower_msg:
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

            # 4) Sıralama ve yanıt üretimi
            sorted_images = self._multi_group_sort(found_images, desired_group)

            for img_file in sorted_images:
                img_url = f"/static/images/{img_file}"
                base_name, _ = os.path.splitext(img_file)
                pretty_name = base_name.replace("_", " ")
                yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

            return

        # 5) Görsel isteği yoksa => normal chat
        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        # 6) (Örnek) OpenAI Chat'te işlem
        try:
            # Bu kısım tamamen demo/dummy
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )

            start_time = time.time()
            timeout = 45

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

    # -------------------------------------------
    # Yardımcı fonksiyonlar
    # -------------------------------------------
    def _is_image_request(self, message: str):
        msg = message.lower()
        return ("resim" in msg) or ("fotoğraf" in msg) or ("görsel" in msg) or ("evet" in msg) or ("Evet" in msg) or ("görseli" in msg) or ("görselleri" in msg)

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
