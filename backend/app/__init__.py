import os

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    CORS(app)

    from .routes import api_bp
    app.register_blueprint(api_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "Genzura API is running"})

    return app