import os
import sys
from flask import Flask
from flask_cors import CORS
from modules.routes import define_routes
from modules.config import Config

# python -m unittest discover tests
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def create_app():
    app = Flask(__name__)
    CORS(app)
    logger = Config.setup_logger()
    define_routes(app, logger)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
