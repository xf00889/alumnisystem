from django.urls import path, include
from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'blocks', views.UserBlockViewSet, basename='block')

conversations_router = routers.NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

app_name = 'chat'

urlpatterns = [
    path('', views.ChatView.as_view(), name='chat'),
    path('<int:conversation>/', views.ChatView.as_view(), name='chat_with_id'),
    path('new/', views.new_conversation, name='new_conversation'),
    path('create-group/', views.create_group, name='create_group'),
    path('send/<int:conversation_id>/', views.send_message, name='send_message'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('open/<int:user_id>/', views.open_conversation, name='open_conversation'),
    path('search-users/', views.search_users, name='search_users'),
    path('api/', include(router.urls)),
    path('api/', include(conversations_router.urls)),
] 