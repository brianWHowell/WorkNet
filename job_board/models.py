from django.db import models
from accounts.models import Account

class JobListing(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('removed', 'Removed'),
    ]

    recruiter = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='listings', limit_choices_to={'account_type': 'recruiter'}, null=True, blank=True)
    title = models.CharField(max_length=200)
    skills = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True, help_text='Latitude for map display (auto-geocoded)')
    longitude = models.FloatField(null=True, blank=True, help_text='Longitude for map display (auto-geocoded)')
    salary = models.IntegerField(default=50000)
    is_remote = models.BooleanField(default=False)
    is_visa_offered = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='approved')
    rejection_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.recruiter.username if self.recruiter else 'Unknown'}"

class Application(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('review', 'Review'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('closed', 'Closed'),
    ]

    job_listing = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    seeker = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='applications', limit_choices_to={'account_type': 'seeker'})
    application_message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job_listing', 'seeker')

    def __str__(self):
        return f"{self.seeker.username} applied to {self.job_listing.title}"