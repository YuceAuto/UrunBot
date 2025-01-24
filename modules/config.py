import os

class Config:
    
    def __init__(self):
        self.static_path = os.path.join(os.getcwd(), "static")
        self.image_paths = os.path.join(self.static_path, "images")
        self.user_states = {}

        self.stopwords = {
            "model", "araç", "arac", "paylaşabilir", "paylaşır",
            "misin", "mısın", "lütfen", "istiyorum", "?",
            "görsel", "resim", "fotoğraf", "fotograf"
        }

        # Assistant configurations
        self.ASSISTANT_CONFIG = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": ["Kamiq"],
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": ["Fabia"],
            "asst_njSG1NVgg4axJFmvVYAIXrpM": ["Scala"],
        }

        self.ASSISTANT_NAME_MAP = {
            "asst_fw6RpRp8PbNiLUR1KB2XtAkK": "Kamiq",
            "asst_yeDl2aiHy0uoGGjHRmr2dlYB": "Fabia",
            "asst_njSG1NVgg4axJFmvVYAIXrpM": "Scala",
        }

        # Monte Carlo list (12 steps)
        self.monte_carlo_12 = [
            ["monte", "carlo", "direksiyon", "simidi"],
            ["monte", "carlo", "döşeme", "standart"],
            ["monte", "carlo", "döşeme", "opsiyonel"],
            ["monte", "carlo", "ön", "dekor", "standart"],
            ["monte", "carlo", "ön", "dekor", "opsiyonel"],
            ["monte", "carlo", "ön", "konsol", "standart"],
            ["monte", "carlo", "ön", "konsol", "opsiyonel"],
            ["monte", "carlo", "gösterge", "paneli"],
            ["monte", "carlo", "multimedya"],
            ["monte", "carlo", "jant", "standart"],
            ["monte", "carlo", "opsiyonel", "pjf", "jant"],
            ["monte", "carlo", "jant", "opsiyonel"],
        ]

        # Premium/Elite list (12 steps)
        self.premium_elite_12 = [
            ["direksiyon", "simidi"],
            ["döşeme", "standart"],
            ["döşeme", "opsiyonel"],
            ["ön", "dekor", "standart"],
            ["ön", "dekor", "opsiyonel"],
            ["ön", "konsol", "standart"],
            ["ön", "konsol", "opsiyonel"],
            ["gösterge", "paneli"],
            ["multimedya"],
            ["jant", "standart"],
            ["jant", "opsiyonel"],
            ["premium", "ve", "monte", "carlo", "opsiyonel", "pjf", "jant"],
        ]

        # Fabia/Scala/Kamiq lists (12 steps)
        self.fabia_12 = [
            ["fabia", "direksiyon", "simidi"],
            ["fabia", "döşeme", "standart"],
            ["fabia", "döşeme", "opsiyonel"],
            ["fabia", "ön", "dekor", "standart"],
            ["fabia", "ön", "dekor", "opsiyonel"],
            ["fabia", "ön", "konsol", "standart"],
            ["fabia", "ön", "konsol", "opsiyonel"],
            ["fabia", "gösterge", "paneli"],
            ["fabia", "multimedya"],
            ["fabia", "jant", "standart"],
            ["fabia", "jant", "opsiyonel"],
            ["fabia", "opsiyonel", "pjf", "jant"],
        ]

        self.scala_12 = [
            ["scala", "direksiyon", "simidi"],
            ["scala", "döşeme", "standart"],
            ["scala", "döşeme", "opsiyonel"],
            ["scala", "ön", "dekor", "standart"],
            ["scala", "ön", "dekor", "opsiyonel"],
            ["scala", "ön", "konsol", "standart"],
            ["scala", "ön", "konsol", "opsiyonel"],
            ["scala", "gösterge", "paneli"],
            ["scala", "multimedya"],
            ["scala", "jant", "standart"],
            ["scala", "jant", "opsiyonel"],
            ["scala", "opsiyonel", "pjf", "jant"],
        ]

        self.kamiq_12 = [
            ["kamiq", "direksiyon", "simidi"],
            ["kamiq", "döşeme", "standart"],
            ["kamiq", "döşeme", "opsiyonel"],
            ["kamiq", "ön", "dekor", "standart"],
            ["kamiq", "ön", "dekor", "opsiyonel"],
            ["kamiq", "ön", "konsol", "standart"],
            ["kamiq", "ön", "konsol", "opsiyonel"],
            ["kamiq", "gösterge", "paneli"],
            ["kamiq", "multimedya"],
            ["kamiq", "jant", "standart"],
            ["kamiq", "jant", "opsiyonel"],
            ["kamiq", "opsiyonel", "pjf", "jant"],
        ]

        self.custom_order_kamiq = [
            ["kamiq", "monte", "carlo", "standart", "direksiyon", "simidi"],  # 1
            ["kamiq", "premium", "standart", "direksiyon", "simidi"],        # 2
            ["kamiq", "elite", "standart", "direksiyon", "simidi"],          # 3
            ["kamiq", "monte", "carlo", "standart", "döşeme"],               # 4
            ["kamiq", "monte", "carlo", "standart", "kapı", "döşeme"],       # 5
            ["kamiq", "premium", "lodge", "standart", "döşeme"],             # 6
            ["kamiq", "premium", "lodge", "standart", "kapı", "döşeme"],     # 7
            ["kamiq", "premium", "suite", "opsiyonel", "döşeme"],            # 8
            ["kamiq", "premium", "suite", "opsiyonel", "kapı", "döşeme"],    # 9
            ["kamiq", "elite", "studio", "standart", "döşeme"],              # 10
            ["kamiq", "elite", "studio", "standart", "kapı", "döşeme"],      # 11
            ["kamiq", "monte", "carlo", "standart", "ön", "dekor"],          # 12
            ["kamiq", "premium", "lodge", "standart", "ön", "dekor"],        # 13
            ["kamiq", "premium", "suite", "opsiyonel", "ön", "dekor"],       # 14
            ["kamiq", "elite", "studio", "standart", "ön", "dekor"],         # 15
            ["kamiq", "monte", "carlo", "standart", "ön", "konsol"],         # 16
            ["kamiq", "premium", "lodge", "standart", "ön", "konsol"],       # 17
            ["kamiq", "premium", "suite", "opsiyonel", "ön", "konsol"],      # 18
            ["kamiq", "elite", "studio", "standart", "ön", "konsol"],        # 19
            ["kamiq", "monte", "carlo", "standart", "dijital", "gösterge", "paneli"], # 20
            ["kamiq", "premium", "standart", "gösterge", "paneli"],          # 21
            ["kamiq", "elite", "standart", "gösterge", "paneli"],            # 22
            ["kamiq", "monte", "carlo", "standart", "multimedya", "sistemi"],# 23
            ["kamiq", "premium", "standart", "multimedya", "sistemi"],       # 24
            ["kamiq", "elite", "standart", "multimedya", "sistemi"],         # 25
            ["kamiq", "monte", "carlo", "pji", "standart", "jant"],          # 26
            ["kamiq", "premium", "pjg", "standart", "jant"],                 # 27
            ["kamiq", "1.0", "premium", "pj7", "opsiyonel", "jant"],         # 28
            ["kamiq", "premium", "pjg", "opsiyonel", "jant"],                # 29
            ["kamiq", "premium", "pjn", "opsiyonel", "jant"],                # 30
            ["kamiq", "premium", "pjp", "opsiyonel", "jant"],                # 31
            ["kamiq", "elite", "p02", "standart", "jant"],                   # 32
            ["kamiq", "1.0", "elite", "pj7", "opsiyonel", "jant"],           # 33
            ["kamiq", "elite", "pjg", "opsiyonel", "jant"],                  # 34
            ["kamiq", "elite", "pjp", "opsiyonel", "jant"],                  # 35
            ["kamiq", "ay", "beyazı"],                                       # 36
            ["kamiq", "gümüş"],                                             # 37
            ["kamiq", "graptihe", "gri"],                                    # 38
            ["kamiq", "büyülü", "siyah"],                                    # 39
            ["kamiq", "kadife", "kırmızısı"],                                # 40
            ["kamiq", "yarış", "mavisi"],                                    # 41
            ["kamiq", "phoenix", "turuncu"]                                  # 42
        ]

        self.custom_order_scala = [
            ["scala", "monte", "carlo", "standart", "direksiyon", "simidi"],  # 1
            ["scala", "premium", "standart", "direksiyon", "simidi"],        # 2
            ["scala", "elite", "standart", "direksiyon", "simidi"],          # 3
            ["scala", "monte", "carlo", "standart", "döşeme"],               # 4
            ["scala", "monte", "carlo", "standart", "kapı", "döşeme"],       # 5
            ["scala", "premium", "lodge", "standart", "döşeme"],             # 6
            ["scala", "premium", "lodge", "standart", "kapı", "döşeme"],     # 7
            ["scala", "premium", "suite", "opsiyonel", "döşeme"],            # 8
            ["scala", "premium", "suite", "opsiyonel", "kapı", "döşeme"],    # 9
            ["scala", "elite", "studio", "standart", "döşeme"],              # 10
            ["scala", "elite", "studio", "standart", "kapı", "döşeme"],      # 11
            ["scala", "monte", "carlo", "standart", "ön", "dekor"],          # 12
            ["scala", "premium", "lodge", "standart", "ön", "dekor"],        # 13
            ["scala", "premium", "suite", "opsiyonel", "ön", "dekor"],       # 14
            ["scala", "elite", "studio", "standart", "ön", "dekor"],         # 15
            ["scala", "monte", "carlo", "standart", "ön", "konsol"],         # 16
            ["scala", "premium", "lodge", "standart", "ön", "konsol"],       # 17
            ["scala", "premium", "suite", "opsiyonel", "ön", "konsol"],      # 18
            ["scala", "elite", "studio", "standart", "ön", "konsol"],        # 19
            ["scala", "monte", "carlo", "standart", "dijital", "gösterge", "paneli"], # 20
            ["scala", "premium", "standart", "gösterge", "paneli"],          # 21
            ["scala", "elite", "standart", "gösterge", "paneli"],            # 22
            ["scala", "monte", "carlo", "standart", "multimedya", "sistemi"],# 23
            ["scala", "premium", "standart", "multimedya", "sistemi"],       # 24
            ["scala", "elite", "standart", "multimedya", "sistemi"],         # 25
            ["scala", "monte", "carlo", "pji", "standart", "jant"],          # 26
            ["scala", "premium", "pj5", "standart", "jant"],                 # 27
            ["scala", "1.0", "premium", "pj7", "opsiyonel", "jant"],         # 28
            ["scala", "premium", "pjg", "opsiyonel", "jant"],                # 29
            ["scala", "premium", "pjn", "opsiyonel", "jant"],                # 30
            ["scala", "premium", "pjp", "opsiyonel", "jant"],                # 31
            ["scala", "elite", "pj5", "standart", "jant"],                   # 32
            ["scala", "elite", "pj7", "opsiyonel", "jant"],                  # 33
            ["scala", "elite", "pjg", "opsiyonel", "jant"],                  # 34
            ["scala", "elite", "pjp", "opsiyonel", "jant"],                  # 35
            ["scala", "ay", "beyazı"],                                       # 36
            ["scala", "gümüş"],                                             # 37
            ["scala", "çelik", "gri"],                                       # 38
            ["scala", "grafit", "gri"],                                      # 39
            ["scala", "büyülü", "siyah"],                                    # 40
            ["scala", "kadife", "kırmızısı"],                                # 41
            ["scala", "yarış", "mavisi"]                                     # 42
        ]
