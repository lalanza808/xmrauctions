from django.urls import path
from . import views


urlpatterns = [
    path('<int:sale_id>/', views.get_sale, name='get_sale'),
    path('<int:sale_id>/cancel', views.cancel_sale, name='cancel_sale'),
    path('<int:sale_id>/confirm_shipment/', views.confirm_shipment, name='confirm_shipment'),
    path('<int:sale_id>/confirm_receipt/', views.confirm_receipt, name='confirm_receipt')
]
