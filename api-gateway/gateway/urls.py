from django.urls import re_path
from .views import ProxyView

urlpatterns = [
    # Capture tout le chemin après le slash
    re_path(r'^(?P<path>.*)$', ProxyView.as_view()),
]