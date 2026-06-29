from django.urls import path
from .views import ContactListCreateView, ContactRetrieveUpdateDestroyView

urlpatterns = [
    path('', ContactListCreateView.as_view(), name='contact-list-create'),
    path('<int:pk>/', ContactRetrieveUpdateDestroyView.as_view(), name='contact-detail'),
]
