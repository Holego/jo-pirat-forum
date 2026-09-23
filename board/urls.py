from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/links/add/', views.add_profile_link, name='add_profile_link'),
    path('profile/links/<int:pk>/delete/', views.delete_profile_link, name='delete_profile_link'),
    path('u/<str:username>/', views.profile_detail, name='profile_detail'),
    path('c/new/', views.new_category, name='new_category'),
    path('c/<str:slug>/', views.category_detail, name='category_detail'),
    path('c/<str:slug>/new/', views.new_topic, name='new_topic'),
    path('c/<str:slug>/t/<int:pk>/', views.topic_detail, name='topic_detail'),
]
