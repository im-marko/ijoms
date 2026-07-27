from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsOperationsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'operations_manager'


class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'supervisor'


class IsTechnician(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'technician'


class IsFinanceOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'finance_officer'


class IsManagerOrAbove(BasePermission):
    """Admin or Operations Manager"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('admin', 'operations_manager')
        )


class IsSupervisorOrAbove(BasePermission):
    """Admin, Operations Manager, or Supervisor"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('admin', 'operations_manager', 'supervisor')
        )


class CanViewJobs(BasePermission):
    """All roles can view jobs; Finance Officer is read-only."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role == 'finance_officer':
            return request.method in SAFE_METHODS
        return True


class CanManageJobs(BasePermission):
    """Operations Manager and Supervisor can create/assign jobs"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('operations_manager', 'supervisor')
        )
