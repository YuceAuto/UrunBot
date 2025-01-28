import re
import logging

from modules.config import Config

class Utils:

    def __init__(self):
        self.config = Config()

    def is_image_request(self, message):
        return any(term in message.lower() for term in ["resim", "fotoğraf", "görsel"])

    def extract_image_keyword(self, message, assistant_name):
        lower_msg = message.lower()
        brand_lower = assistant_name.lower()
        cleaned = lower_msg.replace(brand_lower, "")
        cleaned = re.sub(r"(resim|fotoğraf|görsel)\w*", "", cleaned, flags=re.IGNORECASE)

        common_phrases = [
            r"paylaşabilir\s?misin", r"paylaşır\s?mısın",
            r"lütfen", r"istiyorum", r"\?$"
        ]
        for phrase in common_phrases:
            cleaned = re.sub(phrase, "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip() or None

    def order_key(self, item, custom_order):
        item_lower = item.lower()
        for index, keywords in enumerate(custom_order):
            if all(keyword in item_lower for keyword in keywords):
                return index
        return len(custom_order)

    @staticmethod
    def setup_logger():
        logger = logging.getLogger("ChatbotAPI")
        if not logger.handlers:  # Avoid duplicate handlers
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _custom_scala_sort(self, image_list):
        return sorted(self.order_key(image_list, self.config.custom_order_scala), key=self.order_key)

    def _custom_kamiq_sort(self, image_list):
        return sorted(self.order_key(image_list, self.config.custom_order_kamiq), key=self.order_key)

    def get_priority(self, filename: str, key) -> int:
        lower_f = filename.lower()
        for index, pattern_keywords in enumerate(key):
            if all(k in lower_f for k in pattern_keywords):
                return index
        return 999
    
    def _multi_group_sort(self, image_list, desired_group=None):
        if desired_group == "scala_custom":
            return self._custom_scala_sort(image_list)
        elif desired_group == "kamiq_custom":  # <-- YENİ EKLENDİ
            return self._custom_kamiq_sort(image_list)
        elif desired_group == "monte_carlo":
            image_list.sort(key=self.get_priority(self.config.monte_carlo_12))
            return image_list
        elif desired_group == "premium_elite":
            image_list.sort(key=self.get_priority(self.config.premium_elite_12))
            return image_list
        elif desired_group == "fabia_12":
            image_list.sort(key=self.get_priority(self.config.fabia_12))
            return image_list
        elif desired_group == "scala_12":
            image_list.sort(key=self.get_priority(self.config.scala_12))
            return image_list
        elif desired_group == "kamiq_12":
            image_list.sort(key=self.get_priority(self.config.kamiq_12))
            return image_list
        else:
            # None => 7 aşamalı default
            return self._default_7step_sort(image_list)
    
    def _default_7step_sort(self, image_list):
        def is_monte_carlo_standard(name):
            return ("monte" in name and "carlo" in name and "opsiyonel" not in name)
        def is_monte_carlo_optional(name):
            return ("monte" in name and "carlo" in name and "opsiyonel" in name)
        def is_premium_standard(name):
            return ("premium" in name and "opsiyonel" not in name)
        def is_premium_optional(name):
            return ("premium" in name and "opsiyonel" in name)
        def is_elite_standard(name):
            return ("elite" in name and "opsiyonel" not in name)
        def is_elite_optional(name):
            return ("elite" in name and "opsiyonel" in name)

        monte_carlo_std = []
        monte_carlo_opt = []
        premium_std = []
        premium_opt = []
        elite_std = []
        elite_opt = []
        leftover = []

        for img in image_list:
            lower_name = img.lower()
            if is_monte_carlo_standard(lower_name):
                monte_carlo_std.append(img)
            elif is_monte_carlo_optional(lower_name):
                monte_carlo_opt.append(img)
            elif is_premium_standard(lower_name):
                premium_std.append(img)
            elif is_premium_optional(lower_name):
                premium_opt.append(img)
            elif is_elite_standard(lower_name):
                elite_std.append(img)
            elif is_elite_optional(lower_name):
                elite_opt.append(img)
            else:
                leftover.append(img)

        # Gruplar içinde alfabetik
        monte_carlo_std.sort()
        monte_carlo_opt.sort()
        premium_std.sort()
        premium_opt.sort()
        elite_std.sort()
        elite_opt.sort()
        leftover.sort()

        return (
            monte_carlo_std
            + monte_carlo_opt
            + premium_std
            + premium_opt
            + elite_std
            + elite_opt
            + leftover
        )
    
    def _is_image_request(self, message: str): #### UTILS
        msg = message.lower()
        return ("resim" in msg) or ("fotoğraf" in msg) or ("görsel" in msg)

    def _extract_image_keyword(self, message: str, assistant_name: str): ### UTILS
        lower_msg = message.lower()
        brand_lower = assistant_name.lower()
        cleaned = lower_msg.replace(brand_lower, "")
        cleaned = re.sub(r"(resim|fotoğraf|görsel)\w*", "", cleaned, flags=re.IGNORECASE)

        common_phrases = [
            r"paylaşabilir\s?misin", r"paylaşır\s?mısın",
            r"lütfen", r"istiyorum", r"\?$"
        ]
        for p in common_phrases:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)

        final_keyword = cleaned.strip()
        return final_keyword if final_keyword else None