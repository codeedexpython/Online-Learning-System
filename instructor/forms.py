from django import forms
from core.models import *

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'difficulty_level']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control',"rows": 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = CourseCategory.objects.all()

class CourseModuleForm(forms.ModelForm):
    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control',"rows": 4}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ModuleMaterialFileForm(forms.ModelForm):
    class Meta:
        model = ModuleMaterialFile
        fields = ['file', 'file_type']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-control'}),
        }

from django.forms import inlineformset_factory

ModuleMaterialFileFormSet = inlineformset_factory(
    CourseModule,
    ModuleMaterialFile,
    form=ModuleMaterialFileForm,
    extra=2,  # Number of empty forms to display initially
    can_delete=True  # Allow deleting formsets
)

class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['template_file', 'min_avg_score']
        widgets = {
            'template_file': forms.FileInput(attrs={'class': 'form-control'}),
            'min_avg_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter your message here...'}),
        }
        
class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title']


        