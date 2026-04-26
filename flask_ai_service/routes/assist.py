from flask import Blueprint, jsonify, request

from utils.ai_tools import assist_report, issue_insights


bp = Blueprint("assist", __name__)


@bp.post("/ai/report-assist")
def report_assist():
    payload = request.json or {}
    return jsonify(assist_report(payload))


@bp.post("/ai/issue-insights")
def issue_ai_insights():
    payload = request.json or {}
    return jsonify(issue_insights(payload))
