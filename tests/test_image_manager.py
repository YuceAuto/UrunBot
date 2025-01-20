import unittest
import os
from unittest.mock import patch, mock_open
from modules.image_manager import ImageManager
from PIL import Image
import matplotlib.pyplot as plt

os.environ["TEST_ENV"] = "true"
STATIC_DIR = os.path.join(os.getcwd(), 'static')

class TestImageManager(unittest.TestCase):

    def setUp(self):
        """
        Initialize the ImageManager instance for testing.
        """
        self.test_images_folder = "test_images"
        self.image_manager = ImageManager(images_folder=self.test_images_folder)

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=[STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", STATIC_DIR+"image/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png"])
    def test_load_images(self, mock_listdir, mock_exists):
        """
        Test loading images from a directory.
        """

        self.image_manager.load_images()
        self.assertEqual(len(self.image_manager.image_files), 1)
        self.assertIn(STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", self.image_manager.image_files)
        self.assertIn(STATIC_DIR+"image/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", self.image_manager.image_files)
        self.assertIn(STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png", self.image_manager.image_files)

    @patch("os.path.exists", return_value=False)
    def test_load_images_folder_not_found(self, mock_exists):
        """
        Test loading images when the folder does not exist.
        """
        with self.assertRaises(FileNotFoundError):
            self.image_manager.load_images()

    @patch("os.listdir", return_value=[STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", STATIC_DIR+"image/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png"])
    def test_filter_images_multi_keywords(self, mock_listdir):
        """
        Test filtering images based on multiple keywords.
        """
        self.image_manager.image_files = [STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", STATIC_DIR+"image/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png"]

        self.image_manager.load_images()
        keywords = "fabia beyaz"
        result = self.image_manager.filter_images_multi_keywords(keywords)
        self.assertEqual(len(result), 1)  # Expecting "kamiq_red.jpg"
        self.assertIn(STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", result)

        self.image_manager.load_images()
        keywords = "kamiq premium lodge kapı"
        result = self.image_manager.filter_images_multi_keywords(keywords)
        self.assertEqual(len(result), 1)  # Expecting "kamiq_red.jpg"
        self.assertIn(STATIC_DIR+"image/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", result)

        self.image_manager.load_images()
        keywords = "scala monte carlo kapı"
        result = self.image_manager.filter_images_multi_keywords(keywords)
        self.assertEqual(len(result), 1)  # Expecting "kamiq_red.jpg"
        self.assertIn(STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png", result)

    @patch("os.listdir", return_value=[STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", STATIC_DIR+"image/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png"])
    def test_filter_images_with_stopwords(self, mock_listdir):
        """
        Test filtering images while ignoring stopwords.
        """
        self.image_manager.image_files = [STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", STATIC_DIR+"images/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png"]

        self.image_manager.load_images()
        keywords = "fabia model beyaz"
        result = self.image_manager.filter_images_multi_keywords(keywords)
        self.assertEqual(len(result), 1)  # Expecting "kamiq_red.jpg"
        self.assertIn(STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", result)

    @patch("PIL.Image.open")
    @patch("matplotlib.pyplot.show")
    def test_display_images(self, mock_show, mock_open):
        """
        Test displaying images using matplotlib.
        """
        with patch("os.path.exists", return_value=True):
            test_images = [STATIC_DIR+"images/Fabia_Monte_Carlo_Ay_Beyazı.png", STATIC_DIR+"images/Kamiq_Premium_Lodge_Standart_Kapı_Döşeme.png", STATIC_DIR+"images/Scala_Monte_Carlo_Kapı_Döşeme.png"]
            self.image_manager.display_images(test_images)

            self.assertEqual(mock_open.call_count, 2)
            self.assertEqual(mock_show.call_count, 2)

if __name__ == "__main__":
    unittest.main()
