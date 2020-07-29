from django.urls import path

from . import views

urlpatterns = [
    path('', views.chatroom, name='index'),
    path('welcome', views.welcome),
    path('invisible', views.chatroom, {'invisible': True}),
    #path('invisible', views.invisible),
    path('set_theme', views.set_theme),
    path('set_language', views.set_language),
    path('features', views.features),
    path('online_users_count', views.online_users_count)
    #path('upload', views.upload),
    #path('stream/', views.stream, name='stream'),
]