import os
import time
import logging
import re
import openai
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv

from modules.image_manager import ImageManager
from modules.markdown_utils import MarkdownProcessor
from modules.config import Config
from modules.utils import Utils
from modules.db import create_tables, save_to_db, send_email

import secrets

# EKLENDİ: Scala, Kamiq ve Fabia tabloları
from modules.scala_data import (
    SCALA_ELITE_MD,
    SCALA_PREMIUM_MD,
    SCALA_MONTE_CARLO_MD
)
from modules.kamiq_data import (
    KAMIQ_ELITE_MD,
    KAMIQ_PREMIUM_MD,
    KAMIQ_MONTE_CARLO_MD
)
from modules.fabia_data import (
    FABIA_PREMIUM_MD,
    FABIA_MONTE_CARLO_MD
)

load_dotenv()

class ChatbotAPI:
    def __init__(self, logger=None, static_folder='static', template_folder='templates'):
        self.app = Flask(
            __name__,
            static_folder=os.path.join(os.getcwd(), static_folder),
            template_folder=os.path.join(os.getcwd(), template_folder)
        )
        CORS(self.app)

        # Session için secret key
        self.app.secret_key = secrets.token_hex(16)

        self.logger = logger if logger else self._setup_logger()

        # MSSQL tabloyu oluşturma
        create_tables()

        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai

        self.config = Config()
        self.utils = Utils()

        self.image_manager = ImageManager(images_folder=os.path.join(static_folder, "images"))
        self.image_manager.load_images()

        self.markdown_processor = MarkdownProcessor()

        self.ASSISTANT_CONFIG = self.config.ASSISTANT_CONFIG
        self.ASSISTANT_NAME_MAP = self.config.ASSISTANT_NAME_MAP

        # Session timeout
        self.SESSION_TIMEOUT = 30 * 60  # 30 dakika

        self.user_states = {}

        self._define_routes()

    def _setup_logger(self):
        logger = logging.getLogger("ChatbotAPI")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _define_routes(self):
        @self.app.route("/", methods=["GET"])
        def home():
            # Session reset
            session.pop('last_activity', None)
            return render_template("index.html")

        @self.app.route("/ask", methods=["POST"])
        def ask():
            return self._ask()

        @self.app.route("/check_session", methods=["GET"])
        def check_session():
            if 'last_activity' in session:
                now = time.time()
                if now - session['last_activity'] > self.SESSION_TIMEOUT:
                    return jsonify({"active": False})
            return jsonify({"active": True})

    def _ask(self):
        """
        /ask endpoint -> Kullanıcı sorusu -> _generate_response
        """
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

        if 'last_activity' not in session:
            session['last_activity'] = time.time()

        response_generator = self._generate_response(user_message, user_id)
        return self.app.response_class(response_generator, mimetype="text/plain")

    #
    # EKLENDİ: Yazım hatalarını düzeltme fonksiyonu
    #
    def _correct_typos(self, user_message):
        """
        Kullanıcının "premium", "elite", "monte carlo" kelimelerini 
        %70 benzerlik ile düzeltir.
        """
        # 'monte carlo' 2 kelime olduğundan, basit yaklaşımda 
        # 'monte' ve 'carlo' olarak check edelim, sonra birleştirebiliriz.
        known_words = ["premium", "elite", "monte", "carlo"]

        splitted = user_message.split()
        new_tokens = []

        for token in splitted:
            best = self.utils.fuzzy_find(token, known_words, threshold=0.7)
            if best:
                new_tokens.append(best)
            else:
                new_tokens.append(token)

        # "monte"+"carlo" => "monte carlo"
        combined_tokens = []
        skip_next = False

        for i in range(len(new_tokens)):
            if skip_next:
                skip_next = False
                continue

            if i < len(new_tokens) - 1:
                if new_tokens[i].lower() == "monte" and new_tokens[i+1].lower() == "carlo":
                    combined_tokens.append("monte carlo")
                    skip_next = True
                else:
                    combined_tokens.append(new_tokens[i])
            else:
                combined_tokens.append(new_tokens[i])

        return " ".join(combined_tokens)

    def _generate_response(self, user_message, user_id):
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")

        if user_id not in self.user_states:
            self.user_states[user_id] = {}

        # 1) Önce yazım hatalarını düzeltelim
        corrected_message = self._correct_typos(user_message)
        self.logger.info(f"Düzeltilmiş mesaj: {corrected_message}")
        user_message = corrected_message

        # 2) Daha önce atanmış asistan?
        assistant_id = self.user_states[user_id].get("assistant_id", None)

        # Asistan seçimi (yeni bir model adı geçiyorsa override)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in user_message.lower() for k in keywords):
                assistant_id = aid
                self.user_states[user_id]["assistant_id"] = assistant_id
                break

        lower_msg = user_message.lower()

        # Eklendi: "opsiyonel" geçiyor ama model ismi (kamiq/fabia/scala) geçmiyorsa
        # ve user_states'te halihazırda assistant_id varsa => 
        # sanki user "xx model opsiyonel" demiş gibi kabul et.
        if "opsiyonel" in lower_msg:
            no_model_mentioned = not any(x in lower_msg for x in ["kamiq", "fabia", "scala"])
            if no_model_mentioned and assistant_id:
                model_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "").lower()
                if model_name in ["kamiq", "fabia", "scala"]:
                    user_message = f"{model_name} opsiyonel"
                    lower_msg = user_message.lower()

        # ---------------------------------------------------------
        # 1) Fabia opsiyonel tablolar
        # ---------------------------------------------------------
        if "fabia" in lower_msg and "opsiyonel" in lower_msg:
            if "premium" in lower_msg:
                save_to_db(user_id, user_message, "Fabia Premium opsiyonel donanım tablosu döndürüldü.")
                yield FABIA_PREMIUM_MD.encode("utf-8")
                return
            elif "monte carlo" in lower_msg:
                save_to_db(user_id, user_message, "Fabia Monte Carlo opsiyonel donanım tablosu döndürüldü.")
                yield FABIA_MONTE_CARLO_MD.encode("utf-8")
                return
            else:
                yield ("Fabia modelinde hangi donanımın opsiyonel bilgilerini görmek istersiniz? "
                       "(Premium / Monte Carlo)\n").encode("utf-8")
                return

        # ---------------------------------------------------------
        # 2) Kamiq opsiyonel tablolar
        # ---------------------------------------------------------
        if "kamiq" in lower_msg and "opsiyonel" in lower_msg:
            if "elite" in lower_msg:
                save_to_db(user_id, user_message, "Kamiq Elite opsiyonel donanım tablosu döndürüldü.")
                yield KAMIQ_ELITE_MD.encode("utf-8")
                return
            elif "premium" in lower_msg:
                save_to_db(user_id, user_message, "Kamiq Premium opsiyonel donanım tablosu döndürüldü.")
                yield KAMIQ_PREMIUM_MD.encode("utf-8")
                return
            elif "monte carlo" in lower_msg:
                save_to_db(user_id, user_message, "Kamiq Monte Carlo opsiyonel donanım tablosu döndürüldü.")
                yield KAMIQ_MONTE_CARLO_MD.encode("utf-8")
                return
            else:
                yield ("Kamiq modelinde hangi donanımın opsiyonel bilgilerini görmek istersiniz? "
                       "(Elite / Premium / Monte Carlo)\n").encode("utf-8")
                return

        # ---------------------------------------------------------
        # 3) Scala opsiyonel tablolar
        # ---------------------------------------------------------
        if "scala" in lower_msg and "opsiyonel" in lower_msg:
            if "elite" in lower_msg:
                save_to_db(user_id, user_message, "Scala Elite opsiyonel donanım tablosu döndürüldü.")
                yield SCALA_ELITE_MD.encode("utf-8")
                return
            elif "premium" in lower_msg:
                save_to_db(user_id, user_message, "Scala Premium opsiyonel donanım tablosu döndürüldü.")
                yield SCALA_PREMIUM_MD.encode("utf-8")
                return
            elif "monte carlo" in lower_msg:
                save_to_db(user_id, user_message, "Scala Monte Carlo opsiyonel donanım tablosu döndürüldü.")
                yield SCALA_MONTE_CARLO_MD.encode("utf-8")
                return
            else:
                yield ("Hangi donanım için opsiyonel donanımları görmek istersiniz? "
                       "(Elite / Premium / Monte Carlo)\n").encode("utf-8")
                return

        # Asistan adı (renk/görsel vb. logic)
        assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
        trimmed_msg = user_message.strip().lower()

        # 4) Kullanıcı "evet" derse -> pending_color_images
        if trimmed_msg in ["evet", "evet.", "evet!", "evet?", "evet,"]:
            pending_colors = self.user_states[user_id].get("pending_color_images", [])
            if pending_colors:
                asst_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "scala") if assistant_id else "scala"

                all_found_images = []
                for clr in pending_colors:
                    keywords = f"{asst_name} {clr}"
                    results = self.image_manager.filter_images_multi_keywords(keywords)
                    all_found_images.extend(results)

                if asst_name.lower() == "scala":
                    sorted_images = self.utils.multi_group_sort(all_found_images, "scala_custom")
                elif asst_name.lower() == "kamiq":
                    sorted_images = self.utils.multi_group_sort(all_found_images, "kamiq_custom")
                else:
                    sorted_images = self.utils.multi_group_sort(all_found_images, None)

                if not sorted_images:
                    save_to_db(user_id, user_message, "Bu renklerle ilgili görsel bulunamadı.")
                    yield "Bu renklerle ilgili görsel bulunamadı.\n".encode("utf-8")
                    return

                save_to_db(user_id, user_message, "Renk görselleri listelendi (evet).")
                yield "<b>İşte seçtiğiniz renk görselleri:</b><br>".encode("utf-8")
                for img_file in sorted_images:
                    img_url = f"/static/images/{img_file}"
                    base_name, _ = os.path.splitext(img_file)
                    pretty_name = base_name.replace("_", " ")
                    yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                    yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

                self.user_states[user_id]["pending_color_images"] = []
                return

        # 5) Özel kontrol: fabia + premium + monte carlo + görsel karşılaştırma
        if ("fabia" in lower_msg
            and "premium" in lower_msg
            and "monte carlo" in lower_msg
            and self.utils.is_image_request(user_message)):

            fabia_pairs = [
                ("Fabia_Premium_Ay_Beyazı.png", "Fabia_Monte_Carlo_Ay_Beyazı.png"),
                # ek eşleştirmeler
            ]
            save_to_db(user_id, user_message, "Fabia + Premium + Monte Carlo karşılaştırma gösterildi.")
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

        # 6) Görsel isteği mi?
        if self.utils.is_image_request(user_message):
            if not assistant_id:
                save_to_db(user_id, user_message, "Henüz asistan seçilmedi, görsel yok.")
                yield "Henüz bir asistan seçilmediği için görsel gösteremiyorum.\n".encode("utf-8")
                return

            if not assistant_name:
                save_to_db(user_id, user_message, "Asistan adını bulamadım.")
                yield "Asistan adını bulamadım.\n".encode("utf-8")
                return

            keyword = self.utils.extract_image_keyword(user_message, assistant_name)
            if keyword:
                full_filter = f"{assistant_name} {keyword}"
            else:
                full_filter = assistant_name

            found_images = self.image_manager.filter_images_multi_keywords(full_filter)
            if not found_images:
                save_to_db(user_id, user_message, f"'{full_filter}' için görsel yok.")
                yield f"'{full_filter}' için uygun bir görsel bulamadım.\n".encode("utf-8")
                return

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

            sorted_images = self.utils.multi_group_sort(found_images, desired_group)
            save_to_db(user_id, user_message, f"{len(sorted_images)} görsel bulundu ve listelendi.")

            for img_file in sorted_images:
                img_url = f"/static/images/{img_file}"
                base_name, _ = os.path.splitext(img_file)
                pretty_name = base_name.replace("_", " ")
                yield f"<h4>{pretty_name}</h4>\n".encode("utf-8")
                yield f'<img src="{img_url}" alt="{pretty_name}" style="max-width:300px; margin:5px;" />\n'.encode("utf-8")

            return

        # 7) Normal Chat (OpenAI)
        if not assistant_id:
            save_to_db(user_id, user_message, "Uygun asistan bulunamadı.")
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

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
                            assistant_response = content
                            yield content_md.encode("utf-8")
                    break
                elif run.status == "failed":
                    save_to_db(user_id, user_message, "Yanıt oluşturulamadı.")
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            if not assistant_response:
                save_to_db(user_id, user_message, "Zaman aşımı.")
                yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")
                return

            save_to_db(user_id, user_message, assistant_response)

            if "görsel olarak görmek ister misiniz?" in assistant_response.lower():
                detected_colors = self.utils.parse_color_names(assistant_response)
                if detected_colors:
                    self.user_states[user_id]["pending_color_images"] = detected_colors

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            save_to_db(user_id, user_message, f"Hata: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    def run(self, debug=True):
        self.app.run(debug=debug)
