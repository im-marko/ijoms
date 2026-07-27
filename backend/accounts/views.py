from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from auditlog.mixins import log_action
from .serializers import (
    UserSerializer, MeSerializer, RegisterSerializer, ChangePasswordSerializer,
    AdminUserCreateSerializer, AdminSetPasswordSerializer,
)
from .permissions import IsAdmin

User = get_user_model()


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.filter(email=request.data.get('email', '')).first()
            if user:
                log_action(
                    user=user, action='login', entity_type='User',
                    entity_id=user.pk, request=request,
                )
        return response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password updated successfully.'})


class UserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    queryset = User.objects.all().order_by('id')
    filterset_fields = ['role', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserCreateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        log_action(
            user=self.request.user, action='create', entity_type='User',
            entity_id=user.pk,
            changes={'email': user.email, 'role': user.role},
            request=self.request,
        )


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def perform_update(self, serializer):
        target = self.get_object()
        if target == self.request.user:
            new_role = serializer.validated_data.get('role', target.role)
            new_active = serializer.validated_data.get('is_active', target.is_active)
            if new_role != target.role or not new_active:
                from rest_framework.exceptions import ValidationError
                raise ValidationError('You cannot change your own role or deactivate yourself.')
        user = serializer.save()
        log_action(
            user=self.request.user, action='update', entity_type='User',
            entity_id=user.pk, changes=serializer.validated_data,
            request=self.request,
        )


class SetPasswordView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            target = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminSetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target.set_password(serializer.validated_data['new_password'])
        target.save()
        log_action(
            user=request.user, action='update', entity_type='User',
            entity_id=target.pk, changes={'password': 'reset by administrator'},
            request=request,
        )
        return Response({'detail': f'Password updated for {target.email}.'})


class TechnicianListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(role='technician', is_active=True)
