from django.urls import path
from items import views


urlpatterns = [
    path('', views.list_items, name='list_items'),
    path('create/', views.create_item, name='create_item'),
    path('<int:item_id>/', views.get_item, name='get_item'),
    path('<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('<int:item_id>/delete/', views.delete_item, name='delete_item'),
]
