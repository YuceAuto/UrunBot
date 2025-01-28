import os
import sys
from flask import Flask
from flask_cors import CORS
from modules.routes import Routes
from modules.utils import Utils

# python -m unittest discover tests
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules/tests'))


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Use Config's setup_logger
    logger = Utils.setup_logger()

    Routes.define_routes(app, logger)  # Use Routes class to define routes
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
