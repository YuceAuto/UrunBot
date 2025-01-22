import re

class MarkdownProcessor:

    def __init__(self):
        pass
    
    # Helper function to convert numbers to Turkish text
    def number_to_turkish(self, n):
        numbers = {
            0: "sıfır", 1: "bir", 2: "iki", 3: "üç", 4: "dört", 5: "beş", 
            6: "altı", 7: "yedi", 8: "sekiz", 9: "dokuz", 10: "on", 
            20: "yirmi", 30: "otuz", 40: "kırk", 50: "elli", 
            60: "altmış", 70: "yetmiş", 80: "seksen", 90: "doksan"
        }
        if n < 10:
            return numbers[n]
        elif n < 100:
            tens, ones = divmod(n, 10)
            return numbers[tens * 10] + (" " + numbers[ones] if ones > 0 else "")
        elif n < 1000:
            hundreds, remainder = divmod(n, 100)
            return (numbers[hundreds] + " yüz" if hundreds > 1 else "yüz") + (" " + self.number_to_turkish(remainder) if remainder > 0 else "")
        elif n < 10000:
            thousands, remainder = divmod(n, 1000)
            return (numbers[thousands] + " bin" if thousands > 1 else "bin") + (" " + self.number_to_turkish(remainder) if remainder > 0 else "")
        else:
            return str(n)  # Larger numbers can be handled here if needed
    
    def transform_text_to_markdown(self, input_text):
        """
        Metni Markdown formatına dönüştürür.
        :param input_text: İşlenecek metin
        :return: HTML formatındaki metin
        """
        input_text = str(input_text).replace("\n","").replace("\\","")
        
        pattern = r'value="([^"]+)"'
        match = re.search(pattern, input_text)
        if match:
            extracted_text = match.group(1).replace("\\n", "\n")
            tables = self.extract_markdown_tables_from_text(extracted_text)
            if tables:
                self.logger.info(f"Bulunan tablolar: {tables}")
                for i, tbl in enumerate(tables, 1):
                    html_table = self.markdown_table_to_html(tbl)
                    yield f"\n--- Tablo {i} (HTML) ---\n".encode("utf-8")
                    yield html_table.encode("utf-8")
                    yield b"\n"
        
        
        pattern = r"value='((?:\\'|[^'])*)'"
        match = re.search(pattern, input_text)
        if match:
            input_text = match.group(1)
            print(input_text)
        else:
            pass
        # Satır bazında işleme
        lines = input_text.split('\n')
        transformed_lines = []
        for line in lines:
            stripped_line = line.strip()

            # Çift tırnak ve tek tırnak dönüşümleri
            stripped_line = re.sub(r"(\d)''(\d)", r'\1"\2', stripped_line)
            stripped_line = stripped_line.replace("\\'", "'")

            # Bold metin
            stripped_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped_line)

            # Başlıklar ve liste öğelerini HTML'ye dönüştürme
            if stripped_line.startswith('### '):
                transformed_lines.append(f"<h3>{stripped_line[4:]}</h3>")
            elif stripped_line.startswith('- '):
                transformed_lines.append(f"<li>{stripped_line[2:]}</li>")
            else:
                transformed_lines.append(f"{stripped_line}<br>")

        # HTML çıktısı için birleştir
        return ''.join(transformed_lines)

    def extract_markdown_tables_from_text(self, text):
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

    def fix_table_characters(self, table_markdown: str) -> str:
        fixed_lines = []
        lines = table_markdown.split('\n')
        for line in lines:
            if '|' not in line:
                fixed_lines.append(line)
                continue
            columns = line.split('|')
            fixed_columns = []
            for col in columns:
                col = col.strip()
                col = col.replace('**', '')
                col = re.sub(r'(\d)\'\'(\d)', r'\1/\2', col)
                col = re.sub(r'([A-Za-z])//([A-Za-z])', r"\1'\2", col)
                fixed_columns.append(col)
            fixed_line = ' | '.join(fixed_columns)
            fixed_lines.append(fixed_line)
        return '\n'.join(fixed_lines)

    def markdown_table_to_html(self, md_table_str):
        md_table_str = self.fix_table_characters(md_table_str)
        lines = md_table_str.strip().split("\n")
        if len(lines) < 2:
            return f"<p>{md_table_str}</p>"

        header_cols = [col.strip() for col in lines[0].split("|") if col.strip()]
        body_lines = lines[2:]

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