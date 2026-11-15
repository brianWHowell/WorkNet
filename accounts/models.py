from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    skills_used = models.ManyToManyField(Skill)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.title

class Account(AbstractUser):
    ACCOUNT_TYPES = (
        ('recruiter', 'Recruiter'),
        ('seeker', 'Seeker'),
        ('admin', 'Administrator'),
    )
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    email = models.EmailField(blank=True, null=True, help_text='Email address for the account')
    location = models.CharField(max_length=100, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    projects = models.ManyToManyField(Project, blank=True)
    bio = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)
    suspension_date = models.DateTimeField(null=True, blank=True)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=10, 
        choices=[('public', 'Public'), ('private', 'Private')], 
        default='public',
        help_text='Control overall profile visibility to recruiters'
    )
    hide_location = models.BooleanField(default=False, help_text='Hide location from recruiters')
    hide_skills = models.BooleanField(default=False, help_text='Hide skills from recruiters')
    hide_experience = models.BooleanField(default=False, help_text='Hide years of experience from recruiters')
    hide_projects = models.BooleanField(default=False, help_text='Hide projects from recruiters')

class Recruiter(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    job_listings = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.user.username

class Seeker(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    skills = models.CharField(max_length=500, blank=True, help_text='Comma-separated skills')
    location = models.CharField(max_length=200, blank=True)
    projects = models.TextField(blank=True, help_text='Short description or comma-separated project names')

    def __str__(self):
        return self.user.username

class AdminAction(models.Model):
    """Track admin actions for audit purposes"""
    ACTION_TYPES = (
        ('user_suspend', 'User Suspended'),
        ('user_activate', 'User Activated'),
        ('user_delete', 'User Deleted'),
        ('job_approve', 'Job Approved'),
        ('job_reject', 'Job Rejected'),
        ('job_remove', 'Job Removed'),
    )
    
    admin_user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='admin_actions_received', null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.get_action_type_display()}"

class Conversation(models.Model):
    """Conversation thread between a recruiter and a job seeker"""
    recruiter = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='recruiter_conversations', limit_choices_to={'account_type': 'recruiter'})
    seeker = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='seeker_conversations', limit_choices_to={'account_type': 'seeker'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['recruiter', 'seeker']
    
    def __str__(self):
        return f"Conversation: {self.recruiter.username} ↔ {self.seeker.username}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if user == self.recruiter:
            return self.seeker
        return self.recruiter
    
    def get_unread_count(self, user):
        """Get the count of unread messages for a user"""
        return self.messages.filter(recipient=user, is_read=False).count()
    
    def clean(self):
        """Validate that recruiter and seeker are of correct account types"""
        from django.core.exceptions import ValidationError
        if self.recruiter.account_type != 'recruiter':
            raise ValidationError('Recruiter field must be a recruiter account.')
        if self.seeker.account_type != 'seeker':
            raise ValidationError('Seeker field must be a seeker account.')
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)

class Message(models.Model):
    """Messages between recruiters and seekers"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}: {self.subject or '(no subject)'}"

class UserReport(models.Model):
    """Reports submitted by users about other users or job posts"""
    REPORT_TYPES = (
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('fake', 'Fake Job/Profile'),
        ('harassment', 'Harassment'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    
    reporter = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.reported_user:
            return f"Report against {self.reported_user.username} - {self.get_report_type_display()}"
        return f"Report - {self.get_report_type_display()}"

class SavedSearch(models.Model):
    """Saved search criteria for recruiters"""
    recruiter = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=200, default='Untitled Search')
    skills = models.ManyToManyField(Skill, blank=True)
    location = models.CharField(max_length=100, blank=True)
    years_of_experience = models.IntegerField(null=True, blank=True)
    keywords = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_candidate_id = models.IntegerField(null=True, blank=True, help_text='Track last candidate seen to identify new ones')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recruiter.username} - {self.name}"

class SearchNotification(models.Model):
    """Notifications for recruiters when new candidates match their saved searches"""
    saved_search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE, related_name='notifications')
    candidate = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='search_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['saved_search', 'candidate']
    
    def __str__(self):
        return f"New candidate match: {self.candidate.username} for search: {self.saved_search.name}"

class WorkExperience(models.Model):
    """Work experience entries for job seekers"""
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='work_experiences', limit_choices_to={'account_type': 'seeker'})
    position = models.CharField(max_length=200, help_text='Job title/position')
    company = models.CharField(max_length=200, help_text='Company name')
    start_date = models.DateField(help_text='Start date')
    end_date = models.DateField(null=True, blank=True, help_text='End date (leave blank if currently employed)')
    description = models.TextField(help_text='Job description, responsibilities, and achievements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date', '-end_date']
    
    def __str__(self):
        return f"{self.position} at {self.company} - {self.user.username}"
    
    def clean(self):
        """Validate that end_date is after start_date if provided"""
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date must be after start date.')
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)