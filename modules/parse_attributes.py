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

        :param messages: List of Message objects with content to process.
        :return: A formatted dictionary with attributes and related images.
        """
        formatted_response = {}

        for message in messages:
            if message.role == "assistant":
                for content_block in message.content:
                    if content_block.type == "text":
                        raw_text = content_block.text.value
                        formatted_response.update(self._parse_message_text(raw_text))

        return formatted_response

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

    def parse_data(self, data):
        """
        Determines the appropriate parsing method based on the structure of the JSON data.

        :param data: JSON data containing attributes and details.
        :return: Parsed data in the required format.
        """
        if isinstance(data, dict) and any(isinstance(value, list) for value in data.values()):
            # If the data is a dictionary with lists of objects, use parse_table_data
            return self.parse_table_data(data)
        elif isinstance(data, dict):
            # If the data is a nested dictionary, use parse_nested_structure
            return self.parse_nested_structure(data)
        else:
            raise ValueError("Unsupported data structure")


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
                            try:
                                if isinstance(value, str):
                                    matching_images = self.image_paths.find_similar_images(value)
                                    for name, path in matching_images:
                                        row["Resim"].append({"name": name, "path": path})
                                    break
                            except Exception as e:
                                print(e)
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
