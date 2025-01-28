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
# Örnek renk listesi (ihtiyaca göre genişletebilirsiniz)
# ---------------------------------------------------------
KNOWN_COLORS = [
    "ay beyazı",
    "gümüş",
    "çelik gri",
    "grafit gri",
    "büyülü siyah",
    "kadife kırmızısı",
    "yarış mavisi",
    "phoenix turuncu"
]

def parse_color_names(text: str) -> list:
    """
    Metin içinde bilinen renk isimlerini arar ve bulduğu her bir rengi (küçük harfle) döndürür.
    """
    lower_text = text.lower()
    found = []
    for color in KNOWN_COLORS:
        if color in lower_text:
            found.append(color)
    return found

# ---------------------------------------------------------
# A) Monte Carlo listesi (12 adım)
# ---------------------------------------------------------
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

# C) Fabia / Scala / Kamiq için 12'li örnek listeler
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

        # Burada user_states'ı tutuyoruz: user_id -> { assistant_id: ..., pending_color_images: [...] }
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
        custom_order = [
            ["scala", "monte", "carlo", "standart", "direksiyon", "simidi"], 
            ["scala", "premium", "standart", "direksiyon", "simidi"],        
            ["scala", "elite", "standart", "direksiyon", "simidi"],          
            ["scala", "monte", "carlo", "standart", "döşeme"],               
            ["scala", "monte", "carlo", "standart", "kapı", "döşeme"],       
            ["scala", "premium", "lodge", "standart", "döşeme"],             
            ["scala", "premium", "lodge", "standart", "kapı", "döşeme"],     
            ["scala", "premium", "suite", "opsiyonel", "döşeme"],            
            ["scala", "premium", "suite", "opsiyonel", "kapı", "döşeme"],    
            ["scala", "elite", "studio", "standart", "döşeme"],              
            ["scala", "elite", "studio", "standart", "kapı", "döşeme"],      
            ["scala", "monte", "carlo", "standart", "ön", "dekor"],          
            ["scala", "premium", "lodge", "standart", "ön", "dekor"],        
            ["scala", "premium", "suite", "opsiyonel", "ön", "dekor"],       
            ["scala", "elite", "studio", "standart", "ön", "dekor"],         
            ["scala", "monte", "carlo", "standart", "ön", "konsol"],         
            ["scala", "premium", "lodge", "standart", "ön", "konsol"],       
            ["scala", "premium", "suite", "opsiyonel", "ön", "konsol"],      
            ["scala", "elite", "studio", "standart", "ön", "konsol"],        
            ["scala", "monte", "carlo", "standart", "dijital", "gösterge", "paneli"],
            ["scala", "premium", "standart", "gösterge", "paneli"],          
            ["scala", "elite", "standart", "gösterge", "paneli"],            
            ["scala", "monte", "carlo", "standart", "multimedya", "sistemi"],
            ["scala", "premium", "standart", "multimedya", "sistemi"],       
            ["scala", "elite", "standart", "multimedya", "sistemi"],         
            ["scala", "monte", "carlo", "pji", "standart", "jant"],          
            ["scala", "premium", "pj5", "standart", "jant"],                 
            ["scala", "1.0", "premium", "pj7", "opsiyonel", "jant"],         
            ["scala", "premium", "pjg", "opsiyonel", "jant"],                
            ["scala", "premium", "pjn", "opsiyonel", "jant"],                
            ["scala", "premium", "pjp", "opsiyonel", "jant"],                
            ["scala", "elite", "pj5", "standart", "jant"],                   
            ["scala", "elite", "pj7", "opsiyonel", "jant"],                  
            ["scala", "elite", "pjg", "opsiyonel", "jant"],                  
            ["scala", "elite", "pjp", "opsiyonel", "jant"],                  
            ["scala", "ay", "beyazı"],                                       
            ["scala", "gümüş"],                                             
            ["scala", "çelik", "gri"],                                       
            ["scala", "grafit", "gri"],                                      
            ["scala", "büyülü", "siyah"],                                    
            ["scala", "kadife", "kırmızısı"],                                
            ["scala", "yarış", "mavisi"]                                     
        ]

        def order_key(item):
            item_lower = item.lower()
            for index, keywords in enumerate(custom_order):
                if all(keyword in item_lower for keyword in keywords):
                    return index
            return len(custom_order)

        return sorted(image_list, key=order_key)

    # ----------------------------------------------------
    # 2) Kamiq özel sıralama fonksiyonu
    # ----------------------------------------------------
    def _custom_kamiq_sort(self, image_list):
        custom_order = [
            ["kamiq", "monte", "carlo", "standart", "direksiyon", "simidi"],
            ["kamiq", "premium", "standart", "direksiyon", "simidi"],
            ["kamiq", "elite", "standart", "direksiyon", "simidi"],
            ["kamiq", "monte", "carlo", "standart", "döşeme"],
            ["kamiq", "monte", "carlo", "standart", "kapı", "döşeme"],
            ["kamiq", "premium", "lodge", "standart", "döşeme"],
            ["kamiq", "premium", "lodge", "standart", "kapı", "döşeme"],
            ["kamiq", "premium", "suite", "opsiyonel", "döşeme"],
            ["kamiq", "premium", "suite", "opsiyonel", "kapı", "döşeme"],
            ["kamiq", "elite", "studio", "standart", "döşeme"],
            ["kamiq", "elite", "studio", "standart", "kapı", "döşeme"],
            ["kamiq", "monte", "carlo", "standart", "ön", "dekor"],
            ["kamiq", "premium", "lodge", "standart", "ön", "dekor"],
            ["kamiq", "premium", "suite", "opsiyonel", "ön", "dekor"],
            ["kamiq", "elite", "studio", "standart", "ön", "dekor"],
            ["kamiq", "monte", "carlo", "standart", "ön", "konsol"],
            ["kamiq", "premium", "lodge", "standart", "ön", "konsol"],
            ["kamiq", "premium", "suite", "opsiyonel", "ön", "konsol"],
            ["kamiq", "elite", "studio", "standart", "ön", "konsol"],
            ["kamiq", "monte", "carlo", "standart", "dijital", "gösterge", "paneli"],
            ["kamiq", "premium", "standart", "gösterge", "paneli"],
            ["kamiq", "elite", "standart", "gösterge", "paneli"],
            ["kamiq", "monte", "carlo", "standart", "multimedya", "sistemi"],
            ["kamiq", "premium", "standart", "multimedya", "sistemi"],
            ["kamiq", "elite", "standart", "multimedya", "sistemi"],
            ["kamiq", "monte", "carlo", "pji", "standart", "jant"],
            ["kamiq", "premium", "pjg", "standart", "jant"],
            ["kamiq", "1.0", "premium", "pj7", "opsiyonel", "jant"],
            ["kamiq", "premium", "pjg", "opsiyonel", "jant"],
            ["kamiq", "premium", "pjn", "opsiyonel", "jant"],
            ["kamiq", "premium", "pjp", "opsiyonel", "jant"],
            ["kamiq", "elite", "p02", "standart", "jant"],
            ["kamiq", "1.0", "elite", "pj7", "opsiyonel", "jant"],
            ["kamiq", "elite", "pjg", "opsiyonel", "jant"],
            ["kamiq", "elite", "pjp", "opsiyonel", "jant"],
            ["kamiq", "ay", "beyazı"],
            ["kamiq", "gümüş"],
            ["kamiq", "graptihe", "gri"],
            ["kamiq", "büyülü", "siyah"],
            ["kamiq", "kadife", "kırmızısı"],
            ["kamiq", "yarış", "mavisi"],
            ["kamiq", "phoenix", "turuncu"]
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
          "scala_custom"
          "kamiq_custom"
          None => default 7 aşamalı sort
        """
        if desired_group == "scala_custom":
            return self._custom_scala_sort(image_list)
        elif desired_group == "kamiq_custom":
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

        # 1) Asistan seçimi (Kamiq / Fabia / Scala)
        if user_id not in self.user_states:
            self.user_states[user_id] = {}  # boş dict oluştur

        assistant_id = self.user_states[user_id].get("assistant_id", None)

        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in user_message.lower() for k in keywords):
                assistant_id = aid
                self.user_states[user_id]["assistant_id"] = assistant_id
                break

        lower_msg = user_message.lower()

        # --------------------------------------------------------------------------------
        # 0) Kullanıcı "evet" derse ve pending_color_images varsa -> görselleri otomatik paylaş
        # --------------------------------------------------------------------------------
        if lower_msg.strip() in ["evet", "evet.", "evet!", "evet?", "evet,"]:
            pending_colors = self.user_states[user_id].get("pending_color_images", [])
            if pending_colors:
                # Asistan adını al
                if assistant_id is not None:
                    asst_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "scala")
                else:
                    asst_name = "scala"

                all_found_images = []
                for clr in pending_colors:
                    keywords = f"{asst_name} {clr}"  # "Scala ay beyazı" vb
                    results = self.image_manager.filter_images_multi_keywords(keywords)
                    all_found_images.extend(results)

                # Sıralama
                asst_lower = asst_name.lower()
                if asst_lower == "scala":
                    sorted_images = self._multi_group_sort(all_found_images, "scala_custom")
                elif asst_lower == "kamiq":
                    sorted_images = self._multi_group_sort(all_found_images, "kamiq_custom")
                else:
                    sorted_images = self._multi_group_sort(all_found_images, None)

                if not sorted_images:
                    yield "Bu renklerle ilgili görsel bulunamadı.\n".encode("utf-8")
                    return

                yield "<b>İşte seçtiğiniz renk görselleri:</b><br>".encode("utf-8")
                for img_file in sorted_images:
                    img_url = f"/static/images/{img_file}"
                    base_name, _ = os.path.splitext(img_file)
                    pretty_name = base_name.replace("_", " ")
                    yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                    yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

                self.user_states[user_id]["pending_color_images"] = []
                return

        # ---------------------------------------------------------
        # ÖZEL KONTROL: "fabia + premium + monte carlo" -> çift görsel karşılaştırma
        # ---------------------------------------------------------
        if ("fabia" in lower_msg
            and "premium" in lower_msg
            and "monte carlo" in lower_msg
            and self._is_image_request(user_message)):

            fabia_pairs = [
                ("Fabia_Premium_Ay_Beyazı.png", "Fabia_Monte_Carlo_Ay_Beyazı.png"),
                ("Fabia_Premium_Gümüş.png", "Fabia_Monte_Carlo_Gümüş.png"),
                ("Fabia_Premium_Graphite_Gri.png", "Fabia_Monte_Carlo_Graphite_Gri.png"),
                ("Fabia_Premium_Büyülü_Siyah.png", "Fabia_Monte_Carlo_Büyülü_Siyah.png"),
                ("Fabia_Premium_Phoenix_Turuncu.png", "Fabia_Monte_Carlo_Phoenix_Turuncu.png"),
                ("Fabia_Premium_Yarış_Mavisi.png", "Fabia_Monte_Carlo_Yarış_Mavisi.png"),
                ("Fabia_Premium_Kadife_Kırmızısı.png", "Fabia_Monte_Carlo_Kadife_Kırmızı.png"),
                ("Fabia_Premium_Gösterge_Paneli.png", "Fabia_Monte_Carlo_Gösterge_Paneli.png"),
                ("Fabia_Premium_Direksiyon_Simidi.png", "Fabia_Monte_Carlo_Direksiyon_Simidi.png"),
                ("Fabia_Premium_Suite_Kumaş_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Döşeme.png"),
                ("Fabia_Premium_Suite_Kumaş_Koltuk_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Koltuk_Döşeme.png"),
                ("Fabia_Premium_Suite_Kumaş_Ön_Dekor.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Ön_Dekor.png"),
                ("Fabia_Premium_Lodge_Kumaş_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Döşeme.png"),
                ("Fabia_Premium_Lodge_Kumaş_Koltuk_Döşemesi.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Koltuk_Döşeme.png"),
                ("Fabia_Premium_Lodge_Kumaş_Ön_Dekor.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Ön_Dekor.png"),
                ("Fabia_Premium_Dynamic_Suedia_Kumaş_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Döşeme.png"),
                ("Fabia_Premium_Dynamic_Suedia_Kumaş_Koltuk_Döşeme.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Koltuk_Döşeme.png"),
                ("Fabia_Premium_Dynamic_Suedia_Kumaş_Ön_Dekor.png", "Fabia_Monte_Carlo_Suedia_Kumaş_Ön_Dekor.png"),
                ("Fabia_Premium_Standart_PJ4_Proxima_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
                ("Fabia_Premium_Opsiyonel_PJ9_Procyon_Aero_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
                ("Fabia_Premium_Opsiyonel_PX0_Urus_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
                ("Fabia_Premium_ve_Monte_Carlo_Opsiyonel_PJF_Libra_Jant.png", "Fabia_Monte_Carlo_Standart_PJE_Procyon_Jant.png"),
            ]

            yield "<div style='display: flex; flex-direction: column; gap: 15px;'>".encode("utf-8")

            for left_img, right_img in fabia_pairs:
                left_url = f"/static/images/{left_img}"
                right_url = f"/static/images/{right_img}"
                left_title = left_img.replace("_", " ").replace(".png", "")
                right_title = right_img.replace("_", " ").replace(".png", "")

                html_pair = f"""
                <div style="display: flex; flex-direction: row; align-items: center; gap: 20px;">
                  <img src="{left_url}" alt="{left_title}" style="max-width: 300px;" />
                  <img src="{right_url}" alt="{right_title}" style="max-width: 300px;" />
                </div>
                """
                yield html_pair.encode("utf-8")

            yield "</div>".encode("utf-8")
            return

        # 2-a) Diğer görsel istek akışı
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

            # Sıralama isteği
            if "scala görsel" in lower_msg:
                desired_group = "scala_custom"
            elif "kamiq görsel" in lower_msg:
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

        # 6) (Örnek) OpenAI Chat'te işlem (demo/dummy)
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
            assistant_response = ""

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                if run.status == "completed":
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            content = str(msg.content)
                            content_md = self.markdown_processor.transform_text_to_markdown(content)
                            assistant_response = content  # ham cevabı saklıyoruz
                            yield content_md.encode("utf-8")
                    break
                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            if not assistant_response:
                yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")
                return

            # 7) Asistan cevabında "görsel olarak görmek ister misiniz?" vb. kontrol
            if "görsel olarak görmek ister misiniz?" in assistant_response.lower():
                detected_colors = parse_color_names(assistant_response)  # ["ay beyazı", "gümüş", ...]
                if detected_colors:
                    self.user_states[user_id]["pending_color_images"] = detected_colors

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    # -------------------------------------------
    # Yardımcı fonksiyonlar
    # -------------------------------------------
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
