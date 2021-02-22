from django.urls import path

from .views import Sounds

urlpatterns = [
    path('dashboard/', Sounds.as_view(), name="dashboard"),
]
