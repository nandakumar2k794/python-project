from typing import Any

from .llm_client import ask_json


VALID_CATEGORIES = [
    "Roads",
    "Water",
    "Sanitation",
    "Electricity",
    "Parks",
    "Street Lights",
    "Encroachment",
    "Others",
]


def _normalize_category(value: str) -> str:
    if value in VALID_CATEGORIES:
        return value
    lower = (value or "").strip().lower()
    for category in VALID_CATEGORIES:
        if category.lower() == lower:
            return category
    return "Others"


def _fallback_assist(payload: dict[str, Any]) -> dict[str, Any]:
    description = (payload.get("description") or "").strip()
    title = (payload.get("title") or "").strip()
    category = _normalize_category(payload.get("category") or "Others")
    first_sentence = description.split(".")[0].strip() if description else ""
    improved_title = title or (first_sentence[:70] if first_sentence else "Civic issue needs attention")
    improved_description = description or "Please inspect and resolve this issue at the reported location."
    return {
        "improved_title": improved_title[:100],
        "improved_description": improved_description[:500],
        "suggested_category": category,
        "priority": 3,
        "summary": "Report reviewed and cleaned for submission.",
        "questions": [],
    }


def assist_report(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""
You are helping a citizen file a civic complaint.
Rewrite the report to be clearer, concise, and actionable while preserving meaning.

Return JSON with keys:
- improved_title: string, max 100 chars
- improved_description: string, max 500 chars
- suggested_category: one of {VALID_CATEGORIES}
- priority: integer from 1 to 5 where 5 is most urgent
- summary: one short sentence explaining what was improved
- questions: array of up to 3 short missing-information questions

Input:
title: {payload.get("title", "")}
description: {payload.get("description", "")}
address: {payload.get("address", "")}
category: {payload.get("category", "")}
"""
    try:
        data = ask_json(prompt)
        return {
            "improved_title": str(data.get("improved_title") or "").strip()[:100] or _fallback_assist(payload)["improved_title"],
            "improved_description": str(data.get("improved_description") or "").strip()[:500] or _fallback_assist(payload)["improved_description"],
            "suggested_category": _normalize_category(data.get("suggested_category") or payload.get("category") or "Others"),
            "priority": max(1, min(5, int(data.get("priority", 3)))),
            "summary": str(data.get("summary") or "Report improved for clarity.").strip(),
            "questions": [str(q).strip() for q in (data.get("questions") or []) if str(q).strip()][:3],
        }
    except Exception:
        return _fallback_assist(payload)


def _fallback_issue_insights(issue: dict[str, Any]) -> dict[str, Any]:
    category = _normalize_category(issue.get("category") or "Others")
    status = issue.get("status") or "Submitted"
    return {
        "summary": f"This {category.lower()} issue is currently marked as {status.lower()}.",
        "impact": "Residents may continue to face inconvenience until the issue is resolved.",
        "recommended_actions": [
            "Verify the exact location and visible impact.",
            "Assign the appropriate field team.",
            "Update citizens once inspection is complete.",
        ],
        "department": {
            "Roads": "Road Maintenance",
            "Water": "Water Works",
            "Sanitation": "Sanitation",
            "Electricity": "Electrical Services",
            "Parks": "Parks Department",
            "Street Lights": "Electrical Services",
            "Encroachment": "Revenue and Enforcement",
        }.get(category, "Municipal Operations"),
        "severity": "medium",
    }


def issue_insights(issue: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""
You are an assistant helping citizens and officers understand a civic issue.
Return JSON with keys:
- summary: 1-2 sentence human-friendly summary
- impact: 1 short sentence explaining likely civic impact
- recommended_actions: array of exactly 3 practical next steps
- department: short department/team name
- severity: one of low, medium, high, critical

Issue:
code: {issue.get("issue_code", "")}
title: {issue.get("title", "")}
description: {issue.get("description", "")}
category: {issue.get("category", "")}
status: {issue.get("status", "")}
location: {issue.get("location", {})}
"""
    try:
        data = ask_json(prompt)
        fallback = _fallback_issue_insights(issue)
        severity = str(data.get("severity") or fallback["severity"]).strip().lower()
        if severity not in {"low", "medium", "high", "critical"}:
            severity = fallback["severity"]
        actions = [str(item).strip() for item in (data.get("recommended_actions") or []) if str(item).strip()][:3]
        if len(actions) < 3:
            actions = fallback["recommended_actions"]
        return {
            "summary": str(data.get("summary") or fallback["summary"]).strip(),
            "impact": str(data.get("impact") or fallback["impact"]).strip(),
            "recommended_actions": actions,
            "department": str(data.get("department") or fallback["department"]).strip(),
            "severity": severity,
        }
    except Exception:
        return _fallback_issue_insights(issue)
