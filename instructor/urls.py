from django.urls import path
from .views import *

urlpatterns = [
    path('login/', instructor_login_view, name='instructor_login'),
    path('logout/', user_logout, name='instructor_logout'),

    path('home/',InstructorHomeView.as_view(), name='instructor_dashboard'),

    path('courses/', CourseCreateView.as_view(), name='instructor_courses'),
    path('course/<int:course_id>/delete/', delete_course, name='instructor_course_delete'),
    path('course/<int:course_id>/', CourseDetailView.as_view(), name='instructor_course_detail'),
    path('course/<int:course_id>/delete-module/', DeleteModuleView.as_view(), name='delete_course_module'),

    path('course/<int:course_id>/quiz/', CourseQuiz.as_view(), name='instructor_course_quiz'),
    path('course/<int:course_id>/quiz/delete/', CourseQuiz.as_view(), name='delete_quiz'),
    path('course/<int:course_id>/question/delete/', CourseQuiz.as_view(), name='delete_question'),


    path('course/<int:course_id>/students/', CourseEnrolledStudentsView.as_view(), name='course_enrolled_students'),
    path('course/<int:course_id>/download/', DownloadProgressView.as_view(), name='download_progress'),
    path('enroll/requests/', InstructorPendingRequestsView.as_view(), name='pending_requests'),

    path('certificate/template/', ManageCertificateTemplatesView.as_view(), name='certificate_template'),
]
