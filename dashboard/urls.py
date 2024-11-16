from django.urls import path
from . import views  # Ensure this imports views where your DjangoDash app is defined

app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='homepage'), 
    path('api/v1/create_test_board', views.create_board.CreateBoard.as_view(), name='api'), 
]
