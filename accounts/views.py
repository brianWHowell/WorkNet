from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from .forms import CustomUserCreationForm, CustomErrorList, CandidateSearchForm, SeekerProfileForm, ProjectForm, MessageForm, EmailContactForm, WorkExperienceForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import Account, Recruiter, Seeker, Project, Message, Conversation, SavedSearch, SearchNotification, WorkExperience
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.core.mail import send_mail
from django.conf import settings

@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')

def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(request, username = request.POST['username'], password = request.POST['password'])
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html', {'template_data': template_data})
        else:
            if user.is_suspended:
                template_data['error'] = 'Your account has been banned. :('
                return render(request, 'accounts/login.html', {'template_data': template_data})
            auth_login(request, user)
            return redirect('home.index')

def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            user = form.save()
            return redirect('accounts.login')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})
        
def recruiter_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in first.')
            return redirect('accounts.login')
        if request.user.account_type != 'recruiter':
            messages.warning(request, 'This page is only accessible to recruiters.')
            return redirect('home.index')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@recruiter_required
def search_candidates(request):
    template_data = {}
    template_data['title'] = 'Search Candidates'
    
    # Check if loading a saved search
    saved_search_id = request.GET.get('load')
    if saved_search_id:
        try:
            saved_search = SavedSearch.objects.get(id=saved_search_id, recruiter=request.user)
            # Pre-populate form with saved search data
            initial_data = {
                'location': saved_search.location,
                'years_of_experience': saved_search.years_of_experience,
                'keywords': saved_search.keywords,
            }
            form = CandidateSearchForm(initial=initial_data)
            form.fields['skills'].initial = saved_search.skills.all()
            template_data['loaded_search'] = saved_search
        except SavedSearch.DoesNotExist:
            form = CandidateSearchForm(request.GET or None)
    else:
        form = CandidateSearchForm(request.GET or None)
    
    # Only show public profiles to recruiters
    candidates = Account.objects.filter(account_type='seeker', profile_visibility='public')
    
    if form.is_valid():
        if form.cleaned_data['skills']:
            # Only search skills if candidates haven't hidden their skills
            candidates = candidates.filter(
                skills__in=form.cleaned_data['skills'],
                hide_skills=False
            ).distinct()
        
        if form.cleaned_data['location']:
            # Only search location if candidates haven't hidden their location
            candidates = candidates.filter(
                location__icontains=form.cleaned_data['location'],
                hide_location=False
            )

        if form.cleaned_data['years_of_experience']:
            # Only search experience if candidates haven't hidden their experience
            candidates = candidates.filter(
                years_of_experience__gte=form.cleaned_data['years_of_experience'],
                hide_experience=False
            )
        
        if form.cleaned_data['keywords']:
            keywords = form.cleaned_data['keywords']
            # Only search projects if candidates haven't hidden their projects
            candidates = candidates.filter(
                Q(projects__title__icontains=keywords, hide_projects=False) |
                Q(projects__description__icontains=keywords, hide_projects=False) |
                Q(bio__icontains=keywords)
            ).distinct()
    
    template_data['form'] = form
    template_data['candidates'] = candidates
    template_data['saved_searches'] = SavedSearch.objects.filter(recruiter=request.user)[:5]
    template_data['notification_count'] = SearchNotification.objects.filter(
        saved_search__recruiter=request.user, 
        is_read=False
    ).count()
    
    return render(request, 'accounts/search_candidates.html', {'template_data': template_data})

def seeker_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in first.')
            return redirect('accounts.login')
        if request.user.account_type != 'seeker':
            messages.warning(request, 'This page is only accessible to job seekers.')
            return redirect('home.index')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@seeker_required
def seeker_profile(request):
    template_data = {}
    template_data['title'] = 'My Profile'
    
    if request.method == 'POST':
        form = SeekerProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            # Manually check for notification matches after profile update
            from .signals import check_and_notify
            check_and_notify(request.user.id)
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts.seeker_profile')
    else:
        form = SeekerProfileForm(instance=request.user)
    
    template_data['form'] = form
    template_data['projects'] = request.user.projects.all()
    template_data['work_experiences'] = WorkExperience.objects.filter(user=request.user)
    return render(request, 'accounts/seeker_profile.html', {'template_data': template_data})

@login_required
@seeker_required
def add_project(request):
    template_data = {}
    template_data['title'] = 'Add Project'
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            request.user.projects.add(project)
            messages.success(request, 'Project added successfully!')
            return redirect('accounts.seeker_profile')
    else:
        form = ProjectForm()
    
    template_data['form'] = form
    return render(request, 'accounts/add_project.html', {'template_data': template_data})

@login_required
@seeker_required
def edit_project(request, project_id):
    try:
        project = request.user.projects.get(id=project_id)
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
        return redirect('accounts.seeker_profile')
    
    template_data = {}
    template_data['title'] = 'Edit Project'
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('accounts.seeker_profile')
    else:
        form = ProjectForm(instance=project)
    
    template_data['form'] = form
    template_data['project'] = project
    return render(request, 'accounts/edit_project.html', {'template_data': template_data})

@login_required
@seeker_required
def delete_project(request, project_id):
    try:
        project = request.user.projects.get(id=project_id)
        project.delete()
        messages.success(request, 'Project deleted successfully!')
    except Project.DoesNotExist:
        messages.error(request, 'Project not found.')
    
    return redirect('accounts.seeker_profile')

@login_required
def list_conversations(request):
    """List all conversations for the current user (recruiter or seeker)"""
    if request.user.account_type not in ['recruiter', 'seeker']:
        messages.warning(request, 'This page is only accessible to recruiters and job seekers.')
        return redirect('home.index')
    
    if request.user.account_type == 'recruiter':
        conversations = Conversation.objects.filter(recruiter=request.user).select_related('seeker', 'recruiter').prefetch_related('messages')
    else:  # seeker
        conversations = Conversation.objects.filter(seeker=request.user).select_related('seeker', 'recruiter').prefetch_related('messages')
    
    # Get unread counts and latest message for each conversation
    for conv in conversations:
        conv.unread_count = conv.get_unread_count(request.user)
        # Get the latest message (messages are ordered by created_at ascending, so last() gets the newest)
        conv.latest_message = conv.messages.last() if conv.messages.exists() else None
    
    template_data = {
        'title': 'Messages',
        'conversations': conversations,
    }
    return render(request, 'accounts/list_conversations.html', {'template_data': template_data})

@login_required
def view_conversation(request, conversation_id):
    """View a specific conversation and send messages"""
    if request.user.account_type not in ['recruiter', 'seeker']:
        messages.warning(request, 'This page is only accessible to recruiters and job seekers.')
        return redirect('home.index')
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify user is part of this conversation
    if request.user.account_type == 'recruiter':
        if conversation.recruiter != request.user:
            messages.error(request, 'You do not have permission to view this conversation.')
            return redirect('accounts.list_conversations')
    else:  # seeker
        if conversation.seeker != request.user:
            messages.error(request, 'You do not have permission to view this conversation.')
            return redirect('accounts.list_conversations')
    
    # Get all messages in the conversation
    conversation_messages = conversation.messages.all()
    
    # Mark messages as read when viewed
    conversation_messages.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    # Get the other participant
    other_participant = conversation.get_other_participant(request.user)
    
    # Handle message sending
    if request.method == 'POST':
        # Validate that user can send message
        if request.user.account_type == 'seeker':
            # Seekers can only reply if there's already a message from recruiter
            recruiter_messages = conversation.messages.filter(sender=conversation.recruiter)
            if not recruiter_messages.exists():
                messages.error(request, 'Job seekers cannot start conversations. You can only reply to messages from recruiters.')
                return redirect('accounts.view_conversation', conversation_id=conversation_id)
        
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.recipient = other_participant
            message.save()
            # Update conversation's updated_at timestamp
            conversation.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('accounts.view_conversation', conversation_id=conversation_id)
    else:
        form = MessageForm()
    
    template_data = {
        'title': f'Conversation with {other_participant.username}',
        'conversation': conversation,
        'messages': conversation_messages,
        'form': form,
        'other_participant': other_participant,
    }
    return render(request, 'accounts/view_conversation.html', {'template_data': template_data})

@login_required
@recruiter_required
def start_conversation(request, seeker_id):
    """Start a new conversation with a job seeker (recruiters only)"""
    seeker = get_object_or_404(Account, id=seeker_id, account_type='seeker')
    
    # Validate: recruiters cannot message other recruiters
    if seeker.account_type == 'recruiter':
        messages.error(request, 'Recruiters cannot start conversations with other recruiters.')
        return redirect('accounts.search_candidates')
    
    # Check if conversation already exists
    conversation, created = Conversation.objects.get_or_create(
        recruiter=request.user,
        seeker=seeker
    )
    
    # If conversation already exists and has messages, redirect to it
    if not created and conversation.messages.exists():
        return redirect('accounts.view_conversation', conversation_id=conversation.id)
    
    # Handle initial message
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.recipient = seeker
            message.save()
            # Update conversation's updated_at timestamp
            conversation.save()
            messages.success(request, f'Conversation started with {seeker.username}!')
            return redirect('accounts.view_conversation', conversation_id=conversation.id)
        else:
            # Form is invalid, show errors
            template_data = {
                'title': f'Start Conversation with {seeker.username}',
                'form': form,
                'seeker': seeker,
                'conversation': conversation,
            }
            return render(request, 'accounts/start_conversation.html', {'template_data': template_data})
    else:
        form = MessageForm()
    
    template_data = {
        'title': f'Start Conversation with {seeker.username}',
        'form': form,
        'seeker': seeker,
        'conversation': conversation,
    }
    return render(request, 'accounts/start_conversation.html', {'template_data': template_data})

@login_required
@recruiter_required
@require_POST
def save_search(request):
    """Save search criteria as a saved search"""
    data = json.loads(request.body)
    search_name = data.get('name', 'Untitled Search')
    
    # Create saved search
    saved_search = SavedSearch.objects.create(
        recruiter=request.user,
        name=search_name,
        location=data.get('location', ''),
        years_of_experience=int(data.get('years_of_experience', 0)) if data.get('years_of_experience') else None,
        keywords=data.get('keywords', '')
    )
    
    # Add skills
    skill_ids = data.get('skills', [])
    from .models import Skill
    skills = Skill.objects.filter(id__in=skill_ids)
    saved_search.skills.set(skills)
    
    messages.success(request, f'Search "{search_name}" saved successfully!')
    return JsonResponse({'success': True, 'id': saved_search.id})

@login_required
@recruiter_required
def my_saved_searches(request):
    """View all saved searches for the recruiter"""
    template_data = {
        'title': 'My Saved Searches',
        'saved_searches': SavedSearch.objects.filter(recruiter=request.user),
    }
    return render(request, 'accounts/my_saved_searches.html', {'template_data': template_data})

@login_required
@recruiter_required
def delete_saved_search(request, search_id):
    """Delete a saved search"""
    try:
        saved_search = SavedSearch.objects.get(id=search_id, recruiter=request.user)
        saved_search.delete()
        messages.success(request, 'Search deleted successfully!')
    except SavedSearch.DoesNotExist:
        messages.error(request, 'Search not found.')
    
    return redirect('accounts.my_saved_searches')

@login_required
@recruiter_required
def search_notifications(request):
    """View notifications for the recruiter when new candidates match their saved searches"""
    template_data = {
        'title': 'Search Notifications',
        'notifications': SearchNotification.objects.filter(
            saved_search__recruiter=request.user,
            is_read=False
        ).select_related('candidate', 'saved_search'),
    }
    
    return render(request, 'accounts/search_notifications.html', {'template_data': template_data})

@login_required
@recruiter_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = SearchNotification.objects.get(
            id=notification_id,
            saved_search__recruiter=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except SearchNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})

@login_required
@recruiter_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for the recruiter"""
    SearchNotification.objects.filter(
        saved_search__recruiter=request.user,
        is_read=False
    ).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
@recruiter_required
def send_message(request, seeker_id):
    """Send an in-website message to a seeker (redirects to new conversation system)"""
    # Redirect to start_conversation for backward compatibility
    return redirect('accounts.start_conversation', seeker_id=seeker_id)

@login_required
@recruiter_required
def send_email(request, seeker_id):
    """Send an email to a seeker"""
    seeker = get_object_or_404(Account, id=seeker_id, account_type='seeker')
    
    if request.method == 'POST':
        form = EmailContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message_text = form.cleaned_data['message']
            
            # Send email
            try:
                send_mail(
                    subject=subject,
                    message=f"From: {request.user.get_full_name()} ({request.user.email})\n\n{message_text}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[seeker.email],
                    fail_silently=False,
                )
                messages.success(request, f'Email sent to {seeker.email} successfully! (Check console for email content in development mode)')
                return redirect('accounts.search_candidates')
            except Exception as e:
                # Provide more helpful error messages
                if "No connection could be made" in str(e):
                    messages.error(request, 'Email service is not configured. In development mode, emails are printed to the console. Please check your terminal for the email content.')
                else:
                    messages.error(request, f'Failed to send email: {str(e)}')
    else:
        form = EmailContactForm()
    
    template_data = {
        'title': f'Send Email to {seeker.username}',
        'form': form,
        'seeker': seeker,
    }
    return render(request, 'accounts/send_email.html', {'template_data': template_data})

@login_required
@seeker_required
@require_POST
def add_work_experience(request):
    """Add a new work experience entry"""
    form = WorkExperienceForm(request.POST)
    if form.is_valid():
        work_experience = form.save(commit=False)
        work_experience.user = request.user
        work_experience.save()
        return JsonResponse({
            'success': True,
            'id': work_experience.id,
            'position': work_experience.position,
            'company': work_experience.company,
            'start_date': work_experience.start_date.strftime('%Y-%m-%d'),
            'end_date': work_experience.end_date.strftime('%Y-%m-%d') if work_experience.end_date else '',
            'description': work_experience.description,
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)

@login_required
@seeker_required
@require_POST
def update_work_experience(request, experience_id):
    """Update an existing work experience entry"""
    try:
        work_experience = WorkExperience.objects.get(id=experience_id, user=request.user)
    except WorkExperience.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Work experience not found.'
        }, status=404)
    
    form = WorkExperienceForm(request.POST, instance=work_experience)
    if form.is_valid():
        work_experience = form.save()
        return JsonResponse({
            'success': True,
            'id': work_experience.id,
            'position': work_experience.position,
            'company': work_experience.company,
            'start_date': work_experience.start_date.strftime('%Y-%m-%d'),
            'end_date': work_experience.end_date.strftime('%Y-%m-%d') if work_experience.end_date else '',
            'description': work_experience.description,
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)

@login_required
@seeker_required
@require_POST
def delete_work_experience(request, experience_id):
    """Delete a work experience entry"""
    try:
        work_experience = WorkExperience.objects.get(id=experience_id, user=request.user)
        work_experience.delete()
        return JsonResponse({'success': True})
    except WorkExperience.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Work experience not found.'
        }, status=404)

@login_required
@seeker_required
def get_work_experience(request, experience_id):
    """Get a single work experience entry (for editing)"""
    try:
        work_experience = WorkExperience.objects.get(id=experience_id, user=request.user)
        return JsonResponse({
            'success': True,
            'id': work_experience.id,
            'position': work_experience.position,
            'company': work_experience.company,
            'start_date': work_experience.start_date.strftime('%Y-%m-%d'),
            'end_date': work_experience.end_date.strftime('%Y-%m-%d') if work_experience.end_date else '',
            'description': work_experience.description,
        })
    except WorkExperience.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Work experience not found.'
        }, status=404)