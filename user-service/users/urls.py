from django.urls import path
from .views import UserListCreateView, UserRetrieveView

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserRetrieveView.as_view(), name='user-detail'),
]