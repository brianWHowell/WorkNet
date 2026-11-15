from django.core.management.base import BaseCommand
from accounts.models import Account, Recruiter

class Command(BaseCommand):
    help = 'Create missing Recruiter instances for existing recruiter accounts'

    def handle(self, *args, **options):
        # Find all recruiter accounts that don't have a Recruiter instance
        recruiter_accounts = Account.objects.filter(account_type='recruiter')
        created_count = 0
        
        for account in recruiter_accounts:
            try:
                # Try to get the recruiter instance
                account.recruiter
                self.stdout.write(f'Account {account.username} already has a recruiter instance')
            except Recruiter.DoesNotExist:
                # Create the missing recruiter instance
                Recruiter.objects.create(user=account)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created recruiter instance for {account.username}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} missing recruiter instances')
        )

