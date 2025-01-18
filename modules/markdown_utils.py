import re

class MarkdownProcessor:
    def transform_text_to_markdown(self, input_text):
        """
        Metni Markdown formatına dönüştürür.
        :param input_text: İşlenecek metin
        :return: Markdown formatındaki metin
        """
        lines = input_text.split('\n')
        transformed_lines = []
        for line in lines:
            stripped_line = line.strip()

            # Çift tırnak ve tek tırnak dönüşümleri
            stripped_line = re.sub(r"(\d)''(\d)", r"\1\"\2", stripped_line)
            stripped_line = stripped_line.replace("\\'", "'")

            # ** kelime ** veya **Kelime** biçimlendirmesi için kontrol
            stripped_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped_line)
            
            # PDF referanslarının kaldırılması
            stripped_line = re.sub(r"【.*?】", "", stripped_line).strip()

            # Noktalı paragrafları biçimlendirme
            if stripped_line.endswith(':'):
                stripped_line += ' '

            if stripped_line.startswith('- **') and stripped_line.endswith(':**'):
                heading_content = stripped_line.replace('- **', '').replace(':**', '').strip()
                transformed_lines.append(f'### {heading_content}')
            elif stripped_line.startswith('- '):
                bullet_content = stripped_line[2:]
                transformed_lines.append(f'- {bullet_content}')
            else:
                transformed_lines.append(stripped_line)
        return '\n'.join(transformed_lines)

    def extract_markdown_tables_from_text(self, text):
        """
        Metinden Markdown tablolarını çıkarır.
        :param text: Girdi metni
        :return: Tabloların bir listesi
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

    def fix_table_characters(self, table_markdown: str) -> str:
        """
        Markdown tablosundaki karakter hatalarını düzeltir.
        :param table_markdown: Girdi Markdown tablosu
        :return: Düzeltildiği tablo
        """
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
        """
        Markdown tablosunu HTML formatına dönüştürür.
        :param md_table_str: Markdown tablosu
        :return: HTML formatındaki tablo
        """
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