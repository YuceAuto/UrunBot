import unittest

from modules.chatbot import ChatbotAPI
from unittest.mock import MagicMock

class TestChatbotAPI(unittest.TestCase):
    def setUp(self):
        logger = MagicMock()
        self.chatbot = ChatbotAPI(logger)

    def test_select_assistant(self):
        user_message = "Scala görsel"
        user_id = "test_user"
        assistant_id = self.chatbot._select_assistant(user_message, user_id)
        self.assertEqual(assistant_id, "asst_njSG1NVgg4axJFmvVYAIXrpM")

    def test_image_request(self):
        self.assertTrue(self.chatbot._is_image_request("Lütfen bir resim gönderir misin?"))
        self.assertFalse(self.chatbot._is_image_request("Merhaba!"))

    def test_extract_image_keyword(self):
        result = self.chatbot._extract_image_keyword("Scala görsel paylaşabilir misin?", "Scala")
        self.assertEqual(result, "görsel paylaşabilir misin")
