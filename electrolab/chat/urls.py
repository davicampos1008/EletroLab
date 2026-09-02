from django.urls import path
from . import views

urlpatterns = [
    path('<int:id>/', views.chat_view, name='conversation'),
]