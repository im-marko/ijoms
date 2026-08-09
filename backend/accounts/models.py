from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    invite_code = models.CharField(max_length=12, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def save(self, *args, **kwargs):
        from .utils import generate_company_slug
        if not self.slug:
            self.slug = generate_company_slug(self.name)
        if not self.invite_code:
            self.invite_code = self._unique_invite_code()
        super().save(*args, **kwargs)

    def _unique_invite_code(self):
        from .utils import generate_invite_code
        for _ in range(20):
            code = generate_invite_code(self.name)
            if not Company.objects.filter(invite_code=code).exists():
                return code
        raise RuntimeError('Could not generate a unique invite code.')

    def regenerate_invite_code(self):
        self.invite_code = self._unique_invite_code()
        self.save(update_fields=['invite_code'])
        return self.invite_code

    def __str__(self):
        return self.name


class UserManager(DjangoUserManager):
    """Synthesizes a username from the email when one isn't supplied."""

    def _with_username(self, username, email):
        if not username and email:
            from .utils import generate_username
            username = generate_username(email)
        return username

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        username = self._with_username(username, email)
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        username = self._with_username(username, email)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        OPERATIONS_MANAGER = 'operations_manager', 'Operations Manager'
        SUPERVISOR = 'supervisor', 'Supervisor'
        TECHNICIAN = 'technician', 'Technician'
        FINANCE_OFFICER = 'finance_officer', 'Finance Officer'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.TECHNICIAN)
    phone = models.CharField(max_length=20, blank=True)
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, null=True, blank=True, related_name='users',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_manager_or_above(self):
        return self.role in (self.Role.ADMIN, self.Role.OPERATIONS_MANAGER)

    @property
    def is_supervisor_or_above(self):
        return self.role in (
            self.Role.ADMIN,
            self.Role.OPERATIONS_MANAGER,
            self.Role.SUPERVISOR,
        )
