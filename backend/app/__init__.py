from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv


def create_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(app)

    from .routes import api_bp
    from .lookup import lookup_bp
    from .auth import auth_bp
    from .files import files_bp
    from .reports import reports_bp
    from .assess import assess_bp
    from .trends import trends_bp
    from .admin import admin_bp
    from .whatsapp import whatsapp_bp
    from .agencies import agencies_bp
    from .ussd import ussd_bp
    from .sms import sms_bp
    from .alerts import alerts_bp
    from .partner import partner_bp

    blueprints = [
        api_bp,
        lookup_bp,
        auth_bp,
        files_bp,
        reports_bp,
        assess_bp,
        trends_bp,
        admin_bp,
        whatsapp_bp,
        agencies_bp,
        ussd_bp,
        sms_bp,
        alerts_bp,
        partner_bp,
    ]
    for bp in blueprints:
        app.register_blueprint(bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "Genzura API is running"})

    return app
