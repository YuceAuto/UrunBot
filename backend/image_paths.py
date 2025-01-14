import os

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

        # Store the file path in the dictionary
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

    def get_images_by_keyword(self, keyword):
        """
        Retrieve images whose names contain the given keyword (case-insensitive).

        :param keyword: The search keyword to look for in the image name.
        :return: A list of (name, path) tuples for matching images.
        """
        results = []
        lower_keyword = keyword.lower()
        for name, path in self._images.items():
            if lower_keyword in name.lower():
                results.append((name, path))
        return results

def load_all_images(image_storage):
    """
    Automatically add all Fabia, Scala, and Kamiq images to the provided ImagePaths instance.
    Adjust the paths as needed.
    """
    ROOT_DIR = os.path.abspath(os.curdir)
    ASSET_DIR = ROOT_DIR[:-7]  # Adjust if needed


    # FABIA
    images.add_image("Fabia Monte Carlo Ay Beyazı", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Ay Beyazı.png")
    images.add_image("Fabia Monte Carlo Büyülü Siyah", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Büyülü Siyah.png")
    images.add_image("Fabia Monte Carlo Direksiyon Simidi", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Direksiyon Simidi.png")
    images.add_image("Fabia Monte Carlo Gösterge Paneli", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Gösterge Paneli.png")
    images.add_image("Fabia Monte Carlo Graphite Gri", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Graphite Gri.png")
    images.add_image("Fabia Monte Carlo Gümüş", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Gümüş.png")
    images.add_image("Fabia Monte Carlo Kadife Kırmızı", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Kadife Kırmızı.png")
    images.add_image("Fabia Monte Carlo Phoenix Turuncu", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Phoenix Turuncu.png")
    images.add_image("Fabia Monte Carlo Standart PJE Procyon Jant", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Standart PJE Procyon Jant.png")
    images.add_image("Fabia Monte Carlo Standart Suedia Kumaş Döşeme", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Standart Suedia Kumaş Döşeme.png")
    images.add_image("Fabia Monte Carlo Standart Suedia Kumaş Koltuk Döşeme", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Standart Suedia Kumaş Koltuk Döşeme.png")
    images.add_image("Fabia Monte Carlo Standart Suedia Kumaş Ön Dekor", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Standart Suedia Kumaş Ön Dekor.png")
    images.add_image("Fabia Monte Carlo Yarış Mavisi", ASSET_DIR+"assets\\images\\fabia\\Fabia Monte Carlo Yarış Mavisi.png")
    images.add_image("Fabia Premium Ay Beyazı", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Ay Beyazı.png")
    images.add_image("Fabia Premium Büyülü Siyah", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Büyülü Siyah.png")
    images.add_image("Fabia Premium Direksiyon Simidi", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Direksiyon Simidi.png")
    images.add_image("Fabia Premium Gösterge Paneli", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Gösterge Paneli.png")
    images.add_image("Fabia Premium Graphite Gri", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Graphite Gri.png")
    images.add_image("Fabia Premium Gümüş", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Gümüş.png")
    images.add_image("Fabia Premium Kadife Kırmızısı", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Kadife Kırmızısı.png")
    images.add_image("Fabia Premium Opsiyonel Dynamic Suedia Kumaş Döşeme", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Opsiyonel Dynamic Suedia Kumaş Döşeme.png")
    images.add_image("Fabia Premium Opsiyonel Dynamic Suedia Kumaş Koltuk Döşeme", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Opsiyonel Dynamic Suedia Kumaş Koltuk Döşeme.png")
    images.add_image("Fabia Premium Opsiyonel Dynamic Suedia Kumaş Ön Dekor", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Opsiyonel Dynamic Suedia Kumaş Ön Dekor.png")
    images.add_image("Fabia Premium Opsiyonel PJ9 Procyon Aero Jant", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Opsiyonel PJ9 Procyon Aero Jant.png")
    images.add_image("Fabia Premium Opsiyonel PX0 Urus Jant", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Opsiyonel PX0 Urus Jant.png")
    images.add_image("Fabia Premium Phoenix Turuncu", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Phoenix Turuncu.png")
    images.add_image("Fabia Premium Standart Lodge Kumaş Döşeme", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Standart Lodge Kumaş Döşeme.png")
    images.add_image("Fabia Premium Standart Lodge Kumaş Koltuk Döşemesi", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Standart Lodge Kumaş Koltuk Döşemesi.png")
    images.add_image("Fabia Premium Standart Lodge Kumaş Ön Dekor", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Standart Lodge Kumaş Ön Dekor.png")
    images.add_image("Fabia Premium Standart PJ4 Proxima Jant", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Standart PJ4 Proxima Jant.png")
    images.add_image("Fabia Premium Standart Suite Kumaş Döşeme", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Standart Suite Kumaş Döşeme.png")
    images.add_image("Fabia Premium Standart Suite Kumaş Koltuk Döşeme", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Standart Suite Kumaş Koltuk Döşeme.png")
    images.add_image("Fabia Premium Standart Suite Kumaş Ön Dekor", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Standart Suite Kumaş Ön Dekor.png")
    images.add_image("Fabia Premium ve Monte Carlo  Opsiyonel PJF Libra Jant", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium ve Monte Carlo  Opsiyonel PJF Libra Jant.png")
    images.add_image("Fabia Premium ve Monte Carlo Multimedya Sistemi", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium ve Monte Carlo Multimedya Sistemi.png")
    images.add_image("Fabia Premium Yarış Mavisi", ASSET_DIR+"assets\\images\\fabia\\Fabia Premium Yarış Mavisi.png")
    
    # SCALA
    images.add_image("Scala 1.0 Premium PJ7 Opsiyonel Jant", ASSET_DIR+"assets\\images\\scala\\Scala 1.0 Premium PJ7 Opsiyonel Jant.png")
    images.add_image("Scala Ay Beyazı", ASSET_DIR+"assets\\images\\scala\\Scala Ay Beyazı.png")
    images.add_image("Scala Büyülü Siyah", ASSET_DIR+"assets\\images\\scala\\Scala Büyülü Siyah.png")
    images.add_image("Scala Çelik Gri", ASSET_DIR+"assets\\images\\scala\\Scala Çelik Gri.png")
    images.add_image("Scala Elite Direkisyon Simidi", ASSET_DIR+"assets\\images\\scala\\Scala Elite Direkisyon Simidi.png")
    images.add_image("Scala Elite Gösterge Paneli", ASSET_DIR+"assets\\images\\scala\\Scala Elite Gösterge Paneli.png")
    images.add_image("Scala Elite PJ5 Standart Jant", ASSET_DIR+"assets\\images\\scala\\Scala Elite PJ5 Standart Jant.png")
    images.add_image("Scala Elite PJ7 Opsiyonel Jant", ASSET_DIR+"assets\\images\\scala\\Scala Elite PJ7 Opsiyonel Jant.png")
    images.add_image("Scala Elite PJG Opsiyonel Jant", ASSET_DIR+"assets\\images\\scala\\Scala Elite PJG Opsiyonel Jant.png")
    images.add_image("Scala Elite PJP Opsiyonel Jant", ASSET_DIR+"assets\\images\\scala\\Scala Elite PJP Opsiyonel Jant.png")
    images.add_image("Scala Elite Studio Standart Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Elite Studio Standart Döşeme.png")
    images.add_image("Scala Elite Studio Standart Kapı Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Elite Studio Standart Kapı Döşeme.png")
    images.add_image("Scala Elite Studio Standart Ön Dekor", ASSET_DIR+"assets\\images\\scala\\Scala Elite Studio Standart Ön Dekor.png")
    images.add_image("Scala Elite Studio Standart Ön Konsol", ASSET_DIR+"assets\\images\\scala\\Scala Elite Studio Standart Ön Konsol.png")
    images.add_image("Scala Grafit Gri", ASSET_DIR+"assets\\images\\scala\\Scala Grafit Gri.png")
    images.add_image("Scala Gümüş", ASSET_DIR+"assets\\images\\scala\\Scala Gümüş.png")
    images.add_image("Scala Kadife Kırmızısı", ASSET_DIR+"assets\\images\\scala\\Scala Kadife Kırmızısı.png")
    images.add_image("Scala Monte Carlo Dijital Gösterge Paneli", ASSET_DIR+"assets\\images\\scala\\Scala Monte Carlo Dijital Gösterge Paneli.png")
    images.add_image("Scala Monte Carlo Direksiyon Simidi", ASSET_DIR+"assets\\images\\scala\\Scala Monte Carlo Direksiyon Simidi.png")
    images.add_image("Scala Monte Carlo Kapı Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Monte Carlo Kapı Döşeme.png")
    images.add_image("Scala Monte Carlo Ön Konsol", ASSET_DIR+"assets\\images\\scala\\Scala Monte Carlo Ön Konsol.png")
    images.add_image("Scala Monte Carlo PJI Standart Jant", ASSET_DIR+"assets\\images\\scala\\Scala Monte Carlo PJI Standart Jant.png")
    images.add_image("Scala Monte Carlo Standart Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Monte Carlo Standart Döşeme.png")
    images.add_image("Scala Monte Carlo Standart Ön Dekor", ASSET_DIR+"assets\\images\\scala\\Scala Monte Carlo Standart Ön Dekor.png")
    images.add_image("Scala Multimedya Sistemi", ASSET_DIR+"assets\\images\\scala\\Scala Multimedya Sistemi.png")
    images.add_image("Scala Premium Direkisyon Simidi", ASSET_DIR+"assets\\images\\scala\\Scala Premium Direkisyon Simidi.png")
    images.add_image("Scala Premium Gösterge Paneli", ASSET_DIR+"assets\\images\\scala\\Scala Premium Gösterge Paneli.png")
    images.add_image("Scala Premium Lodge Standart Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Premium Lodge Standart Döşeme.png")
    images.add_image("Scala Premium Lodge Standart Kapı Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Premium Lodge Standart Kapı Döşeme.png")
    images.add_image("Scala Premium Lodge Standart Ön Dekor", ASSET_DIR+"assets\\images\\scala\\Scala Premium Lodge Standart Ön Dekor.png")
    images.add_image("Scala Premium Lodge Standart Ön Konsol", ASSET_DIR+"assets\\images\\scala\\Scala Premium Lodge Standart Ön Konsol.png")
    images.add_image("Scala Premium PJ5 Standart Jant", ASSET_DIR+"assets\\images\\scala\\Scala Premium PJ5 Standart Jant.png")
    images.add_image("Scala Premium PJG Opsiyonel Jant", ASSET_DIR+"assets\\images\\scala\\Scala Premium PJG Opsiyonel Jant.png")
    images.add_image("Scala Premium PJN Opsiyonel Jant", ASSET_DIR+"assets\\images\\scala\\Scala Premium PJN Opsiyonel Jant.png")
    images.add_image("Scala Premium PJP Opsiyonel Jant", ASSET_DIR+"assets\\images\\scala\\Scala Premium PJP Opsiyonel Jant.png")
    images.add_image("Scala Premium Suite Opsiyonel Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Premium Suite Opsiyonel Döşeme.png")
    images.add_image("Scala Premium Suite Opsiyonel Kapı Döşeme", ASSET_DIR+"assets\\images\\scala\\Scala Premium Suite Opsiyonel Kapı Döşeme.png")
    images.add_image("Scala Premium Suite Opsiyonel Ön Dekor", ASSET_DIR+"assets\\images\\scala\\Scala Premium Suite Opsiyonel Ön Dekor.png")
    images.add_image("Scala Premium Suite Opsiyonel Ön Konsol", ASSET_DIR+"assets\\images\\scala\\Scala Premium Suite Opsiyonel Ön Konsol.png")
    images.add_image("Scala Yarış Mavisi", ASSET_DIR+"assets\\images\\scala\\Scala Yarış Mavisi.png")

    # KAMIQ
    images.add_image("Kamiq 1.0 Elite PJ7 Opsiyonel Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq 1.0 Elite PJ7 Opsiyonel Jant.png")
    images.add_image("Kamiq Ay Beyazı", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Ay Beyazı.png")
    images.add_image("Kamiq Büyülü Siyah", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Büyülü Siyah.png")
    images.add_image("Kamiq Elite Direkisyon Simidi", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite Direkisyon Simidi.png")
    images.add_image("Kamiq Elite Gösterge Paneli", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite Gösterge Paneli.png")
    images.add_image("Kamiq Elite P02 Standart Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite P02 Standart Jant.png")
    images.add_image("Kamiq Elite PJG Opsiyonel Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite PJG Opsiyonel Jant.png")
    images.add_image("Kamiq Elite PJP Opsiyonel Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite PJP Opsiyonel Jant.png")
    images.add_image("Kamiq Elite Studio Standart Döşeme", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite Studio Standart Döşeme.png")
    images.add_image("Kamiq Elite Studio Standart Kapı Döşemesi", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite Studio Standart Kapı Döşemesi.png")
    images.add_image("Kamiq Elite Studio Standart Ön Dekor", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite Studio Standart Ön Dekor.png")
    images.add_image("Kamiq Elite Studio Standart Ön Konsol", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Elite Studio Standart Ön Konsol.png")
    images.add_image("Kamiq Graptihe Gri", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Graptihe Gri.png")
    images.add_image("Kamiq Gümüş", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Gümüş.png")
    images.add_image("Kamiq Kadife Kırmızısı", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Kadife Kırmızısı.png")
    images.add_image("Kamiq Monte Carlo Direksiyon Simidi", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Monte Carlo Direksiyon Simidi.png")
    images.add_image("Kamiq Monte Carlo Gösterge Paneli", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Monte Carlo Gösterge Paneli.png")
    images.add_image("Kamiq Monte Carlo PJI Standart Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Monte Carlo PJI Standart Jant.png")
    images.add_image("Kamiq Monte Carlo Standart Döşeme", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Monte Carlo Standart Döşeme.png")
    images.add_image("Kamiq Monte Carlo Standart Kapı Döşeme", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Monte Carlo Standart Kapı Döşeme.png")
    images.add_image("Kamiq Monte Carlo Standart Ön Dekor", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Monte Carlo Standart Ön Dekor.png")
    images.add_image("Kamiq Monte Carlo Standart Ön Konsol", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Monte Carlo Standart Ön Konsol.png")
    images.add_image("Kamiq Multimedya Sistemi", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Multimedya Sistemi.png")
    images.add_image("Kamiq Phoenix Turuncu", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Phoenix Turuncu.png")
    images.add_image("Kamiq Premium Direkisyon Simidi", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Direkisyon Simidi.png")
    images.add_image("Kamiq Premium Gösterge Paneli", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Gösterge Paneli.png")
    images.add_image("Kamiq Premium Lodge Standart Döşeme", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Lodge Standart Döşeme.png")
    images.add_image("Kamiq Premium Lodge Standart Kapı Döşeme", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Lodge Standart Kapı Döşeme.png")
    images.add_image("Kamiq Premium Lodge Standart Ön Dekor", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Lodge Standart Ön Dekor.png")
    images.add_image("Kamiq Premium Lodge Standart Ön Konsol", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Lodge Standart Ön Konsol.png")
    images.add_image("Kamiq Premium PJG Standart Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium PJG Standart Jant.png")
    images.add_image("Kamiq Premium PJN Opsiyonel Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium PJN Opsiyonel Jant.png")
    images.add_image("Kamiq Premium PJP Opsiyonel Jant", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium PJP Opsiyonel Jant.png")
    images.add_image("Kamiq Premium Suite Opsiyonel Döşeme", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Suite Opsiyonel Döşeme.png")
    images.add_image("Kamiq Premium Suite Opsiyonel Kapı Döşeme", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Suite Opsiyonel Kapı Döşeme.png")
    images.add_image("Kamiq Premium Suite Opsiyonel Ön Dekor", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Suite Opsiyonel Ön Dekor.png")
    images.add_image("Kamiq Premium Suite Opsiyonel Ön Konsol", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Premium Suite Opsiyonel Ön Konsol.png")
    images.add_image("Kamiq Yarış Mavisi", ASSET_DIR+"assets\\images\\kamiq\\Kamiq Yarış Mavisi.png")

# 1. Create a global 'images' instance
images = ImagePaths()

# 2. Automatically populate it with Fabia, Scala, Kamiq
load_all_images(images)