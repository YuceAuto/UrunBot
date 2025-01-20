import unittest
from flask import json
from app import ChatbotAPI

class TestChatbotAPI(unittest.TestCase):
    def setUp(self):
        """
        Test setup. Initializes the ChatbotAPI and test client.
        """
        self.chatbot_api = ChatbotAPI()
        self.client = self.chatbot_api.app.test_client()

    def test_home_route(self):
        """
        Test the home route for a successful response and correct content.
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'<title>SkodaBot</title>', response.data)

    def test_ask_with_valid_question(self):
        """
        Test the /ask endpoint with a valid question.
        """
        payload = {
            "question": "Tell me about Kamiq.",
            "user_id": "test_user"
        }
        response = self.client.post('/ask',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'Yanıt', response.data)

    def test_ask_with_empty_question(self):
        """
        Test the /ask endpoint with an empty question.
        """
        payload = {
            "question": "",
            "user_id": "test_user"
        }
        response = self.client.post('/ask',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'Please enter a question.', response.data)

    def test_ask_with_invalid_json(self):
        """
        Test the /ask endpoint with invalid JSON input.
        """
        response = self.client.post('/ask',
                                     data="Invalid JSON",
                                     content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn(f'Invalid JSON format.', response.data)

    def test_feedback_with_valid_data(self):
        """
        Test the /feedback endpoint with valid data.
        """
        payload = {
            "feedback": "Great bot!"
        }
        response = self.client.post('/feedback',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'Thank you for your feedback!', response.data)

    def test_feedback_with_invalid_data(self):
        """
        Test the /feedback endpoint with invalid data.
        """
        response = self.client.post('/feedback',
                                     data="Invalid JSON",
                                     content_type='application/json')
        self.assertEqual(response.status_code, 500)
        self.assertIn(f'An error occurred.', response.data)

if __name__ == '__main__':
    unittest.main()
