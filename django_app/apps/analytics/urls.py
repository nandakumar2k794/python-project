from django.urls import path
from .views import WardView, WardPatchView

urlpatterns=[
    path("wards/", WardView.as_view()),
    path("wards/<str:ward_id>/", WardPatchView.as_view()),
]
