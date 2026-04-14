from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'subject', 'message', 'status',
            'related_job', 'read', 'sent_at', 'created_at',
        ]


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class UnreadCountView(APIView):
    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user, read=False, type='in_app'
        ).count()
        return Response({'unread_count': count})


class MarkReadView(APIView):
    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        notif.read = True
        notif.save()
        return Response({'detail': 'Marked as read.'})


class MarkAllReadView(APIView):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response({'detail': 'All notifications marked as read.'})
