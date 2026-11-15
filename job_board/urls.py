from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='job_board.index'),
    path('my-listings/', views.recruiter_listings, name='job_board.recruiter_listings'),
    path('create-listing/', views.create_listing, name='job_board.create_listing'),
    path('edit-listing/<int:job_id>/', views.edit_listing, name='job_board.edit_listing'),
    path('apply/<int:job_id>/', views.apply_to_job, name='job_board.apply'),
    path('my-applications/', views.my_applications, name='job_board.my_applications'),
    path('manage-applications/', views.manage_applications, name='job_board.manage_applications'),
    path('applications/kanban/<int:job_id>/', views.application_kanban, name='job_board.application_kanban'),
    path('api/jobs-map/', views.jobs_map_api, name='job_board.jobs_map_api'),
    path('api/job-location/<int:job_id>/', views.job_location_api, name='job_board.job_location_api'),
    path('api/applicants-map/<int:job_id>/', views.applicants_map_api, name='job_board.applicants_map_api'),
    path('applications/<int:application_id>/update-status/', views.update_application_status, name='job_board.update_application_status'),
]