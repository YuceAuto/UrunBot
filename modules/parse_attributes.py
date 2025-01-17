import logging

class AttributeParser:
    """
    A class to parse and format attributes like colors, upholstery, decor, multimedia, and wheels.
    """

    def __init__(self, image_paths, config=None):
        """
        Initialize the AttributeParser with an instance of ImagePaths and optional configuration.

        :param image_paths: Instance of ImagePaths to retrieve matching images.
        :param config: Optional dictionary for customization or additional settings.
        """
        self.image_paths = image_paths
        self.config = config or {}

        # Load attribute mappings from configuration or default to hardcoded values
        self.attribute_mappings = self.config.get("attribute_mappings", [
            ("Renk Seçenekleri", "Renkler"),
            ("Döşemeler", "Döşeme"),
            ("Ön Dekor", "Dekor"),
            ("Multimedya", "Multimedya"),
            ("Jant", "Jant")
        ])

    def parse_and_format_attributes(self, parsed_json):
        """
        Parses and formats attributes from the provided JSON.

        :param parsed_json: The parsed JSON containing attributes.
        :return: A formatted dictionary with the attributes and their images.
        """
        formatted_response = {}

        for json_key, display_label in self.attribute_mappings:
            try:
                items = parsed_json.get(json_key, [])
                if items:
                    formatted_response[display_label] = []
                    for item in items:
                        item_entry = {"name": item, "images": []}
                        matching_images = self.image_paths.find_similar_images(item)
                        for name, path in matching_images:
                            item_entry["images"].append({"name": name, "path": path})
                        formatted_response[display_label].append(item_entry)
            except Exception as e:
                logging.error(f"Error processing attribute '{json_key}': {str(e)}")

        return formatted_response

    def parse_custom_message_format(self, messages):
        """
        Custom parser for handling the specific message structure provided.

        :param messages: List of message dictionaries with role and content keys.
        :return: A formatted dictionary with attributes, direct responses, and related images.
        """
        formatted_response = {}

        for message in messages:
            if message.get("role") == "assistant":
                for content_block in message.get("content", []):
                    if content_block.get("type") == "text":
                        raw_text = content_block.get("text", {}).get("value", "")

                        # If the content matches the desired format, send it directly
                        if self._is_direct_response(raw_text):
                            formatted_response = {"response_html": self._format_as_html(raw_text)}
                            return formatted_response

                        # Parse the text for attributes and related images
                        parsed_response = self._parse_message_text(raw_text)
                        if parsed_response:
                            formatted_response.update(parsed_response)

        return formatted_response

    def _is_direct_response(self, text):
        """
        Checks if the text matches a direct response with a bullet-pointed list format.

        :param text: Text content of the message.
        :return: Boolean indicating whether the text is a direct bullet-pointed response.
        """
        return "mevcut renk seçenekleri şunlardır" in text.lower() and any(
            line.strip().startswith("- ") for line in text.split("\n"))

    def _format_as_html(self, text):
        """
        Converts the provided text into a simple HTML format for display on the frontend.

        :param text: Raw text to format as HTML.
        :return: HTML-formatted string.
        """
        lines = text.split("\n")
        formatted_lines = []

        for line in lines:
            if line.strip().startswith("- "):
                formatted_lines.append(f"<li>{line.strip('- ').strip()}</li>")
            else:
                formatted_lines.append(f"<p>{line.strip()}</p>")

        return "\n".join(formatted_lines)

    def _parse_message_text(self, text):
        """
        Parses a single message text for attributes and related images.

        :param text: Text content of the message.
        :return: Dictionary with attributes and their related images.
        """
        parsed_response = {}

        for json_key, display_label in self.attribute_mappings:
            if json_key in text:
                parsed_response[display_label] = []
                items = self._extract_list_from_text(text)
                for item in items:
                    item_entry = {"name": item, "images": []}
                    matching_images = self.image_paths.find_similar_images(item)
                    for name, path in matching_images:
                        item_entry["images"].append({"name": name, "path": path})
                    parsed_response[display_label].append(item_entry)

        return parsed_response

    @staticmethod
    def _extract_list_from_text(text):
        """
        Extracts a list of items from bullet-pointed text.

        :param text: Text containing a list of items.
        :return: List of extracted items.
        """
        lines = text.split("\n")
        items = [line.strip("- ").strip() for line in lines if line.startswith("- ")]
        return items

    def extract_markdown_tables_from_text(self, text):
        """
        Extract potential Markdown tables from text by identifying lines with '|'.

        :param text: Text content to parse.
        :return: List of Markdown table strings.
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

    def markdown_table_to_html(self, md_table_str):
        """
        Converts a simple Markdown table to an HTML table.

        :param md_table_str: Markdown table string.
        :return: HTML string representing the table.
        """
        lines = md_table_str.strip().split("\n")
        if len(lines) < 2:
            return f"<p>{md_table_str}</p>"

        header_cols = [col.strip() for col in lines[0].split("|") if col.strip()]
        body_lines = lines[2:]  # Skip the separator line

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

    def parse_table_data(self, json_data):
        """
        Parses the provided JSON to prepare table data including images.

        :param json_data: JSON data containing attributes and details.
        :return: A list of dictionaries representing table rows.
        """
        table_data = []

        for key, values in json_data.items():
            if isinstance(values, list):
                for item in values:
                    if isinstance(item, dict):
                        row = {key: item.get(key, "N/A") for key in item}
                        row["Resim"] = []

                        # Find matching images for the first string attribute
                        for attr, value in item.items():
                            if isinstance(value, str):
                                matching_images = self.image_paths.find_similar_images(value)
                                for name, path in matching_images:
                                    row["Resim"].append({"name": name, "path": path})
                                break

                        table_data.append(row)

        return table_data

    def parse_nested_structure(self, data, path=None):
        """
        Recursively parses a nested dictionary-like structure and prints key-value pairs with their hierarchical paths.

        :param data: Dictionary or dictionary-like structure to parse.
        :param path: Current hierarchy path (used for recursion).
        :return: List of tuples containing (path, value).
        """
        if path is None:
            path = []

        results = []

        if isinstance(data, dict):
            for key, value in data.items():
                results.extend(self.parse_nested_structure(value, path + [key]))
        elif isinstance(data, list):
            for index, item in enumerate(data):
                results.extend(self.parse_nested_structure(item, path + [f"[{index}]"]))
        else:
            # Base case: leaf node
            results.append(("->".join(path), data))

        return results

    def parse_data(self, data):
        """
        Determines the appropriate parsing method based on the structure of the input.

        :param data: JSON data or a list of Message objects.
        :return: Parsed data in the required format.
        """
        if isinstance(data, list) and all(hasattr(item, 'role') and hasattr(item, 'content') for item in data):
            logging.debug("Data identified as a list of messages. Using parse_custom_message_format.")
            return self.parse_custom_message_format(data)
        elif isinstance(data, dict):
            if any(isinstance(value, list) for value in data.values()):
                logging.debug("Data identified as a dictionary with lists. Using parse_table_data.")
                return self.parse_table_data(data)
            else:
                logging.debug("Data identified as a nested dictionary. Using parse_nested_structure.")
                return self.parse_nested_structure(data)
        elif isinstance(data, str):
            logging.debug("Data identified as text. Extracting Markdown tables.")
            tables = self.extract_markdown_tables_from_text(data)
            return [self.markdown_table_to_html(table) for table in tables]
        else:
            logging.error("Unsupported data structure encountered.")
            raise ValueError("Unsupported data structure")

    def update_mappings(self, new_mappings):
        """
        Update the attribute mappings dynamically.

        :param new_mappings: List of tuples containing new mappings (json_key, display_label).
        """
        self.attribute_mappings = new_mappings

    def set_config(self, config):
        """
        Update the configuration for the AttributeParser.

        :param config: Dictionary containing configuration settings.
        """
        self.config.update(config)

        # Refresh attribute mappings if provided in the new config
        if "attribute_mappings" in config:
            self.attribute_mappings = config["attribute_mappings"]

    def get_config(self):
        """
        Retrieve the current configuration.

        :return: Dictionary containing the current configuration.
        """
        return self.config
