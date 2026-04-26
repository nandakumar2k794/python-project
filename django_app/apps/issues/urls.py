from django.urls import path
from .views import IssuesView,IssueDetailView,IssueStatusView,IssueUpvoteView,IssueCommentView,IssueTimelineView,IssueWorkProofView
urlpatterns=[path("",IssuesView.as_view()),path("<str:issue_id>/",IssueDetailView.as_view()),path("<str:issue_id>/status/",IssueStatusView.as_view()),path("<str:issue_id>/upvote/",IssueUpvoteView.as_view()),path("<str:issue_id>/comments/",IssueCommentView.as_view()),path("<str:issue_id>/timeline/",IssueTimelineView.as_view()),path("<str:issue_id>/work-proof/",IssueWorkProofView.as_view())]
