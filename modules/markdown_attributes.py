import os
import time
import logging
import re

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai

load_dotenv()

class MarkdownAttributes():

    def extract_markdown_tables_from_text(text):
        """
        Verilen text içinde '|' içeren satırları bularak potansiyel Markdown tablo satırlarını döndürür.
        Birden fazla tablo varsa, ardışık satırlara göre ayırır.
        """
        lines = text.splitlines()
        tables = []
        current_table = []

        for line in lines:
            if '|' in line.strip():
                current_table.append(line)
            else:
                if current_table:
                    tables.append('\n'.join(current_table))
                    current_table = []
        if current_table:
            tables.append('\n'.join(current_table))

        return tables

    def markdown_table_to_html(md_table_str):
        """
        Basit bir Markdown tabloyu HTML'e dönüştürür; tablo arka planı .my-blue-table ile mavi yapılır.
        """
        lines = md_table_str.strip().split("\n")
        if len(lines) < 2:
            return f"<p>{md_table_str}</p>"
        
        header_cols = [col.strip() for col in lines[0].split("|") if col.strip()]
        body_lines = lines[2:]  # 2. satır ayraç olduğu için atlıyoruz

        html = '<table class="table table-bordered table-sm my-blue-table">\n'
        html += '<thead><tr>'
        for col in header_cols:
            html += f'<th>{col}</th>'
        html += '</tr></thead>\n<tbody>\n'

        for line in body_lines:
            row = line.strip()
            if not row:
                continue
            cols = [c.strip() for c in row.split("|") if c.strip()]
            html += '<tr>'
            for c in cols:
                html += f'<td>{c}</td>'
            html += '</tr>\n'

        html += '</tbody>\n</table>'
        return html

    def _generate_response(self, user_message, user_id):
        self.logger.info(f"Kullanıcı ({user_id}) mesajı: {user_message}")

        # Kullanıcının mesajındaki anahtar kelimeler doğrultusunda asistan seçimi
        assistant_id = self.user_states.get(user_id)
        for aid, keywords in self.ASSISTANT_CONFIG.items():
            if any(keyword.lower() in user_message.lower() for keyword in keywords):
                assistant_id = aid
                self.user_states[user_id] = assistant_id
                break

        if not assistant_id:
            yield "Uygun bir asistan bulunamadı.\n".encode("utf-8")
            return

        try:
            # Yeni bir thread oluştur
            thread = self.client.beta.threads.create(
                messages=[{"role": "user", "content": user_message}]
            )
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )

            yield "Yanıt hazırlanıyor...\n".encode("utf-8")

            start_time = time.time()
            timeout = 30  # 30 saniye bekleme

            while time.time() - start_time < timeout:
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

                if run.status == "completed":
                    # Asistan cevabı hazır
                    message_response = self.client.beta.threads.messages.list(thread_id=thread.id)
                    for msg in message_response.data:
                        if msg.role == "assistant":
                            # Orijinal içerik
                            content = str(msg.content)

                            # İSTERSENİZ SUNUCU TARAFINDA DA KÖŞELİ PARANTEZLERİ TEMİZLEYEBİLİRSİNİZ:
                            # content = re.sub(r'【.*?】', '', content)

                            # Tabloları bulup HTML'e dönüştürüp eklemek isterseniz:
                            pattern = r'value="([^"]+)"'
                            match = re.search(pattern, content)
                            if match:
                                extracted_text = match.group(1)
                                extracted_text = extracted_text.replace("\\n", "\n")
                                tables = extract_markdown_tables_from_text(extracted_text)

                                if tables:
                                    self.logger.info(f"Bulunan tablolar: {tables}")
                                    for i, tbl in enumerate(tables, 1):
                                        html_table = markdown_table_to_html(tbl)
                                        # Tabloyu HTML olarak chunk halinde gönderebiliriz:
                                        yield f"\n--- Tablo {i} (HTML) ---\n".encode("utf-8")
                                        yield html_table.encode("utf-8")
                                        yield b"\n"

                            # Son olarak orijinal cevabı da gönder
                            yield content.encode("utf-8")
                    return

                elif run.status == "failed":
                    yield "Yanıt oluşturulamadı.\n".encode("utf-8")
                    return

                time.sleep(0.5)

            # Zaman aşımı
            yield "Yanıt alma zaman aşımına uğradı.\n".encode("utf-8")

        except Exception as e:
            self.logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            yield f"Bir hata oluştu: {str(e)}\n".encode("utf-8")

    def _feedback(self):
        """
        Örnek bir feedback endpoint
        """
        try:
            data = request.get_json()
            self.logger.info(f"Geri bildirim alındı: {data}")
            return jsonify({"message": "Geri bildiriminiz için teşekkür ederiz!"})
        except Exception as e:
            self.logger.error(f"Geri bildirim hatası: {str(e)}")
            return jsonify({"error": "Bir hata oluştu."}), 500

    def run(self, debug=True):
        self.app.run(debug=debug)


if __name__ == "__main__":
    markdownattributes = MarkdownAttributes()
    markdownattributes.run(debug=True)