from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('shipping/edit/', views.edit_shipping, name='edit_shipping')
]
