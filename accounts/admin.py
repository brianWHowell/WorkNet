from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils import timezone
from django.contrib import messages
from django.urls import path
from django.http import HttpResponse
import csv
from datetime import datetime
from .models import Account, Recruiter, Seeker, Skill, Project, AdminAction, UserReport, SavedSearch, SearchNotification

admin.site.site_header = 'WorkNet Admins!'
admin.site.site_title = 'WorkNet Admin'
admin.site.index_title = 'WorkNet Admin Panel'
from django.contrib.auth.models import Group
admin.site.unregister(Group)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'account_type']
    list_filter = ['account_type', 'is_active', 'is_suspended', 'date_joined', 'profile_visibility']
    search_fields = []
    readonly_fields = []
    actions = ['ban_users', 'unban_users', 'delete_selected_users', 'export_accounts_csv']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'account_type')
        }),
        ('Profile Details', {
            'fields': ('location', 'bio', 'years_of_experience')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_suspended')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name in form.base_fields:
            form.base_fields[field_name].help_text = ''
        if 'is_suspended' in form.base_fields:
            form.base_fields['is_suspended'].label = 'Banned'
        return form
    
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
        
        return HttpResponseRedirect(reverse('admin:accounts_account_changelist'))
    
    
    def ban_users(self, request, queryset):
        for user in queryset:
            if not user.is_suspended:
                user.is_suspended = True
                user.suspension_reason = f"Banned by admin {request.user.username}"
                user.suspension_date = timezone.now()
                user.save()
                
                AdminAction.objects.create(
                    admin_user=request.user,
                    action_type='user_suspend',
                    target_user=user,
                    reason=f"Banned by admin {request.user.username}"
                )
        
    ban_users.short_description = "Ban selected users"
    
    def unban_users(self, request, queryset):
        for user in queryset:
            if user.is_suspended:
                user.is_suspended = False
                user.suspension_reason = ''
                user.suspension_date = None
                user.save()
                
                AdminAction.objects.create(
                    admin_user=request.user,
                    action_type='user_activate',
                    target_user=user,
                    reason=f"Unbanned by admin {request.user.username}"
                )
        
    unban_users.short_description = "Unban selected users"
    
    def delete_selected_users(self, request, queryset):
        queryset.delete()
    delete_selected_users.short_description = "Delete selected users"
    
    def export_accounts_csv(self, request, queryset):
        """Export selected/filtered accounts to CSV"""
        # Filter to only include seekers and recruiters (exclude admin accounts)
        accounts = queryset.filter(account_type__in=['seeker', 'recruiter'])
        
        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'accounts_export_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'Username',
            'Email',
            'First Name',
            'Last Name',
            'Account Type',
            'Location',
            'Bio',
            'Years of Experience',
            'Is Active',
            'Is Suspended',
            'Suspension Reason',
            'Suspension Date',
            'Profile Visibility',
            'Hide Location',
            'Hide Skills',
            'Hide Experience',
            'Hide Projects',
            'Date Joined',
            'Last Login',
            'Skills',
            'Projects'
        ])
        
        # Write data rows
        for account in accounts:
            # Get skills as comma-separated string
            skills = ', '.join([skill.name for skill in account.skills.all()])
            
            # Get projects as comma-separated string
            projects = ', '.join([project.title for project in account.projects.all()])
            
            # Format dates
            date_joined = account.date_joined.strftime('%Y-%m-%d %H:%M:%S') if account.date_joined else ''
            last_login = account.last_login.strftime('%Y-%m-%d %H:%M:%S') if account.last_login else ''
            suspension_date = account.suspension_date.strftime('%Y-%m-%d %H:%M:%S') if account.suspension_date else ''
            
            writer.writerow([
                account.username or '',
                account.email or '',
                account.first_name or '',
                account.last_name or '',
                account.get_account_type_display() if account.account_type else '',
                account.location or '',
                account.bio or '',
                account.years_of_experience or '',
                'Yes' if account.is_active else 'No',
                'Yes' if account.is_suspended else 'No',
                account.suspension_reason or '',
                suspension_date,
                account.get_profile_visibility_display() if account.profile_visibility else '',
                'Yes' if account.hide_location else 'No',
                'Yes' if account.hide_skills else 'No',
                'Yes' if account.hide_experience else 'No',
                'Yes' if account.hide_projects else 'No',
                date_joined,
                last_login,
                skills,
                projects
            ])
        
        return response
    
    export_accounts_csv.short_description = "Export selected accounts to CSV"

@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_email']
    search_fields = []
    readonly_fields = ['get_username', 'get_email', 'get_location', 'get_job_count', 'get_company_info']
    list_filter = []
    
    fieldsets = (
        ('Recruiter Information', {
            'fields': ('get_username', 'get_email', 'get_location', 'get_company_info')
        }),
        ('Stats', {
            'fields': ('get_job_count',)
        }),
    )
    
    def get_queryset(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(account_type='recruiter')

    def has_add_permission(self, request):
        # Read-only view over Accounts; profiles are created through signup
        return False
    
    def get_username(self, obj):
        return obj.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.email
    get_email.short_description = 'Email'
    
    def get_location(self, obj):
        return obj.location or 'N/A'
    get_location.short_description = 'Location'
    
    def get_company_info(self, obj):
        if obj.bio:
            return obj.bio[:100] + ('...' if len(obj.bio) > 100 else '')
        return 'N/A'
    get_company_info.short_description = 'Company Info'
    
    def get_job_count(self, obj):
        from job_board.models import JobListing
        return JobListing.objects.filter(recruiter=obj, status='approved').count()
    get_job_count.short_description = 'Approved Jobs'
    
    def get_total_jobs(self, obj):
        from job_board.models import JobListing
        return JobListing.objects.filter(recruiter=obj).count()
    get_total_jobs.short_description = 'Total Jobs Posted'
    

@admin.register(Seeker)
class SeekerAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_email']
    search_fields = []
    readonly_fields = ['get_username', 'get_email', 'get_location', 'get_years_experience', 'get_skills_count', 'get_skills_list', 'get_projects_list', 'get_profile_summary']
    list_filter = []
    
    fieldsets = (
        ('Seeker Information', {
            'fields': ('get_username', 'get_email', 'get_location', 'get_years_experience')
        }),
        ('Experience & Skills', {
            'fields': ('get_skills_count', 'get_skills_list')
        }),
        ('Projects Portfolio', {
            'fields': ('get_projects_list',)
        }),
        ('Bio', {
            'fields': ('get_profile_summary',)
        }),
    )
    
    def get_queryset(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(account_type='seeker')

    def has_add_permission(self, request):
        # Read-only view over Accounts; profiles are created through signup
        return False
    
    def get_username(self, obj):
        return obj.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.email
    get_email.short_description = 'Email'
    
    def get_location(self, obj):
        return obj.location or 'N/A'
    get_location.short_description = 'Location'
    
    def get_years_experience(self, obj):
        return obj.years_of_experience or 'N/A'
    get_years_experience.short_description = 'Years Experience'
    
    def get_skills_count(self, obj):
        return obj.skills.count()
    get_skills_count.short_description = 'Skills Count'
    
    def get_skills_list(self, obj):
        skills = obj.skills.all()
        if not skills:
            return "N/A"
        return ", ".join([skill.name for skill in skills])
    get_skills_list.short_description = 'Skills List'
    
    def get_projects_count(self, obj):
        return obj.projects.count()
    get_projects_count.short_description = 'Projects Count'
    
    def get_projects_list(self, obj):
        projects = obj.projects.all()
        if not projects:
            return "N/A"
        return ", ".join([project.title for project in projects])
    get_projects_list.short_description = 'Projects List'
    
    def get_profile_summary(self, obj):
        if obj.bio:
            return f"Bio: {obj.bio[:100]}{'...' if len(obj.bio) > 100 else ''}"
        else:
            return "Bio: N/A"
    get_profile_summary.short_description = 'Profile Summary'

@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ['name', 'recruiter', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'recruiter__username']
    readonly_fields = ['created_at']
    
@admin.register(SearchNotification)
class SearchNotificationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'saved_search', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['candidate__username', 'saved_search__name']
    readonly_fields = ['created_at']
