from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('signup-company/', views.SignupCompanyView.as_view(), name='signup_company'),
    path('join/', views.JoinCompanyView.as_view(), name='join_company'),
    path('google/', views.GoogleAuthView.as_view(), name='google_auth'),
    path('login/', views.LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.MeView.as_view(), name='me'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('company/', views.CompanyView.as_view(), name='company'),
    path('company/regenerate-invite/', views.RegenerateInviteView.as_view(), name='regenerate_invite'),
    path('users/', views.UserListCreateView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/set-password/', views.SetPasswordView.as_view(), name='user_set_password'),
    path('technicians/', views.TechnicianListView.as_view(), name='technician_list'),
]
