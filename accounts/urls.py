from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),
    path('search/candidates/', views.search_candidates, name='accounts.search_candidates'),
    path('profile/', views.seeker_profile, name='accounts.seeker_profile'),
    path('messages/', views.list_conversations, name='accounts.list_conversations'),
    path('messages/conversation/<int:conversation_id>/', views.view_conversation, name='accounts.view_conversation'),
    path('messages/start/<int:seeker_id>/', views.start_conversation, name='accounts.start_conversation'),
    path('profile/projects/add/', views.add_project, name='accounts.add_project'),
    path('profile/projects/<int:project_id>/edit/', views.edit_project, name='accounts.edit_project'),
    path('profile/projects/<int:project_id>/delete/', views.delete_project, name='accounts.delete_project'),
    path('send_message/<int:seeker_id>/', views.send_message, name='accounts.send_message'),
    path('send_email/<int:seeker_id>/', views.send_email, name='accounts.send_email'),
    # Saved searches and notifications
    path('search/save/', views.save_search, name='accounts.save_search'),
    path('search/saved/', views.my_saved_searches, name='accounts.my_saved_searches'),
    path('search/saved/<int:search_id>/delete/', views.delete_saved_search, name='accounts.delete_saved_search'),
    path('notifications/search/', views.search_notifications, name='accounts.search_notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='accounts.mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='accounts.mark_all_notifications_read'),
    # Work experience endpoints
    path('profile/experience/add/', views.add_work_experience, name='accounts.add_work_experience'),
    path('profile/experience/<int:experience_id>/update/', views.update_work_experience, name='accounts.update_work_experience'),
    path('profile/experience/<int:experience_id>/delete/', views.delete_work_experience, name='accounts.delete_work_experience'),
    path('profile/experience/<int:experience_id>/', views.get_work_experience, name='accounts.get_work_experience'),
]