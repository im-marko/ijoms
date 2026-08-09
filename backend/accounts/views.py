from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework_simplejwt.tokens import RefreshToken

from auditlog.mixins import log_action
from ijoms.tenancy import CompanyScopedQuerysetMixin
from jobs.defaults import create_default_categories
from .google import GoogleAuthError, verify_google_token
from .models import Company
from .serializers import (
    UserSerializer, MeSerializer, ChangePasswordSerializer,
    AdminUserCreateSerializer, AdminSetPasswordSerializer,
    SignupCompanySerializer, JoinCompanySerializer, CompanySerializer,
)
from .permissions import IsAdmin

User = get_user_model()


def _auth_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': MeSerializer(user).data,
    }


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


class SignupCompanyView(APIView):
    """Create a company and its first (admin) user."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = SignupCompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_action(
            user=user, action='create', entity_type='Company',
            entity_id=user.company_id, changes={'name': user.company.name},
            request=request, company=user.company,
        )
        return Response(_auth_payload(user), status=status.HTTP_201_CREATED)


class JoinCompanyView(APIView):
    """Join an existing company with its invite code (as technician)."""
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = JoinCompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_action(
            user=user, action='create', entity_type='User',
            entity_id=user.pk, changes={'joined_via': 'invite_code'},
            request=request, company=user.company,
        )
        return Response(_auth_payload(user), status=status.HTTP_201_CREATED)


class CompanyView(APIView):
    """Current user's company; invite code included for admins only."""

    def get(self, request):
        if request.user.company is None:
            return Response({'detail': 'No company assigned.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CompanySerializer(request.user.company, context={'request': request})
        return Response(serializer.data)


class RegenerateInviteView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        company = request.user.company
        if company is None:
            return Response({'detail': 'No company assigned.'}, status=status.HTTP_404_NOT_FOUND)
        code = company.regenerate_invite_code()
        log_action(
            user=request.user, action='update', entity_type='Company',
            entity_id=company.pk, changes={'invite_code': 'regenerated'},
            request=request,
        )
        return Response({'invite_code': code})


class GoogleAuthView(APIView):
    """Sign in or sign up with a Google ID token.

    Existing email -> tokens. New email + invite_code -> join as technician.
    New email + company_name -> create company as admin. New email + neither
    -> {needs_company: true} so the frontend can ask, creating nothing.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'google'

    def post(self, request):
        credential = request.data.get('credential', '')
        try:
            claims = verify_google_token(credential)
        except GoogleAuthError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        email = claims['email']
        user = User.objects.filter(email__iexact=email).first()
        if user is not None:
            if not user.is_active:
                return Response({'detail': 'Account disabled.'}, status=status.HTTP_401_UNAUTHORIZED)
            log_action(user=user, action='login', entity_type='User',
                       entity_id=user.pk, request=request)
            return Response(_auth_payload(user))

        invite_code = (request.data.get('invite_code') or '').strip()
        company_name = (request.data.get('company_name') or '').strip()

        if invite_code:
            company = Company.objects.filter(invite_code__iexact=invite_code).first()
            if company is None:
                return Response(
                    {'invite_code': ['Invalid invite code.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = User.objects.create_user(
                email=email, company=company, role=User.Role.TECHNICIAN,
                first_name=claims['given_name'], last_name=claims['family_name'],
            )
            user.set_unusable_password()
            user.save(update_fields=['password'])
        elif company_name:
            from django.db import transaction
            with transaction.atomic():
                company = Company.objects.create(name=company_name)
                user = User.objects.create_user(
                    email=email, company=company, role=User.Role.ADMIN,
                    first_name=claims['given_name'], last_name=claims['family_name'],
                )
                user.set_unusable_password()
                user.save(update_fields=['password'])
                create_default_categories(company)
        else:
            return Response({
                'needs_company': True,
                'email': email,
                'first_name': claims['given_name'],
                'last_name': claims['family_name'],
            })

        log_action(user=user, action='login', entity_type='User',
                   entity_id=user.pk, request=request)
        return Response(_auth_payload(user), status=status.HTTP_201_CREATED)


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


class UserListCreateView(CompanyScopedQuerysetMixin, generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    queryset = User.objects.all().order_by('id')
    filterset_fields = ['role', 'is_active']
    search_fields = ['first_name', 'last_name', 'email']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserCreateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save(company=self.request.user.company)
        log_action(
            user=self.request.user, action='create', entity_type='User',
            entity_id=user.pk,
            changes={'email': user.email, 'role': user.role},
            request=self.request,
        )


class UserDetailView(CompanyScopedQuerysetMixin, generics.RetrieveUpdateAPIView):
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
            target = User.objects.filter(company=request.user.company).get(pk=pk)
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
        if self.request.user.company_id is None:
            return User.objects.none()
        return User.objects.filter(
            company_id=self.request.user.company_id,
            role='technician', is_active=True,
        )
