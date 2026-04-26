from flask import Blueprint, request, jsonify

bp=Blueprint("chatbot", __name__)

@bp.post("/ai/chat")
def chat():
    message=request.json.get("message", "")
    context=request.json.get("context", {})
    if "status" in message.lower() and context.get("issue_code"):
        return jsonify({"reply": f"Issue {context['issue_code']} is currently under review."})
    return jsonify({"reply": f"I can help with form filling and issue tracking. You asked: {message[:150]}"})
