from django.core.management.base import BaseCommand
from accounts.models import Account, SavedSearch, SearchNotification


class Command(BaseCommand):
    help = 'Check all existing candidates against saved searches and create notifications'

    def handle(self, *args, **options):
        # Get all public seeker accounts
        candidates = Account.objects.filter(
            account_type='seeker',
            profile_visibility='public'
        ).prefetch_related('skills', 'projects')
        
        # Get all saved searches
        saved_searches = SavedSearch.objects.filter(
            recruiter__account_type='recruiter'
        ).prefetch_related('skills')
        
        self.stdout.write(f'Checking {candidates.count()} candidates against {saved_searches.count()} saved searches...')
        
        notifications_created = 0
        
        for candidate in candidates:
            for saved_search in saved_searches:
                if self.matches_saved_search(candidate, saved_search):
                    # Create notification if it doesn't already exist
                    notification, created = SearchNotification.objects.get_or_create(
                        saved_search=saved_search,
                        candidate=candidate
                    )
                    if created:
                        notifications_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created notification for {candidate.username} matching "{saved_search.name}"'
                            )
                        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {candidates.count()} candidates. Created {notifications_created} new notifications.')
        )

    def matches_saved_search(self, candidate, saved_search):
        """Check if a candidate matches the saved search criteria"""
        # Check skills if specified (and not hidden)
        if saved_search.skills.exists() and not candidate.hide_skills:
            candidate_skill_ids = set(candidate.skills.all().values_list('id', flat=True))
            saved_skill_ids = set(saved_search.skills.all().values_list('id', flat=True))
            if not candidate_skill_ids.intersection(saved_skill_ids):
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

