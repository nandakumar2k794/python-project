import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.issues.models import Issue

class CitizenDashboardView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        rows=Issue.objects(reported_by=str(request.user.id)).order_by("-created_at")
        return Response({"my_reports":len(rows),"recent":[{"issue_code":i.issue_code,"status":i.status} for i in rows[:10]]})

class OfficerDashboardView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        if request.user.role not in ["officer","admin"]: return Response({"detail":"Forbidden"}, status=403)
        return Response({"submitted":Issue.objects(status="Submitted").count(),"in_progress":Issue.objects(status="In Progress").count(),"resolved":Issue.objects(status="Resolved").count()})


class AIChatProxyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = {"message": request.data.get("message", ""), "context": request.data.get("context", {})}
        try:
            resp = requests.post(f"{settings.FLASK_AI_SERVICE_URL}/ai/chat", json=payload, timeout=10)
            return Response(resp.json())
        except Exception:
            message = payload["message"]
            return Response({"reply": f"Assistant fallback: I can help you file and track issues. You asked: {message[:120]}"})


class AIReportAssistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = {
            "title": request.data.get("title", ""),
            "description": request.data.get("description", ""),
            "address": request.data.get("address", ""),
            "category": request.data.get("category", ""),
        }
        try:
            resp = requests.post(f"{settings.FLASK_AI_SERVICE_URL}/ai/report-assist", json=payload, timeout=20)
            return Response(resp.json(), status=resp.status_code)
        except Exception:
            description = payload["description"].strip()
            title = payload["title"].strip() or (description[:80] if description else "Civic issue")
            return Response({
                "improved_title": title[:100],
                "improved_description": description[:500],
                "suggested_category": payload["category"] or "Others",
                "priority": 3,
                "summary": "AI assistant is temporarily unavailable, so a basic cleanup was applied.",
                "questions": [],
            })


class AIDescribeIssueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = {
            "image": request.data.get("image", ""),
            "category": request.data.get("category", ""),
            "address": request.data.get("address", ""),
        }
        try:
            # Increased timeout to 120s to accommodate Ollama LLaVA processing time
            resp = requests.post(f"{settings.FLASK_AI_SERVICE_URL}/ai/describe-issue", json=payload, timeout=120)
            resp.raise_for_status()
            response_data = resp.json()
            
            # Ensure we always return title and description
            return Response({
                "title": response_data.get("title", "Issue Report"),
                "description": response_data.get("description", "Image analysis completed"),
                "suggested_category": response_data.get("suggested_category", payload.get("category", "Others")),
                "priority": response_data.get("priority", 3),
                "summary": response_data.get("summary", "Image analyzed successfully")
            }, status=200)
        except requests.exceptions.Timeout:
            return Response({
                "error": "Image analysis service is taking too long",
                "title": "Issue Report",
                "description": "Please provide a manual description. Analysis timeout.",
                "suggested_category": payload.get("category", "Others"),
                "priority": 3,
                "summary": "Service timeout"
            }, status=504)
        except requests.exceptions.HTTPError as http_err:
            # Handle specific HTTP errors like 429
            if hasattr(http_err.response, 'status_code') and http_err.response.status_code == 429:
                return Response({
                    "error": "Rate limited",
                    "title": "Issue Report",
                    "description": "AI service is busy. Please wait a moment and try again, or provide a manual description.",
                    "suggested_category": payload.get("category", "Others"),
                    "priority": 3,
                    "summary": "Service rate limited"
                }, status=429)
            return Response({
                "error": f"HTTP error: {str(http_err)}",
                "title": "Issue Report",
                "description": "Image analysis service error. Please provide a manual description.",
                "suggested_category": payload.get("category", "Others"),
                "priority": 3,
                "summary": "Service error"
            }, status=502)
        except Exception as e:
            import traceback
            return Response({
                "error": f"Unexpected error: {str(e)}",
                "title": "Issue Report",
                "description": "Unable to analyze image. Please provide a manual description.",
                "suggested_category": payload.get("category", "Others"),
                "priority": 3,
                "summary": "Image analysis failed",
                "debug": str(traceback.format_exc()) if settings.DEBUG else None
            }, status=500)


class PublicHomeView(APIView):
    permission_classes = []

    def get(self, request):
        issues = Issue.objects.order_by("-created_at")[:24]
        total = Issue.objects.count()
        resolved = Issue.objects(status="Resolved").count()
        open_count = Issue.objects(status__nin=["Resolved", "Closed"]).count()
        categories = Issue.objects.item_frequencies("category")

        top_categories = sorted(
            [{"name": key or "Others", "count": value} for key, value in categories.items()],
            key=lambda item: item["count"],
            reverse=True,
        )[:5]

        is_authenticated = bool(getattr(request.user, "is_authenticated", False))
        user_id = str(request.user.id) if is_authenticated else None

        return Response({
            "summary": {
                "total_issues": total,
                "open_issues": open_count,
                "resolved_issues": resolved,
                "resolution_rate": 0 if total == 0 else round(resolved * 100 / total, 2),
                "top_categories": top_categories,
            },
            "issues": [
                {
                    "id": str(issue.id),
                    "issue_code": issue.issue_code,
                    "title": issue.title,
                    "description": issue.description[:220] if issue.description else "",
                    "status": issue.status,
                    "priority": issue.priority,
                    "category": issue.category,
                    "location": issue.location or {},
                    "upvote_count": len(issue.upvotes or []),
                    "upvoted": user_id in (issue.upvotes or []) if user_id else False,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                }
                for issue in issues
            ],
        })
