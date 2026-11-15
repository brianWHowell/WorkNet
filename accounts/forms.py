from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django import forms #Supports account type selection
from .models import Account, Skill, Project, Message, WorkExperience

class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))

class CustomUserCreationForm(UserCreationForm):
    account_type = forms.ChoiceField(choices=Account.ACCOUNT_TYPES[:2])
    
    class Meta: #Alerts the form to use accounts.Account instead of auth.User
        model = Account
        fields = ('username', 'password1', 'password2', 'account_type')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update( {'class': 'form-control'} )

class CandidateSearchForm(forms.Form):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled'})
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    years_of_experience = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    keywords = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search in projects and bio'
        })
    )

class SeekerProfileForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'location', 'bio', 'years_of_experience', 'skills', 
                 'profile_visibility', 'hide_location', 'hide_skills', 'hide_experience', 'hide_projects']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York, Remote'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself, your experience, and what you\'re looking for...'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 50}),
            'skills': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'profile_visibility': forms.Select(attrs={'class': 'form-control'}),
            'hide_location': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_skills': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_experience': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hide_projects': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'years_of_experience': 'Years of Experience',
            'profile_visibility': 'Profile Visibility',
            'hide_location': 'Hide Location',
            'hide_skills': 'Hide Skills',
            'hide_experience': 'Hide Experience',
            'hide_projects': 'Hide Projects',
        }

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'start_date', 'end_date', 'skills_used']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe what you built, technologies used, and your role...'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'skills_used': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'skills_used': 'Technologies Used',
        }


class MessageForm(forms.ModelForm):
    body = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Type your message...'}),
        label='Message'
    )
    
    class Meta:
        model = Message
        fields = ['body']

class EmailContactForm(forms.Form):
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email subject'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your message to the candidate...'})
    )

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['position', 'company', 'start_date', 'end_date', 'description']
        widgets = {
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Software Engineer, Product Manager'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your responsibilities, achievements, and key projects...'}),
        }
        labels = {
            'position': 'Job Title/Position',
            'company': 'Company Name',
            'start_date': 'Start Date',
            'end_date': 'End Date (leave blank if currently employed)',
            'description': 'Job Description',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if end_date and start_date and end_date < start_date:
            raise forms.ValidationError('End date must be after start date.')
        
        return cleaned_data