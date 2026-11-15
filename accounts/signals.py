from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from .models import Account, SavedSearch, SearchNotification
from django.db.models import Q
from django.db import transaction

def check_and_notify(candidate_id):
    """Check if a candidate matches any saved searches and create notifications"""
    try:
        # Refresh from database to ensure all relationships are loaded
        candidate = Account.objects.prefetch_related('skills', 'projects').get(id=candidate_id)
        
        if candidate.account_type != 'seeker' or candidate.profile_visibility != 'public':
            return
        
        saved_searches = SavedSearch.objects.filter(
            recruiter__account_type='recruiter'
        ).prefetch_related('skills')
        
        for saved_search in saved_searches:
            if matches_saved_search(candidate, saved_search):
                # Create notification if it doesn't already exist
                SearchNotification.objects.get_or_create(
                    saved_search=saved_search,
                    candidate=candidate
                )
    except Account.DoesNotExist:
        pass

def create_notification_checker(candidate_id):
    """Factory function to create a checker with the candidate_id"""
    def checker():
        check_and_notify(candidate_id)
    return checker

@receiver(post_save, sender=Account)
def account_saved(sender, instance, created, **kwargs):
    """When an account is saved, check if they match any saved searches"""
    if created and instance.account_type == 'seeker' and instance.profile_visibility == 'public':
        # Use Django's transaction.on_commit to execute after the transaction commits
        transaction.on_commit(create_notification_checker(instance.id))

@receiver(m2m_changed, sender=Account.skills.through)
def skills_changed(sender, instance, **kwargs):
    """When skills are added/changed, check if this seeker matches any saved searches"""
    if kwargs['action'] in ['post_add', 'post_remove', 'post_clear']:
        if instance.account_type == 'seeker' and instance.profile_visibility == 'public':
            # Use Django's transaction.on_commit to execute after the transaction commits
            transaction.on_commit(create_notification_checker(instance.id))

def matches_saved_search(candidate, saved_search):
    """Check if a candidate matches the saved search criteria"""
    # Check skills if specified (and not hidden)
    if saved_search.skills.exists() and not candidate.hide_skills:
        if not candidate.skills.filter(id__in=saved_search.skills.all()).exists():
            return False
    
    # Check location if specified (and not hidden)
    if saved_search.location and not candidate.hide_location:
        if saved_search.location.lower() not in candidate.location.lower():
            return False
    
    # Check years of experience if specified (and not hidden)
    if saved_search.years_of_experience is not None and not candidate.hide_experience:
        if candidate.years_of_experience < saved_search.years_of_experience:
            return False
    
    # Check keywords if specified
    if saved_search.keywords:
        keywords_lower = saved_search.keywords.lower()
        matches_keywords = False
        
        # Check bio
        if candidate.bio and keywords_lower in candidate.bio.lower():
            matches_keywords = True
        
        # Check projects (if not hidden)
        if not candidate.hide_projects:
            for project in candidate.projects.all():
                if (keywords_lower in project.title.lower() or 
                    keywords_lower in project.description.lower()):
                    matches_keywords = True
                    break
        
        if not matches_keywords:
            return False
    
    # If all criteria match (or are not specified), return True
    return True

