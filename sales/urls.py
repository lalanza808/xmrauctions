from django.urls import path
from . import views


urlpatterns = [
    path('<int:bid_id>/', views.get_sale, name='get_sale'),
]
