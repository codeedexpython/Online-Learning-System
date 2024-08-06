from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view(), name='student_index'),

    path('register/', StudentRegistrationView.as_view(), name='student_register'),
    path('login/', student_login_view, name='student_login'),
    path('logout/', user_logout, name='logout'),

    path('home/',StudentHomeView.as_view(), name='student_dashboard'),

    path('course/<int:course_id>/', CourseDetailView.as_view(), name='student_course_detail'),
    path('course/enrolled/', EnrolledCoursesListView.as_view(), name='student_enrolled_list'),
    path('course/certificates/', CertificateListView.as_view(), name='student_certificate_list'),
    path('course/<int:course_id>/generate_certificate/', GenerateCertificateView.as_view(), name='generate_certificate'),


    path('profile/update/', ProfileAndPasswordUpdateView.as_view(), name='profile_update'),

    path('password_reset/', CustomPasswordResetView.as_view(), name='student_password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='student_password_reset_done'),
    path('password_reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='student_password_reset_confirm'),
    path('password_reset/complete/', CustomPasswordResetCompleteView.as_view(), name='student_password_reset_complete'),
]