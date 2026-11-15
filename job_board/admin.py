from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.urls import path
from .models import JobListing
from accounts.models import AdminAction

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'recruiter', 'status']
    list_filter = []
    search_fields = []
    readonly_fields = []
    actions = ['approve_jobs', 'remove_jobs', 'delete_jobs']
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        queryset.delete()

    def response_delete(self, request, obj_display, obj_id):
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('admin:job_board_joblisting_changelist'))
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name in form.base_fields:
            form.base_fields[field_name].help_text = ''
        if 'recruiter' in form.base_fields:
            form.base_fields['recruiter'].widget.can_add_related = False
            form.base_fields['recruiter'].widget.can_change_related = False
            form.base_fields['recruiter'].widget.can_delete_related = False
            form.base_fields['recruiter'].widget.can_view_related = False
        return form
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'recruiter', 'skills', 'location', 'salary')
        }),
        ('Job Details', {
            'fields': ('is_remote', 'is_visa_offered')
        }),
        ('Moderation', {
            'fields': ('status',)
        }),
    )
    
    def approve_jobs(self, request, queryset):
        for job in queryset:
            if job.status != 'approved':
                old_status = job.status
                job.status = 'approved'
                job.rejection_reason = ''
                job.save()
                
                AdminAction.objects.create(
                    admin_user=request.user,
                    action_type='job_approve',
                    reason=f"Job status changed from {old_status} to approved by admin {request.user.username}"
                )
    approve_jobs.short_description = "Approve selected jobs"
    
    def remove_jobs(self, request, queryset):
        for job in queryset:
            if job.status != 'removed':
                old_status = job.status
                job.status = 'removed'
                job.save()
                
                AdminAction.objects.create(
                    admin_user=request.user,
                    action_type='job_remove',
                    reason=f"Job status changed from {old_status} to removed by admin {request.user.username}"
                )
    remove_jobs.short_description = "Remove selected jobs"
    
    def delete_jobs(self, request, queryset):
        for job in queryset:
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='job_delete',
                reason=f"Job '{job.title}' deleted by admin {request.user.username}"
            )
        queryset.delete()
    delete_jobs.short_description = "Delete selected jobs"
    
    
    def save_model(self, request, obj, form, change):
        if change:
            original_obj = JobListing.objects.get(pk=obj.pk)
            
            if original_obj.status != obj.status:
                action_type_map = {
                    'approved': 'job_approve',
                    'rejected': 'job_reject',
                    'removed': 'job_remove'
                }
                
                action_type = action_type_map.get(obj.status, 'job_approve')
                reason = f"Status changed from {original_obj.status} to {obj.status} by admin {request.user.username}"
                
                AdminAction.objects.create(
                    admin_user=request.user,
                    action_type=action_type,
                    reason=reason
                )
        
        super().save_model(request, obj, form, change)