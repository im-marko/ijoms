from django.urls import path
from . import views

urlpatterns = [
    path('', views.NoticeListView.as_view(), name='notice_list'),
    path('create/', views.NoticeCreateView.as_view(), name='notice_create'),
    path('<int:pk>/', views.NoticeDetailView.as_view(), name='notice_detail'),
]
