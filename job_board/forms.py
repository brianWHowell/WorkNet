from django import forms
from .models import JobListing

class JobListingCreate(forms.ModelForm):
    # Define skill choices (same as in the filter)
    SKILL_CHOICES = [
        ('Python', 'Python'),
        ('JavaScript', 'JavaScript'),
        ('Java', 'Java'),
        ('C#', 'C#'),
        ('React', 'React'),
        ('Angular', 'Angular'),
        ('Vue.js', 'Vue.js'),
        ('Node.js', 'Node.js'),
        ('Django', 'Django'),
        ('Flask', 'Flask'),
        ('Spring', 'Spring'),
        ('SQL', 'SQL'),
        ('MongoDB', 'MongoDB'),
        ('PostgreSQL', 'PostgreSQL'),
        ('AWS', 'AWS'),
        ('Azure', 'Azure'),
        ('Docker', 'Docker'),
        ('Kubernetes', 'Kubernetes'),
        ('Git', 'Git'),
        ('TypeScript', 'TypeScript'),
    ]
    
    # Override the skills field to use checkboxes
    skills = forms.MultipleChoiceField(
        choices=SKILL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Required Skills'
    )
    
    class Meta:
        model = JobListing
        fields = ['title', 'skills', 'location', 'salary', 'is_remote', 'is_visa_offered']
        labels = {
            'salary': 'Salary ($)',
            'is_remote': 'Is this position remote?',
            'is_visa_offered': 'Is visa sponsorship offered?',
            'location': 'Location (Start typing to see suggestions)',
        }
        widgets = {
            'salary': forms.NumberInput(attrs={'min': 0, 'step': 1000}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_location',
                'autocomplete': 'off',
                'placeholder': 'Type city name (e.g., New York, NY)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing job, populate the checkboxes with current skills
        if self.instance and self.instance.pk and self.instance.skills:
            current_skills = [skill.strip() for skill in self.instance.skills.split(',')]
            self.initial['skills'] = [skill for skill in current_skills if skill in dict(self.SKILL_CHOICES)]
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert selected skills to comma-separated string
        selected_skills = self.cleaned_data.get('skills', [])
        instance.skills = ', '.join(selected_skills)
        if commit:
            instance.save()
        return instance