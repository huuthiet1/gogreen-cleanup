from django.urls import path
from app.views.home import home

urlpatterns = [
    path("", home, name="home"),
]
