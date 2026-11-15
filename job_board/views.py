from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q
from accounts.views import recruiter_required, seeker_required
from accounts.models import Account
from .forms import JobListingCreate
from .models import JobListing, Application
import math

try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

# Try to import geocoder library as a better alternative
try:
    import geocoder
    GEOCODER_AVAILABLE = True
except ImportError:
    GEOCODER_AVAILABLE = False

def index(request):
    # Get only approved job listings for the main job board
    all_jobs = JobListing.objects.filter(status='approved')
    
    # Initialize recommended jobs
    recommended_jobs = []
    user_has_skills = False
    
    # Get recommended jobs for job seekers
    if request.user.is_authenticated and request.user.account_type == 'seeker':
        user_has_skills = len(get_user_skills(request.user)) > 0
        recommended_jobs = get_recommended_jobs(request.user, all_jobs)
    
    # Handle search filters
    title = request.GET.get('title', '')
    location = request.GET.get('location', '')
    salary_range = request.GET.get('salary_range', '')
    work_type = request.GET.get('work_type', '')
    skills = request.GET.getlist('skills')
    visa_sponsorship = request.GET.get('visa_sponsorship')
    distance = request.GET.get('distance', '')
    
    # Handle map bounds filter (search within visible map area)
    map_north = request.GET.get('map_north')
    map_south = request.GET.get('map_south')
    map_east = request.GET.get('map_east')
    map_west = request.GET.get('map_west')
    
    # Create filtered jobs for search results
    search_jobs = all_jobs
    
    # Apply filters to search results
    if title:
        search_jobs = search_jobs.filter(title__icontains=title)
    
    if location:
        search_jobs = search_jobs.filter(location__icontains=location)
    
    if salary_range:
        if salary_range == '0-50000':
            search_jobs = search_jobs.filter(salary__lte=50000)
        elif salary_range == '50000-75000':
            search_jobs = search_jobs.filter(salary__gte=50000, salary__lte=75000)
        elif salary_range == '75000-100000':
            search_jobs = search_jobs.filter(salary__gte=75000, salary__lte=100000)
        elif salary_range == '100000-125000':
            search_jobs = search_jobs.filter(salary__gte=100000, salary__lte=125000)
        elif salary_range == '125000-150000':
            search_jobs = search_jobs.filter(salary__gte=125000, salary__lte=150000)
        elif salary_range == '150000+':
            search_jobs = search_jobs.filter(salary__gte=150000)
    
    if work_type == 'remote':
        search_jobs = search_jobs.filter(is_remote=True)
    elif work_type == 'onsite':
        search_jobs = search_jobs.filter(is_remote=False)
    
    if skills:
        for skill in skills:
            search_jobs = search_jobs.filter(skills__icontains=skill)
    
    if visa_sponsorship:
        search_jobs = search_jobs.filter(is_visa_offered=True)
    
    # Apply distance filter if specified and user is authenticated seeker
    try:
        distance = float(distance) if distance else None
    except ValueError:
        distance = None
    if distance and request.user.is_authenticated and request.user.account_type == 'seeker':
        print(f"\n{'='*50}")
        print(f"🔍 DISTANCE FILTER REQUESTED: {distance} miles")
        print(f"User: {request.user.username}")
        user_location = get_user_location(request.user)
        print(f"User location coordinates: {user_location}")
        
        if user_location:
            print(f"✓ User location found: {user_location}, applying distance filter...")
            search_jobs = filter_by_distance(search_jobs, user_location, distance)
        else:
            print(f"✗ Cannot apply distance filter: user_location={user_location}")
            messages.warning(request, 'Please set your location in your profile (e.g., "Atlanta, GA") to use the distance filter.')
        print(f"{'='*50}\n")
    
    # Apply map bounds filter (filter jobs within visible map area)
    if map_north and map_south and map_east and map_west:
        try:
            north = float(map_north)
            south = float(map_south)
            east = float(map_east)
            west = float(map_west)
            
            print(f"\n🗺️ Map bounds filter: North={north}, South={south}, East={east}, West={west}")
            
            # Filter jobs that have coordinates within the map bounds
            # Only include jobs with stored coordinates
            jobs_in_bounds = []
            for job in search_jobs:
                if job.is_remote:
                    continue  # Skip remote jobs
                
                # Use stored coordinates if available
                if job.latitude is not None and job.longitude is not None:
                    try:
                        lat = float(job.latitude)
                        lng = float(job.longitude)
                        
                        # Check if coordinates are within bounds
                        # Handle longitude wrapping (e.g., if west > east, crossing 180/-180)
                        if west <= east:
                            # Normal case: no wrapping
                            if south <= lat <= north and west <= lng <= east:
                                jobs_in_bounds.append(job.id)
                        else:
                            # Longitude wrapping case
                            if south <= lat <= north and (lng >= west or lng <= east):
                                jobs_in_bounds.append(job.id)
                    except (ValueError, TypeError):
                        continue
            
            if jobs_in_bounds:
                search_jobs = search_jobs.filter(id__in=jobs_in_bounds)
                print(f"✓ Filtered to {len(jobs_in_bounds)} jobs within map bounds")
            else:
                print("⚠ No jobs found within map bounds")
                search_jobs = search_jobs.none()  # Empty queryset
                
        except (ValueError, TypeError) as e:
            print(f"✗ Error parsing map bounds: {e}")
            messages.warning(request, 'Invalid map bounds. Showing all jobs.')
    
    # For backward compatibility, keep 'jobs' variable pointing to search results
    # This ensures existing template logic still works
    jobs = search_jobs
    
    return render(request, 'job_board/index.html', {
        'jobs': jobs,  # Search results (for backward compatibility)
        'all_jobs': all_jobs,  # All jobs (unfiltered)
        'search_jobs': search_jobs,  # Search results (explicit)
        'recommended_jobs': recommended_jobs,  # Recommended jobs for job seekers
        'user_has_skills': user_has_skills  # Whether user has skills filled in
    })

def get_user_skills(user):
    """
    Extract user's skills from both Account and Seeker models
    Returns a list of skill strings (lowercase, stripped)
    """
    user_skills = []
    
    # Get skills from Account model (ManyToManyField)
    try:
        if hasattr(user, 'skills'):
            account_skills = user.skills.all()
            if account_skills:
                user_skills.extend([skill.name.lower().strip() for skill in account_skills if skill.name])
    except Exception:
        pass  # Skills access failed
    
    # Get skills from Seeker model (CharField)
    try:
        if hasattr(user, 'seeker'):
            seeker = user.seeker
            if seeker and seeker.skills:
                seeker_skill_list = [skill.strip().lower() for skill in seeker.skills.split(',') if skill.strip()]
                user_skills.extend(seeker_skill_list)
    except Exception:
        pass  # Seeker profile doesn't exist
    
    # Remove duplicates and empty strings
    user_skills = list(set([skill.strip() for skill in user_skills if skill and skill.strip()]))
    return user_skills

def get_recommended_jobs(user, all_jobs):
    """
    Get recommended jobs based on user's skills matching job requirements
    """
    recommended_jobs = []
    
    # Get user's skills from both Account and Seeker models
    user_skills = get_user_skills(user)
    
    # If no skills found, return empty (user needs to add skills for recommendations)
    if not user_skills:
        return recommended_jobs
    
    # Find jobs that have at least one matching skill
    for job in all_jobs:
        if not job.skills:
            continue
            
        job_skills = [skill.strip().lower() for skill in job.skills.split(',') if skill.strip()]
        
        # Check if any user skill matches any job skill
        if any(user_skill in job_skills for user_skill in user_skills):
            recommended_jobs.append(job)
    
    return recommended_jobs

@login_required
@recruiter_required
def recruiter_listings(request):
    recruiter_listings = JobListing.objects.filter(recruiter=request.user)
    
    # Get recommended candidates for each job
    jobs_with_recommendations = []
    for job in recruiter_listings:
        recommended_candidates = get_recommended_candidates_for_job(job)
        jobs_with_recommendations.append({
            'job': job,
            'recommended_candidates': recommended_candidates
        })
    
    return render(request, 'job_board/recruiter_listings.html', {
        'jobs': recruiter_listings,
        'jobs_with_recommendations': jobs_with_recommendations
    })

def get_recommended_candidates_for_job(job):
    """
    Get recommended candidates based on job requirements matching candidate skills
    """
    from accounts.models import Account, Seeker
    
    recommended_candidates = []
    
    # Get job skills
    job_skills = [skill.strip().lower() for skill in job.skills.split(',') if skill.strip()]
    
    if not job_skills:
        return recommended_candidates
    
    # Get all job seekers
    seekers = Account.objects.filter(account_type='seeker')
    
    for seeker in seekers:
        # Get seeker's skills from both Account and Seeker models
        seeker_skills = []
        
        # Get skills from Account model (ManyToManyField)
        if hasattr(seeker, 'skills'):
            seeker_skills.extend([skill.name.lower() for skill in seeker.skills.all()])
        
        # Get skills from Seeker model (CharField)
        try:
            seeker_profile = seeker.seeker
            if seeker_profile.skills:
                seeker_skill_list = [skill.strip().lower() for skill in seeker_profile.skills.split(',') if skill.strip()]
                seeker_skills.extend(seeker_skill_list)
        except:
            pass  # Seeker profile doesn't exist
        
        # Remove duplicates and empty strings
        seeker_skills = list(set([skill for skill in seeker_skills if skill]))
        
        # Check if any job skill matches any seeker skill
        if any(job_skill in seeker_skills for job_skill in job_skills):
            # Create a candidate object with all skills
            candidate_data = {
                'user': seeker,
                'all_skills': seeker_skills
            }
            recommended_candidates.append(candidate_data)
    
    return recommended_candidates

@login_required
@recruiter_required
def create_listing(request):
    if request.method == 'POST':
        form = JobListingCreate(request.POST)
        if form.is_valid():
            job_listing = form.save(commit=False)
            job_listing.recruiter = request.user
            
            # Get coordinates from hidden form fields (from autocomplete)
            latitude = request.POST.get('latitude', '').strip()
            longitude = request.POST.get('longitude', '').strip()
            
            if latitude and longitude and not job_listing.is_remote:
                try:
                    job_listing.latitude = float(latitude)
                    job_listing.longitude = float(longitude)
                    print(f"✓ Using coordinates from autocomplete for '{job_listing.location}': ({job_listing.latitude}, {job_listing.longitude})")
                except (ValueError, TypeError):
                    print(f"⚠ Invalid coordinates from form, falling back to geocoding")
                    # Fallback to geocoding if coordinates invalid
                    if job_listing.location:
                        coords = geocode_location(job_listing.location)
                        if coords:
                            job_listing.latitude = coords[0]
                            job_listing.longitude = coords[1]
                            print(f"✓ Geocoded location '{job_listing.location}' for new job: ({coords[0]}, {coords[1]})")
            elif job_listing.location and not job_listing.is_remote:
                # Fallback: geocode if no coordinates provided
                coords = geocode_location(job_listing.location)
                if coords:
                    job_listing.latitude = coords[0]
                    job_listing.longitude = coords[1]
                    print(f"✓ Geocoded location '{job_listing.location}' for new job: ({coords[0]}, {coords[1]})")
            
            job_listing.save()
            return redirect('job_board.recruiter_listings')
    else: #GET
        form = JobListingCreate()
    return render(request, 'job_board/create_listing.html', {'form': form})

@login_required
@recruiter_required
def edit_listing(request, job_id):
    job = get_object_or_404(JobListing, id=job_id, recruiter=request.user)
    if request.method == 'POST':
        form = JobListingCreate(request.POST, instance=job)
        if form.is_valid():
            job_listing = form.save(commit=False)
            
            # Get coordinates from hidden form fields (from autocomplete)
            latitude = request.POST.get('latitude', '').strip()
            longitude = request.POST.get('longitude', '').strip()
            
            if latitude and longitude and not job_listing.is_remote:
                try:
                    job_listing.latitude = float(latitude)
                    job_listing.longitude = float(longitude)
                    print(f"✓ Using coordinates from autocomplete for '{job_listing.location}': ({job_listing.latitude}, {job_listing.longitude})")
                except (ValueError, TypeError):
                    print(f"⚠ Invalid coordinates from form, falling back to geocoding")
                    # Fallback to geocoding if coordinates invalid
                    if job_listing.location:
                        coords = geocode_location(job_listing.location)
                        if coords:
                            job_listing.latitude = coords[0]
                            job_listing.longitude = coords[1]
                            print(f"✓ Geocoded location '{job_listing.location}' for job {job_id}: ({coords[0]}, {coords[1]})")
            elif job_listing.is_remote:
                # Clear coordinates for remote jobs
                job_listing.latitude = None
                job_listing.longitude = None
            elif job_listing.location:
                # Fallback: geocode if no coordinates provided
                coords = geocode_location(job_listing.location)
                if coords:
                    job_listing.latitude = coords[0]
                    job_listing.longitude = coords[1]
                    print(f"✓ Geocoded location '{job_listing.location}' for job {job_id}: ({coords[0]}, {coords[1]})")
            
            job_listing.save()
            return redirect('job_board.recruiter_listings')
    else:
        form = JobListingCreate(instance=job)
    return render(request, 'job_board/edit_listing.html', {'form': form, 'job': job})

@login_required
@seeker_required
def apply_to_job(request, job_id):
    """Handle job application submission"""
    job = get_object_or_404(JobListing, id=job_id, status='approved')
    
    # Check if user already applied
    if Application.objects.filter(job_listing=job, seeker=request.user).exists():
        messages.error(request, 'You have already applied to this job.')
        return redirect('job_board.index')
    
    if request.method == 'POST':
        # Create application
        application_message = request.POST.get('application_message', '')
        Application.objects.create(
            job_listing=job,
            seeker=request.user,
            application_message=application_message,
            status='applied'
        )
        messages.success(request, f'Successfully applied to {job.title}!')
        return redirect('job_board.my_applications')
    
    # GET request - show application form
    template_data = {
        'title': f'Apply to {job.title}',
        'job': job,
    }
    return render(request, 'job_board/apply_to_job.html', {'template_data': template_data})

@login_required
@seeker_required
def my_applications(request):
    """View all applications for the current job seeker"""
    applications = Application.objects.filter(seeker=request.user).order_by('-updated_at')
    
    template_data = {
        'title': 'My Applications',
        'applications': applications,
    }
    return render(request, 'job_board/my_applications.html', {'template_data': template_data})


@login_required
@recruiter_required
def manage_applications(request):
    """View all job listings with application counts for the current recruiter"""
    # Get all job listings for this recruiter with application counts
    job_listings = JobListing.objects.filter(recruiter=request.user).annotate(
        total_applications=Count('applications'),
        applied_count=Count('applications', filter=Q(applications__status='applied')),
        review_count=Count('applications', filter=Q(applications__status='review')),
        interview_count=Count('applications', filter=Q(applications__status='interview')),
        offer_count=Count('applications', filter=Q(applications__status='offer')),
        closed_count=Count('applications', filter=Q(applications__status='closed'))
    ).order_by('-id')
    
    template_data = {
        'title': 'Manage Applications',
        'job_listings': job_listings,
    }
    return render(request, 'job_board/manage_applications.html', {'template_data': template_data})

@login_required
@recruiter_required
def application_kanban(request, job_id):
    """Kanban board view for managing applications for a specific job listing"""
    job_listing = get_object_or_404(JobListing, id=job_id, recruiter=request.user)
    
    # Get applications grouped by status
    applications_by_status = {
        'applied': Application.objects.filter(job_listing=job_listing, status='applied').order_by('-applied_at'),
        'review': Application.objects.filter(job_listing=job_listing, status='review').order_by('-updated_at'),
        'interview': Application.objects.filter(job_listing=job_listing, status='interview').order_by('-updated_at'),
        'offer': Application.objects.filter(job_listing=job_listing, status='offer').order_by('-updated_at'),
        'closed': Application.objects.filter(job_listing=job_listing, status='closed').order_by('-updated_at'),
    }
    
    template_data = {
        'title': f'Application Pipeline - {job_listing.title}',
        'job_listing': job_listing,
        'applications_by_status': applications_by_status,
    }
    return render(request, 'job_board/application_kanban.html', {'template_data': template_data})

@login_required
@recruiter_required
def update_application_status(request, application_id):
    """Update the status of an application"""
    application = get_object_or_404(Application, id=application_id)
    
    # Verify the application belongs to a job listing owned by this recruiter
    if application.job_listing.recruiter != request.user:
        messages.error(request, 'You do not have permission to update this application.')
        return redirect('job_board.manage_applications')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['applied', 'review', 'interview', 'offer', 'closed']:
            application.status = new_status
            application.save()
            messages.success(request, f'Application status updated to {application.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status provided.')
    
    return redirect('job_board.application_kanban', job_id=application.job_listing.id)

# Helper functions for geocoding and distance filtering
def geocode_location(location_str):
    """Geocode a location string to latitude and longitude - SIMPLIFIED AND FIXED"""
    if not location_str or not location_str.strip():
        print(f"⚠ Empty location string")
        return None
    
    normalized = location_str.strip()
    print(f"🔍 Geocoding: '{normalized}'")
    
    # US state abbreviations mapping
    US_STATES = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
        'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
        'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
        'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
        'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
        'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
        'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
        'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
        'DC': 'District of Columbia'
    }
    
    # Build variations to try
    variations = [normalized]  # Always try original first
    
    # Normalize location format
    if ',' in normalized:
        parts = [p.strip() for p in normalized.split(',')]
        if len(parts) >= 2:
            city = parts[0].strip()
            second_part = parts[1].strip().upper()
            
            # If second part is a US state abbreviation, expand it
            if len(second_part) == 2 and second_part in US_STATES:
                state_name = US_STATES[second_part]
                variations.extend([
                    f"{city}, {state_name}, USA",
                    f"{city}, {state_name}",
                    f"{city}, {second_part}, USA",
                ])
            else:
                # Try adding USA
                variations.append(f"{normalized}, USA")
    else:
        # Single location - try adding USA
        variations.append(f"{normalized}, USA")
    
    # Strategy 1: Try geocoder library with ArcGIS backend (free, reliable, no rate limits)
    if GEOCODER_AVAILABLE:
        try:
            print(f"  Trying ArcGIS geocoder...")
            g = geocoder.arcgis(normalized)
            if g.ok and g.latlng:
                coords = tuple(g.latlng)
                print(f"✓ Geocoded '{location_str}' using ArcGIS: {coords}")
                return coords
            
            print(f"  ArcGIS failed, trying OSM...")
            g = geocoder.osm(normalized)
            if g.ok and g.latlng:
                coords = tuple(g.latlng)
                print(f"✓ Geocoded '{location_str}' using OSM: {coords}")
                return coords
        except Exception as e:
            print(f"✗ Geocoder library error: {e}")
    
    # Strategy 2: Use Nominatim (free but has rate limits)
    if GEOPY_AVAILABLE:
        import time
        try:
            geolocator = Nominatim(user_agent="worknet_job_board")
            
            # Remove duplicates from variations
            seen = set()
            unique_variations = []
            for v in variations:
                if v and v not in seen:
                    seen.add(v)
                    unique_variations.append(v)
            
            print(f"  Trying {len(unique_variations)} variations with Nominatim...")
            # Try each variation (with small delay between attempts)
            for i, variation in enumerate(unique_variations):
                try:
                    if i > 0:
                        time.sleep(0.3)  # Short delay to avoid rate limiting
                    
                    location = geolocator.geocode(variation, timeout=10, exactly_one=True)
                    if location:
                        coords = (location.latitude, location.longitude)
                        print(f"✓ Geocoded '{location_str}' -> '{variation}' using Nominatim: {coords}")
                        return coords
                except Exception as e:
                    print(f"  Variation '{variation}' failed: {e}")
                    continue
            
            # Final attempt - try original without exactly_one (might return multiple)
            print(f"  Final attempt with original location...")
            time.sleep(0.3)
            try:
                location = geolocator.geocode(normalized, timeout=10, exactly_one=False)
                if location:
                    if hasattr(location, '__iter__') and not isinstance(location, str):
                        first_result = location[0]
                        coords = (first_result.latitude, first_result.longitude)
                        print(f"✓ Geocoded '{location_str}' (multiple results) using Nominatim: {coords}")
                        return coords
            except Exception as e:
                print(f"  Final attempt failed: {e}")
        except Exception as e:
            print(f"✗ Nominatim geocoding error: {e}")
    else:
        print(f"⚠ GEOPY_AVAILABLE = {GEOPY_AVAILABLE}, GEOCODER_AVAILABLE = {GEOCODER_AVAILABLE}")
    
    print(f"✗ FAILED: Could not geocode location '{location_str}' using any method")
    return None

def get_user_location(user):
    """Get user's location coordinates from their profile - FIXED to use city lookup"""
    if not user:
        return None
    
    # Use the utility function which tries city lookup first, then geocoding
    try:
        from job_board.utils import get_user_location_coordinates
        coords = get_user_location_coordinates(user)
        if coords:
            print(f"✓ User location found: {coords}")
            return coords
        else:
            print(f"⚠ No location coordinates found for user {user.username}")
            return None
    except ImportError:
        # Fallback to old method if utils not available
        location_str = None
        try:
            if hasattr(user, 'seeker') and user.seeker and user.seeker.location:
                location_str = user.seeker.location.strip()
        except:
            pass
        
        if not location_str and user.location:
            location_str = user.location.strip()
        
        if location_str:
            coords = geocode_location(location_str)
            return coords if coords else None
        
        return None

def calculate_distance(loc1, loc2):
    """Calculate distance in miles between two coordinates"""
    if not GEOPY_AVAILABLE or not loc1 or not loc2:
        return None
    try:
        return geodesic(loc1, loc2).miles
    except:
        return None

def filter_by_distance(jobs_queryset, user_location, max_distance_miles):
    """Filter jobs by distance from user location - FIXED to use stored coordinates and city lookup"""
    if not user_location:
        print(f"⚠ Distance filter skipped: user_location={user_location}")
        return jobs_queryset
    
    print(f"🔍 Filtering jobs by distance: user_location={user_location}, max_distance={max_distance_miles} miles")
    
    # Import utility functions
    try:
        from job_board.utils import get_city_coordinates, calculate_distance_miles
    except ImportError:
        print("⚠ utils module not available, using fallback method")
        # Fallback to geopy if available
        if not GEOPY_AVAILABLE:
            return jobs_queryset
    
    # Convert queryset to list to allow filtering by distance
    jobs_list = list(jobs_queryset)
    filtered_jobs = []
    user_lat, user_lon = user_location
    
    for job in jobs_list:
        # Skip remote jobs from distance filtering
        if job.is_remote:
            print(f"  Job {job.id}: Remote job, skipping distance filter")
            continue
        
        job_coords = None
        distance = None
        
        # Priority 1: Use stored coordinates if available
        if job.latitude is not None and job.longitude is not None:
            try:
                job_coords = (float(job.latitude), float(job.longitude))
            except (ValueError, TypeError):
                pass
        
        # Priority 2: Try city lookup (fast, no API call)
        if not job_coords:
            try:
                from job_board.utils import get_city_coordinates
                job_coords = get_city_coordinates(job.location)
                if job_coords:
                    print(f"  Job {job.id}: Found coordinates from city database for '{job.location}'")
            except:
                pass
        
        # Priority 3: Fallback to geocoding
        if not job_coords:
            print(f"  Job {job.id}: No stored coordinates or city match, geocoding '{job.location}'...")
            job_coords = geocode_location(job.location)
            if job_coords:
                # Save coordinates for next time
                try:
                    job.latitude = job_coords[0]
                    job.longitude = job_coords[1]
                    job.save(update_fields=['latitude', 'longitude'])
                    print(f"    ✓ Geocoded and saved coordinates for job {job.id}")
                except:
                    pass
        
        # Calculate distance if we have coordinates
        if job_coords:
            try:
                from job_board.utils import calculate_distance_miles
                distance = calculate_distance_miles(user_lat, user_lon, job_coords[0], job_coords[1])
            except:
                # Fallback to geopy if available
                if GEOPY_AVAILABLE:
                    distance = calculate_distance(user_location, job_coords)
            
            if distance is not None:
                print(f"  Job {job.id} ({job.title}) at {job.location}: {distance:.1f} miles")
                if distance <= max_distance_miles:
                    filtered_jobs.append(job.id)
                else:
                    print(f"    ✗ Too far ({distance:.1f} > {max_distance_miles} miles)")
            else:
                print(f"  Job {job.id}: Could not calculate distance")
        else:
            print(f"  Job {job.id}: Could not get coordinates for '{job.location}', excluding from results")
    
    print(f"✅ Distance filter: {len(filtered_jobs)} jobs within {max_distance_miles} miles")
    
    # Return queryset filtered by IDs
    if filtered_jobs:
        return jobs_queryset.filter(id__in=filtered_jobs)
    else:
        return jobs_queryset.none()

# API endpoint for map data
@login_required
@seeker_required
def jobs_map_api(request):
    """API endpoint to return jobs with coordinates for map display"""
    source = request.GET.get('source', 'all')
    
    # Get jobs based on source
    if source == 'recommendations':
        all_jobs = JobListing.objects.filter(status='approved')
        recommended_list = get_recommended_jobs(request.user, all_jobs)
        # Convert list to queryset by IDs
        if recommended_list:
            job_ids = [job.id for job in recommended_list]
            jobs = JobListing.objects.filter(id__in=job_ids, status='approved')
        else:
            jobs = JobListing.objects.none()
    elif source == 'search':
        # Apply same filters as main search
        all_jobs = JobListing.objects.filter(status='approved')
        title = request.GET.get('title', '')
        location = request.GET.get('location', '')
        salary_range = request.GET.get('salary_range', '')
        work_type = request.GET.get('work_type', '')
        skills = request.GET.getlist('skills')
        visa_sponsorship = request.GET.get('visa_sponsorship')
        distance = request.GET.get('distance', '')
        
        jobs = all_jobs
        
        if title:
            jobs = jobs.filter(title__icontains=title)
        if location:
            jobs = jobs.filter(location__icontains=location)
        if salary_range:
            if salary_range == '0-50000':
                jobs = jobs.filter(salary__lte=50000)
            elif salary_range == '50000-75000':
                jobs = jobs.filter(salary__gte=50000, salary__lte=75000)
            elif salary_range == '75000-100000':
                jobs = jobs.filter(salary__gte=75000, salary__lte=100000)
            elif salary_range == '100000-125000':
                jobs = jobs.filter(salary__gte=100000, salary__lte=125000)
            elif salary_range == '125000-150000':
                jobs = jobs.filter(salary__gte=125000, salary__lte=150000)
            elif salary_range == '150000+':
                jobs = jobs.filter(salary__gte=150000)
        if work_type == 'remote':
            jobs = jobs.filter(is_remote=True)
        elif work_type == 'onsite':
            jobs = jobs.filter(is_remote=False)
        if skills:
            for skill in skills:
                jobs = jobs.filter(skills__icontains=skill)
        if visa_sponsorship:
            jobs = jobs.filter(is_visa_offered=True)
        if distance:
            user_location = get_user_location(request.user)
            if user_location and GEOPY_AVAILABLE:
                jobs = filter_by_distance(jobs, user_location, float(distance))
    else:
        jobs = JobListing.objects.filter(status='approved')
    
    # Convert jobs to JSON with coordinates
    jobs_data = []
    jobs_list = list(jobs)  # Evaluate queryset once
    
    geocoded_count = 0
    not_geocoded_count = 0
    remote_count = 0
    
    for job in jobs_list:
        # Ensure location is properly stored and displayed
        location_str = job.location.strip() if job.location else 'Location not specified'
        
        job_data = {
            'id': job.id,
            'title': job.title,
            'location': location_str,  # Store original location exactly as entered
            'salary': job.salary,
            'skills': job.skills,
            'is_remote': job.is_remote,
            'is_visa_offered': job.is_visa_offered,
            'latitude': None,
            'longitude': None,
            'distance': None
        }
        
        # Count remote jobs
        if job.is_remote:
            remote_count += 1
        # Use stored coordinates if available (preferred method)
        elif job.latitude is not None and job.longitude is not None:
            try:
                lat = float(job.latitude)
                lng = float(job.longitude)
                # Validate coordinates
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    job_data['latitude'] = lat
                    job_data['longitude'] = lng
                    geocoded_count += 1
                    print(f"✓ Using stored coordinates for job {job.id}: ({lat}, {lng})")
                    
                    # Calculate distance from user if user location is available
                    user_location = get_user_location(request.user)
                    if user_location:
                        coords = (lat, lng)
                        distance = calculate_distance(user_location, coords)
                        if distance is not None:
                            job_data['distance'] = round(distance, 1)
                else:
                    print(f"⚠ Invalid stored coordinates for job {job.id}: ({lat}, {lng})")
                    # Fall through to geocode again
                    raise ValueError("Invalid coordinates")
            except (ValueError, TypeError) as e:
                print(f"⚠ Error using stored coordinates for job {job.id}: {e}. Will geocode...")
                # Fall through to geocode
                pass
        # Fallback: geocode on-the-fly if coordinates not stored yet
        elif location_str and location_str != 'Location not specified':
            print(f"\n🔍 Geocoding job {job.id}: '{job.title}' at '{location_str}'...")
            coords = geocode_location(location_str)
            if coords and len(coords) == 2:
                try:
                    job_data['latitude'] = float(coords[0])
                    job_data['longitude'] = float(coords[1])
                    geocoded_count += 1
                    
                    # Save coordinates to database for future use
                    job.latitude = float(coords[0])
                    job.longitude = float(coords[1])
                    job.save(update_fields=['latitude', 'longitude'])
                    print(f"✅ SUCCESS: Geocoded and saved job {job.id}: '{location_str}' -> {coords}")
                    
                    # Calculate distance from user if user location is available
                    user_location = get_user_location(request.user)
                    if user_location:
                        distance = calculate_distance(user_location, coords)
                        if distance is not None:
                            job_data['distance'] = round(distance, 1)
                except Exception as e:
                    print(f"✗ ERROR saving coordinates for job {job.id}: {e}")
                    not_geocoded_count += 1
            else:
                # If geocoding fails, log it but still include the job (without coordinates)
                not_geocoded_count += 1
                print(f"✗ FAILED: Could not geocode location '{location_str}' for job {job.id} ({job.title})")
        else:
            # No location specified
            not_geocoded_count += 1
        
        jobs_data.append(job_data)
    
    return JsonResponse({
        'jobs': jobs_data,
        'total': len(jobs_data),
        'geocoded': geocoded_count,
        'not_geocoded': not_geocoded_count,
        'remote': remote_count
    })

# API endpoint for single job location (User Story 17)
@login_required
@recruiter_required
def job_location_api(request, job_id):
    """API endpoint to return a single job's location for map display"""
    try:
        job = JobListing.objects.get(id=job_id, recruiter=request.user)
    except JobListing.DoesNotExist:
        return JsonResponse({'error': 'Job not found or access denied'}, status=404)
    
    # Skip if remote job
    if job.is_remote:
        return JsonResponse({
            'job': {
                'id': job.id,
                'title': job.title,
                'location': job.location,
                'is_remote': True
            },
            'error': 'This is a remote job and has no office location'
        })
    
    location_str = job.location.strip() if job.location else 'Location not specified'
    
    job_data = {
        'id': job.id,
        'title': job.title,
        'location': location_str,
        'salary': job.salary,
        'skills': job.skills,
        'is_remote': job.is_remote,
        'is_visa_offered': job.is_visa_offered,
        'latitude': None,
        'longitude': None
    }
    
    # Use stored coordinates if available
    if job.latitude is not None and job.longitude is not None:
        try:
            lat = float(job.latitude)
            lng = float(job.longitude)
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                job_data['latitude'] = lat
                job_data['longitude'] = lng
                return JsonResponse({'job': job_data})
        except (ValueError, TypeError):
            pass
    
    # Geocode if coordinates not stored
    if location_str and location_str != 'Location not specified':
        coords = geocode_location(location_str)
        if coords and len(coords) == 2:
            try:
                job_data['latitude'] = float(coords[0])
                job_data['longitude'] = float(coords[1])
                
                # Save coordinates to database for future use
                job.latitude = float(coords[0])
                job.longitude = float(coords[1])
                job.save(update_fields=['latitude', 'longitude'])
            except Exception:
                pass
    
    return JsonResponse({'job': job_data})

# API endpoint for applicant locations with clustering support (User Story 18)
@login_required
@recruiter_required
def applicants_map_api(request, job_id):
    """API endpoint to return applicant locations for a job with clustering support"""
    try:
        job = JobListing.objects.get(id=job_id, recruiter=request.user)
    except JobListing.DoesNotExist:
        return JsonResponse({'error': 'Job not found or access denied'}, status=404)
    
    # Get all applications for this job
    applications = Application.objects.filter(job_listing=job)
    
    applicants_data = []
    geocoded_count = 0
    not_geocoded_count = 0
    no_location_count = 0
    
    for application in applications:
        seeker = application.seeker
        
        # Get seeker's location string
        location_str = None
        if hasattr(seeker, 'seeker') and seeker.seeker and seeker.seeker.location:
            location_str = seeker.seeker.location.strip()
        if not location_str and seeker.location:
            location_str = seeker.location.strip()
        
        # Skip if no location
        if not location_str:
            no_location_count += 1
            continue
        
        applicant_data = {
            'id': seeker.id,
            'name': seeker.get_full_name() or seeker.username,
            'username': seeker.username,
            'location': location_str,
            'status': application.status,
            'applied_at': application.applied_at.isoformat(),
            'latitude': None,
            'longitude': None
        }
        
        # Try to get coordinates using utility function (city lookup first)
        try:
            from job_board.utils import get_user_location_coordinates
            coords = get_user_location_coordinates(seeker)
            if coords:
                applicant_data['latitude'] = float(coords[0])
                applicant_data['longitude'] = float(coords[1])
                geocoded_count += 1
                applicants_data.append(applicant_data)
            else:
                not_geocoded_count += 1
        except Exception as e:
            print(f"Error getting coordinates for applicant {seeker.id}: {e}")
            not_geocoded_count += 1
    
    return JsonResponse({
        'job': {
            'id': job.id,
            'title': job.title,
            'location': job.location,
            'latitude': float(job.latitude) if job.latitude is not None else None,
            'longitude': float(job.longitude) if job.longitude is not None else None
        },
        'applicants': applicants_data,
        'total': len(applicants_data),
        'geocoded': geocoded_count,
        'not_geocoded': not_geocoded_count,
        'no_location': no_location_count
    })
