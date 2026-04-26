from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
class NotificationListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,r):
        n=Notification.objects(user_id=str(r.user.id)).order_by("-created_at")
        return Response([{"id":str(i.id),"type":i.type,"message":i.message,"is_read":i.is_read} for i in n])
class NotificationReadAllView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,r):
        Notification.objects(user_id=str(r.user.id)).update(set__is_read=True); return Response({"detail":"updated"})
