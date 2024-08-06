from datetime import datetime
from django.shortcuts import render, redirect,get_object_or_404
from django.views import View
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import user_passes_test
from .models import *
from .forms import *

def superuser_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                login(request, user)
                return redirect('home')  # Redirect to Django admin dashboard
            else:
                form.add_error(None, 'Invalid login for superuser.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('superuser_login')

def home(request):
    student_count = CustomUser.objects.filter(role='student').count()
    instructor_count = CustomUser.objects.filter(role='instructor').count()
    courses = Course.objects.all().count()
    return render(request, 'index.html',{'student':student_count, 'instructor':instructor_count,'course': courses})

class StudentListView(View):
    def get(self, request, *args, **kwargs):
        students = CustomUser.objects.filter(role='student').all()
        form = CustomUserForm()
        return render(request, 'students.html', {'students': students, 'form': form})
    
    def post(self, request, *args, **kwargs):
        if 'create_student' in request.POST:
            form = CustomUserForm(request.POST)
            if form.is_valid():
                student = form.save(commit=False)
                student.role = 'student'
                student.set_password(form.cleaned_data['password'])
                student.save()
                return redirect('student_list')
        
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')
        
        if student_id and action:
            student = get_object_or_404(CustomUser, id=student_id, role='student')
            if action == "activate":
                student.is_active = True
            elif action == "deactivate":
                student.is_active = False
            student.save()
        
        return redirect('student_list')

def student_detail(request, pk):
    student = get_object_or_404(CustomUser, pk=pk, role='student')
    courses =EnrollmentRequest.objects.filter(student=student,status='approved')
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_detail', pk=student.pk)
    else:
        form = UserUpdateForm(instance=student)
    return render(request, 'student_profile.html', {'student': student, 'form':form, 'courses':courses})


class InstructorListView(View):
    def get(self, request, *args, **kwargs):
        instructors = CustomUser.objects.filter(role='instructor').all()
        form = CustomUserForm()
        return render(request, 'instructor.html', {'instructors': instructors, 'form': form})
    

    def post(self, request, *args, **kwargs):
        if 'create_instructor' in request.POST:
            form = CustomUserForm(request.POST)
            if form.is_valid():
                instructor = form.save(commit=False)
                instructor.role = 'instructor'
                instructor.set_password(form.cleaned_data['password'])
                instructor.save()
                return redirect('instructor_list')

        instructor_id = request.POST.get('instructor_id')
        action = request.POST.get('action')
        if instructor_id and action:
            instructor = get_object_or_404(CustomUser, id=instructor_id, role='instructor')
            if action == "activate":
                instructor.is_active = True
            elif action == "deactivate":
                instructor.is_active = False
            instructor.save()
        
        return redirect('instructor_list')

def instructor_detail(request, pk):
    instructor = get_object_or_404(CustomUser, pk=pk, role='instructor')
    courses = Course.objects.filter(instructor=instructor)
    activity = UserActivityLog.objects.filter(user=instructor).order_by('timestamp')[:10]

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=instructor)
        if form.is_valid():
            form.save()
            return redirect('instructor_detail', pk=instructor.pk)
    else:
        form = UserUpdateForm(instance=instructor)
    return render(request, 'instructor_profile.html', 
                  {'instructor': instructor,
                    'courses':courses,
                      'form':form,
                      'activities':activity,
                      })

@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    return redirect('home')

class CourseListView(View):
    def get(self, request, *args, **kwargs):
        courses = Course.objects.all()
        categories = CourseCategory.objects.all()
        instructors = CustomUser.objects.filter(role='instructor')
        return render(request, 'course.html', {'courses': courses, 'categories': categories, 'instructors': instructors})

    def post(self, request, *args, **kwargs):
        course_id = request.POST.get('course_id')
        action = request.POST.get('action')
        
        if course_id and action:
            course = get_object_or_404(Course, id=course_id)
            if action == "publish":
                course.is_published = True
                course.save()
            elif action == "unpublish":
                course.is_published = False
                course.save()
            elif action == "update_course":
                form = CourseForm(request.POST, instance=course)
                if form.is_valid():
                    form.save()
        
        return redirect('course_list')
    
class CourseDetailView(View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        modules = CourseModule.objects.filter(course=course).prefetch_related('files')
        enrolled_students = EnrollmentRequest.objects.filter(course=course, status='approved')
        enrollment_limit, created = CourseEnrollmentLimit.objects.get_or_create(course=course)
        module_form = CourseModuleForm()
        material_form = ModuleMaterialFileForm()
        limit_form = CourseEnrollmentLimitForm(instance=enrollment_limit)

        return render(request, 'course_detail.html', {
            'course': course,
            'modules': modules,
            'module_form': module_form,
            'limit_form': limit_form,
            'material_form': material_form,
            'enrolled_students':enrolled_students,
        })

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        if 'create_module' in request.POST:
            module_form = CourseModuleForm(request.POST)
            if module_form.is_valid():
                module = module_form.save(commit=False)
                module.course = course
                module.save()
                return redirect('course_detail', course_id=course.id)

        elif 'upload_material' in request.POST:
            material_form = ModuleMaterialFileForm(request.POST, request.FILES)
            module_id = request.POST.get('module_id')
            module = get_object_or_404(CourseModule, id=module_id)
            
            if material_form.is_valid():
                file = request.FILES.get('file')
                file_type = material_form.cleaned_data.get('file_type')
                
                ModuleMaterialFile.objects.create(module=module, file=file, file_type=file_type)

                return redirect('course_detail', course_id=course.id)
            
        elif 'action' in request.POST:
            enroll_id = request.POST.get('enroll_id')
            action = request.POST.get('action')
            enrollment_request = get_object_or_404(EnrollmentRequest, id=enroll_id)

            if action == 'remove':
                enrollment_request.status = 'removed'
                enrollment_request.save()
                enrollment_limit = get_object_or_404(CourseEnrollmentLimit, course=enrollment_request.course)
                if enrollment_limit.unenroll_student():
                    print("Student removed successfully")
                else:
                    print("No enrollments to remove")

            return redirect('course_detail', course_id=course.id)
        
        elif 'update_limit' in request.POST:
            limit_form = CourseEnrollmentLimitForm(request.POST)
            if limit_form.is_valid():
                # Ensure we get or create the enrollment limit
                enrollment_limit, created = CourseEnrollmentLimit.objects.get_or_create(course=course)
                
                # Update the enrollment limit with form data
                enrollment_limit.enrollment_limit = limit_form.cleaned_data['enrollment_limit']
                enrollment_limit.save()
                
                return redirect('course_detail', course_id=course.id)

        return redirect('course_detail', course_id=course.id)


@require_POST
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    return redirect('course_list')

class DeleteMaterialView(View):
    def post(self, request, *args, **kwargs):
        material_id = request.POST.get('material_id')
        if material_id:
            material = get_object_or_404(ModuleMaterialFile, id=material_id)
            material.delete()
        return redirect('course_detail', course_id=kwargs.get('course_id'))


class DeleteModuleView(View):
    def post(self, request, *args, **kwargs):
        module_id = request.POST.get('module_id')
        course_id = kwargs.get('course_id')
        if module_id:
            module = get_object_or_404(CourseModule, id=module_id)
            module.delete()
        return redirect('course_detail', course_id=course_id)

class CourseCreate(View):
    def get(self, request, *args, **kwargs):
        categories = MainCategory.objects.all()
        subcategories = CourseCategory.objects.all()
        instructors = CustomUser.objects.filter(role='instructor')
        course_form = CourseForm()
        category_form = MainCategoryForm()
        subcategory_form=CourseCategoryForm()
        return render(request, 'create_course.html', {
            'categories': categories,
            'subcategories': subcategories,
            'instructors': instructors,
            'course_form': course_form,
            'category_form': category_form,
            'subcategory_form': subcategory_form
        })

    def post(self, request, *args, **kwargs):
        if 'create_course' in request.POST:
            form = CourseForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('course_list')
        elif 'create_category' in request.POST:
            category_form = MainCategoryForm(request.POST)
            if category_form.is_valid():
                category_form.save()
                return redirect('create_course')
        elif 'update_category' in request.POST:
            category_id = request.POST.get('category_id')
            category = get_object_or_404(MainCategory, id=category_id)
            category_form = MainCategoryForm(request.POST, instance=category)
            if category_form.is_valid():
                category_form.save()
                return redirect('create_course')
            
        elif 'create_sub_category' in request.POST:
            subcategory_form = CourseCategoryForm(request.POST)
            if subcategory_form.is_valid():
                subcategory_form.save()
                return redirect('create_course')
            
        elif 'update_sub_category' in request.POST:
            sub_category_id = request.POST.get('subcategory_id')
            sub_category = get_object_or_404(CourseCategory, id=sub_category_id)
            subcategory_form = CourseCategoryForm(request.POST, instance=sub_category)
            if subcategory_form.is_valid():
                subcategory_form.save()
                return redirect('create_course')
        return redirect('create_course')
    
class MainCategoryDeleteView(View):
    def post(self, request, *args, **kwargs):
        category_id = kwargs.get('pk')
        category = get_object_or_404(MainCategory, id=category_id)
        category.delete()
        return redirect('create_course')
    
class SubCategoryDeleteView(View):
    def post(self, request, *args, **kwargs):
        subcategory_id = kwargs.get('pk')
        subcategory = get_object_or_404(CourseCategory, id=subcategory_id)
        subcategory.delete()
        return redirect('create_course')
    
class PendingEnrollmentRequestsView(View):
    def get(self, request, *args, **kwargs):
        requests = EnrollmentRequest.objects.filter(status='pending')
        
        return render(request, 'enroll.html', {'requests': requests})
    
    def post(self, request, *args, **kwargs):
        enroll_id = request.POST.get('enroll_id')
        action = request.POST.get('action')
        enrollment_request = get_object_or_404(EnrollmentRequest, id=enroll_id)

        if action == 'approve':
            enrollment_request.status = 'approved'
            enrollment_request.save()
            enrollment_limit = CourseEnrollmentLimit.objects.filter(course=enrollment_request.course).first()
            if enrollment_limit and not enrollment_limit.is_full():
                if enrollment_limit.enroll_student():
                    print("Student enrolled successfully")
                else:
                    print("Enrollment failed: limit is full")
            else:
                print("Enrollment limit not set or course is already full")
                
        elif action == 'reject':
            enrollment_request.status = 'rejected'
            enrollment_request.save()

        return redirect('enrollment_req')
    

class EnrollmentStatisticsView(View):
    def get(self, request, *args, **kwargs):
        # Get all courses
        courses = Course.objects.all()
        
        # Prepare data for each course
        course_data = []

        for course in courses:
            total_requests = EnrollmentRequest.objects.filter(course=course).count()
            approved_requests = EnrollmentRequest.objects.filter(course=course, status='approved').count()
            pending_requests = EnrollmentRequest.objects.filter(course=course, status='pending').count()
            rejected_requests = EnrollmentRequest.objects.filter(course=course, status='rejected').count()
            
            try:
                enrollment_limit = course.enrollment_limit
                limit = enrollment_limit.enrollment_limit
                current_enrollments_count = enrollment_limit.current_enrollments
            except CourseEnrollmentLimit.DoesNotExist:
                limit = None
                current_enrollments_count = 0

            course_data.append({
                'title': course.title,
                'labels': ['Approved', 'Pending', 'Rejected', 'Current Enrollments', 'Enrollment Limit'],
                'data': [approved_requests, pending_requests, rejected_requests, current_enrollments_count, limit if limit is not None else 0],
                'backgroundColor': ['rgba(75, 192, 192, 0.2)', 'rgba(255, 206, 86, 0.2)', 'rgba(255, 99, 132, 0.2)', 'rgba(153, 102, 255, 0.2)', 'rgba(255, 159, 64, 0.2)'],
                'borderColor': ['rgba(75, 192, 192, 1)', 'rgba(255, 206, 86, 1)', 'rgba(255, 99, 132, 1)', 'rgba(153, 102, 255, 1)', 'rgba(255, 159, 64, 1)'],
            })

        context = {
            'course_data': course_data,
        }

        return render(request, 'enroll_sts.html', context)



# certificates
class CertificateTemplateListView(View):
    def get(self, request, *args, **kwargs):
        templates = CertificateTemplate.objects.all()
        return render(request, 'certificate_template_list.html', {'templates': templates})

    def post(self, request, *args, **kwargs):
        form = CertificateTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('certificate_template_list')
        return render(request, 'certificate_template_list.html', {'form': form})


class CertificateListView(View):
    def get(self, request, *args, **kwargs):
        certificates = Certificate.objects.all()
        return render(request, 'certificate_list.html', {'certificates': certificates})
    

from instructor.forms import QuizForm

class QuizDoubtView(View):
    def get(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        modules = CourseModule.objects.filter(course=course)
        quizzes = Quiz.objects.filter(module__in=modules)

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

        quizzes_with_modules = []
        for module in modules:
            quiz = quizzes.filter(module=module).first()
            questions = quiz.questions.all() if quiz else []
            quizzes_with_modules.append((module, quiz, questions))

        quiz_form = QuizForm()
        question_form = QuestionForm()
        options_formset = QuestionOptionFormSet()

        return render(request, 'quiz_doubts.html', {
            'course': course,
            'quizzes_with_modules': quizzes_with_modules,
            'quiz_form': quiz_form,
            'question_form': question_form,
            'options_formset': options_formset,
            'discussions': discussions_dict,
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
            return redirect('quiz_doubt', course_id=course_id)

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
            return redirect('quiz_doubt', course_id=course_id)
        
        if 'admin_delete_quiz' in request.POST:
            quiz_id = request.POST.get('quiz_id')
            if quiz_id:
                quiz = get_object_or_404(Quiz, id=quiz_id)
                quiz.delete()
            return redirect('quiz_doubt', course_id=course_id)

        if 'admin_delete_question' in request.POST:
            question_id = request.POST.get('question_id')
            if question_id:
                question = get_object_or_404(Question, id=question_id)
                question.delete()
            return redirect('quiz_doubt', course_id=course_id)
        
        if 'admin_delete_discussion' in request.POST:
            discussion_id = request.POST.get('discussion_id')
            if discussion_id:
                discussion = get_object_or_404(Discussion, id=discussion_id)
                discussion.delete()
            return redirect('quiz_doubt', course_id=course_id)

        return redirect('quiz_doubt', course_id=course_id)

from django.db.models import Avg

def analytics_dashboard(request):
    # Calculate completion rates
    completion_rates = (
        EnrollmentRequest.objects
        .select_related('course')
        .values('course__title')
        .annotate(avg_progress=Avg('progress'))
    )
    
    # Calculate student performance with course details
    student_performance = (
        QuizAttempt.objects
        .select_related('student', 'quiz__module__course')
        .values('student__username', 'quiz__module__course__title')
        .annotate(avg_score=Avg('score'))
    )
    
    # Get list of all courses for reference
    courses = Course.objects.all()

    # Add data to context
    context = {
        'completion_rates': completion_rates,
        'student_performance': student_performance,
        'courses': courses,
    }
    
    return render(request, 'analytics_dashboard.html', context)


from django.http import HttpResponse
import csv
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="performance_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Quiz', 'Score', 'Attempt Date'])
    
    quiz_attempts = QuizAttempt.objects.all()
    for attempt in quiz_attempts:
        writer.writerow([attempt.student, attempt.quiz, attempt.score, attempt.attempt_date])

    return response

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.lib import colors

def export_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Performance Report", styles['Title']))

    # Course Completion Rates
    content.append(Paragraph("Course Completion Rates", styles['Heading2']))
    data = [["Course", "Average Progress"]]

    # Calculate average progress for each course
    courses = Course.objects.all()
    for course in courses:
        avg_progress = EnrollmentRequest.objects.filter(course=course).aggregate(avg_progress=Avg('progress'))['avg_progress']
        data.append([course.title, f"{avg_progress:.2f}" if avg_progress else "N/A"])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#f2f2f2'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    content.append(table)

    # Student Performance per Course
    content.append(Paragraph("Student Performance per Course", styles['Heading2']))
    data = [["Student", "Course", "Average Score"]]

    # Calculate average score for each student in each course
    student_performance = (
        QuizAttempt.objects
        .select_related('student', 'quiz__course')
        .values('student__username', 'quiz__module__course__title')
        .annotate(avg_score=Avg('score'))
    )

    for item in student_performance:
        data.append([item['student__username'], item['quiz__module__course__title'], f"{item['avg_score']:.2f}" if item['avg_score'] else "N/A"])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#f2f2f2'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    content.append(table)

    doc.build(content)

    # Get PDF data from buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Create a HTTP response with the PDF data
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="performance_report.pdf"'
    return response

def generate_instructor_activity_report(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    title = Paragraph("Instructor Activity Report", styles['Title'])
    
    table_data = [['Instructor Name', 'Activity', 'Timestamp']]
    
    logs = UserActivityLog.objects.filter(user__role='instructor').order_by('-timestamp')
    for log in logs:
        table_data.append([
            log.user.username,
            log.activity,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    doc.build([title, table])
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
