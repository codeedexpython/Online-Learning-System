from django.db import models
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('instructor', 'Instructor'),
        ('student', 'Student'),
        ('admin','Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    def __str__(self):
        return self.username

# User Activity Log
class UserActivityLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    activity = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.username}'

#main category
class MainCategory(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

#course Category
class CourseCategory(models.Model):
    name = models.CharField(max_length=100)
    parent_category = models.ForeignKey(MainCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    
    def __str__(self):
        return self.name

# Course Model
class Course(models.Model):
    DIFFICULTY_LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(CustomUser, limit_choices_to={'role': 'instructor'}, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey('CourseCategory', on_delete=models.SET_NULL, null=True, blank=True,related_name='course')
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='required_by')
    difficulty_level = models.CharField(max_length=50, choices=DIFFICULTY_LEVEL_CHOICES)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} - {self.title}'

def upload_to(instance, filename):
    return f'course_materials/{instance.module.course.title}/{instance.module.title}/{filename}'

class ModuleMaterialFile(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('other', 'Other'),
    ]
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=upload_to)
    file_type = models.CharField(max_length=50, choices=MATERIAL_TYPE_CHOICES, default='other')

    def __str__(self):
        return f'{self.file.name}'
    
class EnrollmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('removed', 'Removed'),
    ]
    
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    course = models.ForeignKey('Course', on_delete=models.CASCADE,related_name='enrollment_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    response_date = models.DateTimeField(null=True, blank=True)
    progress = models.FloatField(default=0.0)

    def __str__(self):
        return f'{self.student.username} - {self.course.title} - {self.status}'

class CourseEnrollmentLimit(models.Model):
    course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='enrollment_limit')
    enrollment_limit = models.PositiveIntegerField(default=0)
    current_enrollments = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f'{self.course.title} - Limit: {self.enrollment_limit} - Current: {self.current_enrollments}'

    def is_full(self):
        return self.current_enrollments >= self.enrollment_limit

    def enroll_student(self):
        if not self.is_full():
            self.current_enrollments += 1
            self.save()
            return True
        return False

    def unenroll_student(self):
        if self.current_enrollments > 0:
            self.current_enrollments -= 1
            self.save()
            return True
        return False


#certificate
class CertificateTemplate(models.Model):
    template_file = models.FileField(upload_to='certificate_templates/')
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='template')
    min_avg_score = models.FloatField(default=35.0) 

    def __str__(self):
        return self.min_avg_score

class Certificate(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    certificate_template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    issued_date = models.DateField(auto_now_add=True)
    certificate_file = models.FileField(upload_to='certificates/', null=True, blank=True)

    def __str__(self):
        return f'{self.student.username} - {self.certificate_template.course.title}'

class Discussion(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussions')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_discussions')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_discussions')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender} to {self.receiver} on {self.course.title}"
    
class Quiz(models.Model):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    is_published=models.BooleanField(default=True)

class Question(models.Model):
    QUESTION_TYPES = [
        ('MC', 'Multiple Choice'),
        ('TF', 'True or False'),
    ]

    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES)

class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)


class QuizAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    attempt_date = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('student', 'quiz')

    def __str__(self):
        return f"{self.student} - {self.quiz}"

class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.attempt} - {self.question}"