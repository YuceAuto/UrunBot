import os
import re
from PIL import Image
import matplotlib.pyplot as plt

class ImageManager:
    def __init__(self, images_folder):
        self.images_folder = images_folder
        self.image_files = []

        self.stopwords = {
            "model", "araç", "arac", "paylaşabilir", "paylaşır",
            "misin", "mısın", "lütfen", "istiyorum", "?",
            "görsel", "resim", "fotoğraf", "fotograf",
        }

    def load_images(self):
        if not os.path.exists(self.images_folder):
            raise FileNotFoundError(f"'{self.images_folder}' klasörü bulunamadı.")

        valid_extensions = ('.png', '.jpg', '.jpeg')
        self.image_files = [
            f for f in os.listdir(self.images_folder)
            if f.lower().endswith(valid_extensions)
        ]

    def filter_images_multi_keywords(self, keywords_string: str):
        splitted_raw = keywords_string.lower().split()
        splitted = [word for word in splitted_raw if word not in self.stopwords]

        matched_files = []
        for img in self.image_files:
            img_lower = img.lower()
            if all(word in img_lower for word in splitted):
                matched_files.append(img)
        return matched_files

    def display_images(self, image_list):
        for image_name in image_list:
            image_path = os.path.join(self.images_folder, image_name)
            with Image.open(image_path) as img:
                plt.figure(figsize=(8, 6))
                plt.imshow(img)
                plt.axis("off")
                plt.title(os.path.splitext(image_name)[0])
                plt.show()
