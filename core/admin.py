from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(MainCategory)
admin.site.register(CourseCategory)
admin.site.register(Course)
admin.site.register(CourseModule)
admin.site.register(ModuleMaterialFile)
admin.site.register(EnrollmentRequest)
admin.site.register(CourseEnrollmentLimit)
admin.site.register(CertificateTemplate)
admin.site.register(Certificate)
admin.site.register(QuizAttempt)




