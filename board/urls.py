from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('c/<str:slug>/', views.category_detail, name='category_detail'),
    path('c/<str:slug>/new/', views.new_topic, name='new_topic'),
    path('c/<str:slug>/t/<int:pk>/', views.topic_detail, name='topic_detail'),
]
