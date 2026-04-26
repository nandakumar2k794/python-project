from flask import Blueprint, request, jsonify
from pymongo import MongoClient
import os
from utils.embeddings import embed, cosine

bp=Blueprint("duplicate", __name__)
client=MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/civic_db"))
db=client.get_default_database()

@bp.post("/ai/duplicate-check")
def duplicate_check():
    issue_id=request.json.get("issue_id")
    issue=db.issues.find_one({"_id": issue_id}) if issue_id else None
    if not issue: return jsonify({"duplicates": []})
    base=embed(issue.get("description", ""))
    out=[]
    for row in db.issues.find({"status": {"$in": ["Submitted","Verified","Assigned","In Progress"]}}).limit(200):
        if row.get("_id")==issue.get("_id"): continue
        score=cosine(base, embed(row.get("description", "")))
        if score>0.9: out.append({"issue_id": str(row.get("_id")), "score": round(score,3)})
    return jsonify({"duplicates": sorted(out, key=lambda x: x["score"], reverse=True)[:5]})
