# Generated by Django 4.2.7 on 2024-07-27 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_course_is_published'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='difficulty_level',
            field=models.CharField(choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')], max_length=50),
        ),
    ]
