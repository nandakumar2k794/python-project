from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.issues.models import Issue, Ward

class AdminAnalyticsView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        if request.user.role!="admin": return Response({"detail":"Forbidden"}, status=403)
        total=Issue.objects.count()
        resolved=Issue.objects(status="Resolved").count()
        return Response({"total_issues":total, "resolution_rate":0 if total==0 else round(resolved*100/total,2), "category_breakdown":Issue.objects.item_frequencies("category")})

class WardView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        return Response([{"id":str(w.id),"name":w.name,"district":w.district} for w in Ward.objects.all()])
    def post(self, request):
        if request.user.role!="admin": return Response({"detail":"Forbidden"}, status=403)
        w=Ward(name=request.data["name"], district=request.data.get("district","District"), boundary_geojson=request.data.get("boundary_geojson",{}))
        w.save()
        return Response({"id":str(w.id)}, status=201)

class WardPatchView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self, request, ward_id):
        if request.user.role!="admin": return Response({"detail":"Forbidden"}, status=403)
        w=Ward.objects.get(id=ward_id)
        for key in ["name","district","boundary_geojson","officer_ids","stats"]:
            if key in request.data: setattr(w,key,request.data[key])
        w.save()
        return Response({"detail":"updated"})
