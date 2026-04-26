from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("login/", TemplateView.as_view(template_name="auth/login.html"), name="login"),
    path("register/", TemplateView.as_view(template_name="auth/register.html"), name="register"),
    path("citizen/", TemplateView.as_view(template_name="citizen/dashboard.html"), name="citizen-dashboard"),
    path("citizen/report/", TemplateView.as_view(template_name="citizen/report.html"), name="citizen-report"),
    path("officer/", TemplateView.as_view(template_name="officer/dashboard.html"), name="officer-dashboard"),
    path("admin-dashboard/", TemplateView.as_view(template_name="admin/dashboard.html"), name="admin-dashboard"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/issues/", include("apps.issues.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/", include("apps.analytics.urls")),
]
