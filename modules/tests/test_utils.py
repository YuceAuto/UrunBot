import unittest

from modules.utils import Utils

class TestUtils(unittest.TestCase):
    def test_is_image_request(self):
        self.assertTrue(Utils._is_image_request("Fotoğraf gönder"))
        self.assertFalse(Utils._is_image_request("Merhaba"))

    def test_extract_image_keyword(self):
        self.assertEqual(Utils._extract_image_keyword("Kamiq resim paylaşır mısın?", "Kamiq"), "paylaşır mısın")
