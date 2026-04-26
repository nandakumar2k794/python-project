from django.urls import path
from .views import CitizenDashboardView, OfficerDashboardView, AIChatProxyView, AIReportAssistView, AIDescribeIssueView, PublicHomeView
from apps.analytics.views import AdminAnalyticsView

urlpatterns=[
    path("public/home/", PublicHomeView.as_view()),
    path("citizen/", CitizenDashboardView.as_view()),
    path("officer/", OfficerDashboardView.as_view()),
    path("admin/analytics/", AdminAnalyticsView.as_view()),
    path("ai/chat/", AIChatProxyView.as_view()),
    path("ai/report-assist/", AIReportAssistView.as_view()),
    path("ai/describe-issue/", AIDescribeIssueView.as_view()),
]
