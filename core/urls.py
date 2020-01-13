from django.urls import path
from django.shortcuts import HttpResponse
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('robots.txt', lambda x: HttpResponse("User-Agent: *\nDisallow: /", content_type="text/plain"), name="robots_file"),
    path('faqs/', views.get_faqs, name='get_faqs'),
    path('privacy/', views.get_privacy, name='get_privacy'),
    path('terms/', views.get_terms, name='get_terms'),
    path('health/', views.health, name='health'),
    path('shipping/edit/', views.edit_shipping, name='edit_shipping'),
]
