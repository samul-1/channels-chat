from django.urls import path


from . import views

urlpatterns = [
    path('', views.chatroom, name='index'),
    path('welcome', views.welcome),
    path('invisible', views.chatroom, {'invisible': True}),
    #path('invisible', views.invisible),
    path('set_theme', views.set_theme),
    path('features', views.features),
    path('upload', views.upload),
    #path('stream/', views.stream, name='stream'),
]