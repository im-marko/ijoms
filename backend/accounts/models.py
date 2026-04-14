from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGING_DIRECTOR = 'managing_director', 'Managing Director'
        OPERATIONS_MANAGER = 'operations_manager', 'Operations Manager'
        SUPERVISOR = 'supervisor', 'Supervisor'
        TECHNICIAN = 'technician', 'Technician'
        FINANCE_OFFICER = 'finance_officer', 'Finance Officer'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.TECHNICIAN)
    phone = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'role']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_manager_or_above(self):
        return self.role in (self.Role.MANAGING_DIRECTOR, self.Role.OPERATIONS_MANAGER)

    @property
    def is_supervisor_or_above(self):
        return self.role in (
            self.Role.MANAGING_DIRECTOR,
            self.Role.OPERATIONS_MANAGER,
            self.Role.SUPERVISOR,
        )
