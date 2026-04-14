from rest_framework.permissions import BasePermission


class IsManagingDirector(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'managing_director'


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
    """Managing Director or Operations Manager"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('managing_director', 'operations_manager')
        )


class IsSupervisorOrAbove(BasePermission):
    """Managing Director, Operations Manager, or Supervisor"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('managing_director', 'operations_manager', 'supervisor')
        )


class CanViewJobs(BasePermission):
    """All roles except Finance Officer can view jobs"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role != 'finance_officer'
        )


class CanManageJobs(BasePermission):
    """Operations Manager and Supervisor can create/assign jobs"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('operations_manager', 'supervisor')
        )
