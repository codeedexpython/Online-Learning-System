from django.shortcuts import render
from django.db.models import Count
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.utils import timezone
from django.views import View
from core. models import *
from .forms import *

# Create your views here.
class IndexView(View):
    def get(self, request, *args, **kwargs):
        # Annotate each MainCategory with the count of related courses
        categories = MainCategory.objects.annotate(course_count=Count('subcategories__course')).order_by('name')
        course=Course.objects.filter(is_published=True)

        return render(request, 'student_index.html', {
            'categories': categories,
            'courses':course,
        })

class StudentRegistrationView(View):
    def get(self, request, *args, **kwargs):
        form = StudentRegistrationForm()
        return render(request, 'student_register.html', {'form': form})

    def post(self, request, *args, **kwargs):
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('student_login')  
        return render(request, 'student_register.html', {'form': form})

def student_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role == 'student': 
                login(request, user)
                UserActivityLog.objects.filter(user=user, activity='login').delete()
                UserActivityLog.objects.create(
                    user=user,
                    activity='login'
                )
                return redirect('student_dashboard') 
            else:
                form.add_error(None, 'Invalid login for student.')
    else:
        form = AuthenticationForm()

    return render(request, 'student_login.html', {'form': form})


def user_logout(request):
    user = request.user
    
    if user.is_authenticated:
        UserActivityLog.objects.filter(user=user, activity='logout').delete()

        # Create a new log entry for logout
        UserActivityLog.objects.create(
            user=user,
            activity='logout'
        )
    
    return redirect('student_index')

class StudentHomeView(View):
    def get(self, request, *args, **kwargs):
        # Get all main categories and their sub-categories
        main_categories = MainCategory.objects.all()
        # Get search parameters from the request
        main_category_id = request.GET.get('main_category')
        course_title = request.GET.get('course_title', '')

        # Filter courses based on selected categories and title
        courses = Course.objects.filter(is_published=True)
        if main_category_id:
            sub_categories = CourseCategory.objects.filter(parent_category_id=main_category_id)
            courses = courses.filter(category__parent_category_id=main_category_id)
        
        if course_title:
            courses = courses.filter(title__icontains=course_title)

        return render(request, 'home.html', {
            'courses': courses,
            'main_categories': main_categories,
            'course_title': course_title,
        })


class CourseDetailView(View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        modules = CourseModule.objects.filter(course=course)
        accepted_count = EnrollmentRequest.objects.filter(course=course, status='approved').count()
        enrollment_request = EnrollmentRequest.objects.filter(course=course, student=request.user).first()
        form = DiscussionForm()

        discussions = Discussion.objects.filter(course=course).order_by('timestamp')

        discussions_dict = {}
        for discussion in discussions:
            if discussion.parent is None:
                discussions_dict[discussion.id] = {
                    'message': discussion,
                    'replies': []
                }
            else:
                if discussion.parent.id in discussions_dict:
                    discussions_dict[discussion.parent.id]['replies'].append(discussion)

        quizzes_with_questions = self.get_quizzes_with_questions(modules, request.user)

        return render(request, 'student_course_detail.html', {
            'course': course,
            'modules': modules,
            'accepted_count': accepted_count,
            'enrollment_request': enrollment_request,
            'discussions': discussions_dict,
            'form': form,
            'quizzes_with_questions': quizzes_with_questions,
        })

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        action = request.POST.get('action')
        enrollment_request = EnrollmentRequest.objects.filter(course=course, student=request.user).first()

        if action == 'enroll':
            existing_request = EnrollmentRequest.objects.filter(course=course, student=request.user).first()
            if not existing_request:
                EnrollmentRequest.objects.create(
                    student=request.user,
                    course=course,
                    status='pending',
                    request_date=timezone.now()
                )
                UserActivityLog.objects.create(
                    user=request.user,
                    activity=f'Requested enrollment in course: {course.title}')
            else:
                if enrollment_request.status == 'rejected':
                    enrollment_request.status = 'pending'
                    enrollment_request.request_date = timezone.now()
                    enrollment_request.save()
        
        elif action == 'unenroll':
            existing_request = EnrollmentRequest.objects.filter(course=course, student=request.user).first()
            if existing_request:
                UserActivityLog.objects.create(
                user=request.user,
                activity=f'Removed enrollment request for course: {course.title}')
                existing_request.delete()

        if 'send_message' in request.POST:
            form = DiscussionForm(request.POST)
            if form.is_valid():
                discussion = form.save(commit=False)
                discussion.course = course
                discussion.sender = request.user
                discussion.receiver = course.instructor
                discussion.save()
                return redirect('student_course_detail', course_id=course_id)
        
        if 'submit_quiz' in request.POST:
            quiz_id = request.POST.get('quiz_id')
            quiz = get_object_or_404(Quiz, id=quiz_id)

            if QuizAttempt.objects.filter(student=request.user, quiz=quiz).exists():
                return redirect('student_course_detail', course_id=course_id)

            total_questions = 0
            correct_answers = 0

            for question in quiz.questions.all():
                user_answer = request.POST.get(f'question_{question.id}')
                if user_answer:
                    option = get_object_or_404(Option, id=user_answer)
                    if option.is_correct:
                        correct_answers += 1
                total_questions += 1

            score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

            QuizAttempt.objects.create(
                student=request.user,
                quiz=quiz,
                score=score
            )

            return redirect('student_course_detail', course_id=course_id)

        return redirect('student_course_detail', course_id=course_id)

    def get_quizzes_with_questions(self, modules, user):
        quizzes_with_questions = []
        for module in modules:
            quizzes = Quiz.objects.filter(module=module)
            quizzes_with_questions.append({
                'module': module,
                'quizzes': [{
                    'quiz': quiz,
                    'questions': quiz.questions.all(),
                    'attempt': QuizAttempt.objects.filter(student=user, quiz=quiz).first()
                } for quiz in quizzes]
            })
        return quizzes_with_questions



class EnrolledCoursesListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        enrollment_requests = EnrollmentRequest.objects.filter(student=request.user, status='approved')

        # Prepare a list to hold course progress data
        course_progress_data = []
        
        for enrollment in enrollment_requests:
            course = enrollment.course
            modules = CourseModule.objects.filter(course=course)
            quizzes_with_questions = self.get_quizzes_with_questions(modules, request.user)
            
            total_quizzes = sum(len(q['quizzes']) for q in quizzes_with_questions)
            completed_quizzes = sum(1 for q in quizzes_with_questions for quiz in q['quizzes'] if quiz['attempt'])
            progress = (completed_quizzes / total_quizzes) * 100 if total_quizzes > 0 else 0
            
            course_progress_data.append({
                'course': course,
                'progress': progress,
                'total_quizzes': total_quizzes,
                'completed_quizzes': completed_quizzes,
            })
        
        return render(request, 'student_courses_list.html', {
            'course_progress_data': course_progress_data,
        })
    
    def get_quizzes_with_questions(self, modules, user):
        quizzes_with_questions = []
        for module in modules:
            quizzes = Quiz.objects.filter(module=module)
            quizzes_with_questions.append({
                'module': module,
                'quizzes': [{
                    'quiz': quiz,
                    'questions': quiz.questions.all(),
                    'attempt': QuizAttempt.objects.filter(student=user, quiz=quiz).first()
                } for quiz in quizzes]
            })
        return quizzes_with_questions
    

    
class ProfileAndPasswordUpdateView(View):
    def get(self, request, *args, **kwargs):
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)
        return render(request, 'profile_update.html', {
            'profile_form': profile_form,
            'password_form': password_form,
        })

    def post(self, request, *args, **kwargs):
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                return redirect('profile_update')  # Redirect to a success page or any other page
        else:
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = request.user
                user.set_password(password_form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in after password change
                logout(request)  # Log out the user after changing the password
                return redirect('student_login')  # Redirect to the login page or any other page

        # Render the page with forms if there are errors
        profile_form = ProfileUpdateForm(instance=request.user)
        return render(request, 'profile_update.html', {
            'profile_form': profile_form,
            'password_form': password_form,
        })

class CertificateListView(View):
    def get(self, request, *args, **kwargs):
        certificates = Certificate.objects.filter(student=request.user)
        return render(request, 'student_certificate.html', {'certificates': certificates})
    

from django.http import HttpResponseForbidden

class GenerateCertificateView(View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        if not request.user.is_authenticated:
            return HttpResponseForbidden("You need to be logged in to generate a certificate.")

        # Check if the user is eligible for the certificate
        self.check_and_generate_certificate(request.user, course)

        return redirect('student_certificate_list')  # Redirect to the certificate list or detail view

    def check_and_generate_certificate(self, student, course):
        quizzes = Quiz.objects.filter(module__course=course)
        total_score = 0
        total_quizzes = 0
        
        for quiz in quizzes:
            attempt = QuizAttempt.objects.filter(student=student, quiz=quiz).first()
            if attempt:
                total_score += attempt.score
                total_quizzes += 1

        average_score = (total_score / total_quizzes) if total_quizzes > 0 else 0

        template = course.template
        if average_score >= template.min_avg_score:
            certificate, created = Certificate.objects.get_or_create(
                student=student,
                certificate_template__course=course,
                defaults={'certificate_template': template}
            )
            if created:
                certificate_file = self.generate_certificate_file(student, course)
                certificate.certificate_file = certificate_file
                certificate.save()

    def generate_certificate_file(self, student, course):
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO
        from django.core.files.base import ContentFile

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica", 12)
        c.drawString(100, height - 100, "Certificate of Completion")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 150, f"This is to certify that {student.get_full_name()}")
        c.drawString(100, height - 175, f"has successfully completed the course:")
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 225, f"{course.title}")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 275, f"Issued Date: {timezone.now().strftime('%Y-%m-%d')}")

        c.showPage()
        c.save()
        buffer.seek(0)
        
        return ContentFile(buffer.getvalue(), 'certificate.pdf') 
    
from django.contrib.auth.views import PasswordResetView,PasswordResetDoneView,PasswordResetConfirmView,PasswordResetCompleteView
from django.urls import reverse_lazy

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    success_url = reverse_lazy('student_password_reset_done')

    def form_valid(self, form):
        return super().form_valid(form)
    
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('student_password_reset_complete')

    def form_valid(self, form):
        # Custom logic (if any) after setting the new password
        return super().form_valid(form)
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'