from django.urls import path

from . import views

urlpatterns = [
    path('', views.chatroom, name='index'),
    path('set_theme', views.set_theme),
    #path('stream/', views.stream, name='stream'),
]
