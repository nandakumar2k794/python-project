from flask import Flask, jsonify
from routes.reports import bp as reports_bp
from routes.assist import bp as assist_bp
from routes.classify import bp as classify_bp
from routes.chatbot import bp as chatbot_bp
from routes.duplicate import bp as duplicate_bp
from utils.ollama_client import check_ollama_health
import logging
import sys

app=Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

app.register_blueprint(reports_bp)
app.register_blueprint(assist_bp)
app.register_blueprint(classify_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(duplicate_bp)

@app.get("/health")
def health():
    ollama_available = check_ollama_health()
    return jsonify({
        "status": "ok",
        "ai_provider": "ollama" if ollama_available else "gemini (fallback)",
        "ollama_available": ollama_available
    })

@app.errorhandler(Exception)
def handle_error(error):
    logger.exception(f"Unhandled exception: {error}")
    return jsonify({"error": str(error)}), 500

if __name__ == "__main__":
    app.run(debug=True)
