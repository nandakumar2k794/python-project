"""
Issue management API views with pagination, validation, and error handling
"""
import logging
import bleach
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Issue, Comment
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)

VALID_STATUSES = ["Submitted", "Verified", "Assigned", "In Progress", "Resolved", "Closed", "Rejected"]
VALID_CATEGORIES = ["Roads", "Water", "Sanitation", "Electricity", "Parks", "Street Lights", "Encroachment", "Others"]
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


def _push_notification(user_id, message, issue_id):
    """Send notification via WebSocket and save to database"""
    try:
        Notification(
            user_id=str(user_id),
            type="issue_update",
            message=message,
            issue_id=str(issue_id)
        ).save()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "notify",
                "payload": {"message": message, "issue_id": str(issue_id)}
            },
        )
    except Exception as e:
        logger.error(f"Failed to push notification: {str(e)}", exc_info=True)


def _serialize_issue(request, issue):
    """Serialize issue document to dictionary"""
    user_id = getattr(getattr(request, "user", None), "id", None)
    return {
        "id": str(issue.id),
        "issue_code": issue.issue_code,
        "title": issue.title,
        "description": issue.description[:200] if issue.description else "",
        "status": issue.status,
        "priority": issue.priority,
        "category": issue.category,
        "reported_by": issue.reported_by,
        "assigned_to": issue.assigned_to,
        "upvote_count": len(issue.upvotes or []),
        "upvoted": str(user_id) in (issue.upvotes or []) if user_id else False,
        "photos": issue.photos or [],
        "work_proof": issue.work_proof or [],
        "location": issue.location,
        "created_at": issue.created_at.isoformat() if issue.created_at else None,
        "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
    }


class IssuesView(APIView):
    """List issues with pagination and filtering"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get issues with pagination and filters"""
        try:
            # Build query filters - show all district issues
            filters = {}
            status = request.query_params.get("status")
            category = request.query_params.get("category")
            ward = request.query_params.get("ward")
            mine = request.query_params.get("mine", "").lower() in {"1", "true", "yes"}
            search = request.query_params.get("search", "").strip()

            if status and status in VALID_STATUSES:
                filters["status"] = status
            if category and category in VALID_CATEGORIES:
                filters["category"] = category
            if ward:
                filters["location__ward_id"] = ward
            if mine:
                filters["reported_by"] = str(request.user.id)

            # Get base queryset
            queryset = Issue.objects(**filters).order_by("-created_at")

            # Apply search filter
            if search:
                queryset = queryset.filter(
                    title__icontains=search
                ) | queryset.filter(
                    description__icontains=search
                ) | queryset.filter(
                    issue_code__icontains=search
                )

            # Pagination
            page_size = min(int(request.query_params.get("page_size", DEFAULT_PAGE_SIZE)), MAX_PAGE_SIZE)
            page_num = int(request.query_params.get("page", 1))

            results = list(queryset)
            paginator = Paginator(results, page_size)
            if paginator.count == 0:
                return Response({
                    "count": 0,
                    "total_pages": 0,
                    "current_page": 1,
                    "page_size": page_size,
                    "results": [],
                })
            try:
                page_obj = paginator.page(page_num)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            return Response({
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "page_size": page_size,
                "results": [_serialize_issue(request, i) for i in page_obj.object_list],
            })
        except Exception as e:
            logger.error(f"Failed to fetch issues: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to fetch issues"},
                status=500
            )

    def post(self, request):
        """Create new issue with validation"""
        try:
            if request.user.role != "citizen":
                return Response({"detail": "Only citizens can create issues"}, status=403)

            # Validate required fields
            title = request.data.get("title", "").strip()
            description = request.data.get("description", "").strip()
            category = request.data.get("category", "").strip()

            if not title or len(title) < 3:
                return Response({"detail": f"Title must be at least 3 characters (got {len(title)})"}, status=400)
            if not description or len(description) < 10:
                return Response({"detail": f"Description must be at least 10 characters (got {len(description)})"}, status=400)
            if not category or category not in VALID_CATEGORIES:
                return Response({"detail": f"Category must be one of {VALID_CATEGORIES}"}, status=400)

            # Clean HTML
            title = bleach.clean(title, tags=[], strip=True)
            description = bleach.clean(description, tags=[], strip=True)

            # Get AI classification
            ai_data = {"category": category, "priority": 3, "confidence": 0.8}
            try:
                ai_response = requests.post(
                    f"{settings.FLASK_AI_SERVICE_URL}/ai/classify",
                    json={"description": description},
                    timeout=5,
                )
                if ai_response.status_code == 200:
                    ai_data.update(ai_response.json())
            except Exception as e:
                logger.warning(f"AI classification failed: {str(e)}")

            # Create issue
            issue_count = Issue.objects.count()
            issue = Issue(
                issue_code=f"DIST-{datetime.utcnow().year}-{issue_count + 1:05d}",
                title=title,
                description=description,
                category=ai_data.get("category", category),
                sub_category=ai_data.get("sub_category", "general"),
                status="Submitted",
                priority=min(int(ai_data.get("priority", 3)), 5),
                location=request.data.get("location", {}),
                photos=request.data.get("photos", [])[:5],
                reported_by=str(request.user.id),
                timeline=[{
                    "status": "Submitted",
                    "at": datetime.utcnow().isoformat(),
                    "by": str(request.user.id)
                }],
                ai_meta={
                    "category_confidence": ai_data.get("confidence", 0.8),
                    "duplicate_flag": False,
                    "sentiment_score": 0.0,
                },
            )
            issue.save()
            _push_notification(request.user.id, f"Issue {issue.issue_code} submitted successfully", issue.id)
            
            logger.info(f"Issue created: {issue.issue_code} by {request.user.id}")
            return Response(
                {"id": str(issue.id), "issue_code": issue.issue_code},
                status=201
            )
        except Exception as e:
            logger.error(f"Failed to create issue: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Failed to create issue"},
                status=500
            )


class IssueDetailView(APIView):
    """Get single issue details"""
    permission_classes = []

    def get(self, request, issue_id):
        """Retrieve issue details"""
        try:
            issue = Issue.objects.get(id=issue_id)
            
            # Get comments
            comments = Comment.objects(issue_id=str(issue_id))
            serialized_comments = [
                {
                    "id": str(c.id),
                    "author_id": c.author_id,
                    "text": c.text,
                    "is_internal": c.is_internal,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in comments
            ]

            ai_insights = None
            try:
                ai_response = requests.post(
                    f"{settings.FLASK_AI_SERVICE_URL}/ai/issue-insights",
                    json={
                        "issue_code": issue.issue_code,
                        "title": issue.title,
                        "description": issue.description,
                        "category": issue.category,
                        "status": issue.status,
                        "location": issue.location or {},
                    },
                    timeout=10,
                )
                if ai_response.status_code == 200:
                    ai_insights = ai_response.json()
            except Exception as exc:
                logger.warning(f"Failed to load AI insights: {str(exc)}")

            return Response({
                **_serialize_issue(request, issue),
                "description": issue.description or "",
                "comments": serialized_comments,
                "timeline": issue.timeline,
                "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
                "ai_insights": ai_insights,
            })
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found"}, status=404)
        except Exception as e:
            logger.error(f"Failed to fetch issue detail: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to fetch issue"}, status=500)


class IssueStatusView(APIView):
    """Update issue status"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, issue_id):
        """Update issue status with validation"""
        try:
            issue = Issue.objects.get(id=issue_id)
            next_status = request.data.get("status", "").strip()

            if not next_status or next_status not in VALID_STATUSES:
                return Response(
                    {"detail": f"Status must be one of {VALID_STATUSES}"},
                    status=400
                )

            # Check permissions
            is_officer_or_admin = request.user.role in ["officer", "admin"]
            is_reporter = issue.reported_by == str(request.user.id)
            
            # Allow citizen to reopen recent issues
            can_reopen = (
                request.user.role == "citizen"
                and is_reporter
                and issue.status in ["Resolved", "Closed"]
                and issue.updated_at >= datetime.utcnow() - timedelta(days=30)
                and next_status == "Submitted"
            )

            if not is_officer_or_admin and not can_reopen:
                return Response(
                    {"detail": "You don't have permission to update this issue"},
                    status=403
                )

            old_status = issue.status
            issue.status = next_status
            issue.timeline.append({
                "status": next_status,
                "at": datetime.utcnow().isoformat(),
                "by": str(request.user.id)
            })
            issue.updated_at = datetime.utcnow()

            if next_status == "Resolved":
                issue.resolved_at = datetime.utcnow()

            issue.save()
            _push_notification(
                issue.reported_by,
                f"{issue.issue_code}: Status changed from {old_status} to {next_status}",
                issue.id
            )

            logger.info(f"Issue {issue.issue_code} status updated: {old_status} -> {next_status}")
            return Response({"before": old_status, "after": next_status})
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found"}, status=404)
        except Exception as e:
            logger.error(f"Failed to update issue status: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to update issue"}, status=500)


class IssueUpvoteView(APIView):
    """Toggle issue upvote"""
    permission_classes = [IsAuthenticated]

    def post(self, request, issue_id):
        """Add/remove upvote"""
        try:
            issue = Issue.objects.get(id=issue_id)
            user_id = str(request.user.id)
            
            if user_id not in (issue.upvotes or []):
                issue.upvotes = issue.upvotes or []
                issue.upvotes.append(user_id)
            else:
                issue.upvotes.remove(user_id)

            issue.save()
            return Response({"upvotes": len(issue.upvotes or [])})
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found"}, status=404)
        except Exception as e:
            logger.error(f"Failed to upvote issue: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to upvote issue"}, status=500)


class IssueCommentView(APIView):
    """Create and list comments"""
    permission_classes = [IsAuthenticated]

    def post(self, request, issue_id):
        """Create new comment"""
        try:
            # Verify issue exists
            Issue.objects.get(id=issue_id)

            text = request.data.get("text", "").strip()
            if not text or len(text) < 3:
                return Response({"detail": "Comment must be at least 3 characters"}, status=400)

            text = bleach.clean(text, tags=[], strip=True)
            is_internal = bool(request.data.get("is_internal", False)) and request.user.role in ["officer", "admin"]

            comment = Comment(
                issue_id=str(issue_id),
                author_id=str(request.user.id),
                text=text,
                is_internal=is_internal,
            )
            comment.save()

            logger.info(f"Comment created on issue {issue_id}")
            return Response(
                {
                    "id": str(comment.id),
                    "text": comment.text,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                },
                status=201
            )
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found"}, status=404)
        except Exception as e:
            logger.error(f"Failed to create comment: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to create comment"}, status=500)

    def get(self, request, issue_id):
        """Get comments for issue"""
        try:
            # Verify issue exists
            Issue.objects.get(id=issue_id)
            
            comments = Comment.objects(issue_id=str(issue_id)).order_by("-created_at")
            return Response([
                {
                    "id": str(c.id),
                    "author_id": c.author_id,
                    "text": c.text,
                    "is_internal": c.is_internal,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in comments
            ])
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found"}, status=404)
        except Exception as e:
            logger.error(f"Failed to fetch comments: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to fetch comments"}, status=500)


class IssueTimelineView(APIView):
    """Get issue timeline"""
    permission_classes = [IsAuthenticated]

    def get(self, request, issue_id):
        """Retrieve issue timeline"""
        try:
            issue = Issue.objects.get(id=issue_id)
            return Response(issue.timeline or [])
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found"}, status=404)
        except Exception as e:
            logger.error(f"Failed to fetch timeline: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to fetch timeline"}, status=500)


class IssueWorkProofView(APIView):
    """Upload work completion proof for officer/admin verification"""
    permission_classes = [IsAuthenticated]

    def post(self, request, issue_id):
        try:
            if request.user.role not in ["officer", "admin"]:
                return Response({"detail": "Only officers or admins can upload work proof"}, status=403)

            issue = Issue.objects.get(id=issue_id)
            photos = request.data.get("photos", [])[:5]
            note = bleach.clean(request.data.get("note", "").strip(), tags=[], strip=True)

            if not photos:
                return Response({"detail": "At least one work proof photo is required"}, status=400)

            if issue.work_proof is None:
                issue.work_proof = []

            issue.work_proof.append({
                "photos": photos,
                "note": note,
                "uploaded_by": str(request.user.id),
                "uploaded_at": datetime.utcnow().isoformat(),
            })
            issue.updated_at = datetime.utcnow()
            issue.timeline.append({
                "status": issue.status,
                "at": datetime.utcnow().isoformat(),
                "by": str(request.user.id),
                "event": "work_proof_uploaded",
                "note": note,
            })
            issue.save()

            _push_notification(
                issue.reported_by,
                f"{issue.issue_code}: Work completion proof uploaded for verification",
                issue.id
            )

            return Response({"detail": "Work proof uploaded", "work_proof": issue.work_proof})
        except Issue.DoesNotExist:
            return Response({"detail": "Issue not found"}, status=404)
        except Exception as e:
            logger.error(f"Failed to upload work proof: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to upload work proof"}, status=500)
