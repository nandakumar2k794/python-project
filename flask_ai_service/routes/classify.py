from flask import Blueprint, request, jsonify
from utils.gemini_client import classify_description

bp=Blueprint("classify", __name__)

@bp.post("/ai/classify")
def classify():
    return jsonify(classify_description(request.json.get("description","")))
