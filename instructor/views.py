from django.utils import timezone
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.forms import AuthenticationForm
from core.models import *
from core.forms import CertificateTemplateForm
from .forms import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST


def instructor_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role == 'instructor':  # Ensure the user is an instructor
                login(request, user)
                UserActivityLog.objects.filter(user=user, activity='login').delete()

                UserActivityLog.objects.create(
                    user=user,
                    activity='login'
                )
                return redirect('instructor_dashboard')  # Redirect to the instructor's dashboard or home page
            else:
                form.add_error(None, 'Invalid login for instructor.')
    else:
        form = AuthenticationForm()

    return render(request, 'instructor_login.html', {'form': form})

def user_logout(request):
    user = request.user
    
    if user.is_authenticated:
        UserActivityLog.objects.filter(user=user, activity='logout').delete()

        # Create a new log entry for logout
        UserActivityLog.objects.create(
            user=user,
            activity='logout'
        )
        logout(request)
    return redirect('instructor_login')

class InstructorHomeView(View):
    def get(self, request, *args, **kwargs):
        user=request.user
        course=Course.objects.filter(instructor=user)
        return render(request, 'instructor_dashboard.html', {'courses': course})
    
class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'instructor_course.html'
    success_url = reverse_lazy('instructor_dashboard')

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        response = super().form_valid(form)

        # Log the course creation activity
        UserActivityLog.objects.create(
            user=self.request.user,
            activity=f'Created course: {form.instance.title}'
        )

        return response

@require_POST
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    UserActivityLog.objects.create(
        user=request.user,
        activity=f'Deleted course: {course.title}'
    )
    course.delete()
    return redirect('instructor_dashboard')

#course module
class CourseDetailView(View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        module_form = CourseModuleForm()
        module_formset = ModuleMaterialFileFormSet(instance=CourseModule())  # Pass a new, empty instance
        modules = CourseModule.objects.filter(course=course)
        course_form = CourseForm(instance=course)
        pending_count = EnrollmentRequest.objects.filter(course=course, status='pending').count()
        accepted_count = EnrollmentRequest.objects.filter(course=course, status='approved').count()
        discussion_form = DiscussionForm()
        discussions = Discussion.objects.filter(course=course).order_by('timestamp')

        # Organize discussions into a dictionary with message IDs as keys
        discussions_dict = {}
        for discussion in discussions:
            if discussion.parent is None:
                # This is a top-level message
                discussions_dict[discussion.id] = {
                    'message': discussion,
                    'replies': []
                }
            else:
                # This is a reply
                if discussion.parent.id in discussions_dict:
                    discussions_dict[discussion.parent.id]['replies'].append(discussion)


        return render(request, 'instructor_course_detail.html', {
            'course': course,
            'module_form': module_form,
            'module_formset': module_formset,
            'modules': modules,
            'course_form': course_form,
            'pending_count': pending_count,
            'accepted_count': accepted_count,
            'discussions': discussions_dict,
            'discussion_form': discussion_form
        })

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        # Handling the publishing and unpublishing actions
        if 'publish' in request.POST:
            course.is_published = True
            UserActivityLog.objects.create(
                user=request.user,
                activity=f'Published {course.title} course'
            )
            course.save()
            return redirect('instructor_course_detail', course_id=course.id)

        if 'unpublish' in request.POST:
            course.is_published = False
            UserActivityLog.objects.create(
                user=request.user,
                activity=f'Unpublish {course.title} course'
            )
            course.save()
            return redirect('instructor_course_detail', course_id=course.id)

        # Handling form submission for creating modules and materials
        module_form = CourseModuleForm(request.POST)
        module_formset = ModuleMaterialFileFormSet(request.POST, request.FILES)

        if module_form.is_valid() and module_formset.is_valid():
            module = module_form.save(commit=False)
            module.course = course  # Set the course
            module.save()

            # Save the formset for the module materials
            module_formset.instance = module
            module_formset.save()

            return redirect('instructor_course_detail', course_id=course.id)

        # Handling form submission for editing the course
        course_form = CourseForm(request.POST, instance=course)

        if course_form.is_valid():
            course_form.save()
            return redirect('instructor_course_detail', course_id=course.id)

        # Handling form submission for sending replies
        if 'send_reply' in request.POST:
            message_id = request.POST.get('message_id')
            parent_message = get_object_or_404(Discussion, id=message_id)

            # Create a new reply
            Discussion.objects.create(
                course=course,
                sender=request.user,
                receiver=parent_message.sender,  # Reply to the sender of the original message
                message=request.POST.get('message'),
                parent=parent_message  # Set the parent message
            )
            return redirect('instructor_course_detail', course_id=course_id)

        return redirect('instructor_course_detail', course_id=course_id)



class DeleteModuleView(View):
    def post(self, request, *args, **kwargs):
        module_id = request.POST.get('module_id')
        course_id = kwargs.get('course_id')
        if module_id:
            module = get_object_or_404(CourseModule, id=module_id)
            module.delete()
        return redirect('instructor_course_detail', course_id=course_id)
    
class InstructorPendingRequestsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Fetch courses taught by the logged-in instructor
        instructor_courses = Course.objects.filter(instructor=request.user)
        
        # Initialize the queryset for pending requests
        pending_requests = EnrollmentRequest.objects.filter(course__in=instructor_courses, status='pending')

        # Filter by course ID if provided
        course_id = request.GET.get('course_id')
        if course_id:
            pending_requests = pending_requests.filter(course_id=course_id)
        
        return render(request, 'pending_requests.html', {
            'pending_requests': pending_requests,
        })

    def post(self, request, *args, **kwargs):
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        enrollment_request = get_object_or_404(EnrollmentRequest, id=request_id)
        if enrollment_request.course.instructor == request.user:
            if action == 'approve':
                enrollment_request.status = 'approved'
                enrollment_request.response_date = timezone.now()  # Update response date
                UserActivityLog.objects.create(
                user=request.user,
                activity=f'{enrollment_request.student.username} {enrollment_request.course.title} course request approved'
            )
                enrollment_request.save()
                
                # Check enrollment limits and enroll the student if possible
                enrollment_limit = CourseEnrollmentLimit.objects.filter(course=enrollment_request.course).first()
                if enrollment_limit and not enrollment_limit.is_full():
                    if enrollment_limit.enroll_student():
                        print("Student enrolled successfully")
                    else:
                        print("Enrollment failed: limit is full")
                else:
                    print("Enrollment limit not set or course is already full")

            # Handle reject action
            elif action == 'reject':
                enrollment_request.status = 'rejected'
                enrollment_request.response_date = timezone.now()
                UserActivityLog.objects.create(
                user=request.user,
                activity=f'{enrollment_request.student.username} {enrollment_request.course.title} course request rejected'
            )
                enrollment_request.save()

        return redirect('pending_requests')
    

class CourseEnrolledStudentsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        # Fetch enrolled students for the specified course
        enrolled_students = EnrollmentRequest.objects.filter(course=course, status='approved').select_related('student')

        student_progress_data = []
        for enrollment in enrolled_students:
            student = enrollment.student
            modules = CourseModule.objects.filter(course=course)
            quizzes_with_questions = self.get_quizzes_with_questions(modules, student)

            total_quizzes = sum(len(q['quizzes']) for q in quizzes_with_questions)
            completed_quizzes = sum(1 for q in quizzes_with_questions for quiz in q['quizzes'] if quiz['attempt'])
            progress = (completed_quizzes / total_quizzes) * 100 if total_quizzes > 0 else 0
            total_score = sum(attempt.score for attempt in QuizAttempt.objects.filter(student=student, quiz__in=[q['quiz'] for q in quizzes_with_questions for q in q['quizzes']]))
            average_score = (total_score / total_quizzes) if total_quizzes > 0 else 0
            student_progress_data.append({
                'student': student,
                'progress': progress,
                'total_quizzes': total_quizzes,
                'completed_quizzes': completed_quizzes,
                'average_score': average_score,
                'response_date': enrollment.response_date,
            })

        return render(request, 'enrolled_students.html', {
            'course': course,
            'student_progress_data': student_progress_data,
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

class ManageCertificateTemplatesView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user_courses = Course.objects.filter(instructor=request.user)
        templates = []
        for course in user_courses:
            template = CertificateTemplate.objects.filter(course=course).first()
            form = CertificateTemplateForm(instance=template) if template else CertificateTemplateForm(initial={'course': course})
            templates.append((course, form))
        
        return render(request, 'add_template.html', {
            'templates': templates
        })

    def post(self, request, *args, **kwargs):
        user_courses = Course.objects.filter(instructor=request.user)
        for course in user_courses:
            form = CertificateTemplateForm(request.POST, request.FILES, instance=CertificateTemplate.objects.filter(course=course).first())
            
            if form.is_valid():
                template = form.save(commit=False)
                template.course = course
                template.save()
        return redirect('certificate_template')


from core.forms import QuestionForm, QuestionOptionFormSet 
class CourseQuiz(View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        modules = CourseModule.objects.filter(course=course)
        quizzes = Quiz.objects.filter(module__in=modules)
        
        quizzes_with_modules = []
        for module in modules:
            quiz = quizzes.filter(module=module).first()
            questions = quiz.questions.all() if quiz else []
            quizzes_with_modules.append((module, quiz, questions))
        
        quiz_form = QuizForm()
        question_form = QuestionForm()
        options_formset = QuestionOptionFormSet()

        return render(request, 'instructor_course_quiz.html', {
            'course': course,
            'quizzes_with_modules': quizzes_with_modules,
            'quiz_form': quiz_form,
            'question_form': question_form,
            'options_formset': options_formset,
            
        })

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        if 'create_quiz' in request.POST:
            module_id = request.POST.get('module_id')
            module = get_object_or_404(CourseModule, id=module_id)
            quiz_form = QuizForm(request.POST)
            if quiz_form.is_valid():
                Quiz.objects.create(module=module, **quiz_form.cleaned_data)
            return redirect('instructor_course_quiz', course_id=course_id)

        if 'create_question_with_options' in request.POST:
            quiz_id = request.POST.get('quiz_id')
            if not quiz_id:
                return redirect('quiz_doubt', course_id=course_id)
            quiz = get_object_or_404(Quiz, id=quiz_id)
            question_form = QuestionForm(request.POST)
            options_formset = QuestionOptionFormSet(request.POST)
            if question_form.is_valid() and options_formset.is_valid():
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.save()
                options_formset.instance = question
                options_formset.save()
            return redirect('instructor_course_quiz', course_id=course_id)

        if 'delete_quiz' in request.POST:
            print(request.POST)
            quiz_id = request.POST.get('quiz_id')
            if quiz_id:
                quiz = get_object_or_404(Quiz, id=quiz_id)
                quiz.delete()
            return redirect('instructor_course_quiz', course_id=course_id)

        if 'delete_question' in request.POST:
            question_id = request.POST.get('question_id')
            if question_id:
                question = get_object_or_404(Question, id=question_id)
                question.delete()
            return redirect('instructor_course_quiz', course_id=course_id)

        return redirect('instructor_course_quiz', course_id=course_id)


from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from io import BytesIO

class DownloadProgressView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Fetch enrolled students
        enrolled_students = EnrollmentRequest.objects.filter(course=course, status='approved').select_related('student')

        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        styles = getSampleStyleSheet()
        title_style = styles['Title']
        normal_style = styles['Normal']

        # Title
        story.append(Paragraph(f"Course Progress Report for {course.title}", title_style))
        story.append(Paragraph("Generated on: ", normal_style))

        # Table data
        table_data = [
            ['Student', 'Enrollment Date', 'Completed Quizzes', 'Total Quizzes', 'Progress(%)', 'Avg.Score(%)']
        ]

        for enrollment in enrolled_students:
            student = enrollment.student
            modules = CourseModule.objects.filter(course=course)
            quizzes_with_questions = self.get_quizzes_with_questions(modules, student)

            total_quizzes = sum(len(q['quizzes']) for q in quizzes_with_questions)
            completed_quizzes = sum(1 for q in quizzes_with_questions for quiz in q['quizzes'] if quiz['attempt'])
            progress = (completed_quizzes / total_quizzes) * 100 if total_quizzes > 0 else 0
            total_score = sum(attempt.score for attempt in QuizAttempt.objects.filter(student=student, quiz__in=[q['quiz'] for q in quizzes_with_questions for q in q['quizzes']]))
            average_score = (total_score / total_quizzes) if total_quizzes > 0 else 0

            table_data.append([
                student.username,
                enrollment.request_date.strftime('%Y-%m-%d'),
                completed_quizzes,
                total_quizzes,
                f"{progress:.2f}",
                f"{average_score:.2f}"
            ])

        # Create table
        table = Table(table_data, colWidths=[100, 100, 150, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#d5a6a0'),
            ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f4cccc'),
            ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
        ]))

        story.append(table)
        doc.build(story)
        buffer.seek(0)

        filename = f"{course.title}_enrollment_report.pdf"
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

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


