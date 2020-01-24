from django.urls import path
from django.shortcuts import HttpResponse
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('robots.txt', lambda x: HttpResponse("User-Agent: *\nDisallow: /", content_type="text/plain"), name="robots_file"),
    path('help/', views.get_help, name='get_help'),
    path('health/', views.health, name='health'),
    path('shipping/edit/', views.edit_shipping, name='edit_shipping'),
]
