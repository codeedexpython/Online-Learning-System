from django import forms
from .models import *
from django.forms import inlineformset_factory

class SuperuserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username')
    password = forms.CharField(widget=forms.PasswordInput(), label='Password')

# CustomUser Form
class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [ 'username','first_name', 'last_name', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={"class":"form-control"}),
            "first_name":forms.TextInput(attrs={"class":"form-control"}),
            "last_name":forms.TextInput(attrs={"class":"form-control"}),
            "email":forms.TextInput(attrs={"class":"form-control"}),
            "username":forms.TextInput(attrs={"class":"form-control"}),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets={
            "first_name":forms.TextInput(attrs={"class":"form-control"}),
            "last_name":forms.TextInput(attrs={"class":"form-control"}),
            "email":forms.TextInput(attrs={"class":"form-control"}),
        }

# UserActivityLog Form
class UserActivityLogForm(forms.ModelForm):
    class Meta:
        model = UserActivityLog
        fields = ['user', 'activity']

# MainCategory Form
class MainCategoryForm(forms.ModelForm):
    class Meta:
        model = MainCategory
        fields = ['name']
        widgets = {
            "name":forms.TextInput(attrs={"class":"form-control"}),
        }

# CourseCategory Form
class CourseCategoryForm(forms.ModelForm):
    class Meta:
        model = CourseCategory
        fields = ['name', 'parent_category']
        widgets = {
            "name":forms.TextInput(attrs={"class":"form-control"}),
            'parent_category': forms.Select(attrs={"class":"form-control"}), 
        }

# Course Form
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'instructor', 'category', 'difficulty_level']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control',"rows": 4}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
        }

# CourseModule Form
class CourseModuleForm(forms.ModelForm):
    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control',"rows": 4}),
            'order': forms.NumberInput(attrs={'class': 'form-control'})}

class ModuleMaterialFileForm(forms.Form):
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True
    )
    file_type = forms.ChoiceField(
        choices=ModuleMaterialFile.MATERIAL_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

# EnrollmentRequest Form
class EnrollmentRequestForm(forms.ModelForm):
    class Meta:
        model = EnrollmentRequest
        fields = ['student', 'course', 'status']

# CourseEnrollmentLimit Form
class CourseEnrollmentLimitForm(forms.ModelForm):
    class Meta:
        model = CourseEnrollmentLimit
        fields = ['enrollment_limit']
        widgets = {
            'enrollment_limit': forms.NumberInput(attrs={'class': 'form-control'})}

# CertificateTemplate Form

class CertificateTemplateForm(forms.ModelForm):
    class Meta:
        model = CertificateTemplate
        fields = ['template_file', 'course','min_avg_score']
        widgets = {
            'template_file': forms.FileInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'min_avg_score': forms.NumberInput(attrs={'class': 'form-control'})
        }

class IssueCertificateForm(forms.Form):
    student = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role='student'), label='Student')



class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Answer Options', 'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']
        widgets = {
            'text': forms.Textarea(attrs={'placeholder': 'Question', 'rows': 2, 'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-control'})
        }

QuestionOptionFormSet = inlineformset_factory(
    Question,
    Option,
    form=OptionForm,
    extra=2,  # Default number of forms
    min_num=2,  # Minimum number of forms
    max_num=4,  # Maximum number of forms
    can_delete=True
)