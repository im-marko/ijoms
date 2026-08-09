from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Company

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'role_display', 'phone', 'is_active', 'date_joined',
            'company', 'company_name',
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'company', 'company_name']


class MeSerializer(UserSerializer):
    """Self-service profile serializer — identity/authorization fields locked."""
    has_usable_password = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['has_usable_password']
        read_only_fields = [
            'id', 'username', 'email', 'role', 'is_active', 'date_joined',
            'company', 'company_name', 'has_usable_password',
        ]

    def get_has_usable_password(self, obj):
        return obj.has_usable_password()


class CompanySerializer(serializers.ModelSerializer):
    invite_code = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'created_at', 'invite_code']

    def get_invite_code(self, obj):
        request = self.context.get('request')
        if request and request.user.role == User.Role.ADMIN:
            return obj.invite_code
        return None


class BaseSignupSerializer(serializers.Serializer):
    """Shared personal fields for the two self-signup flows."""
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs


class SignupCompanySerializer(BaseSignupSerializer):
    company_name = serializers.CharField(max_length=200)

    def create(self, validated_data):
        from django.db import transaction
        from jobs.defaults import create_default_categories

        with transaction.atomic():
            company = Company.objects.create(name=validated_data.pop('company_name'))
            user = User.objects.create_user(
                company=company, role=User.Role.ADMIN, **validated_data,
            )
            create_default_categories(company)
        return user


class JoinCompanySerializer(BaseSignupSerializer):
    invite_code = serializers.CharField(max_length=12)

    def validate_invite_code(self, value):
        company = Company.objects.filter(invite_code__iexact=value.strip()).first()
        if company is None:
            raise serializers.ValidationError('Invalid invite code.')
        self._company = company
        return value

    def create(self, validated_data):
        validated_data.pop('invite_code')
        return User.objects.create_user(
            company=self._company, role=User.Role.TECHNICIAN, **validated_data,
        )


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'phone', 'is_active', 'password',
        ]
        read_only_fields = ['id', 'username']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class AdminSetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[validate_password])


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Incorrect current password.')
        return value
