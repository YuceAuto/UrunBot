# python -m unittest test_attribute_parser.py
# python -m unittest discover -s modules/test

import os
import unittest
from modules.image_paths import ImagePaths
from modules.parse_attributes import AttributeParser

ASSET_DIR = "static/images"

class MockImagePaths:
    def find_similar_images(self, keyword):
        asset_dir=os.path.abspath(ASSET_DIR)
        return [
            (f"Fabia Monte Carlo Standart Suedia Kumaş Koltuk Döşeme", asset_dir+f"\\fabia\\Fabia Monte Carlo Standart Suedia Kumaş Koltuk Döşeme.png"),
            (f"Kamiq Monte Carlo Direksiyon Simidi", asset_dir+f"\\kamiq\\Kamiq Monte Carlo Direksiyon Simidi.png"),
            (f"Scala Premium Suite Opsiyonel Döşeme", asset_dir+f"\\scala\\Scala Premium Suite Opsiyonel Döşeme.png")
        ]
class MockMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content

class TestAttributeParser(unittest.TestCase):
        
    def setUp(self):
        self.mock_image_paths = MockImagePaths()
        self.parser = AttributeParser(self.mock_image_paths)

    def test_parse_and_format_attributes(self):
        asset_dir=os.path.abspath(ASSET_DIR)
        parsed_json = {
            "Renk Seçenekleri": ["Kırmızı", "Siyah"],
            "Jant": ["16\" Alaşım"]
        }
        expected_output = {
            "Renkler": [
                {"name": "Kırmızı", "images": [
                    {"name": "Fabia Monte Carlo Ay Beyazı", "path": asset_dir+"\\fabia\\Fabia Monte Carlo Ay Beyazı.png"},
                    {"name": "Kamiq Büyülü Siyah", "path": asset_dir+"\\kamiq\\Kamiq Büyülü Siyah.png"},
                    {"name": "Scala Yarış Mavisi", "path": asset_dir+"\\scala\\Scala Yarış Mavisi.png"}
                ]},
                {"name": "Siyah", "images": [
                    {"name": "Fabia Premium Büyülü Siyah", "path": asset_dir+"\\fabia\\Fabia Premium Büyülü Siyah.png"},
                    {"name": "Kamiq Büyülü Siyah", "path": asset_dir+"\\kamiq\\Kamiq Büyülü Siyah.png"},
                    {"name": "Scala Büyülü Siyah", "path": asset_dir+"\\scala\\Scala Büyülü Siyah.png"}
                ]}
            ],
            "Jant": [
                {"name": "Jant", "images": [
                    {"name": "Fabia Premium Opsiyonel PJ9 Procyon Aero Jant", "path": asset_dir+"\\fabia\\Fabia Premium Opsiyonel PJ9 Procyon Aero Jant.png"},
                    {"name": "Kamiq Elite PJP Opsiyonel Jant", "path": asset_dir+"\\kamiq\\Kamiq Elite PJP Opsiyonel Jant.png"},
                    {"name": "Scala Premium PJ5 Standart Jant", "path": asset_dir+"\\scala\\Scala Premium PJ5 Standart Jant.png"}
                ]}
            ]
        }

        result = self.parser.parse_and_format_attributes(parsed_json)
        self.maxDiff = None
        self.assertEqual(result, expected_output)

    def test_parse_custom_message_format(self):
        messages = [
            MockMessage(
                "assistant",
                [{"type": "text", "text": {"value": "Renk Seçenekleri:\n- Kırmızı\n- Siyah"}}]
            )
        ]

        expected_output = {
            "response_html": "<p>Renk Seçenekleri:</p>\n<li>Kırmızı</li>\n<li>Siyah</li>"
        }

        result = self.parser.parse_custom_message_format(messages)
        self.assertEqual(result, expected_output)

    def test_markdown_table_to_html(self):
        md_table = "| Name  | Age |\n|-------|-----|\n| Alice | 30  |\n| Bob   | 25  |"
        expected_html = (
            '<table class="table table-bordered table-sm my-blue-table">\n'
            '<thead><tr><th>Name</th><th>Age</th></tr></thead>\n'
            '<tbody>\n'
            '<tr><td>Alice</td><td>30</td></tr>\n'
            '<tr><td>Bob</td><td>25</td></tr>\n'
            '</tbody>\n</table>'
        )

        result = self.parser.markdown_table_to_html(md_table)
        self.assertEqual(result, expected_html)

    def test_parse_nested_structure(self):
        nested_json = {
            "Car": {
                "Make": "Skoda",
                "Models": [
                    {"Name": "Kamiq", "Type": "SUV"},
                    {"Name": "Octavia", "Type": "Sedan"}
                ]
            }
        }

        expected_output = [
            ("Car->Make", "Skoda"),
            ("Car->Models->[0]->Name", "Kamiq"),
            ("Car->Models->[0]->Type", "SUV"),
            ("Car->Models->[1]->Name", "Octavia"),
            ("Car->Models->[1]->Type", "Sedan")
        ]

        result = self.parser.parse_nested_structure(nested_json)
        self.assertEqual(result, expected_output)

    def test_parse_data(self):
        # Test for JSON input
        json_data = {
            "Renk Seçenekleri": ["Kırmızı", "Siyah"],
            "Jant": ["Fabia Premium Opsiyonel PX0 Urus Jant"]
        }
        result = self.parser.parse_data(json_data)
        self.assertTrue("Renkler" in result)
        self.assertTrue("Jant" in result)

        # Test for messages input
        messages = [
            MockMessage(
                "assistant",
                [{"type": "text", "text": {"value": "Renk Seçenekleri:\n- Kırmızı\n- Siyah"}}]
            )
        ]
        result = self.parser.parse_data(messages)
        self.assertTrue("response_html" in result)

if __name__ == "__main__":
    unittest.main()
