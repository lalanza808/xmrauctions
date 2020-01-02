from django.urls import path
from . import views


urlpatterns = [
    path('', views.list_bids, name='list_bids'),
    path('<int:bid_id>/accept/', views.accept_bid, name='accept_bid'),
    path('<int:bid_id>/delete/', views.delete_bid, name='delete_bid'),
    path('<int:bid_id>/edit/', views.edit_bid, name='edit_bid'),
    path('item/<int:item_id>/create/', views.create_bid, name='create_bid'),
]
