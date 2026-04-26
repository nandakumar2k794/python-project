from django.urls import path
from .views import NotificationListView,NotificationReadAllView
urlpatterns=[path("",NotificationListView.as_view()),path("read-all/",NotificationReadAllView.as_view())]
