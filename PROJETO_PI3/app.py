from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

from routes.usuarios import usuarios_bp
from routes.pacientes import pacientes_bp
from routes.triagens import triagens_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)

CORS(app, origins=Config.CORS_ORIGINS.split(","))

app.register_blueprint(usuarios_bp)
app.register_blueprint(pacientes_bp)
app.register_blueprint(triagens_bp)
app.register_blueprint(dashboard_bp)

@app.route("/")
def home():
    return jsonify({
        "sistema": "Vital Class API",
        "status": "online"
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5005, debug=True, use_reloader=False)