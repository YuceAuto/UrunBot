import os
import logging

class ImagePaths:
    """
    A class to manage a dictionary of image names and their paths.
    """

    def __init__(self, asset_dir="static/images", logger=None):
        """
        Initialize the ImagePaths class.

        :param asset_dir: Root directory for images.
        :param logger: Optional logger instance.
        """
        self.asset_dir = os.path.abspath(asset_dir)
        self._images = {}
        self.logger = logger or self._setup_logger()
        self.load_images()

    def _setup_logger(self):
        """Set up a logger for ImagePaths."""
        logger = logging.getLogger("ImagePaths")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def add_image(self, name, path):
        """
        Add or update an image entry in the dictionary.

        :param name: Name or key for the image.
        :param path: The file path to the image.
        :raises FileNotFoundError: If the specified file does not exist.
        """
        abs_path = os.path.abspath(path)
        if not os.path.isfile(abs_path):
            self.logger.warning(f"File not found: {abs_path}")
            raise FileNotFoundError(f"The file '{abs_path}' does not exist.")
        self._images[name] = abs_path
        self.logger.info(f"Added image: {name} -> {abs_path}")

    def get_image(self, name):
        """
        Retrieve the file path of an image by exact name.

        :param name: Name or key for the image.
        :return: The file path if found, or None if not found.
        """
        return self._images.get(name)

    def list_images(self):
        """
        Retrieve a copy of the entire dictionary of images.

        :return: A dictionary of all image entries (name -> path).
        """
        return dict(self._images)

    def find_similar_images(self, keyword):
        """
        Retrieve images whose names contain the given keyword (case-insensitive).

        :param keyword: The search keyword to look for in the image name.
        :return: A list of (name, path) tuples for matching images.
        """
        keyword_lower = keyword.lower()
        matches = [
            (name, path) for name, path in self._images.items()
            if keyword_lower in name.lower()
        ]
        self.logger.info(f"Found {len(matches)} matching images for keyword: '{keyword}'")
        return matches

    def load_images(self):
        """
        Load images dynamically from the predefined asset directory.
        """
        if not os.path.isdir(self.asset_dir):
            self.logger.warning(f"Asset directory not found: {self.asset_dir}")
            return

        for root, _, files in os.walk(self.asset_dir):
            for file in files:
                if file.endswith((".png", ".jpg", ".jpeg", ".gif")):
                    file_path = os.path.join(root, file)
                    image_name = os.path.splitext(os.path.basename(file_path))[0]
                    try:
                        self.add_image(image_name, file_path)
                    except FileNotFoundError as e:
                        self.logger.warning(str(e))

    def reload_images(self):
        """
        Clear and reload all images from the asset directory.
        """
        self._images.clear()
        self.load_images()
        self.logger.info("Reloaded all images from the asset directory.")


# Example Usage
if __name__ == "__main__":
    image_manager = ImagePaths()

    # Test adding an image
    try:
        image_manager.add_image("Test Image", "static/images/test_image.png")
    except FileNotFoundError:
        pass

    # List all images
    print("All Images:", image_manager.list_images())

    # Find similar images
    print("Matches for 'Fabia':", image_manager.find_similar_images("Fabia"))