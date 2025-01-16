import os
import logging

class ImagePaths:
    """
    A simple class to maintain a dictionary of image names and their paths.
    """
    def __init__(self):
        # Initialize an empty dictionary or pre-populate if desired
        self._images = {}

    def add_image(self, name, path):
        """
        Add or update an image entry in the dictionary.

        :param name: Name or key for the image.
        :param path: The file path to the image.
        :raises FileNotFoundError: If the specified file does not exist.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"The file '{path}' does not exist.")
        self._images[name] = path

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
        return [
            (name, path) for name, path in self._images.items()
            if keyword_lower in name.lower()
        ]

def load_all_images(image_storage):
    """
    Automatically add all Fabia, Scala, and Kamiq images to the provided ImagePaths instance.
    Adjust the paths as needed.
    """
    ROOT_DIR = os.path.abspath(os.curdir)
    ASSET_DIR = os.path.join(ROOT_DIR, "assets", "images")

    image_definitions = {
        # FABIA
        "Fabia Monte Carlo Ay Beyazı": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Ay Beyazı.png"),
        "Fabia Monte Carlo Büyülü Siyah": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Büyülü Siyah.png"),
        "Fabia Monte Carlo Direksiyon Simidi": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Direksiyon Simidi.png"),
        "Fabia Monte Carlo Gösterge Paneli": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Gösterge Paneli.png"),
        "Fabia Monte Carlo Graphite Gri": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Graphite Gri.png"),
        "Fabia Monte Carlo Gümüş": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Gümüş.png"),
        "Fabia Monte Carlo Kadife Kırmızı": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Kadife Kırmızı.png"),
        "Fabia Monte Carlo Phoenix Turuncu": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Phoenix Turuncu.png"),
        "Fabia Monte Carlo Standart PJE Procyon Jant": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Standart PJE Procyon Jant.png"),
        "Fabia Monte Carlo Standart Suedia Kumaş Döşeme": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Standart Suedia Kumaş Döşeme.png"),
        "Fabia Monte Carlo Standart Suedia Kumaş Koltuk Döşeme": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Standart Suedia Kumaş Koltuk Döşeme.png"),
        "Fabia Monte Carlo Standart Suedia Kumaş Ön Dekor": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Standart Suedia Kumaş Ön Dekor.png"),
        "Fabia Monte Carlo Yarış Mavisi": os.path.join(ASSET_DIR, "fabia", "Fabia Monte Carlo Yarış Mavisi.png"),
        "Fabia Premium Ay Beyazı": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Ay Beyazı.png"),
        "Fabia Premium Büyülü Siyah": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Büyülü Siyah.png"),
        "Fabia Premium Direksiyon Simidi": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Direksiyon Simidi.png"),
        "Fabia Premium Gösterge Paneli": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Gösterge Paneli.png"),
        "Fabia Premium Graphite Gri": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Graphite Gri.png"),
        "Fabia Premium Gümüş": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Gümüş.png"),
        "Fabia Premium Kadife Kırmızısı": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Kadife Kırmızısı.png"),
        "Fabia Premium Opsiyonel Dynamic Suedia Kumaş Döşeme": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Opsiyonel Dynamic Suedia Kumaş Döşeme.png"),
        "Fabia Premium Opsiyonel Dynamic Suedia Kumaş Koltuk Döşeme": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Opsiyonel Dynamic Suedia Kumaş Koltuk Döşeme.png"),
        "Fabia Premium Opsiyonel Dynamic Suedia Kumaş Ön Dekor": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Opsiyonel Dynamic Suedia Kumaş Ön Dekor.png"),
        "Fabia Premium Opsiyonel PJ9 Procyon Aero Jant": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Opsiyonel PJ9 Procyon Aero Jant.png"),
        "Fabia Premium Opsiyonel PX0 Urus Jant": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Opsiyonel PX0 Urus Jant.png"),
        "Fabia Premium Phoenix Turuncu": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Phoenix Turuncu.png"),
        "Fabia Premium Standart Lodge Kumaş Döşeme": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Standart Lodge Kumaş Döşeme.png"),
        "Fabia Premium Standart Lodge Kumaş Koltuk Döşemesi": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Standart Lodge Kumaş Koltuk Döşemesi.png"),
        "Fabia Premium Standart Lodge Kumaş Ön Dekor": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Standart Lodge Kumaş Ön Dekor.png"),
        "Fabia Premium Standart PJ4 Proxima Jant": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Standart PJ4 Proxima Jant.png"),
        "Fabia Premium Standart Suite Kumaş Döşeme": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Standart Suite Kumaş Döşeme.png"),
        "Fabia Premium Standart Suite Kumaş Koltuk Döşeme": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Standart Suite Kumaş Koltuk Döşeme.png"),
        "Fabia Premium Standart Suite Kumaş Ön Dekor": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Standart Suite Kumaş Ön Dekor.png"),
        "Fabia Premium ve Monte Carlo  Opsiyonel PJF Libra Jant": os.path.join(ASSET_DIR, "fabia", "Fabia Premium ve Monte Carlo  Opsiyonel PJF Libra Jant.png"),
        "Fabia Premium ve Monte Carlo Multimedya Sistemi": os.path.join(ASSET_DIR, "fabia", "Fabia Premium ve Monte Carlo Multimedya Sistemi.png"),
        "Fabia Premium Yarış Mavisi": os.path.join(ASSET_DIR, "fabia", "Fabia Premium Yarış Mavisi.png"),
        
        # SCALA
        "Scala 1.0 Premium PJ7 Opsiyonel Jant": os.path.join(ASSET_DIR, "scala", "Scala 1.0 Premium PJ7 Opsiyonel Jant.png"),
        "Scala Ay Beyazı": os.path.join(ASSET_DIR, "scala", "Scala Ay Beyazı.png"),
        "Scala Büyülü Siyah": os.path.join(ASSET_DIR, "scala", "Scala Büyülü Siyah.png"),
        "Scala Çelik Gri": os.path.join(ASSET_DIR, "scala", "Scala Çelik Gri.png"),
        "Scala Elite Direkisyon Simidi": os.path.join(ASSET_DIR, "scala", "Scala Elite Direkisyon Simidi.png"),
        "Scala Elite Gösterge Paneli": os.path.join(ASSET_DIR, "scala", "Scala Elite Gösterge Paneli.png"),
        "Scala Elite PJ5 Standart Jant": os.path.join(ASSET_DIR, "scala", "Scala Elite PJ5 Standart Jant.png"),
        "Scala Elite PJ7 Opsiyonel Jant": os.path.join(ASSET_DIR, "scala", "Scala Elite PJ7 Opsiyonel Jant.png"),
        "Scala Elite PJG Opsiyonel Jant": os.path.join(ASSET_DIR, "scala", "Scala Elite PJG Opsiyonel Jant.png"),
        "Scala Elite PJP Opsiyonel Jant": os.path.join(ASSET_DIR, "scala", "Scala Elite PJP Opsiyonel Jant.png"),
        "Scala Elite Studio Standart Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Elite Studio Standart Döşeme.png"),
        "Scala Elite Studio Standart Kapı Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Elite Studio Standart Kapı Döşeme.png"),
        "Scala Elite Studio Standart Ön Dekor": os.path.join(ASSET_DIR, "scala", "Scala Elite Studio Standart Ön Dekor.png"),
        "Scala Elite Studio Standart Ön Konsol": os.path.join(ASSET_DIR, "scala", "Scala Elite Studio Standart Ön Konsol.png"),
        "Scala Grafit Gri": os.path.join(ASSET_DIR, "scala", "Scala Grafit Gri.png"),
        "Scala Gümüş": os.path.join(ASSET_DIR, "scala", "Scala Gümüş.png"),
        "Scala Kadife Kırmızısı": os.path.join(ASSET_DIR, "scala", "Scala Kadife Kırmızısı.png"),
        "Scala Monte Carlo Dijital Gösterge Paneli": os.path.join(ASSET_DIR, "scala", "Scala Monte Carlo Dijital Gösterge Paneli.png"),
        "Scala Monte Carlo Direksiyon Simidi": os.path.join(ASSET_DIR, "scala", "Scala Monte Carlo Direksiyon Simidi.png"),
        "Scala Monte Carlo Kapı Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Monte Carlo Kapı Döşeme.png"),
        "Scala Monte Carlo Ön Konsol": os.path.join(ASSET_DIR, "scala", "Scala Monte Carlo Ön Konsol.png"),
        "Scala Monte Carlo PJI Standart Jant": os.path.join(ASSET_DIR, "scala", "Scala Monte Carlo PJI Standart Jant.png"),
        "Scala Monte Carlo Standart Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Monte Carlo Standart Döşeme.png"),
        "Scala Monte Carlo Standart Ön Dekor": os.path.join(ASSET_DIR, "scala", "Scala Monte Carlo Standart Ön Dekor.png"),
        "Scala Multimedya Sistemi": os.path.join(ASSET_DIR, "scala", "Scala Multimedya Sistemi.png"),
        "Scala Premium Direkisyon Simidi": os.path.join(ASSET_DIR, "scala", "Scala Premium Direkisyon Simidi.png"),
        "Scala Premium Gösterge Paneli": os.path.join(ASSET_DIR, "scala", "Scala Premium Gösterge Paneli.png"),
        "Scala Premium Lodge Standart Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Premium Lodge Standart Döşeme.png"),
        "Scala Premium Lodge Standart Kapı Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Premium Lodge Standart Kapı Döşeme.png"),
        "Scala Premium Lodge Standart Ön Dekor": os.path.join(ASSET_DIR, "scala", "Scala Premium Lodge Standart Ön Dekor.png"),
        "Scala Premium Lodge Standart Ön Konsol": os.path.join(ASSET_DIR, "scala", "Scala Premium Lodge Standart Ön Konsol.png"),
        "Scala Premium PJ5 Standart Jant": os.path.join(ASSET_DIR, "scala", "Scala Premium PJ5 Standart Jant.png"),
        "Scala Premium PJG Opsiyonel Jant": os.path.join(ASSET_DIR, "scala", "Scala Premium PJG Opsiyonel Jant.png"),
        "Scala Premium PJN Opsiyonel Jant": os.path.join(ASSET_DIR, "scala", "Scala Premium PJN Opsiyonel Jant.png"),
        "Scala Premium PJP Opsiyonel Jant": os.path.join(ASSET_DIR, "scala", "Scala Premium PJP Opsiyonel Jant.png"),
        "Scala Premium Suite Opsiyonel Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Premium Suite Opsiyonel Döşeme.png"),
        "Scala Premium Suite Opsiyonel Kapı Döşeme": os.path.join(ASSET_DIR, "scala", "Scala Premium Suite Opsiyonel Kapı Döşeme.png"),
        "Scala Premium Suite Opsiyonel Ön Dekor": os.path.join(ASSET_DIR, "scala", "Scala Premium Suite Opsiyonel Ön Dekor.png"),
        "Scala Premium Suite Opsiyonel Ön Konsol": os.path.join(ASSET_DIR, "scala", "Scala Premium Suite Opsiyonel Ön Konsol.png"),
        "Scala Yarış Mavisi": os.path.join(ASSET_DIR, "scala", "Scala Yarış Mavisi.png"),

        # KAMIQ
        "Kamiq 1.0 Elite PJ7 Opsiyonel Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq 1.0 Elite PJ7 Opsiyonel Jant.png"),
        "Kamiq Ay Beyazı": os.path.join(ASSET_DIR, "kamiq","Kamiq Ay Beyazı.png"),
        "Kamiq Büyülü Siyah": os.path.join(ASSET_DIR, "kamiq","Kamiq Büyülü Siyah.png"),
        "Kamiq Elite Direkisyon Simidi": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite Direkisyon Simidi.png"),
        "Kamiq Elite Gösterge Paneli": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite Gösterge Paneli.png"),
        "Kamiq Elite P02 Standart Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite P02 Standart Jant.png"),
        "Kamiq Elite PJG Opsiyonel Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite PJG Opsiyonel Jant.png"),
        "Kamiq Elite PJP Opsiyonel Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite PJP Opsiyonel Jant.png"),
        "Kamiq Elite Studio Standart Döşeme": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite Studio Standart Döşeme.png"),
        "Kamiq Elite Studio Standart Kapı Döşemesi": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite Studio Standart Kapı Döşemesi.png"),
        "Kamiq Elite Studio Standart Ön Dekor": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite Studio Standart Ön Dekor.png"),
        "Kamiq Elite Studio Standart Ön Konsol": os.path.join(ASSET_DIR, "kamiq","Kamiq Elite Studio Standart Ön Konsol.png"),
        "Kamiq Graptihe Gri": os.path.join(ASSET_DIR, "kamiq","Kamiq Graptihe Gri.png"),
        "Kamiq Gümüş": os.path.join(ASSET_DIR, "kamiq","Kamiq Gümüş.png"),
        "Kamiq Kadife Kırmızısı": os.path.join(ASSET_DIR, "kamiq","Kamiq Kadife Kırmızısı.png"),
        "Kamiq Monte Carlo Direksiyon Simidi": os.path.join(ASSET_DIR, "kamiq","Kamiq Monte Carlo Direksiyon Simidi.png"),
        "Kamiq Monte Carlo Gösterge Paneli": os.path.join(ASSET_DIR, "kamiq","Kamiq Monte Carlo Gösterge Paneli.png"),
        "Kamiq Monte Carlo PJI Standart Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq Monte Carlo PJI Standart Jant.png"),
        "Kamiq Monte Carlo Standart Döşeme": os.path.join(ASSET_DIR, "kamiq","Kamiq Monte Carlo Standart Döşeme.png"),
        "Kamiq Monte Carlo Standart Kapı Döşeme": os.path.join(ASSET_DIR, "kamiq","Kamiq Monte Carlo Standart Kapı Döşeme.png"),
        "Kamiq Monte Carlo Standart Ön Dekor": os.path.join(ASSET_DIR, "kamiq","Kamiq Monte Carlo Standart Ön Dekor.png"),
        "Kamiq Monte Carlo Standart Ön Konsol": os.path.join(ASSET_DIR, "kamiq","Kamiq Monte Carlo Standart Ön Konsol.png"),
        "Kamiq Multimedya Sistemi": os.path.join(ASSET_DIR, "kamiq","Kamiq Multimedya Sistemi.png"),
        "Kamiq Phoenix Turuncu": os.path.join(ASSET_DIR, "kamiq","Kamiq Phoenix Turuncu.png"),
        "Kamiq Premium Direkisyon Simidi": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Direkisyon Simidi.png"),
        "Kamiq Premium Gösterge Paneli": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Gösterge Paneli.png"),
        "Kamiq Premium Lodge Standart Döşeme": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Lodge Standart Döşeme.png"),
        "Kamiq Premium Lodge Standart Kapı Döşeme": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Lodge Standart Kapı Döşeme.png"),
        "Kamiq Premium Lodge Standart Ön Dekor": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Lodge Standart Ön Dekor.png"),
        "Kamiq Premium Lodge Standart Ön Konsol": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Lodge Standart Ön Konsol.png"),
        "Kamiq Premium PJG Standart Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium PJG Standart Jant.png"),
        "Kamiq Premium PJN Opsiyonel Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium PJN Opsiyonel Jant.png"),
        "Kamiq Premium PJP Opsiyonel Jant": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium PJP Opsiyonel Jant.png"),
        "Kamiq Premium Suite Opsiyonel Döşeme": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Suite Opsiyonel Döşeme.png"),
        "Kamiq Premium Suite Opsiyonel Kapı Döşeme": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Suite Opsiyonel Kapı Döşeme.png"),
        "Kamiq Premium Suite Opsiyonel Ön Dekor": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Suite Opsiyonel Ön Dekor.png"),
        "Kamiq Premium Suite Opsiyonel Ön Konsol": os.path.join(ASSET_DIR, "kamiq","Kamiq Premium Suite Opsiyonel Ön Konsol.png"),
        "Kamiq Yarış Mavisi": os.path.join(ASSET_DIR, "kamiq","Kamiq Yarış Mavisi.png"),
    }
    for name, path in image_definitions.items():
        try:
            image_storage.add_image(name, path)
        except FileNotFoundError as e:
            logging.warning(f"Could not load image '{name}': {e}")

# Create a global instance and load images
images = ImagePaths()
load_all_images(images)