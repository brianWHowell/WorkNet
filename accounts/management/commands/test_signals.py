from django.core.management.base import BaseCommand
from accounts.models import Account, SearchNotification


class Command(BaseCommand):
    help = 'Delete all notifications for testing'

    def handle(self, *args, **options):
        count = SearchNotification.objects.count()
        SearchNotification.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {count} notifications. You can now create a new candidate to test signals.')
        )

