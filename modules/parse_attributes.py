import json
import logging
from modules.image_paths import ImagePaths, load_all_images  # Import the necessary modules

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
        :return: A formatted string with the attributes and their images.
        """
        formatted_response = ""

        for json_key, display_label in self.attribute_mappings:
            try:
                items = parsed_json.get(json_key, [])
                if items:
                    formatted_response += f"{display_label}:
"
                    for item in items:
                        formatted_response += f"- {item}
"
                        matching_images = self.image_paths.find_similar_images(item)
                        for name, path in matching_images:
                            formatted_response += f"  [Image: {name}]({path})
"
                    formatted_response += "\n"
            except Exception as e:
                logging.error(f"Error processing attribute '{json_key}': {str(e)}")

        return formatted_response

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