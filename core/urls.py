from django.urls import path
from .views import *

urlpatterns = [
    path('login/', superuser_login_view, name='superuser_login'),
    path('logout/', user_logout, name='admin_logout'),
    path('home/', home, name='home'),

    path('students/', StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', student_detail, name='student_detail'),
    path('user/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('instructors/', InstructorListView.as_view(), name='instructor_list'),
    path('instructors/<int:pk>/', instructor_detail, name='instructor_detail'),
    
    path('course/', CourseListView.as_view(), name='course_list'),
    path('course/<int:course_id>/', CourseDetailView.as_view(), name='course_detail'),
    path('course/<int:course_id>/delete-material/', DeleteMaterialView.as_view(), name='delete_material'),
    path('course/<int:course_id>/delete-module/', DeleteModuleView.as_view(), name='delete_module'),
    path('course/<int:course_id>/delete/', delete_course, name='delete_course'),

    path('course/<int:course_id>/quiz/', QuizDoubtView.as_view(), name='quiz_doubt'),
    path('course/<int:course_id>/quiz/delete/', QuizDoubtView.as_view(), name='admin_delete_quiz'),
    path('course/<int:course_id>/question/delete/', QuizDoubtView.as_view(), name='admin_delete_question'),
    path('course/create/', CourseCreate.as_view(), name='create_course'),

    path('course/category/<int:pk>/', MainCategoryDeleteView.as_view(), name='delete_category'),
    path('course/subcategory/<int:pk>/', SubCategoryDeleteView.as_view(), name='delete_subcategory'),

    path('enrollment/requests/', PendingEnrollmentRequestsView.as_view(), name='enrollment_req'),
    path('enrollment/statistics/', EnrollmentStatisticsView.as_view(), name='enrollment_statistics'),

    path('certificate/templates/', CertificateTemplateListView.as_view(), name='certificate_template_list'),
    path('certificates/', CertificateListView.as_view(), name='certificate_list'),

    path('export/pdf/', export_pdf, name='export_pdf'),
    path('export/instructor_activity/', generate_instructor_activity_report, name='instructor_activity_report'),

    path('export/csv/', export_csv, name='export_csv'),
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),

    
    

]
