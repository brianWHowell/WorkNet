"""
Management command to geocode existing job listings that don't have coordinates
"""
from django.core.management.base import BaseCommand
from job_board.models import JobListing
from job_board.views import geocode_location


class Command(BaseCommand):
    help = 'Geocode existing job listings that are missing latitude/longitude coordinates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-geocode all jobs, even if they already have coordinates',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of jobs to geocode',
        )

    def handle(self, *args, **options):
        force = options['force']
        limit = options['limit']
        
        # Get jobs that need geocoding
        if force:
            jobs = JobListing.objects.filter(location__isnull=False).exclude(location='')
        else:
            jobs = JobListing.objects.filter(
                location__isnull=False
            ).exclude(location='').filter(
                latitude__isnull=True,
                longitude__isnull=True
            ).exclude(is_remote=True)
        
        if limit:
            jobs = jobs[:limit]
        
        total = jobs.count()
        self.stdout.write(f'Found {total} job(s) to geocode')
        
        success_count = 0
        fail_count = 0
        
        for i, job in enumerate(jobs, 1):
            if job.is_remote:
                self.stdout.write(self.style.WARNING(
                    f'[{i}/{total}] Skipping remote job {job.id}: {job.title}'
                ))
                continue
            
            self.stdout.write(f'[{i}/{total}] Geocoding job {job.id}: "{job.title}" at "{job.location}"...')
            
            coords = geocode_location(job.location)
            if coords:
                job.latitude = coords[0]
                job.longitude = coords[1]
                job.save(update_fields=['latitude', 'longitude'])
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Success: ({coords[0]}, {coords[1]})'
                ))
                success_count += 1
            else:
                self.stdout.write(self.style.ERROR(
                    f'  ✗ Failed to geocode location: "{job.location}"'
                ))
                fail_count += 1
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Geocoding complete!'))
        self.stdout.write(f'  ✓ Successfully geocoded: {success_count}')
        self.stdout.write(f'  ✗ Failed: {fail_count}')
        self.stdout.write(f'  Total processed: {success_count + fail_count}')

