from django.urls import path

from . import api_views

urlpatterns = [
    path('', api_views.api_root, name='api_root'),
    path('auth/login/', api_views.LoginView.as_view(), name='api_login'),
    path('auth/register/', api_views.RegisterView.as_view(), name='api_register'),
    path('auth/logout/', api_views.LogoutView.as_view(), name='api_logout'),
    path('me/', api_views.MeView.as_view(), name='api_me'),
    path('categories/', api_views.CategoryList.as_view(), name='api_categories'),
    path('categories/<str:slug>/topics/', api_views.CategoryTopicList.as_view(), name='api_category_topics'),
    path('topics/<int:pk>/', api_views.TopicDetail.as_view(), name='api_topic'),
    path('topics/<int:pk>/posts/', api_views.TopicPostList.as_view(), name='api_topic_posts'),
    path('messages/', api_views.ConversationList.as_view(), name='api_conversations'),
    path('messages/<str:username>/', api_views.ConversationThread.as_view(), name='api_conversation'),
]
