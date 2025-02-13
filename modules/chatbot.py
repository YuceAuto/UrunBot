import os
import time
import logging
import re
import openai
import difflib  # Fuzzy matching
import queue    # Kuyruğumuz için
import threading  # Arka plan worker

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv

from modules.image_manager import ImageManager
from modules.markdown_utils import MarkdownProcessor
from modules.config import Config
from modules.utils import Utils
from modules.db import create_tables, save_to_db, send_email, get_db_connection

import secrets

# Fabia, Kamiq, Scala tabloları
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
        # Flask yapılandırması
        self.app = Flask(
            __name__,
            static_folder=os.path.join(os.getcwd(), static_folder),
            template_folder=os.path.join(os.getcwd(), template_folder)
        )
        CORS(self.app)

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

        # Asistan konfigürasyonları
        self.ASSISTANT_CONFIG = self.config.ASSISTANT_CONFIG
        self.ASSISTANT_NAME_MAP = self.config.ASSISTANT_NAME_MAP

        # Session timeout (30 dakika)
        self.SESSION_TIMEOUT = 30 * 60

        # Kullanıcı bazlı state: user_states => { user_id: {...} }
        self.user_states = {}

        # ----- Fuzzy Cache ve Queue -----
        # user_id -> list of { "question": str, "answer_bytes": bytes }
        self.fuzzy_cache = {}

        # DB'ye kaydı arka planda yapmak için FIFO kuyruk
        self.fuzzy_cache_queue = queue.Queue()

        # Arka plan worker thread kontrolü
        self.stop_worker = False
        self.worker_thread = threading.Thread(target=self._background_db_writer, daemon=True)
        self.worker_thread.start()

        # (Opsiyonel) DB'den önbelleğe veri yükleme
        # self._load_cache_from_db()

        # Flask route tanımları
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

    # ----------------------------------------------------------------
    # ARKA PLANDA DB'YE YAZAN THREAD
    # ----------------------------------------------------------------
    def _background_db_writer(self):
        """
        Kuyruğa eklenen (user_id, question, answer_bytes, tstamp) kayıtlarını
        arka planda DB'ye yazan worker.
        """
        self.logger.info("Background DB writer thread started.")
        while not self.stop_worker:
            try:
                record = self.fuzzy_cache_queue.get(timeout=5.0)  # 5 sn bekliyor
                if record is None:
                    continue
                (user_id, q_lower, ans_bytes, tstamp) = record

                # DB bağlantısı al
                conn = get_db_connection()
                cursor = conn.cursor()

                # Örnek tablo: cache_faq (id, user_id, question, answer, created_at)
                # created_at otomatik DATETIME veya GETDATE() vb. olabilir.
                sql = """
                INSERT INTO cache_faq (user_id, question, answer, created_at)
                VALUES (?, ?, ?, GETDATE())
                """
                cursor.execute(sql, (user_id, q_lower, ans_bytes.decode("utf-8")))
                conn.commit()
                conn.close()

                self.logger.info(f"[BACKGROUND] Kaydedildi -> {user_id}, {q_lower[:30]}...")
                self.fuzzy_cache_queue.task_done()

            except queue.Empty:
                # Süre doldu, yeni kayıt yok, tekrar dene
                pass
            except Exception as e:
                self.logger.error(f"[BACKGROUND] DB yazma hatası: {str(e)}")
                time.sleep(2)

        self.logger.info("Background DB writer thread stopped.")

    def _load_cache_from_db(self):
        """
        (Opsiyonel) Uygulama açılırken DB'den son X kaydı çekip, fuzzy_cache'e yükleyebilirsiniz.
        """
        self.logger.info("[_load_cache_from_db] Cache verileri DB'den yükleniyor...")

        conn = get_db_connection()
        cursor = conn.cursor()
        # Son 1000 kaydı alalım
        sql = """
        SELECT TOP 1000 user_id, question, answer
        FROM cache_faq
        ORDER BY id DESC
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            user_id = row[0]
            q_lower = row[1]
            ans_txt = row[2]
            ans_bytes = ans_txt.encode("utf-8")

            if user_id not in self.fuzzy_cache:
                self.fuzzy_cache[user_id] = []
            self.fuzzy_cache[user_id].append({
                "question": q_lower,
                "answer_bytes": ans_bytes
            })

        self.logger.info("[_load_cache_from_db] Tamamlandı.")

    # ----------------------------------------------------------------
    # FUZZY CACHE İŞLEMLERİ
    # ----------------------------------------------------------------
    def _find_fuzzy_cached_answer(self, user_id: str, new_question: str, threshold=0.8):
        """
        Soru benzerliğini arar. Yakın bir eşleşme varsa, answer_bytes'ı döndürür.
        Yoksa None döner.
        """
        if user_id not in self.fuzzy_cache:
            return None

        new_q_lower = new_question.strip().lower()
        best_ratio = 0.0
        best_answer = None

        for item in self.fuzzy_cache[user_id]:
            old_q = item["question"]  # lower saklıyoruz
            ratio = difflib.SequenceMatcher(None, new_q_lower, old_q).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_answer = item["answer_bytes"]

        if best_ratio >= threshold:
            return best_answer
        return None

    def _store_in_fuzzy_cache(self, user_id: str, question: str, answer_bytes: bytes):
        """
        Yanıtı bellek (self.fuzzy_cache) içine ekler, ardından DB'ye
        yazması için self.fuzzy_cache_queue'ye gönderir.
        """
        q_lower = question.strip().lower()
        if user_id not in self.fuzzy_cache:
            self.fuzzy_cache[user_id] = []

        self.fuzzy_cache[user_id].append({
            "question": q_lower,
            "answer_bytes": answer_bytes
        })

        # Kuyruğa da ekle
        record = (user_id, q_lower, answer_bytes, time.time())
        self.fuzzy_cache_queue.put(record)

    # ----------------------------------------------------------------
    # /ask ENDPOINT
    # ----------------------------------------------------------------
    def _ask(self):
        """
        /ask endpoint -> Kullanıcı sorusu -> Fuzzy cache kontrolü -> Gerekirse OpenAI/Tablo.
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

        # Session aktivite güncellemesi
        if 'last_activity' not in session:
            session['last_activity'] = time.time()
        else:
            session['last_activity'] = time.time()

        # 1) Fuzzy cache'te var mı diye kontrol
        cached_answer = self._find_fuzzy_cached_answer(user_id, user_message, threshold=0.8)
        if cached_answer:
            self.logger.info("Fuzzy cache match bulundu, önbellekten yanıt dönüyor.")
            return self.app.response_class(cached_answer, mimetype="text/plain")

        # 2) Yoksa cevap üret (generator). Bittiğinde cache'e ekle.
        def caching_generator():
            chunks = []
            for chunk in self._generate_response(user_message, user_id):
                chunks.append(chunk)
                yield chunk

            # Cevap parçaları bitti -> birleştirip cache'e yaz
            final_bytes = b"".join(chunks)
            self._store_in_fuzzy_cache(user_id, user_message, final_bytes)

        return self.app.response_class(caching_generator(), mimetype="text/plain")

    # ----------------------------------------------------------------
    # MESAJI DÜZELTME FONKSİYONU (TYPO CORRECTION)
    # ----------------------------------------------------------------
    def _correct_typos(self, user_message):
        """
        Kullanıcının "premium", "elite", "monte carlo" kelimelerini 
        %70 benzerlik ile düzelten örnek fonksiyon.
        """
        known_words = ["premium", "elite", "monte", "carlo"]

        splitted = user_message.split()
        new_tokens = []

        for token in splitted:
            best = self.utils.fuzzy_find(token, known_words, threshold=0.7)
            if best:
                new_tokens.append(best)
            else:
                new_tokens.append(token)

        # "monte" + "carlo" => "monte carlo"
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

    # ----------------------------------------------------------------
    # CEVAP OLUŞTURMA (GENERATOR)
    # ----------------------------------------------------------------
    def _generate_response(self, user_message, user_id):
        """
        Mevcut chatbot mantığınız: 
        - Yazım hatası düzeltme
        - Opsiyonel tablo kontrolü
        - Görsel istekleri
        - OpenAI (multi-turn) vb.
        """
        self.logger.info(f"[_generate_response] Kullanıcı ({user_id}): {user_message}")

        # user_states içinde yoksa ekliyoruz
        if user_id not in self.user_states:
            self.user_states[user_id] = {}

        # 1) Yazım hatalarını düzelt
        corrected_message = self._correct_typos(user_message)
        user_message = corrected_message
        lower_msg = user_message.lower()

        # 2) Assistant seçimi (model tayini)
        assistant_id = self.user_states[user_id].get("assistant_id", None)

        # Asistan konfigürasyonunda tanımlı anahtar kelimeler geçiyorsa assistant_id güncelle
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(k.lower() in lower_msg for k in keywords):
                assistant_id = aid
                self.user_states[user_id]["assistant_id"] = assistant_id
                break

        # "opsiyonel" geçiyor ama model belirtilmemiş ve user_states'te assistant_id varsa
        if "opsiyonel" in lower_msg:
            no_model_mentioned = not any(x in lower_msg for x in ["kamiq", "fabia", "scala"])
            if no_model_mentioned and assistant_id:
                model_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "").lower()
                if model_name in ["kamiq", "fabia", "scala"]:
                    user_message = f"{model_name} opsiyonel"
                    lower_msg = user_message.lower()

        #
        # -------------- OPSİYONEL TABLOLAR --------------
        #
        # 1) Fabia
        if "fabia" in lower_msg and "opsiyonel" in lower_msg:
            if "premium" in lower_msg:
                save_to_db(user_id, user_message, "Fabia Premium opsiyonel tablosu.")
                yield FABIA_PREMIUM_MD.encode("utf-8")
                return
            elif "monte carlo" in lower_msg:
                save_to_db(user_id, user_message, "Fabia Monte Carlo opsiyonel tablosu.")
                yield FABIA_MONTE_CARLO_MD.encode("utf-8")
                return
            else:
                yield (
                    "Fabia modelinde hangi donanımın opsiyonel bilgilerini görmek istersiniz? "
                    "(Premium / Monte Carlo)\n"
                ).encode("utf-8")
                return

        # 2) Kamiq
        if "kamiq" in lower_msg and "opsiyonel" in lower_msg:
            if "elite" in lower_msg:
                save_to_db(user_id, user_message, "Kamiq Elite opsiyonel tablosu.")
                yield KAMIQ_ELITE_MD.encode("utf-8")
                return
            elif "premium" in lower_msg:
                save_to_db(user_id, user_message, "Kamiq Premium opsiyonel tablosu.")
                yield KAMIQ_PREMIUM_MD.encode("utf-8")
                return
            elif "monte carlo" in lower_msg:
                save_to_db(user_id, user_message, "Kamiq Monte Carlo opsiyonel tablosu.")
                yield KAMIQ_MONTE_CARLO_MD.encode("utf-8")
                return
            else:
                yield (
                    "Kamiq modelinde hangi donanımın opsiyonel bilgilerini görmek istersiniz? "
                    "(Elite / Premium / Monte Carlo)\n"
                ).encode("utf-8")
                return

        # 3) Scala
        if "scala" in lower_msg and "opsiyonel" in lower_msg:
            if "elite" in lower_msg:
                save_to_db(user_id, user_message, "Scala Elite opsiyonel tablosu.")
                yield SCALA_ELITE_MD.encode("utf-8")
                return
            elif "premium" in lower_msg:
                save_to_db(user_id, user_message, "Scala Premium opsiyonel tablosu.")
                yield SCALA_PREMIUM_MD.encode("utf-8")
                return
            elif "monte carlo" in lower_msg:
                save_to_db(user_id, user_message, "Scala Monte Carlo opsiyonel tablosu.")
                yield SCALA_MONTE_CARLO_MD.encode("utf-8")
                return
            else:
                yield (
                    "Scala modelinde hangi donanımın opsiyonel bilgilerini görmek istersiniz? "
                    "(Elite / Premium / Monte Carlo)\n"
                ).encode("utf-8")
                return

        # Asistan adı
        assistant_name = self.ASSISTANT_NAME_MAP.get(assistant_id, "")
        trimmed_msg = user_message.strip().lower()

        # "evet" kontrolü -> pending_color_images
        if trimmed_msg in ["evet", "evet.", "evet!", "evet?", "evet,"]:
            pending_colors = self.user_states[user_id].get("pending_color_images", [])
            if pending_colors:
                asst_name = assistant_name.lower() if assistant_name else "scala"

                all_found_images = []
                for clr in pending_colors:
                    keywords = f"{asst_name} {clr}"
                    results = self.image_manager.filter_images_multi_keywords(keywords)
                    all_found_images.extend(results)

                # Sıralama (utils.multi_group_sort)
                if asst_name == "scala":
                    sorted_images = self.utils.multi_group_sort(all_found_images, "scala_custom")
                elif asst_name == "kamiq":
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

                # İş bittikten sonra pending temizle
                self.user_states[user_id]["pending_color_images"] = []
                return

        # Özel case: Fabia + Premium + Monte Carlo + görsel karşılaştırma
        if ("fabia" in lower_msg
            and "premium" in lower_msg
            and "monte carlo" in lower_msg
            and self.utils.is_image_request(user_message)):

            # Örnek resim çiftleri
            fabia_pairs = [
                ("Fabia_Premium_Ay_Beyazı.png", "Fabia_Monte_Carlo_Ay_Beyazı.png"),
                # İsterseniz ek resim çiftleri ekleyebilirsiniz...
            ]

            save_to_db(user_id, user_message, "Fabia Premium vs Monte Carlo görsel karşılaştırma.")
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

            # Gruplama seçimi
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

        # 7) Normal Chat (OpenAI) => Multi-turn
        if not assistant_id:
            save_to_db(user_id, user_message, "Uygun asistan bulunamadı.")
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        try:
            # user_states içinde thread_id var mı?
            if "thread_id" not in self.user_states[user_id]:
                # Yoksa yeni bir thread
                new_thread = self.client.beta.threads.create(
                    messages=[{"role": "user", "content": user_message}]
                )
                thread_id = new_thread.id
                self.user_states[user_id]["thread_id"] = thread_id
            else:
                # Varsa, mevcut thread_id üzerinde yeni mesaj
                thread_id = self.user_states[user_id]["thread_id"]
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=user_message
                )

            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )

            start_time = time.time()
            timeout = 30
            assistant_response = ""

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                if run.status == "completed":
                    msg_response = self.client.beta.threads.messages.list(thread_id=thread_id)
                    for msg in msg_response.data:
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

            # Mesajı DB'ye kaydet
            save_to_db(user_id, user_message, assistant_response)

            # Asistan cevabında "görsel olarak görmek ister misiniz?" geçiyorsa
            # Renk yakalama
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

    def shutdown(self):
        """
        Uygulama kapanırken background thread'i durdurur.
        """
        self.stop_worker = True
        self.worker_thread.join(5.0)
        self.logger.info("ChatbotAPI shutdown complete.")
